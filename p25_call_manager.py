#!/usr/bin/env python


from stompest.config import StompConfig
from stompest.sync import Stomp
from stompest.protocol import StompSpec

import json
import threading
import time
import uuid
import sys
import signal

from redis_demod_manager import redis_demod_manager

class p25_call_manager():
        def __init__(self, host=None, port=None):
		self.demod_type = 'p25'

		self.redis_demod_manager = redis_demod_manager(self)


                if(host != None):
                        self.host = host
                else:
                        self.host = '127.0.0.1' #manually set here until there is a better place
                if(port != None):
                        self.port = port
                else:
                        self.port = 61613 #manually set here until there is a better place

                self.client = None
                self.connection_issue = True
		self.continue_running = True
		self.subscriptions = {}


		self.instance_metadata = {}
		

                connection_handler = threading.Thread(target=self.connection_handler)
                connection_handler.daemon = True
                connection_handler.start()

		#time.sleep(0.25)
		publish_loop = threading.Thread(target=self.publish_loop)
		publish_loop.daemon = True
		publish_loop.start()

        def init_connection(self):
                if(self.client != None and self.client.session.state == 'connected'):
                        try:
                                self.client.disconnect()
                        except:
                                pass

                config = StompConfig('tcp://%s:%s' % (self.host, self.port), version=StompSpec.VERSION_1_1, check=True)
                self.client = Stomp(config)
                self.client.connect(heartBeats=(30000, 0), connectTimeout=1, connectedTimeout=1)

        def connection_handler(self):
                #This func will just try to reconnect repeatedly in a thread if we're flagged as having an issue.
                while(True):
                        if(self.connection_issue == True):
                                try:
                                        self.init_connection()
                                        self.connection_issue = False
                                except:
                                        pass
                        time.sleep(1)
	def subscribe(self, queue):
		#This needs to exist so we can keep track of what subs we have and re-sub on reconnect
		if queue in self.subscriptions:
			return True #we're already subscribed

		if(self.connection_issue == True):
                        return None	
	
		this_uuid = '%s' % uuid.uuid4()
		try:
			self.subscriptions[queue] = this_uuid
			self.client.subscribe(queue, {StompSpec.ID_HEADER: this_uuid, StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL, })
		except Exception as e:
			print '%s' % e
			self.connection_issue = True


	def unsubscribe(self, queue):
		if queue not in self.subscriptions:
                        return False #cant unsubscribe, we're not subscribed

                if(self.connection_issue == True):
                        return None

                try:
                        self.client.unsubscribe(self.subscriptions[queue], {StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL})
			del self.subscriptions[queue]
                except Exception as e:
			print '%s' % e
                        self.connection_issue = True

        def send_event_lazy(self, destination, body):
                #If it gets there, then great, if not, well we tried!
                if(self.connection_issue == True):
                        return None

                try:
                        self.client.send(destination, json.dumps(body))
                except:
                        self.connection_issue = True

	def notify_demod_new(self, demod_instance_uuid):
		print 'Notified of new demod %s' % (demod_instance_uuid)
		self.subscribe('/topic/raw_control/%s' % (demod_instance_uuid))

	def notify_demod_expire(self, demod_instance_uuid):
		print 'Notified of expired demod %s' % (demod_instance_uuid)
		self.unsubscribe('/topic/raw_control/%s' % (demod_instance_uuid))

	def call_user_to_group(self, instance, channel, group_address, user_address=0):
		print 'New Call %s %s %s %s' %(instance, channel, group_address, user_address)

	def publish_loop(self):
		print 'publish_loop()'
		print '%s' % self.redis_demod_manager.demods
		while self.continue_running:
			if self.connection_issue == False:
				try:
					if not self.client.canRead(0.1):
						print '-'
						continue
		        		frame = self.client.receiveFrame()
				        t = json.loads(frame.body)
					instance_uuid = frame.headers['destination'].replace('/topic/raw_control/', '')
					instance = self.redis_demod_manager.demods[instance_uuid]

					if instance_uuid not in self.instance_metadata:
                                                        self.instance_metadata[instance_uuid] = {'channel_identifier_table': {}}

					if 'crc' in t and t['crc'] != 0:
						continue #Don't bother trying to work with bad data
						
                                        if t['name'] == 'IDEN_UP_VU':
						try:
	                                               self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                                        'BW': t['BW VU'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset VU'],
                                                        'Type': 'FDMA',
                                                        'Slots': 1,
                                                        }
						except:
							pass
					elif t['name'] == 'IDEN_UP':
						try:
	                                               self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                                        'BW': t['BW'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset'],
                                                        'Type': 'FDMA',
                                                        'Slots': 1,
                                                        }
						except:
							pass
					elif t['name'] == 'IDEN_UP_TDMA':
						try:
	                                                self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                                        'BW': t['BW'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset TDMA'],
                                                        'Type': t['Access Type'],
                                                        'Slots': t['Slots'],
                                                        }
						except:
							pass
					elif t['name'] == 'GRP_V_CH_GRANT' :
						self.call_user_to_group(instance_uuid, t['Channel'], t['Group Address'], t['Source Address'])
					elif t['name'] == 'MOT_PAT_GRP_VOICE_CHAN_GRANT':
						self.call_user_to_group(instance_uuid, t['Channel'], t['Super Group'], t['Source Address'])
					elif(t['name'] == 'GRP_V_CH_GRANT_UPDT':
						self.call_user_to_group(instance_uuid, t['Channel 0'], t['Group Address 0'])
						self.call_user_to_group(instance_uuid, t['Channel 1'], t['Group Address 1'])
					elif(t['name'] == 'MOT_PAT_GRP_VOICE_CHAN_GRANT_UPDT':
                                                self.call_user_to_group(instance_uuid, t['Channel 0'], t['Super Group 0'])
                                                self.call_user_to_group(instance_uuid, t['Channel 1'], t['Super Group 1'])

				        self.client.ack(frame)
				except Exception as e:
					print 'except: %s' % e
					raise
					self.connection_issue = True

if __name__ == '__main__':

	main = p25_call_manager()
	while True:
		time.sleep(1)
