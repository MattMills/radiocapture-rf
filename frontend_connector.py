#!/usr/bin/env python

import zmq
import random
import threading
import time
import logging

class frontend_connector():
	def __init__(self, dest='10.5.0.128', host='10.5.0.129', port=50000):
		#temp hack until I have auto-frontend figured out

                self.log = logging.getLogger('overseer.frontend_connector')
	
                self.thread_lock = threading.Lock()
		self.dest = dest

		#self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#self.s.connect((host,port))
                self.log.debug('Initializing Frontend Connector')

		self.context = zmq.Context()
		self.socket = self.context.socket(zmq.REQ)
                self.log.debug('Attempting ZMQ socket connection to tcp://%s:%s' % (host, port))

		self.socket.connect("tcp://%s:%s" % (host, port))
                self.log.debug('Successful ZMQ socket connection to tcp://%s:%s' % (host, port))
		self.my_client_id = None
		self.channel_id = None
		self.current_port = None
	
		self.continue_running = True

                self.log.debug('Sending connect command')
		self.socket.send('connect')
		data = self.socket.recv()

		data = data.split(',')
		self.my_client_id = int(data[1])
                self.log.debug('Received client ID %s' % self.my_client_id)

		connection_handler = threading.Thread(target=self.connection_handler, name='connection_handler')
                connection_handler.daemon = True
                connection_handler.start()
		
	def __exit__(self):
		try:
			self.socket.send('quit,%s' % self.my_client_id)
		except:
			pass

	def set_port(self, port):
                self.log.debug('Setting port to %s' % port)
		self.current_port = port
        def scan_mode_set_freq(self, freq):
                self.log.debug('scan_mode_set_freq(freq = %s)' % freq)
                self.thread_lock.acquire()

                self.socket.send('scan_mode_set_freq,%s' % (freq))
                data = self.socket.recv()

                self.thread_lock.release()
                
                if data == 'success':
                    return True
                else:
                    return False

	def create_channel(self, channel_rate, freq):
		if self.current_port == None:
                        self.log.fatal('create_channel() called before set_port()')
			raise Exception('Port not set')

                self.thread_lock.acquire()
                
                self.log.debug('create_channel(channel_rate = %s, freq = %s)' % (channel_rate, freq))
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
                self.log.debug('release_channel()')
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
	def exit(self):
                self.log.debug('exit() called')
		self.continue_running = False

	def connection_handler(self):
                self.log.debug('connection_handler() init')
		time.sleep(0.1)
		while self.continue_running == True:
			self.thread_lock.acquire()
                        self.log.debug('Sending heartbeat')
			self.socket.send('hb,%s' % self.my_client_id)
			data = self.socket.recv(1024)
			data = data.strip().split(',')
			self.thread_lock.release()
			time.sleep(0.25)
		
		self.thread_lock.acquire()
                self.log.debug('Sending quit command to ZMQ socket')
		self.socket.send('quit,%s' % self.my_client_id)
		self.socket.close()
		self.context.destroy()
		
		self.thread_lock.release()
		self.log.debug('connection_handler() exit')
			

if __name__ == '__main__':
	test = frontend_connector()
	channel_id = test.create_channel(25000, 855000000)
	if channel_id == False:
		raise Exception('test failed: create')
	if test.release_channel(channel_id) == False:
		raise Exception('test failed: release')

	print 'function test pass'

	channels = []
	start = time.time()
	for i in range(0,100):
		channels.append(test.create_channel(25000, 855000000))

	for i in channels:
		test.release_channel(i)
	end = time.time()

	print 'speed test %s' % (end-start)
