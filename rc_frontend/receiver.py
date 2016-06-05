#!/usr/bin/env python

from gnuradio import gr, filter
from gnuradio import blocks
from gnuradio.filter import pfb, firdes
import gnuradio.filter.optfir as optfir

import time
import threading
import math
import os

import channel
import copy
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
	
		self.config = config = rc_config()
                self.realsources = config.sources

		self.sources = {}
		numsources = 0
		for source in self.realsources:
			if config.receiver_split2:
				newsource1 = copy.copy(self.realsources[source])
				newsource2 = copy.copy(self.realsources[source])
	
				decim = 2
				samp_rate = self.realsources[source]['samp_rate']
				channel_rate = (samp_rate/decim)/2
				transition = channel_rate*0.5
				
				taps = firdes.low_pass(1,samp_rate,channel_rate,transition)
				print taps
	
		                filt1 = filter.freq_xlating_fir_filter_ccc(decim, (taps), -samp_rate/4, samp_rate)
				filt2 = filter.freq_xlating_fir_filter_ccc(decim, (taps), samp_rate/4, samp_rate)

                        if self.realsources[source]['type'] == 'usrp':
				from gnuradio import uhd

                                this_dev = uhd.usrp_source(
                                        device_addr=self.realsources[source]['device_addr'],
                                        stream_args=uhd.stream_args(
                                                cpu_format="fc32",
                                                otw_format=self.realsources[source]['otw_format'],
                                                args=self.realsources[source]['args'],
                                        ),
                                )
                                this_dev.set_samp_rate(self.realsources[source]['samp_rate'])
                                this_dev.set_center_freq(self.realsources[source]['center_freq'])
                                this_dev.set_gain(self.realsources[source]['rf_gain'])

                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect(this_dev, null_sink)

                                self.realsources[source]['block'] = this_dev
                        if self.realsources[source]['type'] == 'usrp2x':
				from gnuradio import uhd

                                this_dev = uhd.usrp_source(
                                        device_addr=self.realsources[source]['device_addr'],
                                        stream_args=uhd.stream_args(
                                                cpu_format="fc32",
                                                otw_format=self.realsources[source]['otw_format'],
                                                args=self.realsources[source]['args'],
                                                channels=range(2),
                                        ),
                                )

                                this_dev.set_subdev_spec('A:RX1 A:RX2', 0)
                                this_dev.set_samp_rate(self.realsources[source]['samp_rate'])

                                this_dev.set_center_freq(self.realsources[source]['center_freq'], 0)
                                this_dev.set_center_freq(self.realsources[source+1]['center_freq'], 1)
                                this_dev.set_gain(self.realsources[source]['rf_gain'], 0)
                                this_dev.set_gain(self.realsources[source+1]['rf_gain'], 1)

                                multiply = blocks.multiply_const_vcc((1, ))
                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect((this_dev,0), multiply, null_sink)
                                self.realsources[source]['block'] = multiply

                                multiply = blocks.multiply_const_vcc((1, ))
                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect((this_dev,1), multiply, null_sink)
                                self.realsources[source+1]['block'] = multiply
                        if self.realsources[source]['type'] == 'bladerf':
				import osmosdr

                                this_dev = osmosdr.source( args=self.realsources[source]['args'] )
                                this_dev.set_sample_rate(self.realsources[source]['samp_rate'])
                                this_dev.set_center_freq(self.realsources[source]['center_freq'], 0)
                                this_dev.set_freq_corr(0, 0)
                                #this_dev.set_dc_offset_mode(0, 0)
                                #this_dev.set_iq_balance_mode(0, 0)
                                this_dev.set_gain_mode(0, 0)
                                this_dev.set_gain(self.realsources[source]['rf_gain'], 0)
                                this_dev.set_if_gain(20, 0)
                                this_dev.set_bb_gain(self.realsources[source]['bb_gain'], 0)
                                this_dev.set_antenna("", 0)
                                this_dev.set_bandwidth(0, 0)


                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect(this_dev, null_sink)

                                self.realsources[source]['block'] = this_dev
			if self.realsources[source]['type'] == 'rtlsdr':
				import osmosdr

                                #process = os.popen('CellSearch -i '+ str(self.realsources[source]['serial']) +' -s 739e6 -e 739e6 -b | grep 739M | awk \'{sum+=$10} END { printf("%.10f", sum/NR)}\'')
                                #output = float(process.read())
                                #process.close()
                                #self.realsources[source]['offset'] = (1000000-(output*1000000))
				#self.realsources[source]['offset'] = 0
                                #print 'Measured PPM - Dev#%s: %s' % (source, self.realsources[source]['offset'])

                                this_dev = osmosdr.source( args=self.realsources[source]['args'] )
                                this_dev.set_sample_rate(self.realsources[source]['samp_rate'])
                                this_dev.set_center_freq(self.realsources[source]['center_freq']+self.realsources[source]['offset'], 0)
                                #this_dev.set_freq_corr(self.realsources[source]['offset'], 0)

                                this_dev.set_dc_offset_mode(1, 0)
                                this_dev.set_iq_balance_mode(1, 0)
                                this_dev.set_gain_mode(0, 0)
                                this_dev.set_gain(self.realsources[source]['rf_gain'], 0)
				this_dev.set_if_gain(30, 0)
                                this_dev.set_bb_gain(self.realsources[source]['bb_gain'], 0)


                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                self.connect(this_dev, null_sink)

                                self.realsources[source]['block'] = this_dev
                        if config.receiver_split2:
                                newsource1 = copy.copy(self.realsources[source])
                                newsource2 = copy.copy(self.realsources[source])

                                decim = 2
                                samp_rate = self.realsources[source]['samp_rate']
                                channel_rate = (samp_rate/decim)/2
                                transition = channel_rate*0.5

                                taps = firdes.low_pass(1,samp_rate,channel_rate,transition)
                                print taps

                                filt1 = filter.freq_xlating_fir_filter_ccc(decim, (taps), -samp_rate/4, samp_rate)
                                filt2 = filter.freq_xlating_fir_filter_ccc(decim, (taps), samp_rate/4, samp_rate)

				null_sink1 = blocks.null_sink(gr.sizeof_gr_complex*1)
				null_sink2 = blocks.null_sink(gr.sizeof_gr_complex*1)

				self.connect(self.realsources[source]['block'], filt1, null_sink1)
				self.connect(self.realsources[source]['block'], filt2, null_sink2)
			
				newsource1['block'] = filt1
				newsource1['center_freq'] = self.realsources[source]['center_freq']-self.realsources[source]['samp_rate']/4
				newsource1['samp_rate'] = newsource1['samp_rate']/decim
				newsource2['block'] = filt2
				newsource2['center_freq'] = self.realsources[source]['center_freq']+self.realsources[source]['samp_rate']/4
				newsource2['samp_rate'] = newsource2['samp_rate']/decim
		
				
		
				self.sources[numsources] = newsource1
				numsources = numsources+1
				self.sources[numsources] = newsource2
				numsources = numsources+1
			else:
				self.sources[numsources] = self.realsources[source]
				numsources = numsources+1
		if self.config.frontend_mode == 'pfb':
	                for source in self.sources:
	                        self.target_size = target_size = 400000
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
				self.connect(self.sources[source]['block'], self.sources[source]['pfb'])

		self.channels = []
		#for i in self.sources.keys():
		#	self.channels[i] = []

		self.access_lock.release()
        def connect_channel(self, channel_rate, freq, dest, port):
		if self.config.frontend_mode == 'pfb':
			return self.connect_channel_pfb(channel_rate, freq, dest, port)
		elif self.config.frontend_mode == 'xlat':
			return self.connect_channel_xlat(channel_rate, freq, dest, port)
		else:
			raise Exception('No frontend_mode selected')

	def connect_channel_xlat(self, channel_rate, freq, dest, port):
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

		#We have all our parameters, lets see if we can re-use an idling channel
                self.access_lock.acquire()
		block = None

                for c in self.channels:
                        if c.source_id == source_id and c.in_use == False:
                                block = c
                                block_id = c.block_id
                                block.set_offset(offset)
                                block.udp.disconnect()
                                #TODO: move UDP output
                                break

                if block == None:
                        block = channel.channel(dest, port, channel_rate,(source_samp_rate), offset)
                        block.source_id = source_id

                        self.channels.append(block)
                        block_id = len(self.channels)-1
                        block.block_id = block_id

                        self.lock()
                        self.connect(source, block)

                        #While we're locked to connect this block, look for any idle channels and disco/destroy.
                        for c in self.channels:
                            if c.channel_close_time != 0 and time.time()-c.channel_close_time > 10 and block != c:
                                self.disconnect(source, c)
                                c.destroy()
                                c = None
                                del c
                        self.unlock()

                block.in_use = True
                block.udp.connect(dest, port)

                self.access_lock.release()

                return block.block_id

	def connect_channel_pfb(self, channel_rate, freq, dest, port):
	
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

		

		if pfb_offset < (-1*(pfb_samp_rate/2))+(channel_rate/2) or pfb_offset > (pfb_samp_rate/2)-(channel_rate/2):
			print 'warning: %s edge boundary' % freq
		#We have all our parameters, lets see if we can re-use an idling channel
		self.access_lock.acquire()

		block = None	

		for c in self.channels:
			if c.source_id == source_id and c.pfb_id == pfb_id and c.in_use == False:
				block = c
				block_id = c.block_id
				block.set_offset(pfb_offset)
				block.udp.disconnect()
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
			self.channels[block_id].udp.connect('127.0.0.1', 9999)
			self.channels[block_id].udp.disconnect()
                        self.channel_close_time = time.time()
		except:
			self.access_lock.release()
			raise Exception('Failed to release channel')

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
	client_hb = {}

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
	                       	print '%s Created channel ar: %s %s %s %s %s %s' % ( time.time(), len(tb.channels), channel_rate, freq, dest, port, result)
				clients[c].append(result)
				return 'create,%s' % result
		elif data[0] == 'release':
			try:
				c = int(data[1])
				block_id = int(data[2])
				result = tb.release_channel(block_id)
				
				if result == -1:
	                                #Channel failed to release
					print 'failed to release %s' % block_id
					return 'na,%s\n' % block_id
	                        else:
					print '%s Released channel %s' % ( time.time(), block_id)
					clients[c].remove(block_id)
					return 'release,%s\n'
                        except Exception as e:
				return 'na\n'
		elif data[0] == 'quit':
			c = int(data[1])
			for x in clients[c]:
				tb.release_channel(x)

                        clients[c] = []
                        try:
                            del client_hb[c]
                        except:
                            pass
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
	start_time = time.time()

	while 1:
                deletions = []
                for client in client_hb:
                    if time.time()-client_hb[client] > 1:
                        for x in clients[client]:
                            tb.release_channel(x)
                        clients[client] = []

                        deletions.append(client)
                for c in deletions:
                    del client_hb[c]

		msg = socket.recv()
		resp = handler(msg, tb)
		socket.send(resp)
                #print(tb.channels)
