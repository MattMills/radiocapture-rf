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
try:
	import osmosdr
except:
	pass
from gnuradio import blocks

import time
import threading


# import custom modules
from moto_control_receiver import moto_control_receiver
from edacs_control_receiver import edacs_control_receiver
from scanning_receiver import scanning_receiver
from p25_control_receiver import p25_control_receiver

from logging_receiver import logging_receiver
from config import rc_config
from frontend_connector import frontend_connector

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
		config = rc_config()
		self.sources = config.sources
		self.blacklists = config.blacklists
		self.control_source = 0
                self.systems = config.systems


	
		##################################################
		# Connections
		##################################################
		for system in self.systems:
			if self.systems[system]['type'] == 'moto':
				self.systems[system]['block'] = moto_control_receiver( self.systems[system], self.sources[0]['samp_rate'], self.sources, self, system)
			elif self.systems[system]['type'] == 'edacs':
				self.systems[system]['block'] = edacs_control_receiver( self.systems[system], self.sources[0]['samp_rate'], self.sources, self, system)
			elif self.systems[system]['type'] == 'scanner':
                                self.systems[system]['block'] = scanning_receiver( self.systems[system], self.sources[0]['samp_rate'], self.sources, self, system)
			elif self.systems[system]['type'] == 'p25':
                                self.systems[system]['block'] = p25_control_receiver( self.systems[system], self.sources[0]['samp_rate'], self.sources, self, system)
			else:
				raise Exception('Invalid system type %s' % (self.systems[system]['type']))
			this_block = self.systems[system]['block']
			self.systems[system]['source'] = 0
			self.connect(self.sources[0]['block'], this_block)
		
		self.active_receivers = []
		self.ar_lock = threading.RLock()
		self.connector = frontend_connector()

	def retune_control(self, system, freq):
		channel = self.systems[system]['block']
		for i in self.sources.keys():
			if(abs(freq-self.sources[i]['center_freq']) < self.sources[i]['samp_rate']/2):
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
			if(abs(freq-self.sources[i]['center_freq']) < self.sources[i]['samp_rate']/2):
				self.lock()
				self.connect((self.sources[i]['block']), channel)
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
		tb.ar_lock.acquire()
		for i,receiver in enumerate(tb.active_receivers):
			if 'hang_time' in receiver.cdr:
				hang_time = receiver.cdr['hang_time']
			else:
				hang_time = 3.5
			if receiver.in_use == True and time.time()-receiver.time_activity > hang_time and receiver.time_activity != 0 and receiver.time_open != 0:
				receiver.close({})
			if receiver.in_use == True and receiver.time_open != 0 and time.time()-receiver.time_open > 120:
				cdr = receiver.cdr
				audio_rate = receiver.audio_rate
				receiver.close({})
				receiver.open(cdr,audio_rate)
		#	if receiver.in_use == False and time.time()-receiver.time_last_use > 120:
		#		tb.lock()
		#		tb.disconnect(tb.active_receivers[i])
		#		del tb.active_receivers[i]
		#		tb.unlock()
		tb.ar_lock.release()
		time.sleep(0.1)

