#!/usr/bin/env python

import json
import threading
import time
import redis
from rtlsdr import librtlsdr
from ctypes import *
import socket
import hashlib

class device_discovery():
        def __init__(self, host=None, port=None):
		
		if(host != None):
			self.host = host
		else:
			self.host = '127.0.0.1' #manually set here until there is a better place
		if(port != None):
			self.port = port
		else:
			self.port = 6379 #manually set here until there is a better place



		self.client = None
		self.continue_running = True
		
		self.demods = {}

		self.init_connection()

		manager_loop = threading.Thread(target=self.manager_loop)
                manager_loop.daemon = True
                manager_loop.start()
	def init_connection(self):
		self.client = redis.StrictRedis(host=self.host, port=self.port, db=0)
	def publish_device(self, device_id, device_detail):
		pipe = self.client.pipeline()
                pipe.set('device_table:%s' % device_id, json.dumps(device_detail))
		#pipe.expire('device_table:%s' % device_id, 300)
                result = pipe.execute()
	def build_device_table_rtlsdr(self):
		def get_serial(device_index):
	            bfr = (c_ubyte * 256)()
	            r = librtlsdr.rtlsdr_get_device_usb_strings(device_index, None, None, bfr)
	            if r != 0:
	                raise IOError(
	                    'Error code %d when reading USB strings (device %d)' % (r, device_index)
	                )
	            return ''.join((chr(b) for b in bfr if b > 0))

	        num_devices = librtlsdr.rtlsdr_get_device_count()
		dongles = []
		hostname = socket.gethostname()
        	for i in range(num_devices):
			dongle = {
				'index': i,
				'serial': get_serial(i),
				'host': hostname,
				'type': 'rtlsdr',
				'last_seen': time.time(),
				}
			dongle['hash'] = hashlib.sha256('%s%s%s%s' % (i, dongle['serial'], dongle['host'], dongle['type'])).hexdigest()
			self.publish_device(dongle['hash'], dongle)
			dongles.append(dongle)
		return dongles
			
	def manager_loop(self):
		print 'manager_loop()'

		while self.continue_running:
			rtlsdr_devices = self.build_device_table_rtlsdr()
	                print 'Device auto detect published, current state (RTLSDR): %s' % rtlsdr_devices
			time.sleep(10)
		
device_discovery = device_discovery()
while True:
	time.sleep(3600)
