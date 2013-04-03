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
import threading


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
		self.samp_rate = samp_rate = 2400000
		self.control_source = 0
		
		self.offset = offset = 0

		self.sources[0]['center_freq'] = 855050000
		self.sources[0]['offset'] = 44.99 #C
		self.sources[0]['serial'] = 'rtl=2'

		self.sources[1]['center_freq'] = 857450000
		self.sources[1]['offset'] = 12.43 #B
		self.sources[1]['serial'] = 'rtl=1'

		self.sources[2]['center_freq'] = 859850000
		self.sources[2]['offset'] = 23.46 #A
		self.sources[2]['serial'] = 'rtl=0'

		self.systems = {0:{}, 1:{}}

                #Denver Public Safety - EDACS
                self.systems[0]['type'] = 'edacs'
                self.systems[0]['id'] = 1
                self.systems[0]['symbol_rate'] = 9600.0
                self.systems[0]['esk'] = True
                self.systems[0]['channels'] = {
				1: 854987500,
                                2: 855487500,
                                3: 855987500,
                                4: 856487500,
                                5: 857237500,
                                6: 857737500,
                                7: 858487500,
                                8: 859237500,
                                9: 859737500,
                                10: 854437500,
                                11: 855237500,
                                12: 855737500,
                                13: 856237500,
                                14: 856737500,
                                15: 857487500,
                                16: 858237500,
                                17: 858737500,
                                18: 859487500,
                                19: 854062500,
                                20: 854562500
                        }
		#Aurora City - EDACS
		self.systems[1]['type'] = 'edacs'
		self.systems[1]['id'] = 2
		self.systems[1]['symbol_rate'] = 9600.0
		self.systems[1]['esk'] = False
		self.systems[1]['channels'] = {
				1: 856762500,
                                2: 856937500,
                                3: 856962500,
                                4: 856987500,
                                5: 857762500,
                                6: 857937500,
                                7: 857962500,
                                8: 857987500,
                                9: 858762500,
                                10: 858937500,
                                11: 858962500,
                                12: 858987500,
                                13: 859762500,
                                14: 859937500,
                                15: 859962500,
                                16: 859987500,
                                17: 860762500,
                                18: 860937500,
                                19: 860962500,
                                20: 860987500
			}

		#del self.systems[1]

		quality_check = threading.Thread(target=self.quality_check)
                quality_check.daemon = True
                quality_check.start()
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
				self.systems[system]['block'] = edacs_control_receiver( self.systems[system], self.samp_rate, self.sources, self, system)
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
					channel.source_id = i
					return i
		raise Exception('Control Frequency out of range %s' % (freq))

	def connect_channel(self, freq, channel):
		for i in self.sources.keys():
			if(abs(freq-self.sources[i]['center_freq']) < self.samp_rate/2):
				self.lock()
				self.connect(self.sources[i]['block'], channel)
				self.unlock()
				channel.source_id = i
				return self.sources[i]['center_freq']
		raise Exception('Frequency out of range %s' % (freq))
        def quality_check(self):
                while True:
                        time.sleep(10); #only check messages once per 10second
			for i,channel in enumerate(self.active_receivers):
				if channel.in_use == True:
					print "System: %s %s %s" %(i, channel.source_id, channel.probe.level())
			
				

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

