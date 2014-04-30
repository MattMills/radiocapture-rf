#!/usr/bin/env python

import zmq
import json
import zlib
import time

class watchdog:
        def __init__(self, host='127.0.0.1', port=50002):

                context = zmq.Context()
                self.socket = context.socket(zmq.REQ)
                self.socket.connect("tcp://%s:%s" % (host, port))

		#threading.Thread.__init__ (self, **kwds)
		#self.setDaemon(1)
		#self.start()

	def handler(self, msg):

		if msg['action'] == 'ALL_GET_STATUS':
			resp['data'] = {}

			for system in self.tb.systems:
				try:
					resp['data'][system] = self.tb.systems[system]['block']['quality'][-1]
				except:
					resp['data'][system] = -1
		elif msg['action'] == 'ALL_GET_STATUS_AVG':
                        resp['data'] = {}

                        for system in self.tb.systems:
                                try:
					l = self.tb.systems[system]['block']['quality']
                                        resp['data'][system] = reduce(lambda x, y: x + y, l) / len(l)
                                except:
                                        resp['data'][system] = -1
		elif msg['action'] == 'ALL_GET_UPTIME':
                        resp['data'] = {}

                        for system in self.tb.systems:
                                try:
					start = self.tb.systems[system]['start_time']
                                        resp['data'][system] = time.time()-start
                                except:
                                        resp['data'][system] = -1
		else:
			resp['fail'] = True
			resp['data'] = 'UNKNOWN ACTION'

		return resp

	def send_message(self, msg):
		self.socket.send(zlib.compress(json.dumps(msg)))
                resp = json.loads(zlib.decompress(self.socket.recv()))

		return resp
	def all_get_status(self):
		return self.send_message({'action': 'ALL_GET_STATUS'})['data']
	def all_get_status_avg(self):
		return self.send_message({'action': 'ALL_GET_STATUS_AVG'})['data']
	def all_get_uptime(self):
		return self.send_message({'action': 'ALL_GET_UPTIME'})['data']
if __name__ == '__main__':
	w = watchdog()
	
	while 1:
		print w.all_get_status()
		print w.all_get_status_avg()
		print w.all_get_uptime()
		time.sleep(10)



