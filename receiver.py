#!/usr/bin/env python
###################################################
#                                                 #
# Radoicapture.com Trunked radio receiver         #
# Developer: Matt Mills (mmills@2bn.net)          #
# Date: 2/21/2013                                 #
#                                                 #
# Copyright 2013 Matt Mills                       #
# All rights reserved                             #
#                                                 #
# Unauthorized use or distribution of this code   #
# is prohibited.                                  #
#                                                 #
###################################################

from gnuradio import gr
from gnuradio import uhd

import time
import threading


# import custom modules
from moto_control_receiver import moto_control_receiver
from edacs_control_receiver import edacs_control_receiver

from logging_receiver import logging_receiver

class receiver(gr.top_block):

	def __init__(self):
		gr.top_block.__init__(self, "RadioCapture.com receiver")

		#Attempt to turn on real time scheduling, not available in GRAS
		try:
			gr.enable_realtime_scheduling()
		except:
			pass
		

		##################################################
		# Variables
		##################################################
		self.sources = {0:{}}#, 1:{}}

		self.packets = 0
		self.packets_bad = 0
		self.samp_rate = samp_rate = 8000000
		self.control_source = 0
		
		self.offset = offset = 0


                #self.sources[0]['center_freq'] = 856150000
                self.sources[0]['center_freq'] = 864700000

                self.systems = {0:{}, 1:{}}

                #San Diego - South Zone (1)
                self.systems[0]['type'] = 'moto'
                self.systems[0]['id'] = 0x470f
                self.systems[0]['channels'] = {
                        0x259: 866037500,
                        0x25d: 866137500,
                        0x268: 866412500,
                        0x269: 866437500,
                        0x271: 866637500,
                        0x27b: 866887500,
                        0x27c: 866912500,
                        0x282: 867062500,
                        0x285: 867137500,
                        0x28f: 867387500,
                        0x290: 867412500,
                        0x298: 867612500,
                        0x299: 867637500,
                        0x2a4: 867912500,
                        #0x: 868075000, #doesnt show up on unitrunker list
                        0x2ad: 868137500,
                        0x2b8: 868412500,
                        0x2b9: 868437500#,
                        #868600000 #this either
                        }
                #San Diego City - Site 1
                self.systems[1]['type'] = 'moto'
                self.systems[1]['id'] = 0x2b2e
                self.systems[1]['channels'] = {
                        0xc9: 856025000,
                        0xca: 856050000,
                        0xcb: 856075000,
                        0xf0: 857000000,
                        0xf1: 857025000,
                        0xf2: 857050000,
                        0x118: 858000000,
                        0x119: 858025000,
                        0x11a: 858050000,
                        0x140: 859000000,
                        0x141: 859025000,
                        0x141: 859050000,
                        0x168: 860000000,
                        0x169: 860025000,
                        0x16a: 860050000,
                        0x1ba: 862050000,
                        0x1bc: 862100000,
                        0x1e2: 863050000,
                        0x20a: 864050000,
                        0x232: 865050000
                }

		del self.systems[1]		

		##################################################
		# Blocks
		##################################################

		self.uhd = uhd.usrp_source(
			#device_addr="",
			device_addr="recv_frame_size=49152,num_recv_frames=512",#fpga=/usr/local/share/uhd/images/usrp_b100_fpga_2rx.bin",
			stream_args=uhd.stream_args(
				cpu_format="fc32",
				#otw_format="sc8",
				#args="peak=0.1",
				#channels=range(2),
			),
		)
#		self.uhd.set_subdev_spec("A:RX1 A:RX2", 0)
		self.uhd.set_samp_rate(samp_rate)
		self.uhd.set_center_freq(self.sources[0]['center_freq'])
#		self.uhd.set_center_freq(self.sources[1]['center_freq'], 1)
		self.uhd.set_gain(0)
#		self.uhd.set_gain(0, 1)

		self.null_sink0 = gr.null_sink(gr.sizeof_gr_complex*1)
#		self.null_sink1 = gr.null_sink(gr.sizeof_gr_complex*1)
		self.connect((self.uhd, 0), self.null_sink0)
#		self.connect((self.uhd, 1), self.null_sink1)
		self.source = self.uhd

		##################################################
		# Connections
		##################################################
		for system in self.systems:
			if self.systems[system]['type'] == 'moto':
				self.systems[system]['block'] = moto_control_receiver( self.systems[system], self.samp_rate, self.sources, self, system)
			elif self.systems[system]['type'] == 'edacs':
				self.systems[system]['block'] = edacs_control_receiver( self.systems[system], self.samp_rate, self.sources, self, system)
			else:
				raise Exception('Invalid system type %s' % (self.systems[system]['type']))
			this_block = self.systems[system]['block']
			self.systems[system]['source'] = 0
			self.connect((self.source,0), (this_block, 0))
		
		self.active_receivers = []
		self.ar_lock = threading.RLock()

	def retune_control(self, system, freq):
		channel = self.systems[system]['block']
		for i in self.sources.keys():
			if(abs(freq-self.sources[i]['center_freq']) < self.samp_rate/2):
				if i == self.systems[system]['source']:
					return i
				else:
					self.lock()
					self.disconnect((self.source, self.systems[system]['source']), channel)
					self.connect((self.source, i), channel)
					self.systems[system]['source'] = i
					self.unlock()
					return i
		raise Exception('Control Frequency out of range %s' % (freq))

	def connect_channel(self, freq, channel):
		for i in self.sources.keys():
			if(abs(freq-self.sources[i]['center_freq']) < self.samp_rate/2):
				self.lock()
				self.connect((self.source, i), channel)
				self.unlock()
				return self.sources[i]['center_freq']
		raise Exception('Frequency out of range %s' % (freq))

if __name__ == '__main__':
####################################################################################################
	
	if gr.enable_realtime_scheduling() != gr.RT_OK:
		print "Error: failed to enable realtime scheduling."
	tb = receiver()
	tb.start()
	print 'Entering top_block loop'

	while 1:
		for i,receiver in enumerate(tb.active_receivers):
			if receiver.in_use == True and time.time()-receiver.time_activity > 2.5 and receiver.time_activity != 0 and receiver.time_open != 0:
				receiver.close({})
#			if receiver.in_use == False and time.time()-receiver.time_last_use > 120:
#				tb.lock()
#				tb.disconnect(tb.active_receivers[i])
#				del tb.active_receivers[i]
#				tb.unlock()
		time.sleep(0.1)

