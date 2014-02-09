#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks
import time
import threading

from channel import channel
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
		self.channel_rate = 25000
                for source in self.sources:
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
                                self.connect(this_dev, null_sink)

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
                                self.connect((this_dev,0), multiply, null_sink)
                                self.sources[source]['block'] = multiply

                                multiply = blocks.multiply_const_vcc((1, ))
                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                self.connect((this_dev,1), multiply, null_sink)
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
                                self.connect(this_dev, null_sink)

                                self.sources[source]['block'] = this_dev

	
		self.channels = {}
		for i in self.sources.keys():
			self.channels[i] = []

		self.access_lock.release()
	def connect_channel(self, channel_rate, freq, dest, port):
	
		source_id = None

		for i in self.sources.keys():
			if abs(freq-self.sources[i]['center_freq']) < self.sources[i]['samp_rate']/2:
				source_id = i
				break

		if source_id == None:
			return False

		source_center_freq = self.sources[source_id]['center_freq']
		source_samp_rate = self.sources[source_id]['samp_rate']
		source = self.sources[source_id]['block']

		offset = source_center_freq - freq

		#We have all our parameters, lets see if we can re-use an idling channel
		self.access_lock.acquire()

		block = None	

		for channel in self.channels[source_id]:
			if channel.in_use == False:
				block = channel
				block_id = block_id
				break

		if block == None:
			block = channel(dest, port, channel_rate, source_samp_rate, offset)
			
			self.channels.append(block)
			block_id = len(self.channels)-1
			block.block_id = block_id

			self.lock()
			self.connect(source, block)
			self.unlock()

		block.in_use = True

		self.access_lock.release()

		return block.block_id

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
	                if data[0] == 'create':
				dest = data[1]
				port = int(data[2])
				channel_rate = int(data[3])
				freq = int(data[4])
				
				result = tb.connect_channel(channel_rate, freq, dest, port)

				if result == False:
					#Channel failed to create, probably freq out of range
					client.send('na %s\n' % freq)
				else:
		                        client.send('create %s\n' % result)

	                        print 'Created channel ar: %s' % (len(tb.channels))
			elif data[0] == 'release':
				block_id = int(data[1])
				freq = int(data[2])

				tb.release_channel(freq, block_id)
				print 'Released channel'
			elif data[0] == 'quit':
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

