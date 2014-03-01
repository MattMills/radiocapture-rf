#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks
from gnuradio.filter import pfb
import gnuradio.filter.optfir as optfir

import time
import threading
import math
import os

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

                for source in self.sources:
			self.target_size = target_size = 100000
			if(self.sources[source]['samp_rate']%target_size):
				raise Exception('samp_rate not round enough')

			num_channels = int(math.ceil(self.sources[source]['samp_rate']/target_size))
			self.sources[source]['pfb'] = pfb.channelizer_ccf(
	                  num_channels,
	                  (optfir.low_pass(1,num_channels,0.5, 0.5+0.2, 0.1, 80)),
	                  1.0,
	                  100
			)
			self.sources[source]['pfb'].set_channel_map(([]))
			#null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
			#self.connect((self.sources[source]['pfb'], 0), null_sink)
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
                                #this_dev.set_dc_offset_mode(0, 0)
                                #this_dev.set_iq_balance_mode(0, 0)
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
			if self.sources[source]['type'] == 'rtlsdr':
				import osmosdr

                                process = os.popen('CellSearch -i '+ str(self.sources[source]['serial']) +' -s 739e6 -e 739e6 -b | grep 739M | awk \'{sum+=$10} END { printf("%.10f", sum/NR)}\'')
                                output = float(process.read())
                                process.close()
                                self.sources[source]['offset'] = (1000000-(output*1000000))
                                print 'Measured PPM - Dev#%s: %s' % (source, self.sources[source]['offset'])

                                this_dev = osmosdr.source( args=self.sources[source]['args'] )
                                this_dev.set_sample_rate(self.sources[source]['samp_rate'])
                                this_dev.set_center_freq(self.sources[source]['center_freq'], 0)
                                this_dev.set_freq_corr(self.sources[source]['offset'], 0)

                                this_dev.set_dc_offset_mode(1, 0)
                                this_dev.set_iq_balance_mode(1, 0)
                                this_dev.set_gain_mode(0, 0)
                                this_dev.set_gain(self.sources[source]['rf_gain'], 0)
                                this_dev.set_bb_gain(self.sources[source]['bb_gain'], 0)


                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                self.connect(this_dev, null_sink)

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

		pfb_samp_rate = self.target_size #1000000
		pfb_center_freq = source_center_freq - (pfb_samp_rate/2)

		num_channels = source_samp_rate/pfb_samp_rate

		offset = freq - source_center_freq
		chan = int(round(offset/float(pfb_samp_rate)))
		if chan < 0:
			chan = chan + num_channels

		pfb_offset = offset-(chan*(pfb_samp_rate))

		pfb_id = chan

		if pfb_offset < -40000 or pfb_offset > 40000:
			print 'warning: %s edge boundary' % freq
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
			block = channel.channel(dest, port, channel_rate,(pfb_samp_rate), pfb_offset)
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
	import zmq
	import thread
	import time
	clients = []
	client_hb = []

	def handler(msg, tb):
		global clients
		global client_hb
		#if not data: 
		#	for x in my_channels:
                #       	tb.release_channel(x)
		#	break
		data = msg.strip().split(',')
	        if data[0] == 'create':
			c = int(data[1])
			dest = data[2]
			port = int(data[3])
			channel_rate = int(data[4])
			freq = int(data[5])
			
			result = tb.connect_channel(channel_rate, freq, dest, port)

			if result == -1:
				#Channel failed to create, probably freq out of range
				print 'failed to create channel %s' % freq
				return 'na,%s' % freq
			else:
	                       	print 'Created channel ar: %s %s %s %s %s' % (len(tb.channels), channel_rate, freq, dest, port)
				clients[c].append(result)
				return 'create,%s' % result
		elif data[0] == 'release':
			c = int(data[1])
			block_id = int(data[2])

			result = tb.release_channel(block_id)
			if result == -1:
                                #Channel failed to release
				print 'failed to release %s' % block_id
				return 'na,%s\n' % block_id
                        else:
				print 'Released channel'
				clients[c].remove(block_id)
				return 'release,%s\n' % block_id
		elif data[0] == 'quit':
			c = data[1]
			for x in clients[c]:
				tb.release_channel(x)
			return 'quit,%s' % c
		elif data[0] == 'connect':
			c = len(clients)
			clients.append([])
			return 'connect,%s' % c
		elif data[0] == 'hb':
			c = int(data[1])
			client_hb[c] = time.time()
			return 'hb,%s' % c
			
	context = zmq.Context()
	socket = context.socket(zmq.REP)
	socket.bind("tcp://0.0.0.0:50000")
	
	while 1:
		msg = socket.recv()
		resp = handler(msg, tb)
		socket.send(resp)
