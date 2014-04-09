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
import random

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
		
		self.ar_lock = threading.RLock()

		##################################################
		# Variables
		##################################################
		config = rc_config()
		self.sources = config.sources
		self.blacklists = config.blacklists
		self.control_source = 0
                self.systems = config.systems


		self.connector = frontend_connector()
	
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
			self.systems[system]['channel_id'] = None

			udp_source = blocks.udp_source(gr.sizeof_gr_complex*1, "127.0.0.1", (1000+system), 1472, True)
			self.connect(udp_source, this_block)
			self.systems[system]['source'] = udp_source
			self.retune_control(system, random.choice(self.systems[system]['channels'].values()))
		
		self.active_receivers = []

	def retune_control(self, system, freq):
		channel = self.systems[system]['block']
		source = self.systems[system]['source']
	
		self.ar_lock.acquire()

		if(self.systems[system]['channel_id'] != None):
			self.connector.release_channel(self.systems[system]['channel_id'])
		channel_id = self.connector.create_channel(channel.channel_rate, freq)
		if channel_id == False:
			self.ar_lock.release()
			raise Exception('Unable to tune CC %s' % (freq))	
			
	
		self.systems[system]['channel_id'] = channel_id
		self.lock()
		source.disconnect()
		self.disconnect(source,channel)
		source = None
		self.systems[system]['source'] = None
		#del source
		source = blocks.udp_source(gr.sizeof_gr_complex*1, "0.0.0.0", self.connector.channel_id_to_port[channel_id], 1472, True)
		self.connect(source,channel)
		self.systems[system]['source'] = source
		#source.connect('127.0.0.1', self.connector.channel_id_to_port[channel_id])
		print 'connected %s %s %s %s' % (system, freq, channel.channel_rate, self.connector.channel_id_to_port[channel_id])
		self.unlock()

		self.ar_lock.release()
	def connect_channel(self, freq, channel_rate):
		self.ar_lock.acquire()
                channel_id = self.connector.create_channel(channel_rate, freq)
                if channel_id == False:
			self.ar_lock.release()
                        raise Exception('Unable to tune audio channel %s' % (freq))

		port = self.connector.channel_id_to_port[channel_id]
		channel = logging_receiver(port)
		channel.start()

		channel.channel_id = channel_id
		self.active_receivers.append(channel)
		
                print 'connected %s %s %s' % (freq, channel_rate, self.connector.channel_id_to_port[channel_id])
		self.ar_lock.release()
		return channel
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
			#if receiver == None:
			#	continue
			if 'hang_time' in receiver.cdr:
				hang_time = receiver.cdr['hang_time']
			else:
				hang_time = 3.5
			if time.time()-receiver.time_activity > hang_time and receiver.time_activity != 0 and receiver.time_open != 0:
				tb.connector.release_channel(receiver.channel_id)
				receiver.close({})
				#receiver.destroy()

				#tb.active_receivers[i] = None
				#receiver = None
				#del tb.active_receivers[i]
				#continue
			if receiver.in_use == True and receiver.time_open != 0 and time.time()-receiver.time_open > 120:
				try:
					cdr = receiver.cdr
					audio_rate = receiver.audio_rate
					receiver.close({}, emergency=True)
					receiver.open(cdr,audio_rate)
				except:
					pass
			if receiver.destroyed == True:
				#tb.lock()
				#tb.disconnect(tb.active_receivers[i])
				#del tb.active_receivers[i]
				#tb.unlock()
				#receiver.destroy()

                                tb.active_receivers[i] = None
                                receiver = None
                                del tb.active_receivers[i]
		tb.ar_lock.release()
		time.sleep(0.1)

