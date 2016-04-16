#!/usr/bin/env python

import zmq
import random
import threading


class frontend_connector():
	def __init__(self, dest='10.5.0.23', host='10.5.0.22', port=50000):
		#temp hack until I have auto-frontend figured out
	
                self.thread_lock = threading.Lock()
		self.dest = dest

		#self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#self.s.connect((host,port))
		context = zmq.Context()
		self.socket = context.socket(zmq.REQ)
		self.socket.connect("tcp://%s:%s" % (host, port))
		self.my_client_id = None
		self.channel_id = None
		self.current_port = None

		self.socket.send('connect')
		data = self.socket.recv()

		data = data.split(',')
		self.my_client_id = int(data[1])
		
	def __exit__(self):
		try:
			#self.s.send('quit')
			#self.s.close()
			self.socket.send('quit,%s' % self.my_client_id)
		except:
			pass

	def set_port(self, port):
		self.current_port = port

	def create_channel(self, channel_rate, freq):
		if self.current_port == None:
			raise Exception('Port not set')

                self.thread_lock.acquire()

		self.socket.send('create,%s,%s,%s,%s,%s' % (self.my_client_id, self.dest, self.current_port, channel_rate, freq))
		data = self.socket.recv()
		data = data.strip().split(',')

		if data[0] == 'na': #failed
                        self.thread_lock.release()
			return False
		elif data[0] == 'create': #succeeded
			channel_id = data[1]
			self.channel_id = channel_id

                        self.thread_lock.release()
			return channel_id
		else:
                        self.thread_lock.release()
			return False
                        
	def release_channel(self):
		if self.current_port == None or self.channel_id == None:
			return False
		#if we dont have a port set, we can't have a channel.

                self.thread_lock.acquire()
		self.socket.send('release,%s,%s' % (self.my_client_id, self.channel_id))
                data = self.socket.recv(1024)
                data = data.strip().split(',')
		
		
                if data[0] == 'na': #failed
                        self.thread_lock.release()
                        return False
                elif data[0] == 'release': #succeeded
                        channel_id = data[1]

			self.channel_id = None
                        self.thread_lock.release()
                        return channel_id
		else:
                        self.thread_lock.release()
			return False

if __name__ == '__main__':
	test = frontend_connector()
	channel_id = test.create_channel(25000, 855000000)
	if channel_id == False:
		raise Exception('test failed: create')
	if test.release_channel(channel_id) == False:
		raise Exception('test failed: release')

	print 'function test pass'

	channels = []
	import time
	start = time.time()
	for i in range(0,100):
		channels.append(test.create_channel(25000, 855000000))

	for i in channels:
		test.release_channel(i)
	end = time.time()

	print 'speed test %s' % (end-start)
