#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks
from gnuradio.filter import pfb
import time
import threading
import math

import channel
from config import rc_config

class receiver(gr.top_block):
	def __init__(self):
		gr.top_block.__init__(self, 'receiver')

		try:
                        gr.enable_realtime_scheduling()
                except:
                        pass

		self.access_lock = threading.RLock()
		self.access_lock.acquire()
	
		config = rc_config()
                self.sources = config.sources
		self.channel_rate = 12500

                for source in self.sources:
			target_size = 1000000
			if(self.sources[source]['samp_rate']%target_size):
				raise Exception('samp_rate not round enough')

			num_channels = int(math.ceil(self.sources[source]['samp_rate']/target_size))
			self.sources[source]['pfb'] = pfb.channelizer_ccf(
	                  num_channels,
	                  (),
	                  1.0,
	                  100
			)
			self.sources[source]['pfb'].set_channel_map(([]))
			for x in range(0,num_channels):
				null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
				self.connect((self.sources[source]['pfb'], x), null_sink)


                        if self.sources[source]['type'] == 'usrp':
				from gnuradio import uhd

                                this_dev = uhd.usrp_source(
                                        device_addr=self.sources[source]['device_addr'],
                                        stream_args=uhd.stream_args(
                                                cpu_format="fc32",
                                                otw_format=self.sources[source]['otw_format'],
                                                args=self.sources[source]['args'],
                                        ),
                                )
                                this_dev.set_samp_rate(self.sources[source]['samp_rate'])
                                this_dev.set_center_freq(self.sources[source]['center_freq'])
                                this_dev.set_gain(self.sources[source]['rf_gain'])

                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect(this_dev, null_sink)

                                self.sources[source]['block'] = this_dev
                        if self.sources[source]['type'] == 'usrp2x':
				from gnuradio import uhd

                                this_dev = uhd.usrp_source(
                                        device_addr=self.sources[source]['device_addr'],
                                        stream_args=uhd.stream_args(
                                                cpu_format="fc32",
                                                otw_format=self.sources[source]['otw_format'],
                                                args=self.sources[source]['args'],
                                                channels=range(2),
                                        ),
                                )

                                this_dev.set_subdev_spec('A:RX1 A:RX2', 0)
                                this_dev.set_samp_rate(self.sources[source]['samp_rate'])

                                this_dev.set_center_freq(self.sources[source]['center_freq'], 0)
                                this_dev.set_center_freq(self.sources[source+1]['center_freq'], 1)
                                this_dev.set_gain(self.sources[source]['rf_gain'], 0)
                                this_dev.set_gain(self.sources[source+1]['rf_gain'], 1)

                                multiply = blocks.multiply_const_vcc((1, ))
                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect((this_dev,0), multiply, null_sink)
                                self.sources[source]['block'] = multiply

                                multiply = blocks.multiply_const_vcc((1, ))
                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect((this_dev,1), multiply, null_sink)
                                self.sources[source+1]['block'] = multiply
                        if self.sources[source]['type'] == 'bladerf':
				import osmosdr

                                this_dev = osmosdr.source( args=self.sources[source]['args'] )
                                this_dev.set_sample_rate(self.sources[source]['samp_rate'])
                                this_dev.set_center_freq(self.sources[source]['center_freq'], 0)
                                this_dev.set_freq_corr(0, 0)
                                this_dev.set_dc_offset_mode(0, 0)
                                this_dev.set_iq_balance_mode(0, 0)
                                this_dev.set_gain_mode(0, 0)
                                this_dev.set_gain(self.sources[source]['rf_gain'], 0)
                                this_dev.set_if_gain(20, 0)
                                this_dev.set_bb_gain(self.sources[source]['bb_gain'], 0)
                                this_dev.set_antenna("", 0)
                                this_dev.set_bandwidth(0, 0)


                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect(this_dev, null_sink)

                                self.sources[source]['block'] = this_dev

			self.connect(self.sources[source]['block'], self.sources[source]['pfb'])
	
		self.channels = []
		#for i in self.sources.keys():
		#	self.channels[i] = []

		self.access_lock.release()
	def connect_channel(self, channel_rate, freq, dest, port):
	
		source_id = None

		for i in self.sources.keys():
			if abs(freq-self.sources[i]['center_freq']) < self.sources[i]['samp_rate']/2:
				source_id = i
				break

		if source_id == None:
			return -1

		source_center_freq = self.sources[source_id]['center_freq']
		source_samp_rate = self.sources[source_id]['samp_rate']
		source = self.sources[source_id]['block']

		offset = freq-source_center_freq

		pfb = self.sources[source_id]['pfb']
		pfb_samp_rate = 1000000
		num_channels = source_samp_rate/pfb_samp_rate
		pfb_id = (freq-source_center_freq) / pfb_samp_rate
		if pfb_id < 0: 
			pfb_id = pfb_id + num_channels
		pfb_offset = ((freq-source_center_freq) % pfb_samp_rate)-(pfb_samp_rate/2)


		#We have all our parameters, lets see if we can re-use an idling channel
		self.access_lock.acquire()

		block = None	

		for c in self.channels:
			if c.source_id == source_id and c.pfb_id == pfb_id and c.in_use == False:
				block = c
				block_id = c.block_id
				block.set_offset(pfb_offset)
				#TODO: move UDP output
				break

		if block == None:
			block = channel.channel(dest, port, channel_rate, pfb_samp_rate, pfb_offset)
			block.source_id = source_id
			block.pfb_id = pfb_id

			self.channels.append(block)
			block_id = len(self.channels)-1
			block.block_id = block_id

			self.lock()
			self.connect((pfb,pfb_id), block)
			self.unlock()

		block.in_use = True
		block.udp.connect(dest, port)

		self.access_lock.release()

		return block.block_id
	def release_channel(self, block_id):
		self.access_lock.acquire()
		try:
			self.channels[block_id].in_use = False
		except:
			self.access_lock.release()
			return -1

		#TODO: move UDP output

		self.access_lock.release()
		return True

if __name__ == '__main__':
	tb = receiver()
	tb.start()
	#print len(tb.channels)
	#tb.wait()
	import socket
	import thread

	def handler(client, addr, tb):
		my_channels = []
		while 1:
			data = client.recv(size)
			print data
			if not data: 
				client.close()
				for x in my_channels:
                                        tb.release_channel(x)
				break
			data = data.strip().split(',')
	                if data[0] == 'create':
				dest = data[1]
				port = int(data[2])
				channel_rate = int(data[3])
				freq = int(data[4])
				
				result = tb.connect_channel(channel_rate, freq, dest, port)

				if result == -1:
					#Channel failed to create, probably freq out of range
					client.send('na,%s\n' % freq)
					print 'failed to create channel %s' % freq
				else:
		                        client.send('create,%s\n' % result) #success
	                        	print 'Created channel ar: %s %s %s %s %s' % (len(tb.channels), channel_rate, freq, dest, port)
					my_channels.append(result)

			elif data[0] == 'release':
				block_id = int(data[1])

				result = tb.release_channel(block_id)
				if result == -1:
                                        #Channel failed to release
                                        client.send('na,%s\n' % block_id)
					print 'failed to release %s' % block_id
                                else:
                                        client.send('release,%s\n' % block_id) #success
					print 'Released channel'
					my_channels.remove(block_id)
			elif data[0] == 'quit':
				client.close()
				for x in my_channels:
					tb.release_channel(x)
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

