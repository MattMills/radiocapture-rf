#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: fft_vector
# GNU Radio version: 3.8.1.0

from gnuradio import blocks
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio import zeromq

import argparse

class fft_vector(gr.top_block):

    def __init__(self, index):
        gr.top_block.__init__(self, "fft_vector")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 2400000
        self.length = length = 1024*16

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_gr_complex, 1, 'ipc:///tmp/rx_source_%s' % index, 100, False, -1)
        self.fft_vxx_0 = fft.fft_vcc(length, True, window.blackmanharris(length), True, 1)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, length)
        self.blocks_skiphead_0 = blocks.skiphead(gr.sizeof_float*length, 999)
        self.blocks_nlog10_ff_0 = blocks.nlog10_ff(1, length, 1)
        self.blocks_moving_average_xx_1 = blocks.moving_average_ff(100, 1, 1200, length)
        self.blocks_head_0 = blocks.head(gr.sizeof_float*length, 1000)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_float*length, '/tmp/fft_source_%s' % index, False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(length)



        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_nlog10_ff_0, 0))
        self.connect((self.blocks_head_0, 0), (self.blocks_skiphead_0, 0))
        self.connect((self.blocks_moving_average_xx_1, 0), (self.blocks_head_0, 0))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.blocks_moving_average_xx_1, 0))
        self.connect((self.blocks_skiphead_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.zeromq_sub_source_0, 0), (self.blocks_stream_to_vector_0, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_length(self):
        return self.length

    def set_length(self, length):
        self.length = length



def main(top_block_cls=fft_vector, options=None):



    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--index', help="Device config index, if specified, all other configured sources will be deleted")
    args = parser.parse_args()

    tb = top_block_cls(args.index)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start(1)
    tb.wait()


if __name__ == '__main__':
    main()
