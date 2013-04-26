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
import osmosdr

import time
import threading
import os


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
			2:{},
			3:{},
			4:{},
			5:{},
			6:{}
		}

		self.packets = 0
		self.packets_bad = 0
		self.symbol_rate = symbol_rate = 3600.0
		self.samp_rate = samp_rate = 2400000
		self.control_source = 0
		
		self.offset = offset = 0

		self.cf_key = 0
		self.cf = {} #center_freqs
		self.cf[0] = 855050000
		self.cf[1] = 857450000
		self.cf[2] = 859850000
		self.cf[3] = 852200000
		self.cf[4] = 853850000
		self.cf[5] = 844850000

		self.sources[0]['serial'] = '0'
		self.sources[1]['serial'] = '1'
		self.sources[2]['serial'] = '2'
		self.sources[3]['serial'] = '3'
                self.sources[4]['serial'] = '4'
                self.sources[5]['serial'] = '5'
                self.sources[6]['serial'] = '6'
		#del self.sources[3]
		#del self.sources[4]
		del self.sources[5]
		del self.sources[6]

		self.systems = {0:{}, 1:{}, 2:{}}

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

		#DIA - EDACS
		#self.systems[2]['type'] = 'edacs'
		#self.systems[2]['id'] = 3
		#self.systems[2]['symbol_rate'] = 9600.0
		#self.systems[2]['esk'] = False
		#self.systems[2]['channels'] = {
		#		1: 855212500,
		#		2: 855712500,
		#		3: 856462500,
		#		4: 857212500,
		#		5: 857712500,
		#		6: 851362500,
		#		7: 851662500,
		#		8: 851937500,
		#		9: 852537500,
		#		10: 852837500,
		#		11: 856437500,
		#		12: 857437500,
		#		13: 858437500,
		#		14: 859437500,
		#		15: 857637500
		#	}

		#del self.systems[2]
		self.systems[2]['type'] = 'edacs'
                self.systems[2]['id'] = 4
                self.systems[2]['symbol_rate'] = 9600.0
                self.systems[2]['esk'] = False
                self.systems[2]['channels'] = {
			1: 851062500,
			2: 851762500,
			3: 852062500,
			4: 852325000,
			5: 853925000,
			6: 851312500,
			7: 852162500,
			8: 852887500,
			9: 853350000,
			10: 853650000
			}
		quality_check = threading.Thread(target=self.quality_check)
                quality_check.daemon = True
		##################################################
		# Blocks
		##################################################
		for source in self.sources.keys():
			process = os.popen('CellSearch -i '+ self.sources[source]['serial'] +' -s 739e6 -e 739e6 -b | grep 739M | awk \'{sum+=$10} END { printf("%.10f", sum/NR)}\'')
			output = float(process.read())
			process.close()
			self.sources[source]['offset'] = (1000000-(output*1000000))
			print 'Measured PPM - Dev#%s: %s' % (source, self.sources[source]['offset'])

		self.lock()
		for source in self.sources.keys():
			self.sources[source]['freq_offset'] = 0
			self.rtlsdr = osmosdr.source_c( args="nchan=" + str(1) + " rtl=" + self.sources[source]['serial'] )
        	        self.rtlsdr.set_sample_rate(samp_rate)
                	self.rtlsdr.set_center_freq(self.cf[source], 0)
	                self.rtlsdr.set_freq_corr(self.sources[source]['offset'], 0)
	                self.rtlsdr.set_gain_mode(0, 0)
	                self.rtlsdr.set_gain(46, 0)
	                self.rtlsdr.set_if_gain(15, 0)

			self.sources[source]['block'] = self.rtlsdr
			self.sources[source]['center_freq'] = self.cf[source] #default CF
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
		self.unlock()
		quality_check.start()
	def cycle_tuners(self):
		self.cf_key = self.cf_key+1
		self.lock()
		for i in self.sources.keys():
			old_cf = (self.cf_key-1+i)%self.cf_key.count()
			new_cf = (self.cf_key+i)%self.cf_key.count()
			for x in self.systems.keys():
				if self.systems[x]['source'] == i:
					self.disconnect(self.sources[i]['block'], self.systems[x]['block'])
					#self.connect(

		self.unlock()
			
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
                        time.sleep(5); #only check messages once per 10second
			for i in self.systems.keys():
				source_id = self.systems[i]['source']

				if self.systems[i]['block'].is_locked == True:
					self.sources[source_id]['freq_offset'] = self.sources[source_id]['freq_offset'] + (200*self.systems[i]['block'].probe.level())
					print "System: %s %s %s %s" % (source_id, self.systems[i]['id'], self.systems[i]['block'].probe.level(), self.sources[source_id]['freq_offset'])
					self.sources[source_id]['block'].set_center_freq(self.sources[source_id]['center_freq']+self.sources[source_id]['freq_offset'], 0)
			
				

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

