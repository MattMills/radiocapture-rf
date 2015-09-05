#!/usr/bin/env python

import zmq
import json
import zlib
import time
import threading

class backend_controller(threading.Thread):
        def __init__(self, tb, host='0.0.0.0', port=50002):

		self.tb = tb
                context = zmq.Context()
                self.socket = context.socket(zmq.REP)
                self.socket.bind("tcp://%s:%s" % (host, port))

		threading.Thread.__init__ (self)
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
					resp['data'][system] = self.tb.systems[system]['block'].quality[-1]
				except:
					resp['data'][system] = -1
		elif msg['action'] == 'ALL_GET_STATUS_AVG':
                        resp['data'] = {}

                        for system in self.tb.systems:
                                try:
					l = self.tb.systems[system]['block'].quality
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
		elif msg['action'] == 'RESTART_RECEIVER':
			resp['data'] = {}
			system = int(msg['system'])
			try:
				thread = threading.Thread(target=self.tb.rebuild_receiver, args=(system,))
				thread.setDaemon(1)
				thread.start()
				#self.tb.rebuild_receiver(system)
				resp['data'][system] = 1
			except Exception as e:
				print 'System: %s' % (dir(e))
				print 'System: %s' % (e)
				resp['data'][system] = -1
				raise
			
		else:
			resp['fail'] = True
			resp['data'] = 'UNKNOWN ACTION'

		return resp

	def run(self):

	        while 1:
	                msg = json.loads(zlib.decompress(self.socket.recv()))
	                resp = self.handler(msg)
	                self.socket.send(zlib.compress(json.dumps(resp)))
