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
import math
import logging

from logging_receiver import logging_receiver

class call_recorder():
        def __init__(self, host=None, port=None):
                self.log = logging.getLogger('overseer.call_recorder')
                self.log.info('Initializing call_recorder')
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
		self.outbound_msg_queue = []
	
		self.call_table = {}


                connection_handler = threading.Thread(target=self.connection_handler)
                connection_handler.daemon = True
                connection_handler.start()
		
		send_event_hopeful_thread = threading.Thread(target=self.send_event_hopeful_thread)
                send_event_hopeful_thread.daemon = True
                send_event_hopeful_thread.start()


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
					for subscription in self.subscriptions:
						self.subscribe(subscription, resub=True)
						
                                except:
                                        pass
			else:
				try:
					self.client.beat()
				except:
					pass
                        time.sleep(1)
	def subscribe(self, queue, resub=False):
		#This needs to exist so we can keep track of what subs we have and re-sub on reconnect
		if queue in self.subscriptions and not resub:
			return True #we're already subscribed

		this_uuid = '%s' % uuid.uuid4()
		if(self.connection_issue == True):
			self.subscriptions[queue] = this_uuid
                        return None	
	
		try:
			self.subscriptions[queue] = this_uuid
			self.client.subscribe(queue, {StompSpec.ID_HEADER: this_uuid, StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL, })
		except Exception as e:
			self.log.fatal('%s' % e)
                        raise
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
			self.log.error('%s' % e)
                        self.connection_issue = True

        def send_event_lazy(self, destination, body):
                #If it gets there, then great, if not, well we tried!
                if(self.connection_issue == True):
                        return None

                try:
                        self.client.send(destination, json.dumps(body))
                except:
                        self.connection_issue = True

#		cdr = {
#			'type': 'p25',
#			'call_uuid': call_uuid,
#	                'system_id': system_uuid,
#			'instance_uuid': instance_uuid,
#                        'system_group_local': group_address,
#                        'system_user_local': user_address,
#                        'system_channel_local': channel,
#                        'type': 'group',
#			'frequency': channel_frequency,
#			'channel_bandwidth': channel_bandwidth,
#			'modulation_type': modulation,
#			'slot': slot,
#                        'hang_time': self.hang_time,
#			'time_open': time.time(),
#			'time_activity': time.time(),
#                        }
	def send_event_hopeful(self, destination, body):
		self.outbound_msg_queue.append({'destination': destination, 'body': body})

	def send_event_hopeful_thread(self):

		while self.continue_running:
			time.sleep(0.01)
			if(self.connection_issue == True):
				continue
			while len(self.outbound_msg_queue) > 1 and self.connection_issue == False:
				try:
					item = self.outbound_msg_queue.pop(0)
                	        	self.client.send(item['destination'], json.dumps(item['body']), {'persistent': 'true'})
					
	                	except:
					self.outbound_msg_queue.insert(0,item)
	        	                self.connection_issue = True
			

	def publish_loop(self):
		self.log.info('publish_loop()')
		self.subscribe('/queue/call_management/new_call')
		self.subscribe('/queue/call_management/timeout')
		while self.continue_running:
			if self.connection_issue == False:
				try:
					if not self.client.canRead(0.1):
						continue
		        		frame = self.client.receiveFrame()
				        cdr = json.loads(frame.body)
					
					action = frame.headers['destination'].replace('/queue/call_management/', '')

					if action == 'new_call':
						if time.time()-cdr['time_open'] > 5:
							self.client.ack(frame)
							continue
						if cdr['instance_uuid'] not in self.call_table:
							self.call_table[cdr['instance_uuid']] = {}

						self.call_table[cdr['instance_uuid']][cdr['call_uuid']] = logging_receiver(cdr)
					elif action == 'timeout':
						try:
							self.call_table[cdr['instance_uuid']][cdr['call_uuid']].close({}, self.send_event_hopeful)
							del self.call_table[cdr['instance_uuid']][cdr['call_uuid']]
						except KeyError as e:
							pass
						except:
							raise
							pass
					else:
						raise Exception('Received uncoded action, this isnt possible?')						

				        self.client.ack(frame)
				except Exception as e:
					self.log.fatal('except: %s' % e)
                                        raise
					self.connection_issue = True

if __name__ == '__main__':

	main = call_recorder()
	while True:
		time.sleep(100)
		for t in threading.enumerate():
			main.log.debug('%s' % t)
		
