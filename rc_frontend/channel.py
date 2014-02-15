#!/usr/bin/env python

import os
import sys
import threading
import binascii
import uuid
import datetime

from gnuradio import gr, uhd, filter, analog, blocks
from gnuradio.filter import firdes
from time import sleep,time

class channel ( gr.hier_block2):
	def __init__(self, dest, port, channel_rate, samp_rate, offset):
		gr.hier_block2.__init__(self, "channel",
                        gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
                        gr.io_signature(0, 0, 0)) # Output signature

		self.samp_rate = samp_rate
		self.channel_rate = channel_rate
		self.dest = dest
		self.port = port
		self.offset = offset
		self.in_use = False
		self.source_id = None

		decim = int(samp_rate/(channel_rate*2))
		taps = firdes.low_pass(1,self.samp_rate,self.channel_rate,self.channel_rate/2)
		print 'taps: %s' % len(taps)
		self.prefilter = filter.freq_xlating_fir_filter_ccc(decim, (taps), offset, samp_rate)
		self.udp = blocks.udp_sink(gr.sizeof_gr_complex*1, dest, port, 1472, True)
		
		self.connect(self, self.prefilter, self.udp)

	def get_samp_rate(self):
		return self.samp_rate
	def set_samp_rate(self, samp_rate):
		self.samp_rate = samp_rate
		self.set_taps(firdes.low_pass(1,self.samp_rate,self.channel_rate,self.channel_rate/4))
		self.set_decim(int(self.samp_rate/(self.channel_rate*1.5)))
	def get_channel_rate(self):
		return self.channel_rate
	def set_channel_rate(self, channel_rate):
		self.channel_rate = channel_rate
		self.set_taps(firdes.low_pass(1,self.samp_rate,self.channel_rate,self.channel_rate/4))
		self.set_decim(int(self.samp_rate/(self.channel_rate*1.5)))
	def set_taps(self, taps):
		self.prefilter.set_taps((taps))

	def get_offset(self):
		return self.offset
	def set_offset(self, offset):
		self.offset = offset
		self.prefilter.set_center_freq(self.offset)


