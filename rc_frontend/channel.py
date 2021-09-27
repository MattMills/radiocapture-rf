#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

import os
import sys
import threading
import binascii
import uuid
import datetime
import time

from gnuradio import gr, uhd, filter, analog, blocks, zeromq
from gnuradio.filter import firdes


class channel ( gr.top_block):
        def __init__(self, parent_zmq_address, port, channel_rate, samp_rate, offset):
                gr.top_block.__init__(self, "channel")

                self.parent_zmq_address = parent_zmq_address
                self.samp_rate = samp_rate
                self.channel_rate = channel_rate
                self.port = port
                self.offset = offset
                self.in_use = False
                self.source_id = None

                self.zmq_sub_source = zeromq.sub_source(gr.sizeof_gr_complex, 1, parent_zmq_address, 100, False, -1)

                decim = int(samp_rate/(channel_rate))/2
                #taps = firdes.low_pass(1,self.samp_rate,(self.channel_rate-2000)/2,4000)
                taps = firdes.low_pass_2(1.0,float(samp_rate),(channel_rate)/2,channel_rate/2, 20.0, firdes.WIN_HAMMING)
                #print 'taps: %s' % len(taps)
                self.prefilter = filter.freq_xlating_fir_filter_ccc(decim, (taps), offset, samp_rate)
                self.sink = zeromq.pub_sink(gr.sizeof_gr_complex*1, 1, 'tcp://0.0.0.0:%s' % port)
                
                self.connect(self.zmq_sub_source, self.prefilter, self.sink)
                self.init_time = time.time()
                self.channel_close_time = 0
        def __str__(self):
            return "Channel: port:%s channel_rate:%s samp_rate:%s offset:%s init_time:%s" % (self.port, self.channel_rate, self.samp_rate, self.offset, self.init_time)
        def __repr__(self):
            return "<Channel port:%s channel_rate:%s samp_rate:%s offset:%s init_time:%s>" % (self.port, self.channel_rate, self.samp_rate, self.offset, self.init_time)

        def get_samp_rate(self):
                return self.samp_rate
        def set_samp_rate(self, samp_rate):
                self.samp_rate = samp_rate
                self.set_taps(firdes.low_pass(1,self.samp_rate,(self.channel_rate-2000)/2, 4000))
        def get_channel_rate(self):
                return self.channel_rate
        def set_channel_rate(self, channel_rate):
                self.channel_rate = channel_rate
                self.set_taps(firdes.low_pass(1,self.samp_rate,(self.channel_rate-2000)/2, 4000))
        def set_taps(self, taps):
                self.prefilter.set_taps((taps))

        def get_offset(self):
                return self.offset
        def set_offset(self, offset):
                self.offset = offset
                self.prefilter.set_center_freq(self.offset)
        def destroy(self):
            self.prefilter = None
            self.sink = None
            self.stop()

