#!/usr/bin/env python

import socket
import random


class frontend_connector():
	def __init__(self, dest='127.0.0.1', host='127.0.0.1', port=50000):
	
		self.dest = dest

		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((host,port))

		self.used_ports = []
		self.channel_id_to_port = {}
	def __exit__(self):
		try:
			self.s.send('quit')
			self.s.close()
		except:
			pass

	def create_channel(self, channel_rate, freq):
		while True:
			port = random.randrange(10000,20000)
			if port not in self.used_ports:
				break

		self.s.send('create,%s,%s,%s,%s' % (self.dest, port, channel_rate, freq))
		data = self.s.recv(1024)
		data = data.strip().split(',')

		if data[0] == 'na': #failed
			return False
		elif data[0] == 'create': #succeeded
			channel_id = data[1]
			self.used_ports.append(port)
			self.channel_id_to_port[channel_id] = port

			return channel_id
                        
	def release_channel(self, channel_id):
		self.s.send('release,%s' % (channel_id))
                data = self.s.recv(1024)
                data = data.strip().split(',')
		
		
                if data[0] == 'na': #failed
                        return False
                elif data[0] == 'release': #succeeded
                        channel_id = data[1]

			port = self.channel_id_to_port[channel_id]
			del self.channel_id_to_port[channel_id]

                        self.used_ports.remove(port)

                        return channel_id

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
