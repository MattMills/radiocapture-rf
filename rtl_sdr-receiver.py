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

#from gnuradio import digital
#from gnuradio import eng_notation
#from gnuradio import filter
from gnuradio import gr
import osmosdr
#from gnuradio.eng_option import eng_option
#from gnuradio.filter import firdes
#from gnuradio.gr import firdes
#from optparse import OptionParser

#import binascii
import time
#import threading


# import custom modules
from moto_control_receiver import moto_control_receiver
from edacs_control_receiver import edacs_control_receiver

from logging_receiver import logging_receiver

class receiver(gr.top_block):

	def __init__(self):
		gr.top_block.__init__(self, "RadioCapture.com receiver")


		#gr.enable_realtime_scheduling()
		##################################################
		# Variables
		##################################################
		self.sources = {
			0:{}, 
			1:{},
			2:{}
		}

		self.packets = 0
		self.packets_bad = 0
		self.symbol_rate = symbol_rate = 3600.0
		self.samp_rate = samp_rate = 2850000
		self.control_source = 0
		
		self.offset = offset = 0

		self.sources[0]['center_freq'] = 867500000
		self.sources[0]['offset'] = -99.5
		self.sources[0]['serial'] = 'rtl=1'

		self.sources[1]['center_freq'] = 855825000
		self.sources[1]['offset'] = -103.5
		self.sources[1]['serial'] = 'rtl=2'

		self.sources[2]['center_freq'] = 858742500
		self.sources[2]['offset'] = -122
		self.sources[2]['serial'] = 'rtl=0'

		self.systems = {0:{}, 1:{}, 2:{}, 3:{}, 4:{}}
		#San Bernadino County 06/7
                self.systems[0]['type'] = 'moto'
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
                                #0x188: 860812500,
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
                self.systems[1]['type'] = 'moto'
                self.systems[1]['id'] = 0x363f
                self.systems[1]['channels'] = {
                                0xfe: 857362500,
                                0x14f: 859387500,
                                0x160: 859812500,
                                #0x189: 860837500,
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
                self.systems[2]['type'] = 'moto'
                self.systems[2]['id'] = 0x262c
                self.systems[2]['channels'] = {
                                #014x: 851500000, #Not valid standard, valid splinter
                                #0x62: 853450000, #Not valid standard, valid splinter
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
                                0x2c9: 868837500#,
                                #0x2cd: 868937500
                }
                # CCCS Countywide
                # FIRST CHANNEL IS out of range
                self.systems[3]['type'] = 'moto'
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
                               0x166: 859962500
                               #0x170: 860212500,
                               #0x17a: 860462500,
                               #0x184: 860712500,
                               #0x18e: 860962500
                       }
                #Riverside EDACS - West site
                self.systems[4]['type'] = 'edacs'
                self.systems[4]['id'] = 1
                self.systems[4]['symbol_rate'] = 9600.0
                self.systems[4]['esk'] = False
                self.systems[4]['channels'] = {
                                1: 866212500,
                                2: 866262500,
                                3: 866712500,
                                4: 866762500,
                                5: 867212500,
                                6: 867712500,
                                7: 868212500,
                                8: 867262500,
                                9: 868262500,
                                10: 868712500,
                                11: 867787500,
                                12: 868787500
                        }
		#del self.systems[3]
                #del self.systems[4]

		##################################################
		# Blocks
		##################################################

		for source in self.sources.keys():
			self.rtlsdr = osmosdr.source_c( args="nchan=" + str(1) + " " + self.sources[source]['serial'] )
        	        self.rtlsdr.set_sample_rate(samp_rate)
                	self.rtlsdr.set_center_freq(self.sources[source]['center_freq'], 0)
	                self.rtlsdr.set_freq_corr(self.sources[source]['offset'], 0)
	                self.rtlsdr.set_gain_mode(0, 0)
	                self.rtlsdr.set_gain(30, 0)
	                self.rtlsdr.set_if_gain(15, 0)

			self.sources[source]['block'] = self.rtlsdr
			null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                	self.connect(self.rtlsdr, null_sink)
		
		self.source = self.sources[0]['block']
		#self.samp_rate = self.rtlsdr.get_sample_rate()
		##################################################
		# Connections
		##################################################
		for system in self.systems:
			if self.systems[system]['type'] == 'moto':
				self.systems[system]['block'] = moto_control_receiver( self.systems[system], self.samp_rate, self.sources, self, system)
			elif self.systems[system]['type'] == 'edacs':
				self.systems[system]['block'] = edacs_control_receiver( self.systems[system], self.samp_rate, self.sources, self)
			else:
				raise Exception('Invalid system type %s' % (self.systems[system]['type']))
			this_block = self.systems[system]['block']
			self.systems[system]['source'] = 0
			self.connect(self.source, this_block)
		
		self.active_receivers = []

	def retune_control(self, system, freq):
		channel = self.systems[system]['block']
		for i in self.sources.keys():
			if(abs(freq-self.sources[i]['center_freq']) < self.samp_rate/2):
				if i == self.systems[system]['source']:
					return i
				else:
					self.lock()
					self.disconnect(self.sources[self.systems[system]['source']]['block'], channel)
					self.connect(self.sources[i]['block'], channel)
					self.systems[system]['source'] = i
					self.unlock()
					return i
		raise Exception('Control Frequency out of range %s' % (freq))

	def connect_channel(self, freq, channel):
		for i in self.sources.keys():
			if(abs(freq-self.sources[i]['center_freq']) < self.samp_rate/2):
				self.lock()
				self.connect(self.sources[i]['block'], channel)
				self.unlock()
				return self.sources[i]['center_freq']
		raise Exception('Frequency out of range %s' % (freq))

if __name__ == '__main__':
####################################################################################################
	
	#parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
	#(options, args) = parser.parse_args()
	if gr.enable_realtime_scheduling() != gr.RT_OK:
		print "Error: failed to enable realtime scheduling."
	tb = receiver()
	tb.start()
	print 'Entering top_block loop'

	while 1:
		for i,receiver in enumerate(tb.active_receivers):
			#receiver = tb.active_receivers[i]
			if receiver.in_use == True and time.time()-receiver.time_activity > 2.5 and receiver.time_activity != 0 and receiver.time_open != 0:
				receiver.close({})
			if receiver.in_use == False and time.time()-receiver.time_last_use > 120:
				tb.lock()
				tb.disconnect(tb.active_receivers[i])
				del tb.active_receivers[i]
				tb.unlock()
		time.sleep(0.1)

