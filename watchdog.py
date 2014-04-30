#!/usr/bin/env python

import zmq
import json
import zlib
import time

class watchdog:
        def __init__(self, host='127.0.0.1', port=50002):

                context = zmq.Context()
                self.socket = context.socket(zmq.REQ)
		self.socket.setsockopt(zmq.LINGER, 0)
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
		try:
			self.socket.send(zlib.compress(json.dumps(msg)), zmq.NOBLOCK)
		except:
			return {'data': 'Timeout'}

		loop_continue = True
		loop_start = time.time()
		while loop_continue:
			try:
		                resp = json.loads(zlib.decompress(self.socket.recv(zmq.NOBLOCK)))
			except Exception as e:
				if e.errno == zmq.EAGAIN and time.time() - loop_start < 1:
					pass #continue waiting for data
				else:
					loop_continue = False 
					if resp == None:
						resp = {'data':'Timeout'}

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
		all_status = w.all_get_status()
		all_status_avg = w.all_get_status_avg()
		all_uptime =  w.all_get_uptime()
		
		if all_status == 'Timeout' or all_status_avg == 'Timeout' or all_uptime == 'Timeout':
			print "Host connect timeout"
			break
		else:
			print all_status
			print all_status_avg
			print all_uptime
		time.sleep(10)



