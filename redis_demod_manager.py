#!/usr/bin/env python

import json
import threading
import time
import redis

class redis_demod_manager():
        def __init__(self, parent_call_manager, host=None, port=None):
		
		if(host != None):
			self.host = host
		else:
			self.host = '127.0.0.1' #manually set here until there is a better place
		if(port != None):
			self.port = port
		else:
			self.port = 6379 #manually set here until there is a better place


		self.parent_call_manager = parent_call_manager

		self.client = None
		self.continue_running = True
		
		self.demods = {}

		self.init_connection()

		manager_loop = threading.Thread(target=self.manager_loop)
                manager_loop.daemon = True
                manager_loop.start()
	def init_connection(self):
		self.client = redis.StrictRedis(host=self.host, port=self.port, db=0)
	def publish_call_table(self, instance_uuid, call_table):
		pipe = self.client.pipeline()
                pipe.set('call_table:%s' % instance_uuid, json.dumps(call_table))
		pipe.expire('call_table:%s' % instance_uuid, 300)
                result = pipe.execute()
	def manager_loop(self):
		print 'manager_loop()'
		while self.continue_running:
			demod_type = self.parent_call_manager.demod_type
			
			demods = {}
			for instance_uuid in self.client.smembers('demod:%s' % demod_type):
				demods[instance_uuid] = json.loads(self.client.get(instance_uuid))
			
			deletions = []
			for demod in demods:
				if demod not in self.demods:
					self.parent_call_manager.notify_demod_new(demod)

				timestamp = demods[demod]['timestamp']
				if(timestamp < time.time()-5):
					self.client.srem('demod:%s' % demod_type, demod)
					self.client.delete(demod)
					deletions.append(demod)
		
					self.parent_call_manager.notify_demod_expire(demod)
			
			for deletion in deletions:
				del demods[deletion]

			self.demods = demods

			time.sleep(5)
			
