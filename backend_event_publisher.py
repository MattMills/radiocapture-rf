#!/usr/bin/env python

from stompest.config import StompConfig
from stompest.sync import Stomp
import json
import zlib


class backend_event_publisher():
        def __init__(self):

		self.config = StompConfig('tcp://23.239.220.248:61613')
		self.client = Stomp(self.config)
		self.client.connect()


	def publish_raw_control(self, location_id, system_id, item):
		dest_queue = '/topic/raw/%s/%s' % (location_id, system_id)
		self.client.send(dest_queue, json.dumps(item))

