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
from redis_demod_manager import redis_demod_manager

class p25_metadata_agent():
        def __init__(self, host=None, port=None):
                self.log = logging.getLogger('overseer.p25_metadata_agent')
                self.log.info('Initializing p25_metadata_agent')
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
                self.parameters = {}


		self.hang_time = 0.5
		self.instance_metadata = {}
		self.system_metadata = {}
		

                connection_handler = threading.Thread(target=self.connection_handler)
                connection_handler.daemon = True
                connection_handler.start()

		#time.sleep(0.25)
		publish_loop = threading.Thread(target=self.publish_loop)
		publish_loop.daemon = True
		publish_loop.start()

        def init_connection(self):
                self.log.info('init_connection() (activemq) to tcp://%s/:%s' % (self.host, self.port))
                if(self.client != None and self.client.session.state == 'connected'):
                        try:
                                self.client.disconnect()
                        except:
                                pass

                config = StompConfig('tcp://%s:%s' % (self.host, self.port), version=StompSpec.VERSION_1_1, check=True)
                self.client = Stomp(config)
                self.client.connect(heartBeats=(30000, 0), connectTimeout=1, connectedTimeout=1)

        def connection_handler(self):
                self.log.info('connection_handler() startup')
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
			self.log.fatal('%s' % e)
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
		self.log.info('Notified of new demod %s' % (demod_instance_uuid))
		self.subscribe('/topic/raw_control/%s' % (demod_instance_uuid))

	def notify_demod_expire(self, demod_instance_uuid):
		self.log.info('Notified of expired demod %s' % (demod_instance_uuid))
		self.unsubscribe('/topic/raw_control/%s' % (demod_instance_uuid))

	def get_channel_detail(self, instance, channel):
                chan_ident = (channel & 0xf000)>>12
                chan_number = channel & 0x0fff
                try:
                        base_freq = self.instance_metadata[instance]['channel_identifier_table'][chan_ident]['Base Frequency']
                        chan_spacing = self.instance_metadata[instance]['channel_identifier_table'][chan_ident]['Channel Spacing']/1000
                        slots = self.instance_metadata[instance]['channel_identifier_table'][chan_ident]['Slots']
			modulation = self.instance_metadata[instance]['channel_identifier_table'][chan_ident]['Type']
                except KeyError:
                        return False, False, False, False
                chan_freq = ((chan_number/slots)*chan_spacing)
                slot_number = (chan_number % slots)
                channel_frequency = math.floor((base_freq + chan_freq)*1000000)
                channel_bandwidth = self.instance_metadata[instance]['channel_identifier_table'][chan_ident]['BW']*1000

                return channel_frequency, channel_bandwidth, slot_number, modulation

	def get_system_from_instance(self, instance_uuid):
		try:
			return self.redis_demod_manager.demods[instance_uuid]['system_uuid']
		except:
			return False
        def is_updated(self, instance, parameter, value):
            if instance not in self.parameters:
                self.parameters[instance] = {}
            if parameter not in self.parameters[instance]:
                self.parameters[instance][parameter] = value
                return True
            elif self.parameters[instance][parameter] != value:
                self.parameters[instance][parameter] = value
                return True
            else:
                return False

	def publish_loop(self):
		self.log.info('publish_loop() startup')
		while self.continue_running:
			if self.connection_issue == False:
				try:
					if not self.client.canRead(0.1):
						continue
		        		frame = self.client.receiveFrame()
				        t = json.loads(frame.body)
					instance_uuid = frame.headers['destination'].replace('/topic/raw_control/', '')
					instance = self.redis_demod_manager.demods[instance_uuid]
					#system_uuid = self.get_system_from_instance(instance_uuid)

					if instance_uuid not in self.instance_metadata:
                                                self.instance_metadata[instance_uuid] = {'channel_identifier_table': {}}

					if 'crc' not in t or t['crc'] != 0:
						continue #Don't bother trying to work with bad data
					to_check = []

                                        if t['name'] == 'IDEN_UP_VU':
                                            to_check.append(
                                                {
                                                'parameter': 'FIT-%s' % t['Identifier'],
                                                'value': {
                                                        'BW': t['BW VU'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset VU'],
                                                        'Type': 'FDMA',
                                                        'Slots': 1,
                                                    }
                                                })
                                            self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                                        'BW': t['BW VU'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset VU'],
                                                        'Type': 'FDMA',
                                                        'Slots': 1,
                                                        }
					elif t['name'] == 'IDEN_UP':
                                            to_check.append(
                                                { 
                                                    'parameter': 'FIT-%s' % t['Identifier'],
 	                                            'value': {
                                                        'BW': t['BW'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset'],
                                                        'Type': 'FDMA',
                                                        'Slots': 1,
                                                    }
                                                })
                                            self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                                        'BW': t['BW'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset'],
                                                        'Type': 'FDMA',
                                                        'Slots': 1,
                                                        }
					elif t['name'] == 'IDEN_UP_TDMA':
                                            to_check.append(
                                                {
                                                    'parameter': 'FIT-%s' % t['Identifier'],
	                                            'value': {
                                                        'BW': t['BW'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset TDMA'],
                                                        'Type': t['Access Type'],
                                                        'Slots': t['Slots'],
                                                    }
                                                })
                                            self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                                        'BW': t['BW'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset TDMA'],
                                                        'Type': t['Access Type'],
                                                        'Slots': t['Slots'],
                                                        }

                                        elif t['name'] == 'NET_STS_BCST':
                                                to_check.append({'parameter': 'WACN ID', 'value': hex(int(t['WACN ID']))})
                                                to_check.append({'parameter': 'System ID', 'value': hex(int(t['System ID']))})
                                                to_check.append({'parameter': 'System Service Class', 'value':  t['System Service Class']})
						
                                                frequency, bandwidth, slot_number, modulation = self.get_channel_detail(instance_uuid, t['Channel'])       
						if frequency != False:
 	                                               to_check.append({'parameter': 'Control Channel', 'value': {'frequency': frequency, 'bandwidth': bandwidth}})
                                        elif t['name'] == 'RFSS_STS_BCST':
                                                to_check.append({'parameter': 'Site ID', 'value': t['Site ID']})
                                                to_check.append({'parameter': 'RF Sub-system ID', 'value':  t['RF Sub-system ID']})
                                                to_check.append({'parameter': 'RFSS Network Connection', 'value':  t['A']})
                                        elif t['name'] == 'ADJ_STS_BCST':
						print '%s' % t
                                                pass
                                        for d in to_check:
                                            if self.is_updated(instance_uuid, d['parameter'], d['value']):
                                                print 'Updated! %s %s %s' % (instance_uuid, d['parameter'], d['value'])
						message =	{
									'transmit_site_uuid': self.redis_demod_manager.demods[instance_uuid]['transmit_site_uuid'],
									'receive_site_uuid': self.redis_demod_manager.demods[instance_uuid]['site_uuid'],
									'parameter': d['parameter'],
									'value': d['value'],
								}
							
						self.send_event_lazy('/queue/metadata/site_update', message)

				        self.client.ack(frame)
				except Exception as e:
					self.log.fatal('except: %s' % e)
					raise
					self.connection_issue = True

if __name__ == '__main__':

	main = p25_metadata_agent()
	while True:
		time.sleep(1)
