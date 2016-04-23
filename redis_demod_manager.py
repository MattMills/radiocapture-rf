#!/usr/bin/env python

import json
import threading
import time
import redis

class redis_demod_manager():
        def __init__(self, host=None, port=None, parent_demod_manager):
		
		if(host != None):
			self.host = host
		else:
			self.host = '127.0.0.1' #manually set here until there is a better place
		if(port != None):
			self.port = port
		else:
			self.port = 6379 #manually set here until there is a better place

		if(parent_demod == None):
			raise Exception('parent_demod cannot be null')

		self.parent_demod_manager = parent_demod_manager

		self.client = None
		self.continue_running = True

		self.init_connection()

		manager_loop = threading.Thread(target=self.publish_loop)
                manager_loop.daemon = True
                manager_loop.start()
	def init_connection(self):
		self.client = redis.StrictRedis(host=self.host, port=self.port, db=0)

	def manager_loop(self):
		print 'manager_loop()'
		while self.continue_running:
			demod_type = self.parent_demod_manager.demod_type
			
			demods = {}
			for instance_uuid in self.client.smembers('demod:%s' % demod_type):
				demods[instance_uuid] = json.loads(self.client.get(instance_uuid))
			
			
			for demod in demods:
				timestamp = demods[demod]['timestamp']
				if(timestamp < time.time()-5):
					self.client.srem('demod:%s' % demod_type, demod)
					self.client.del(demod)
					del demods[demod]
			
			self.demods = demods

			time.sleep(5)
			
