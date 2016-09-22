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
        def __init__(self):
                self.log = logging.getLogger('overseer.call_recorder')
                self.log.info('Initializing call_recorder')

                self.client = None
                self.connection_issue = True
		self.continue_running = True
		self.subscriptions = {}
		self.outbound_msg_queue = []
	
		self.call_table = {}

		self.client_activemq = client_activemq(4)
		self.client_activemq2 = client_activemq(4)
		self.client_activemq3 = client_activemq(4)
		self.client_activemq4 = client_activemq(4)
		time.sleep(0.25)

		self.client_activemq.subscribe('/queue/call_management/new_call', self, self.process_new_call.im_func)
		self.client_activemq.subscribe('/queue/call_management/timeout', self, self.process_call_timeout.im_func)
		self.client_activemq2.subscribe('/queue/call_management/new_call', self, self.process_new_call.im_func)
                self.client_activemq2.subscribe('/queue/call_management/timeout', self, self.process_call_timeout.im_func)
		self.client_activemq3.subscribe('/queue/call_management/new_call', self, self.process_new_call.im_func)
                self.client_activemq3.subscribe('/queue/call_management/timeout', self, self.process_call_timeout.im_func)
		self.client_activemq4.subscribe('/queue/call_management/new_call', self, self.process_new_call.im_func)
                self.client_activemq4.subscribe('/queue/call_management/timeout', self, self.process_call_timeout.im_func)

	def process_new_call(self, cdr, headers):
		if time.time()-cdr['time_open'] > 5:
			self.log.info('ignored stale call %s %s'  % (cdr['instance_uuid'], cdr['call_uuid']))
		else:
			self.log.info('Call Open received %s %s' % (cdr['instance_uuid'], cdr['call_uuid']))
			if cdr['instance_uuid'] not in self.call_table:
				self.call_table[cdr['instance_uuid']] = {}
			self.call_table[cdr['instance_uuid']][cdr['call_uuid']] = logging_receiver(cdr, self.client_activemq)
	def process_call_timeout(self, cdr, headers):
		self.log.info('Call Timeout received %s %s' % (cdr['instance_uuid'], cdr['call_uuid']))
		try:
			self.call_table[cdr['instance_uuid']][cdr['call_uuid']].close({})
			del self.call_table[cdr['instance_uuid']][cdr['call_uuid']]
		except KeyError as e:
			pass


if __name__ == '__main__':
	with open('config.logging.json', 'rt') as f:
	    config = json.load(f)

	logging.config.dictConfig(config)

	main = call_recorder()
	while True:
		time.sleep(5)
		for system in main.call_table.keys():
			for call in main.call_table[system].keys():
				try:
					if time.time()-main.call_table[system][call].time_open > 120:
						self.log.error('Call 120s timeout')
						main.call_table[system][call].close()
				except:
					pass
		#time.sleep(100)
		#for t in threading.enumerate():
		#	main.log.info('Thread Debug: %s' % t)
		
