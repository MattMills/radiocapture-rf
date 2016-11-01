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
import logging.config

from logging_receiver import logging_receiver
from client_activemq import client_activemq

class call_recorder():
        def __init__(self, instance_uuid):
                self.log = logging.getLogger('overseer.call_recorder')
                self.log.info('Initializing call_recorder')
		self.instance_uuid = instance_uuid
                self.client = None
                self.connection_issue = True
		self.keep_running = True
		self.subscriptions = {}
		self.outbound_msg_queue = []
	
		self.call_table = {}
		self.call_table_lock = threading.RLock()
		self.outbound_client = client_activemq(1)
		self.client_activemq = client_activemq(4)
		time.sleep(0.25)

		self.client_activemq.subscribe('/queue/call_management/new_call/%s' % instance_uuid, self, self.process_new_call.im_func)
		self.client_activemq.subscribe('/queue/call_management/timeout/%s' % instance_uuid, self, self.process_call_timeout.im_func)
	def process_new_call(self, cdr, headers):
		if time.time()-cdr['time_open'] > 5:
			self.log.info('ignored stale call %s %s'  % (cdr['instance_uuid'], cdr['call_uuid']))
		else:
			self.log.info('Call Open received %s %s' % (cdr['instance_uuid'], cdr['call_uuid']))
			with self.call_table_lock:
				if cdr['instance_uuid'] not in self.call_table:
					self.call_table[cdr['instance_uuid']] = {}
				if cdr['call_uuid'] not in self.call_table[cdr['instance_uuid']]:
					self.call_table[cdr['instance_uuid']][cdr['call_uuid']] = logging_receiver(cdr, self.outbound_client)
	def process_call_timeout(self, cdr, headers):
		self.log.info('Call Timeout received %s %s' % (cdr['instance_uuid'], cdr['call_uuid']))
		try:
			with self.call_table_lock:
				self.call_table[cdr['instance_uuid']][cdr['call_uuid']].close({})
				del self.call_table[cdr['instance_uuid']][cdr['call_uuid']]
		except KeyError as e:
			pass


if __name__ == '__main__':
	with open('config.logging.json', 'rt') as f:
	    config = json.load(f)

	logging.config.dictConfig(config)

	main = call_recorder(instance_uuid)
	while True:
		time.sleep(5)
		#print '%s' % main.call_table
		for system in main.call_table.keys():
			for call in main.call_table[system].keys():
				try:
					print '%s %s %s' % (main.call_table[system][call].destroyed, main.call_table[system][call].protocol,main.call_table[system][call].cdr)
					if time.time()-main.call_table[system][call].cdr['time_open'] > 120:
						with main.call_table_lock:
							main.log.error('Call ht timeout')
							main.call_table[system][call].close({})
							del main.call_table[system][call]
				except KeyError as e:
					pass
				except:
					raise

		#time.sleep(100)
		#for t in threading.enumerate():
		#	main.log.info('Thread Debug: %s' % t)
		
