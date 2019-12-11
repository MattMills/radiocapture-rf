#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

from gnuradio import filter, analog
from gnuradio import gr
from gnuradio import blocks
from gnuradio.filter import firdes

import time
import threading

from logging_receiver import logging_receiver

class scanning_receiver(gr.hier_block2):

	def __init__(self, system, top_block, block_id):

                gr.hier_block2.__init__(self, "scanning_receiver",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
                                gr.io_signature(0, 0, 0)) # Output signature

		##################################################
		# Variables
		##################################################

		self.hang_time = 0.5
		self.channel_rate = 12500

		self.tb = top_block
		self.block_id = block_id
		self.system = system
		print self.system
		self.system_id = system['id']
		self.channels = system['channels']

		##################################################
		# Threads
		##################################################

		receive_engine = threading.Thread(target=self.receive_engine)
		receive_engine.daemon = True
		receive_engine.start()

		##################################################
		# Blocks
		##################################################

		self.source = self

		#self.complex_to_mag_squared = blocks.complex_to_mag_squared(1)
		#self.probe = blocks.probe_signal_f()
		self.squelch = analog.simple_squelch_cc(self.system['threshold'], 0.1)
		self.sink = blocks.null_sink(gr.sizeof_gr_complex*1)
	
		##################################################
		# Connections
		##################################################
		#self.connect(self, self.complex_to_mag_squared, self.probe)
		self.connect(self, self.squelch, self.sink)

	def call_progress(self, freq):
		self.tb.ar_lock.acquire()

		for r in self.tb.active_receivers:
			if(r.cdr != {} and r.cdr['system_id'] == self.system['id'] and r.cdr['system_channel_local'] == freq and r.in_use == True):
				r.activity()
				self.tb.ar_lock.release()
				return None

		#new call, either find empty receiver or create a new one, then insert into call table
		try:
                        allocated_receiver = self.tb.connect_channel(int(freq), int(self.channel_rate))
                except:
                        self.tb.ar_lock.release()
                        return False


		allocated_receiver.set_rate(self.channel_rate)
		if self.system['modulation'] == 'p25':
			allocated_receiver.configure_blocks('p25')
		elif self.system['modulation'] == 'provoice':
			allocated_receiver.configure_blocks('provoice')
		else:
			allocated_receiver.configure_blocks('analog')
			
		cdr = {
			'system_id': self.system['id'],
			'system_group_local': freq,
			'system_user_local': 0,
			'system_channel_local': freq,
			'type': 'group',
			'hang_time': self.hang_time
		}

		allocated_receiver.open(cdr)
		self.tb.ar_lock.release()
		
###################################################################################################
	def receive_engine(self):
		print 'scanning_receiver: receive_engine() startup'
		print self.channels
		#time.sleep(3)
		if len(self.channels) > 1:
			raise Exception('scan: canner ghetto rig, 1 channel per scanner pls')


		while(True):
			for key,freq in self.channels.iteritems():
				time.sleep(0.010)
				#if self.probe.level() > 3.0e-4:
				if self.squelch.unmuted():
					self.call_progress(freq)
				#	print '*Freq: %s Level: %s' % (freq, self.probe.level())
				#elif self.probe.level() > 9.0e-7:
				#	print ' Freq: %s Level: %s' % (freq, self.probe.level())
				#else:
				#print 'scan: Freq: %s Level: %s' % (freq, self.probe.level())
