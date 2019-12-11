#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

from stompest.config import StompConfig
from stompest.sync import Stomp
from stompest.protocol import StompSpec
import json
import zlib
import threading
import time
from config import rc_config

class backend_event_publisher():
        def __init__(self, host=None, port=None):
		
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

                connection_handler = threading.Thread(target=self.connection_handler)
                connection_handler.daemon = True
                connection_handler.start()

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
				except:
					pass
			time.sleep(1)
	
	def send_event_lazy(self, destination, body):
		#If it gets there, then great, if not, well we tried!
		if(self.connection_issue == True):
			return None

		try:
			self.client.send(destination, json.dumps(body), {'persistent': 'false'})
		except:
			self.connection_issue = True

	def publish_raw_control(self, instance_uuid, system_type, item):
		item['system_type'] = system_type

		self.send_event_lazy('/topic/raw_control/%s' % (instance_uuid), item)

	def publish_call(self, location_id, system_id, system_type, group_local, user_local, channel_local, call_type):
		item = {
			'system_type': system_type, 
			'group_local': group_local, 
			'user_local': user_local, 
			'channel_local': channel_local, 
			'call_type': call_type
			}

		self.send_event_lazy('/topic/call/%s/%s' % (location_id, system_id), item)

