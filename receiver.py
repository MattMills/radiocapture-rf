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
import copy

# import custom modules
from moto_control_receiver import moto_control_receiver
from edacs_control_receiver import edacs_control_receiver
from scanning_receiver import scanning_receiver
from p25_control_receiver import p25_control_receiver

from logging_receiver import logging_receiver
from config import rc_config
from frontend_connector import frontend_connector

from backend_controller import backend_controller
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
		try:
			self.blacklists = config.blacklists
		except:
			self.blacklists = {}
		self.control_source = 0
		self.freq_offset = 0
                self.systems = config.systems


		self.connector = frontend_connector(config.backend_ip, config.frontend_ip)
	
		##################################################
		# Connections
		##################################################
		self.active_receivers = []

		for system in self.systems:
			self.build_receiver(system)
			self.retune_control(system, random.choice(self.systems[system]['channels'].values()))
		
		self.backend_controller = backend_controller(self)

                offset_correction = threading.Thread(target=self.offset_correction)
                offset_correction.daemon = True
                offset_correction.start()


	def build_receiver(self, system, capture = True):
		if self.systems[system]['type'] == 'moto':
                        self.systems[system]['block'] = moto_control_receiver( self.systems[system], self, system)
                elif self.systems[system]['type'] == 'edacs':
                        self.systems[system]['block'] = edacs_control_receiver( self.systems[system], self, system)
                elif self.systems[system]['type'] == 'scanner':
                        self.systems[system]['block'] = scanning_receiver( self.systems[system], self, system)
                elif self.systems[system]['type'] == 'p25':
                        self.systems[system]['block'] = p25_control_receiver( self.systems[system], self, system)
                else:
                        raise Exception('Invalid system type %s' % (self.systems[system]['type']))

		self.systems[system]['block'].enable_capture = capture
                self.systems[system]['channel_id'] = None
		self.systems[system]['start_time'] = time.time()

                udp_source = blocks.udp_source(gr.sizeof_gr_complex*1, "127.0.0.1", (8123), 147200, True) #Nonsense port gets changed in retune_control
		udp_source.set_min_output_buffer(1280*1024)

		self.lock()
                self.connect(udp_source, self.systems[system]['block'])
		self.unlock()

                self.systems[system]['source'] = udp_source
		self.systems[system]['freq_offset'] = 0
	
	def rebuild_receiver(self, system):
		old_receiver = self.systems[system]['block']
		old_freq = self.systems[system]['block'].control_channel

		self.build_receiver(system, False)
                self.retune_control(system, old_freq)
		
		loop_continue = True
		loop_start = time.time()
		#60s timeout loop to attempt to get control channel lock before becoming authoritative receiver
		print 'System: rebuild loop start'
		while loop_continue:
			if loop_start - time.time() > 60:
				loop_continue = False	
			elif self.systems[system]['block'].is_locked :
				loop_continue = False
			else:
				time.sleep(0.2)
		print 'System: Rebuild loop end'

		old_receiver.enable_capture = False
		self.systems[system]['block'].enable_capture = True
		old_receiver.keep_running = False
			

	def retune_control(self, system, freq):
		self.ar_lock.acquire()
		channel = self.systems[system]['block']
                source = self.systems[system]['source']

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
		source = blocks.udp_source(gr.sizeof_gr_complex*1, "0.0.0.0", self.connector.channel_id_to_port[channel_id], 147200, True)
		source.set_min_output_buffer(1280*1024)
		self.connect(source,channel)
		self.systems[system]['source'] = source
		#source.connect('127.0.0.1', self.connector.channel_id_to_port[channel_id])
		print 'connected %s %s %s %s' % (system, freq, channel.channel_rate, self.connector.channel_id_to_port[channel_id])
		self.unlock()
		self.systems[system]['current_freq'] = freq
		self.systems[system]['freq_offset'] = 0

		self.ar_lock.release()
	def connect_channel(self, freq, channel_rate, controller):
		self.ar_lock.acquire()
                channel_id = self.connector.create_channel(channel_rate, int(freq+self.systems[controller.block_id]['freq_offset']))
                if channel_id == False:
			self.ar_lock.release()
                        raise Exception('Unable to tune audio channel %s' % (freq))

		port = self.connector.channel_id_to_port[channel_id]
		channel = logging_receiver(self, port, controller)
		channel.start()

		channel.channel_id = channel_id
		self.active_receivers.append(channel)
		
                print 'connected %s %s %s' % (freq, channel_rate, self.connector.channel_id_to_port[channel_id])
		self.ar_lock.release()
		return channel
	def offset_correction(self):
		time.sleep(10)
		while True:
			for system in self.systems:
				probe_level = self.systems[system]['block'].probe.level()
				if probe_level > 0.05:
					self.systems[system]['freq_offset'] = self.systems[system]['freq_offset'] + (probe_level*100)
					print 'System: %s %s' % (system, int(self.systems[system]['current_freq']+self.systems[system]['freq_offset']))
					self.ar_lock.acquire()
			                self.systems[system]['block'].control_source = self.retune_control(self.systems[system]['block'].block_id, int(self.systems[system]['current_freq']+self.systems[system]['freq_offset']))
					self.ar_lock.release()
	
			time.sleep(1)
		

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

			if receiver.in_use == True and time.time()-receiver.time_activity > hang_time:
				receiver.close(receiver.controller.patches, False)

			if receiver.in_use == True and time.time()-receiver.time_open > 120:
				cdr = receiver.cdr
				audio_rate = receiver.channel_rate
				receiver.close(receiver.controller.patches, True)
				receiver.open(cdr,audio_rate)
			#if receiver.in_use == False and time.time()-receiver.time_activity > 120:
			#	receiver.destroy()
			if receiver.destroyed == True:
                                tb.active_receivers[i] = None
                                receiver = None
                                del tb.active_receivers[i]
		tb.ar_lock.release()
		time.sleep(0.1)

