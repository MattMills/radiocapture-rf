#!/usr/bin/env python

from gnuradio import gr
from gnuradio import uhd
from gnuradio import blocks
import time

from channel import channel

class receiver(gr.top_block):
	def __init__(self):
		gr.top_block.__init__(self, 'receiver')

		try:
                        gr.enable_realtime_scheduling()
                except:
                        pass

	
		self.samp_rate = 8000000 #samp_rate
		self.channel_rate = 25000

		self.source = source = uhd.usrp_source(device_addr='recv_frame_size=24576,num_recv_frames=512',
				stream_args=uhd.stream_args(
					cpu_format="fc32",
					otw_format="sc16",
					args="",
				),
			)
		source.set_samp_rate(8000000)
		source.set_center_freq(855000000)
		source.set_gain(3)
	
		self.channels = []
		for i in range(0,100):
			block = channel('10.5.0.7', 2000+i, self.channel_rate, self.samp_rate, 12500*i)
			self.channels.append(block)
			self.connect(source, block)

		#def __init__(self, dest, port, channel_rate, samp_rate, offset):

if __name__ == '__main__':
	tb = receiver()
	tb.start()
	#print len(tb.channels)
	#tb.wait()
	import socket
	import thread

	def handler(client, addr, tb):
		while 1:
			data = client.recv(size)
			if not data: 
				client.close()
				break
			data = data.strip().split(',')
	                if data[0] == 'r':
	                        block = channel(data[1], int(data[2]), int(data[3]), tb.samp_rate, int(data[4]))
	                        tb.lock()
	                        tb.connect(tb.source, block)
	                        tb.unlock()
	                        tb.channels.append(block)
	                        client.send('create')
	                        print 'Created channel ar: %s' % (len(tb.channels))
			if data[0] == 'q':
				client.close()
				break

	host = ''
	port = 50000
	backlog = 5
	size = 1024
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((host,port))
	s.listen(backlog)
	while 1:
		client, address = s.accept()
		thread.start_new_thread(handler, (client, address, tb))

