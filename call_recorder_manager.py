#!/usr/bin/env python

import json
import threading
import time
import sys
import math
import logging
import logging.config
import multiprocessing

from redis_demod_manager import redis_demod_manager

from call_recorder import call_recorder

class call_recorder_manager():
        def __init__(self):
                self.log = logging.getLogger('overseer.call_recorder_manager')
                self.log.debug('Initializing call_recorder_manager')

		self.demod_type = 'all'
		self.redis_demod_manager = redis_demod_manager(self)

		self.call_recorders = {}
	def notify_demod_new(self, demod_instance_uuid):
		self.log.info('Notified of new demod %s' % (demod_instance_uuid))
		if demod_instance_uuid not in self.call_recorders:
			cr = multiprocessing.Process(target=self.worker, args=(call_recorder,demod_instance_uuid, ))
			cr.start()
			self.call_recorders[demod_instance_uuid] = call_recorder
	def notify_demod_expire(self, demod_instance_uuid):
		self.log.info('Notified of expired demod %s' % (demod_instance_uuid))
		if demod_instance_uuid in self.call_recorders:
			self.call_recorders[demod_instance_uuid].keep_running = False
			del self.call_recorders[demod_instance_uuid]
	def worker(self, func, *args, **kwargs):
	        new_process = func(*args, **kwargs)
	        while(True):
        	        time.sleep(3600)

if __name__ == '__main__':
	with open('config.logging.json', 'rt') as f:
	    config = json.load(f)

	logging.config.dictConfig(config)

	main = call_recorder_manager()
	while True:
		time.sleep(1)
