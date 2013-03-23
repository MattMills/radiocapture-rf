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
		self.sources = {0:{}}

		self.packets = 0
		self.packets_bad = 0
		self.symbol_rate = symbol_rate = 3600.0
		self.samp_rate = samp_rate = 2000000
		self.control_source = 0
		
		self.offset = offset = 0

		self.sources[0]['center_freq'] = 502000000

		self.systems = {0:{}}
                #Bucks County Moto - Site 2 - South
                self.systems[0]['type'] = 'moto'
                self.systems[0]['id'] = 0x710b
                self.systems[0]['channels'] = {
                                0x17c: 501037500,
                                0x182: 501187500,
                                0x183: 501212500,
                                0x184: 501237500,
                                0x185: 501262500,
				0x18b: 501412500,
				0x192: 501587500,
				0x195: 501662500,
				0x199: 501762500
                }

		##################################################
		# Blocks
		##################################################

		self.rtlsdr = osmosdr.source_c( args="nchan=" + str(1) + " " + "rtl=0" )
                self.rtlsdr.set_sample_rate(samp_rate)
                self.rtlsdr.set_center_freq(self.sources[0]['center_freq'], 0)
                self.rtlsdr.set_freq_corr(-111, 0)
                self.rtlsdr.set_gain_mode(0, 0)
                self.rtlsdr.set_gain(30, 0)
                self.rtlsdr.set_if_gain(15, 0)

		self.source = self.rtlsdr
		self.samp_rate = self.rtlsdr.get_sample_rate()
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

