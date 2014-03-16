#!/usr/bin/env python

import zmq
import json
import zlib
import time

class receiver_controller(threading.Thread):
        def __init__(self, tb, host='*', port=50002):

		self.tb = tb
                context = zmq.Context()
                self.socket = context.socket(zmq.REP)
                self.socket.connect("tcp://%s:%s" % (host, port))

		threading.Thread.__init__ (self, **kwds)
		self.setDaemon(1)
		self.start()

	def handler(self, msg):
		resp = {
				'action': msg['action'], 
				'fail': False
			}

		if msg['action'] == 'ALL_GET_STATUS':
			resp['data'] = {}

			for system in self.tb.systems:
				try:
					resp['data'][system] = self.tb.systems[system][quality][-1]
				except:
					resp['data'][system] = -1
		elif msg['action'] == 'ALL_GET_STATUS_AVG':
                        resp['data'] = {}

                        for system in self.tb.systems:
                                try:
					l = self.tb.systems[system][quality]
                                        resp['data'][system] = reduce(lambda x, y: x + y, l) / len(l)
                                except:
                                        resp['data'][system] = -1
		elif msg['action'] == 'ALL_GET_UPTIME':
                        resp['data'] = {}

                        for system in self.tb.systems:
                                try:
					start = self.tb.systems[system][start_time]
                                        resp['data'][system] = time.time()-start
                                except:
                                        resp['data'][system] = -1
		else:
			resp['fail'] = True
			resp['data'] = 'UNKNOWN ACTION'

		return resp

	def run(self):
	        while 1:
			
	                msg = json.loads(zlib.decompress(socket.recv()))
	                resp = self.handler(msg)
	                self.socket.send(zlib.compress(json.dumps(resp)))
