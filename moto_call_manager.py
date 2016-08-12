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

class moto_call_manager():
        def __init__(self, host=None, port=None):
                self.log = logging.getLogger('overseer.moto_call_manager')
                self.log.info('Initializing moto_call_manager')
		self.demod_type = 'moto'

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


		self.hang_time = 1.0
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

	def get_system_from_instance(self, instance_uuid):
		try:
			return self.redis_demod_manager.demods[instance_uuid]['system_uuid']
		except:
			return False

	def call_user_to_group(self, instance_uuid, frequency, group_address, user_address=0, digital=False):
		system_uuid = self.get_system_from_instance(instance_uuid)
		if system_uuid == False:
			return False

		sct = self.system_metadata[system_uuid]['call_table']
		ict = self.instance_metadata[instance_uuid]['call_table']

		for call in ict:
			if ict[call]['system_channel_local'] == frequency and ict[call]['system_group_local'] == group_address and (user_address == 0 or ict[call]['system_user_local'] == user_address):
				ict[call]['time_activity'] = time.time()
				return True
					
			
		#Not a continuation, new call
		call_uuid = None
		for call in sct:
			if sct[call]['system_group_local'] == group_address and (user_address == 0 or sct[call]['system_user_local'] == user_address) and time.time() - sct[call]['time_open'] < 1:
				call_uuid = sct[call]['call_uuid']
				break

		if call_uuid == None:
			#call is new systemwide, assign new UUID
			call_uuid = '%s' % uuid.uuid4()
		instance = self.redis_demod_manager.demods[instance_uuid]	
		cdr = {
			'call_uuid': call_uuid,
	                'system_id': system_uuid,
			'transmit_site_uuid': instance['transmit_site_uuid'],
			'instance_uuid': instance_uuid,
                        'system_group_local': group_address,
                        'system_user_local': user_address,
                        'system_channel_local': frequency,
                        'type': 'group',
			'frequency': frequency,
			'channel_bandwidth': 12500,
			'modulation_type': '%s' % ('p25' if digital == True else 'analog'),
                        'hang_time': self.hang_time,
			'time_open': time.time(),
			'time_activity': time.time(),
                        }

		ict[call_uuid] = cdr
		if call_uuid not in sct:
			sct[call_uuid] = cdr
			sct[call_uuid]['instances'] = {instance_uuid: True}
		else:
			sct[call_uuid]['instances'][instance_uuid] = True
			
		

		#event call open to record subsys
		self.send_event_lazy('/queue/call_management/new_call', cdr)
		self.redis_demod_manager.publish_call_table(instance_uuid, ict)
		self.log.info('OPEN: %s %s %s %s' % (cdr['instance_uuid'], cdr['call_uuid'], cdr['system_group_local'], cdr['system_user_local']) )

	def publish_loop(self):
		self.log.info('publish_loop()')
		while self.continue_running:
			for instance in self.instance_metadata:
				ict = self.instance_metadata[instance]['call_table']
				system_uuid = self.get_system_from_instance(instance)
				if system_uuid == False:
					continue
				sct = self.system_metadata[system_uuid]['call_table']

				closed_calls = []
				for call_uuid in ict:
					if time.time()-ict[call_uuid]['time_activity'] > ict[call_uuid]['hang_time']:
						closed_calls.append(call_uuid)
						#event call close to record subsys on call specific queue
						self.send_event_lazy('/queue/call_management/timeout', {'call_uuid': call_uuid, 'instance_uuid': instance})						

						self.log.info('%s CLOSE: %s' % (time.time(), ict[call_uuid]))
				for call_uuid in closed_calls:
					del ict[call_uuid]
					del sct[call_uuid]['instances'][instance]
					if len(sct[call_uuid]['instances']) == 0:
						del sct[call_uuid]
				if len(closed_calls) > 0:
					self.redis_demod_manager.publish_call_table(instance, ict)
					


			if self.connection_issue == False:
				try:
					if not self.client.canRead(0.1):
						continue
		        		frame = self.client.receiveFrame()
				        t = json.loads(frame.body)
					instance_uuid = frame.headers['destination'].replace('/topic/raw_control/', '')
					instance = self.redis_demod_manager.demods[instance_uuid]
					system_uuid = self.get_system_from_instance(instance_uuid)

					if instance_uuid not in self.instance_metadata:
                                                self.instance_metadata[instance_uuid] = {'channel_identifier_table': {}, 'patches': {}, 'call_table': {}}

					if system_uuid not in self.system_metadata:
						self.system_metadata[system_uuid] = {'call_table': {}}

					#if 'crc' in t and t['crc'] != 0:
					#	continue #Don't bother trying to work with bad data
						
                                        if t['type'] == 'IDEN_UP_VU' and t['crc'] == 0:
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
					elif t['type'] == 'IDEN_UP' and t['crc'] == 0:
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
					elif t['type'] == 'IDEN_UP_TDMA' and t['crc'] == 0:
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
					elif t['type'] == 'Analog Call' :
						#{u'lid': u'0x510', u'status': 0, u'cmd': u'0x18c', u'sys': 15143, u'frequency': 860912500, u'system_type': u'moto', u'dual': True, u'ind': u'I', u'tg': 1296, u'type': u'Analog Call', u'user_local': 20974}
						#{u'lid': u'0x5f0', u'status': 0, u'cmd': u'0x188', u'sys': 15143, u'frequency': 860812500, u'system_type': u'moto', u'dual': False, u'ind': u'I', u'tg': 1520, u'type': u'Call Continuation', u'user_local': 0}
						self.log.debug('ANALOG CALL %s %s %s %s' % (instance_uuid, t['frequency'], t['tg'], t['user_local']))
						self.call_user_to_group(instance_uuid, t['frequency'], t['tg'], t['user_local'])
					elif t['type'] == 'Digital Call':
						self.log.debug('DIGITAL CALL %s %s %s %s' % (instance_uuid, t['frequency'], t['tg'], t['user_local']))
                                                self.call_user_to_group(instance_uuid, t['frequency'], t['tg'], t['user_local'], digital=True)
					elif t['type'] == 'Call Continuation':
						self.log.debug('Call Continuation %s %s %s %s' % (instance_uuid, t['frequency'], t['tg'], t['user_local']))
                                                self.call_user_to_group(instance_uuid, t['frequency'], t['tg'], t['user_local'])
				        self.client.ack(frame)
				except Exception as e:
					self.log.fatal('except: %s' % e)
					self.connection_issue = True

if __name__ == '__main__':

	main = moto_call_manager()
	while True:
		time.sleep(1)
