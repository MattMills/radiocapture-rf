#!/usr/bin/env python

import zmq
import random
import threading
import time
import logging

class frontend_connector():
	def __init__(self, dest='127.0.0.1', host='127.0.0.1', port=50000):
		#temp hack until I have auto-frontend figured out

                self.log = logging.getLogger('overseer.frontend_connector')
	
                self.thread_lock = threading.Lock()
                self.send_lock = threading.Lock()
		self.dest = dest

		#self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#self.s.connect((host,port))
                self.log.debug('Initializing Frontend Connector')

		self.continue_running = True
		self.host = host
		self.port = port
                self.channel_port = 0
		
		self.connection_init()
		self.connect()

		connection_handler = threading.Thread(target=self.connection_handler, name='connection_handler')
                connection_handler.daemon = True
                connection_handler.start()
	def connection_init(self):
		self.context = zmq.Context()
                self.socket = self.context.socket(zmq.REQ)
                self.socket.setsockopt(zmq.RCVTIMEO, 1000) 
                self.socket.setsockopt(zmq.LINGER, 0)
                self.log.info('Attempting ZMQ socket connection to tcp://%s:%s' % (self.host, self.port))
                
                self.socket.connect("tcp://%s:%s" % (self.host, self.port))
                self.log.info('Successful ZMQ socket connection to tcp://%s:%s' % (self.host, self.port))
                self.my_client_id = None
                self.channel_id = None
                self.channel_port = 0
	def connection_teardown(self):
            try:
		self.socket.close()
            except: 
                pass
            try:
                self.context.term()
            except:
                pass
            try:
		self.context.destroy()
            except: 
                pass

        def send(self, data):
            tries = 0
            while tries < 5:
                try:
                    with self.send_lock:
                        self.socket.send(data)
                        response = self.socket.recv()
                        response = response.split(',')
                        return response
                except Exception as e:
                    self.log.error('Exception in frontend_connector.send(): %s %s' % (type(e), e))
                    tries += 1

            return None

	def connect(self):
		self.log.debug('Sending connect command')
                data = self.send('connect')

                if data == None:
                        return None
                self.my_client_id = int(data[1])
                self.log.debug('Received client ID %s' % self.my_client_id)
	def __exit__(self):
		try:
			aself.send('quit,%s' % self.my_client_id)
		except:
			pass

	def set_port(self, port):
                self.log.debug('Setting port to %s' % port)
		self.current_port = port
        def scan_mode_set_freq(self, freq):
                self.log.debug('scan_mode_set_freq(freq = %s)' % freq)
                with self.thread_lock:
                    data = self.send('scan_mode_set_freq,%s' % (freq))

                
                if data == 'success':
                    return True
                else:
                    return False

	def create_channel(self, channel_rate, freq):
                self.thread_lock.acquire()
                
                self.log.debug('create_channel(channel_rate = %s, freq = %s)' % (channel_rate, freq))
		data = self.send('create,%s,%s,%s' % (self.my_client_id, channel_rate, freq))

		if data == None or data[0] == 'na': #failed
                        self.thread_lock.release()
			self.log.error('Failed to create channel')
			return False, False
		elif data[0] == 'create': #succeeded
			channel_id = data[1]
			port = data[2]
			self.channel_port = port
			self.channel_id = channel_id

                        self.thread_lock.release()
			return channel_id, port
		else:
                        self.thread_lock.release()
			return False, False
                        
	def release_channel(self):
		self.thread_lock.acquire()
		if self.channel_id == None:
			self.thread_lock.release()
			return False
		#if we dont have a port set, we can't have a channel.

                self.log.debug('release_channel()')
		data = self.send('release,%s,%s' % (self.my_client_id, self.channel_id))
		
		
                if data == None or  data[0] == 'na': #failed
			self.log.error('Failed to release channel, probably leaking channels')
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
	def report_offset(self, offset):
		self.thread_lock.acquire()
		if self.channel_id == None:
			self.thread_lock.release()
			return False #We're not running, cant change offset
		self.log.debug('report_offset(%s)' % offset)
		data = self.send('offset,%s,%s,%s' % (self.my_client_id, self.channel_id, offset))

		if data == None or data[0] == 'na': #failed
                        self.log.error('Failed to set offset')
                        self.thread_lock.release()
                        return False
		elif data[0] == 'offset': #success
			self.thread_lock.release()
			return True
	def exit(self):
                self.log.debug('exit() called')
		self.continue_running = False

	def connection_handler(self):
                self.log.debug('connection_handler() init')
		time.sleep(0.1)
		while self.continue_running == True:
			self.thread_lock.acquire()
                        self.log.debug('Sending heartbeat')
			try:
				data = self.send('hb,%s' % self.my_client_id)

				if data == None or data[0] == 'fail':
                                        self.log.error('Failed to heartbeat')
					self.connection_teardown()
					self.connection_init()
					self.connect()
			except Exception as e:
				self.log.error('Failed to heartbeat: %s' % e)
				self.connection_teardown()
                                self.connection_init()
                                self.connect()
			self.thread_lock.release()
			time.sleep(0.25)
		
		self.thread_lock.acquire()
                self.log.debug('Sending quit command to ZMQ socket')
		self.send('quit,%s' % self.my_client_id)
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
