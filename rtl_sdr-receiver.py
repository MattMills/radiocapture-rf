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

from config import rc_config

class receiver(gr.top_block):

	def __init__(self):
		gr.top_block.__init__(self, "RadioCapture.com receiver")


		#gr.enable_realtime_scheduling()
		##################################################
		# Variables
		##################################################
		config = rc_config()
		self.sources = config.sources
		self.cf = config.center_freq #center_freqs
                self.systems = config.systems
		self.samp_rate = samp_rate = config.samp_rate
		
		self.cf_key = 0

		quality_check = threading.Thread(target=self.quality_check)
                quality_check.daemon = True
		##################################################
		# Blocks
		##################################################
		for source in self.sources.keys():
			process = os.popen('CellSearch -i '+ str(self.sources[source]['serial']) +' -s 739e6 -e 739e6 -b | grep 739M | awk \'{sum+=$10} END { printf("%.10f", sum/NR)}\'')
			output = float(process.read())
			process.close()
			self.sources[source]['offset'] = (1000000-(output*1000000))
			print 'Measured PPM - Dev#%s: %s' % (source, self.sources[source]['offset'])

		self.lock()
		for source in self.sources.keys():
			self.sources[source]['freq_offset'] = 0
			self.rtlsdr = osmosdr.source_c( args="nchan=" + str(1) + " rtl=" + str(self.sources[source]['serial']) )
        	        self.rtlsdr.set_sample_rate(samp_rate)
                	self.rtlsdr.set_center_freq(self.cf[source], 0)
	                self.rtlsdr.set_freq_corr(self.sources[source]['offset'], 0)
	                self.rtlsdr.set_gain_mode(0, 0)
	                self.rtlsdr.set_gain(config.gain, 0)
	                self.rtlsdr.set_if_gain(config.if_gain, 0)

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
		self.ar_lock = threading.RLock()
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
		tb.ar_lock.acquire()
		for i,receiver in enumerate(tb.active_receivers):
			#receiver = tb.active_receivers[i]
			if receiver.in_use == True and time.time()-receiver.time_activity > 2.5 and receiver.time_activity != 0 and receiver.time_open != 0:
				receiver.close({})
			if receiver.in_use == False and time.time()-receiver.time_last_use > 120:
				tb.lock()
				tb.disconnect(tb.active_receivers[i])
				del tb.active_receivers[i]
				tb.unlock()
		tb.ar_lock.release()
		time.sleep(0.1)

