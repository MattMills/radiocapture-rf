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


class client_activemq():
        def __init__(self):
                self.log = logging.getLogger('client_activemq')
                self.log.debug('Initializing client_activemq')

                self.host = '127.0.0.1' #manually set here until there is a better place
                self.port = 61613 #manually set here until there is a better place

                self.client = None
                self.connection_issue = True
		self.continue_running = True
		self.subscriptions = {}
		self.outbound_msg_queue = []
		self.outbound_msg_queue_lazy = []

		self.lock = threading.Lock()

                connection_handler = threading.Thread(target=self.connection_handler)
                connection_handler.daemon = True
                connection_handler.start()
		
		send_event_hopeful_thread = threading.Thread(target=self.send_event_hopeful_thread)
                send_event_hopeful_thread.daemon = True
                send_event_hopeful_thread.start()
	
		send_event_lazy_thread = threading.Thread(target=self.send_event_lazy_thread)
                send_event_lazy_thread.daemon = True
                send_event_lazy_thread.start()


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
				self.lock.acquire()
                                try:
                                        self.init_connection()
                                        self.connection_issue = False
					for subscription in self.subscriptions:
						self.log.info('Re-subscribing upon reconnection: %s' % subscription)
						self.subscribe(subscription, self.subscriptions[subscription]['callback_class'], self.subscriptions[subscription]['callback'], resub=True)
						
                                except Exception as e:
					self.log.critical('Except: %s' % e)
                                        pass
				finally:
					self.lock.release()
			else:
				
				try:
					self.client.beat()
				except:
					pass
                        time.sleep(1)
	def subscribe(self, queue, callback_class, callback, resub=False):
		#This needs to exist so we can keep track of what subs we have and re-sub on reconnect
		if queue in self.subscriptions and not resub:
			self.log.info('Ignoring existing subscription %s' % queue)
			return True #we're already subscribed

		this_uuid = '%s' % uuid.uuid4()
		self.log.info('Attempting to acquire lock')
		self.lock.acquire()
		self.log.info('Lock Acquired')
		if(self.connection_issue == True):
			self.log.info('Cannot process subscription request as were not properly connected')
			self.subscriptions[queue] = {'uuid': this_uuid, 'callback': callback, 'callback_class': callback_class}
			self.lock.release()
                        return None
		self.log.info('subscribe(%s %s %s %s)' %( queue, callback_class, callback, resub))
	
		try:
			self.subscriptions[queue] = {'uuid': this_uuid, 'callback': callback, 'callback_class': callback_class}
			self.client.subscribe(queue, {StompSpec.ID_HEADER: this_uuid, StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL, })
		except Exception as e:
			self.log.fatal('%s' % e)
			self.connection_issue = True
		finally:
			self.lock.release()

	def unsubscribe(self, queue):
		if queue not in self.subscriptions:
                        return False #cant unsubscribe, we're not subscribed

		self.lock.acquire()

                if(self.connection_issue == True):
			del self.subscriptions[queue]
			self.lock.release()
                        return None
                try:
                        self.client.unsubscribe(self.subscriptions[queue]['uuid'])
			del self.subscriptions[queue]
                except Exception as e:
			self.log.error('%s' % e)
                        self.connection_issue = True
		finally:
			self.lock.release()
        def send_event_lazy(self, destination, body, persistent = True):
		self.outbound_msg_queue_lazy.append({'destination': destination, 'body': body, 'persistent': persistent})

	def send_event_lazy_thread(self):
		while self.continue_running:
			time.sleep(0.01)
	                #If it gets there, then great, if not, well we tried!
        	        if(self.connection_issue == True):
                	        continue
			while len(self.outbound_msg_queue_lazy) > 1 and self.connection_issue == False:
	        	        try:
					item = self.outbound_msg_queue_lazy.pop(0)
					if item['persistent'] == True:
						persist = 'true'
					else:
						persist = 'false'
					
	                	        self.client.send(item['destination'], json.dumps(item['body']), {'persistent': persist} )
		                except Exception as e:
					self.log.critical('Except: %s' % e)
					self.outbound_msg_queue_lazy.insert(0,item)
        		                self.connection_issue = True

	def send_event_hopeful(self, destination, body, persist):
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
					
	                	except Exception as e:
					self.log.critical('Except: %s' % e)
					self.outbound_msg_queue.insert(0,item)
	        	                self.connection_issue = True
			

	def publish_loop(self):
		self.log.debug('publish_loop() init')
		while self.continue_running:
			if self.connection_issue == False:
				try:
					if not self.client.canRead(0.1):
						continue
					try:
			        		frame = self.client.receiveFrame()
					        data = json.loads(frame.body)
						queue = frame.headers['destination']

						self.subscriptions[queue]['callback'](self.subscriptions[queue]['callback_class'], data, frame.headers)
					        self.client.ack(frame)
					except Exception as e:
						self.log.critical('Except: %s' % e)
						self.client.nack(frame)
				except Exception as e:
					self.log.fatal('except: %s' % e)
					self.connection_issue = True

		
