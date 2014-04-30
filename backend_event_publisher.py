#!/usr/bin/env python

import zmq
import json
import zlib


class receiver_publisher():
        def __init__(self, host='*', port=50001):

                context = zmq.Context()
                self.socket = context.socket(zmq.PUB)
                self.socket.connect("tcp://%s:%s" % (host, port))

		self.obq = []

	def detail(self, system_id, item):
		
		self.socket.send("%s %s" % (system_id, zlib.compress(json.dumps(item))))
