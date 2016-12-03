#!/usr/bin/env python

from gnuradio import gr, filter
from gnuradio import blocks
from gnuradio.filter import pfb, firdes
import gnuradio.filter.optfir as optfir

import time
import threading
import math
import os
import random
import json
import logging
import logging.config

import channel
import copy
from config import rc_config

class receiver(gr.top_block):
	def __init__(self):
		gr.top_block.__init__(self, 'receiver')

		self.log = logging.getLogger('frontend')

		try:
                        gr.enable_realtime_scheduling()
                except:
                        pass

		self.access_lock = threading.RLock()
		self.access_lock.acquire()

	
		self.config = config = rc_config()

                try:
                    self.scan_mode = config.scan_mode
                except:
                    self.scan_mode = False

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
                                this_dev.set_gain_mode(False, 0)
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

		self.channels = {}
		#for i in self.sources.keys():
		#	self.channels[i] = []

		self.start()
		self.access_lock.release()
        def connect_channel(self, channel_rate, freq):

		if self.config.frontend_mode == 'pfb':
			return self.connect_channel_pfb(channel_rate, freq)
		elif self.config.frontend_mode == 'xlat':
			return self.connect_channel_xlat(channel_rate, freq)
		else:
			raise Exception('No frontend_mode selected')

	def connect_channel_xlat(self, channel_rate, freq):
		source_id = None
		source_distance = None

                if self.scan_mode == False:
                    for i in self.sources.keys():
                        if abs(freq-self.sources[i]['center_freq']) < self.sources[i]['samp_rate']/2:
				if source_distance == None or abs(freq-self.sources[i]['center_freq']) < source_distance:
	                                source_id = i
					source_distance = abs(freq-self.sources[i]['center_freq'])
    
                    if source_id == None:
                    	raise Exception('Unable to find source for frequency %s' % freq)
                else:
                    source_id = 0
		
		source_center_freq = self.sources[source_id]['center_freq']
                source_samp_rate = self.sources[source_id]['samp_rate']
                source = self.sources[source_id]['block']

		offset = freq-source_center_freq
                if freq < 10000000:
                   offset = freq #scan mode, relative freq 

		#We have all our parameters, lets see if we can re-use an idling channel
                self.access_lock.acquire()
		block = None

                for c in self.channels.keys():
                        if self.channels[c].source_id == source_id and self.channels[c].channel_rate == channel_rate and self.channels[c].in_use == False:
                                block = self.channels[c]
                                block_id = block.block_id
				port = block.port
                                block.set_offset(offset)
                                #TODO: move UDP output
                                break

                if block == None:
			for x in range(0, 3):
                                port = random.randint(10000,60000)
                                try:
                                        block = channel.channel(port, channel_rate,(source_samp_rate), offset)
                                except RuntimeError as err:
                                        self.log.error('Failed to build channel on port: %s attempt: %s' % (port, x))
                                        return False, False

                        block.source_id = source_id

                        self.channels[port] = block
                        block_id = port
                        block.block_id = block_id

                        self.lock()
                        self.connect(source, block)

                        #While we're locked to connect this block, look for any idle channels and disco/destroy.
                        for c in self.channels.keys():
                            if self.channels[c].channel_close_time != 0 and time.time()-self.channels[c].channel_close_time > 10 and block != self.channels[c]:
				print 'disconnecting channel'
                                self.disconnect(self.sources[self.channels[c].source_id]['block'], self.channels[c])
                                self.channels[c].destroy()
                                del self.channels[c]
			time.sleep(0.001)
                        self.unlock()

                block.in_use = True

                self.access_lock.release()
                return block.block_id, port

	def connect_channel_pfb(self, channel_rate, freq):
	
		source_id = None

                if self.scan_mode == False:
                    for i in self.sources.keys():
			if abs(freq-self.sources[i]['center_freq']) < self.sources[i]['samp_rate']/2:
				source_id = i
				break

		    if source_id == None:
			raise Exception('Unable to find source for frequency %s' % freq)

		source_center_freq = self.sources[source_id]['center_freq']
		source_samp_rate = self.sources[source_id]['samp_rate']
		source = self.sources[source_id]['block']

		offset = freq-source_center_freq

                if freq < 10000000:
                    offset = freq #scan mode, relative freq

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
			self.log.warning('warning: %s edge boundary' % freq)
		#We have all our parameters, lets see if we can re-use an idling channel
		self.access_lock.acquire()

		block = None	

		for c in self.channels.keys():
			if self.channels[c].source_id == source_id and self.channels[c].pfb_id == pfb_id and self.channels[c].in_use == False:
				block = self.channels[c]
				block_id = self.channels[c].block_id
				block.set_offset(pfb_offset)
				#TODO: move UDP output
				break

		if block == None:
			for x in range(0, 3):
				port = random.randint(10000,60000)
				try:
					block = channel.channel(port, channel_rate,(pfb_samp_rate), pfb_offset)
				except RuntimeError as err:
					self.log.error('Failed to build channel on port: %s attempt: %s' % (port, x))
					pass

			block.source_id = source_id
			block.pfb_id = pfb_id

			self.channels[port] = block
			block_id = port
			block.block_id = block_id

			self.lock()
			self.connect((pfb,pfb_id), block)
			self.unlock()

		block.in_use = True

		self.access_lock.release()

		return block.block_id, port
	def release_channel(self, block_id):
		self.access_lock.acquire()
		try:
			self.channels[block_id].in_use = False
                        self.channels[block_id].channel_close_time = time.time()
		except KeyError as e:
			pass #Since this is called during HB and quit I think it might cause problems
		except:
			self.access_lock.release()
			raise
			raise Exception('Failed to release channel')

		#TODO: move UDP output
		
		self.access_lock.release()
		return True
	def source_offset(self, block_id, offset):
		return 
		if self.scan_mode:
			return False
		try:
			center_freq = self.sources[self.channels[block_id].source_id]['center_freq']
			base_offset = self.sources[self.channels[block_id].source_id]['offset']
		except:
			return False
		if offset > 1 or offset < -1:
			hz_offset = offset*50
		elif offset > 0.5 or offset < -0.5:
			hz_offset = offset*10
		else:
			hz_offset = offset*4
		if hz_offset < 5 and hz_offset > -5:
			return True
		new_center_freq = center_freq+hz_offset
		self.log.info('Source %s New Center freq %s %s' % (self.channels[block_id].source_id, new_center_freq, offset))
		self.access_lock.acquire()
		self.sources[self.channels[block_id].source_id]['block'].set_center_freq(new_center_freq+base_offset,0)
		self.sources[self.channels[block_id].source_id]['center_freq'] = new_center_freq
		self.access_lock.release()
		return True

if __name__ == '__main__':
	with open('config.logging.json', 'rt') as f:
	    config = json.load(f)

	logging.config.dictConfig(config)
	log = logging.getLogger('frontend')


	tb = receiver()
	#print len(tb.channels)
	#tb.wait()
	import zmq
	import thread
	import time
	clients = {}
	client_hb = {}
	client_num = 0

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
			channel_rate = int(data[2])
			freq = int(data[3])
			try:
				block_id, port = tb.connect_channel(channel_rate, freq)
			except Exception as e:
				block_id = -1
				log.error('Exception: %s' % e)

			if block_id == -1 or block_id == False:
				#Channel failed to create, probably freq out of range
				log.error('failed to create channel %s' % freq)
				return 'na,%s' % freq
			else:
	                       	log.info('%s Created channel ar: %s %s %s %s %s' % ( time.time(), len(tb.channels), channel_rate, freq, port, block_id))
				try:
					clients[c].append(block_id)
				except KeyError as e:
					pass
				except Exception as e:
					print clients
					raise
					log.error('Exception in channel creation %s' % e)
					tb.release_channel(block_id)
					return 'na,%s' % freq
				return 'create,%s,%s' % (block_id, port)
		elif data[0] ==  'release':
			try:
				c = int(data[1])
				block_id = int(data[2])
				result = tb.release_channel(block_id)
				
				if result == -1:
	                                #Channel failed to release
					log.error('failed to release %s' % block_id)
					return 'na,%s\n' % block_id
	                        else:
					log.info('%s Released channel %s' % ( time.time(), block_id))
					try:
						clients[c].remove(block_id)
					except ValueError as e:
						pass
					return 'release,%s\n'
                        except Exception as e:
				return 'na\n'
                elif data[0] == 'scan_mode_set_freq':
                    freq = int(data[1])
                    try:
                        log.info('attempting to set center freq to %s' % freq)
                        if 'offset' in tb.realsources[0]:
                            tb.realsources[0]['block'].set_center_freq(freq+tb.realsources[0]['offset'], 0)
                        else:
                            tb.realsources[0]['block'].set_center_freq(freq, 0)
                        log.info('success set center freq')
                        return 'success'
                    except:
                        raise
                        return 'fail'

		elif data[0] == 'quit':
			c = int(data[1])
			log.info('quit received from client %s' % c)
			try:
				for x in clients[c]:
					tb.release_channel(x)
			except:
				pass

                        try:
                            del client_hb[c]
			except:
			    pass
			try:
			    clients[c] = []
			    del clients[c]
                        except:
                            pass
			return 'quit,%s' % c
		elif data[0] == 'connect':
			global client_num
			c = client_num
			client_num = client_num + 1
			clients[c] = []
			log.info('connect received from %s' % c)
			return 'connect,%s' % c
		elif data[0] == 'hb':
			c = int(data[1])
			client_hb[c] = time.time()
			return 'hb,%s' % c
		elif data[0] == 'offset':
			client_id = int(data[1])
			block_id = int(data[2])
			offset = float(data[3])
	
			tb.source_offset(block_id, offset)
			
			return 'offset,%s' % client_id

	context = zmq.Context()
	socket = context.socket(zmq.REP)
	socket.bind("tcp://0.0.0.0:50000")
	start_time = time.time()

	while 1:
                deletions = []
                for client in client_hb:
			try:
        	            if time.time()-client_hb[client] > 5:
				log.warning('Client heartbeat timeout %s' % client)
                	        for x in clients[client]:
                        	    tb.release_channel(x)
	                        clients[client] = []

	                        deletions.append(client)
			except:
				raise
				pass
                for c in deletions:
                    del client_hb[c]
		    del clients[c]

		msg = socket.recv()
		resp = handler(msg, tb)
		socket.send(resp)
                #print(tb.channels)
