#!/usr/bin/env python

from stompest.config import StompConfig
from stompest.sync import Stomp
import json
import zlib


class backend_event_publisher():
        def __init__(self):

		self.config = StompConfig('tcp://10.5.1.138:61613')
		self.client = Stomp(self.config)
		self.client.connect()


	def publish_raw_control(self, location_id, system_id, system_type, item):
		item['system_type'] = system_type
		dest_queue = '/topic/raw/%s/%s' % (location_id, system_id)
		self.client.send(dest_queue, json.dumps(item))
	def publish_call(self, location_id, system_id, system_type, group_local, user_local, channel_local, call_type):
                dest_queue = '/topic/call/%s/%s' % (location_id, system_id)

		item = {'system_type': system_type, 'group_local': group_local, 'user_local': user_local, 'channel_local': channel_local, 'call_type': call_type}
                self.client.send(dest_queue, json.dumps(item))

