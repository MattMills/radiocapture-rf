#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Moto Smartzone Test1
# Generated: Thu Oct  4 23:49:39 2012
##################################################

from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.gr import firdes
from optparse import OptionParser

import binascii
#import baz
import time
import threading

from logging_receiver import logging_receiver
from control_receiver import moto_control_receiver

class moto_smartzone_test1(gr.top_block):

	def __init__(self):
		gr.top_block.__init__(self, "Moto Smartzone Test1")

		##################################################
		# Variables
		##################################################
		self.sources = {0:{}, 1:{}}

		self.packets = 0
		self.packets_bad = 0
		self.symbol_rate = symbol_rate = 3600.0
		self.samp_rate = samp_rate = 8000000
		self.control_source = 0
		
		self.offset = offset = 0

		self.sources[0]['center_freq'] = 857400000
		self.sources[1]['center_freq'] = 865000000

		self.systems = {0:{}, 1:{}, 2:{}, 3:{}}
		
		#San Bernadino County 06/07
		self.systems[0]['id'] = 0x3c33
		self.systems[0]['channels'] = {
				0x99: 854837500,
				0xa7: 855187500,
				0xb0: 855412500,
				0xb1: 855437500,
				0xb7: 855587500,
				0xb8: 855612500,
				0xba: 855662500,
				0xc2: 855862500,
				0xe8: 856812500,
				0x110: 857812500,
				0x161: 859837500,
				0x188: 860812500,
				0x265: 866337500,
				0x267: 866387500,
				0x270: 866612500,
				0x279: 866837500,
				0x27b: 866887500,
				0x286: 867162500,
				0x28e: 867362500,
				0x290: 867412500,
				0x299: 867637500,
				0x29b: 867687500,
				0x2a3: 867887500,
				0x2ae: 868162500,
				0x2b5: 868337500,
				0x2b7: 868387500,
				0x2c0: 868612500,
				0x2c2: 868662500

			}
		#San Bernadino County 08
		self.systems[1]['id'] = 0x363f
		self.systems[1]['channels'] = {
				0xfe: 857362500,
                                0x14f: 859387500,
                                0x160: 859812500,
                                0x189: 860837500,
                                0x25f: 866187500,
                                0x273: 866687500,
                                0x284: 867112500,
                                0x28d: 867337500,
                                0x2a1: 867837500,
                                0x2ac: 868112500,
                                0x2c3: 868687500,
                                0x2cc: 868912500
		}

		#San Bernadino County 09
		#First channel is OUT OF RANGE
                self.systems[2]['id'] = 0x262c
                self.systems[2]['channels'] = {
                                #014x: 851500000, #Not valid standard, valid splinter
                                0x62: 853450000, #Not valid standard, valid splinter
                                0xd9: 856425000, #Not Valid standard, valid splinter
                                0x25d: 866137500,
                                0x25e: 866162500,
                                0x266: 866362500,
                                0x271: 866637500,
                                0x27a: 866862500,
                                0x27c: 866912500,
                                0x285: 867137500,
                                0x28f: 867387500,
                                0x298: 867612500,
                                0x29a: 867662500,
                                0x2a2: 867862500,
                                0x2a4: 867912500,
                                0x2ad: 868137500,
                                0x2af: 868187500,
                                0x2b6: 868362500,
                                0x2b8: 868412500,
                                0x2c1: 868637500,
                                0x2c9: 868837500,
                                0x2cd: 868937500
		}
		# CCCS Countywide
		# FIRST CHANNEL IS out of range
		self.systems[3]['id'] = 0x6c3f
                self.systems[3]['channels'] = {
				#0x??: 851062500,
                               0xbc:  855712500,
                               0xd0:  856212500,
                               0xda:  856462500,
                               0xe4:  856712500,
                               0xee:  856962500,
                               0xf8:  857212500,
                               0x102: 857462500,
                               0x10c: 857712500,
                               0x116: 857962500,
                               0x120: 858212500,
                               0x12a: 858462500,
                               0x134: 858712500,
                               0x13e: 858962500,
                               0x148: 859212500,
                               0x152: 859462500,
                               0x15c: 859712500,
                               0x166: 859962500,
                               0x170: 860212500,
                               0x17a: 860462500,
                               0x184: 860712500,
                               0x18e: 860962500
                       }

		##################################################
		# Blocks
		##################################################

		self.source = uhd.usrp_source(
			#device_addr="",
			device_addr="recv_frame_size=16384,num_recv_frames=32",
			stream_args=uhd.stream_args(
				cpu_format="fc32",
				otw_format="sc8",
				#args="peak=0.1",
				channels=range(2),
			),
		)
		self.source.set_subdev_spec("A:RX1 A:RX2", 0)
		self.source.set_samp_rate(samp_rate)
		self.source.set_center_freq(self.sources[0]['center_freq'], 0)
		self.source.set_center_freq(self.sources[1]['center_freq'], 1)
		print self.source.get_center_freq(0)
		print self.source.get_center_freq(1)
		self.source.set_gain(0, 0)
		self.source.set_gain(0, 1)

	
		##################################################
		# Connections
		##################################################
		for system in self.systems:
			self.systems[system]['block'] = moto_control_receiver( self.systems[system], self.samp_rate, self.sources, self)
			this_block = self.systems[system]['block']
			self.connect((self.source,0), (this_block, 0))
			self.connect((self.source,1), (this_block, 1))
		
		self.active_receivers = []

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
	
	parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
	(options, args) = parser.parse_args()
	if gr.enable_realtime_scheduling() != gr.RT_OK:
		print "Error: failed to enable realtime scheduling."
	tb = moto_smartzone_test1()
	tb.start()
	print 'Entering top_block loop'

	while 1:
		for receiver in tb.active_receivers:
			if receiver.in_use == True and time.time()-receiver.time_activity > 1 and receiver.time_activity != 0 and receiver.time_open != 0:
				receiver.close()
		time.sleep(0.1)

