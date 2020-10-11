#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

import math
import os
import sys
import threading
import binascii
import uuid
import datetime
import json

from gnuradio import gr, uhd, filter, analog, blocks, digital, zeromq
from gnuradio.filter import firdes
from math import pi, floor
import op25_repeater as repeater
import op25
from time import sleep,time


from p25_cai import p25_cai
from p25_moto import p25_moto

from frontend_connector import frontend_connector
from redis_demod_publisher import redis_demod_publisher
from client_redis import client_redis


import logging
import logging.config

import zmq

# The P25 receiver
#
class p25_control_demod (gr.top_block):
        def __init__(self, system, site_uuid, overseer_uuid):
        
                gr.top_block.__init__(self, "p25 receiver")

                self.zmq_context = zmq.Context()
                self.zmq_socket = self.zmq_context.socket(zmq.SUB)
                self.zmq_socket.setsockopt(zmq.SUBSCRIBE, b"")

                #set globals
                self.is_locked = False
                self.system = system
                self.instance_uuid = '%s' % str(uuid.uuid4())

                self.log = logging.getLogger('overseer.p25_control_demod.%s' % self.instance_uuid)
                self.protocol_log = logging.getLogger('protocol.%s' % self.instance_uuid)
                self.log.info('Initializing instance: %s site: %s overseer: %s' % (self.instance_uuid, site_uuid, overseer_uuid))

                self.site_uuid = site_uuid
                self.overseer_uuid = overseer_uuid



                self.control_channel = system['channels'][system['default_control_channel']]
                self.control_channel_i = system['default_control_channel']
                
                
                self.channel_identifier_table = {}

                try:
                        self.modulation = system['modulation']
                except:
                        self.modulation = 'C4FM'

                self.channel_rate = 12500
                symbol_rate = 4800

                self.site_detail = {}
                self.site_detail['WACN ID'] = None
                self.site_detail['System ID'] = None
                self.site_detail['Control Channel'] = None
                self.site_detail['System Service Class'] = None
                self.site_detail['Site ID'] = None
                self.site_detail['RF Sub-system ID'] = None
                self.site_detail['RFSS Network Connection'] = None



                self.bad_messages = 0
                self.total_messages = 0
                self.quality = []
        
                self.keep_running = True
        
              
                self.source = None


                # channel filter
                channel_rate = self.channel_rate*2
                self.control_prefilter = filter.freq_xlating_fir_filter_ccc(1, (1,), 0, channel_rate)
        
                # power squelch
                #power_squelch = gr.pwr_squelch_cc(squelch, 1e-3, 0, True)
                #self.connect(self.channel_filter, power_squelch)

                autotuneq = gr.msg_queue(2)
                self.demod_watcher = demod_watcher(self)
                self.symbol_deviation = 600.0

                if self.modulation == 'C4FM':
                        # FM demodulator
                        fm_demod_gain = channel_rate / (2.0 * pi * self.symbol_deviation)
                        self.fm_demod = fm_demod = analog.quadrature_demod_cf(fm_demod_gain)

                        moving_sum = blocks.moving_average_ff(10000, 1, 40000)
                        subtract = blocks.sub_ff(1)
                        divide_const = blocks.multiply_const_vff((0.0001, ))
                        self.probe = blocks.probe_signal_f()
                        self.connect(self.fm_demod, moving_sum, divide_const, self.probe)
        
                        # symbol filter        
                        symbol_decim = 1
                        samples_per_symbol = channel_rate // symbol_rate
                        symbol_coeffs = (1.0/samples_per_symbol,) * samples_per_symbol
                        symbol_filter = filter.fir_filter_fff(symbol_decim, symbol_coeffs)
        
                        demod_fsk4 = op25.fsk4_demod_ff(autotuneq, channel_rate, symbol_rate)
                elif self.modulation == 'CQPSK':
                        # FM demodulator
                        fm_demod_gain = channel_rate / (2.0 * pi * self.symbol_deviation)
                        self.fm_demod = fm_demod = analog.quadrature_demod_cf(fm_demod_gain)

                        moving_sum = blocks.moving_average_ff(10000, 1, 40000)
                        subtract = blocks.sub_ff(1)
                        divide_const = blocks.multiply_const_vff((0.0001, ))
                        self.probe = blocks.probe_signal_f()
                        self.connect(fm_demod, moving_sum, divide_const, self.probe)

                        #self.resampler = filter.pfb.arb_resampler_ccf(float(48000)/float(channel_rate))
                        self.resampler = blocks.multiply_const_cc(1.0)
                        self.agc = analog.feedforward_agc_cc(1024,1.0)
                        self.symbol_filter_c = blocks.multiply_const_cc(1.0)

                        gain_mu= 0.025
                        omega = float(channel_rate) / float(symbol_rate)
                        gain_omega = 0.1  * gain_mu * gain_mu
        
                        alpha = 0.04
                        beta = 0.125 * alpha * alpha
                        fmax = 1200     # Hz
                        fmax = 2*pi * fmax / float(channel_rate)

                        self.clock = repeater.gardner_costas_cc(omega, gain_mu, gain_omega, alpha,  beta, fmax, -fmax)
                        self.diffdec = digital.diff_phasor_cc()
                        self.to_float = blocks.complex_to_arg()
                        self.rescale = blocks.multiply_const_ff( (1 / (pi / 4)) )

                # symbol slicer
                levels = [ -2.0, 0.0, 2.0, 4.0 ]
                slicer = op25.fsk4_slicer_fb(levels)
        
                # frame decoder
                self.qsink = qsink = zeromq.pub_sink(gr.sizeof_char, 1, 'tcp://127.0.0.1:*')
                print('%s' % qsink.last_endpoint())
                self.zmq_socket.connect(qsink.last_endpoint())
                #blocks.message_sink(gr.sizeof_char, self.decodequeue, False)
                self.decoder = decoder = repeater.p25_frame_assembler('', 0, 0, False, True, True, autotuneq, False, False)
        
                if self.modulation == 'C4FM':
                        self.connect(self.control_prefilter, fm_demod, symbol_filter, demod_fsk4, slicer, decoder, qsink)
                elif self.modulation == 'CQPSK':
                        self.connect(self.resampler, self.agc)
                        self.connect(self.agc, self.symbol_filter_c)
                        self.connect(self.symbol_filter_c, self.clock)
                        self.connect(self.clock, self.diffdec)
                        self.connect(self.diffdec, self.to_float)
                        self.connect(self.to_float, self.rescale)
                        self.connect(self.rescale, slicer)
                        self.connect(slicer, decoder)
                        self.connect(decoder, qsink)
        
                ##################################################
                # Threads
                ##################################################
                self.connector = frontend_connector()
                self.client_redis = client_redis()
                self.redis_demod_publisher = redis_demod_publisher(parent_demod=self)

                quality_check_0 = threading.Thread(target=self.quality_check)
                quality_check_0.daemon = True
                quality_check_0.start()
            # Adjust the channel offset
            #
                self.tune_next_control_channel()

                #self.receive_engine()

                receive_engine = threading.Thread(target=self.receive_engine)
                receive_engine.daemon = True
                receive_engine.start()

        def adjust_channel_offset(self, delta_hz):
                return False #Disable
                max_delta_hz = 6000.0
                delta_hz *= self.symbol_deviation      
                delta_hz = max(delta_hz, -max_delta_hz)
                delta_hz = min(delta_hz, max_delta_hz)
                #self.control_prefilter.set_center_freq(0 + delta_hz)
                self.log.info('adjust control deltz_hz = %s' % (delta_hz))
        def tune_next_control_channel(self):
                self.control_channel_i += 1
                if(self.control_channel_i >= len(self.system['channels'])):
                        self.control_channel_i = 0

                self.control_channel = self.system['channels'][self.control_channel_i]
                self.lock()
                if self.source != None:
                        if self.modulation == 'C4FM':
                                self.disconnect(self.source, self.control_prefilter)
                        elif self.modulation == 'CQPSK':
                                self.disconnect(self.source, self.fm_demod)
                                self.disconnect(self.source, self.resampler)
                self.connector.release_channel()
                port = False
                while port == False:
                    channel_id, port = self.connector.create_channel(self.channel_rate, self.control_channel)
                    self.log.info('Frontend connector.create_channel(%s, %s) = (%s, %s)' % (self.channel_rate, self.control_channel, channel_id, port))
                    if port == False:
                        sleep(0.05)
                for x in range(0, 3):
                        try:
                                self.source = zeromq.sub_source(gr.sizeof_gr_complex*1, 1, 'tcp://%s:%s' % (self.connector.host, port))
                                break
                        except Exception as e:
                                self.log.error('Exception in zeromq source creation (%s), try: %s' % (e, x))
                                sleep(0.1)
                
                
                if self.modulation == 'C4FM':
                        self.connect(self.source, self.control_prefilter)
                elif self.modulation == 'CQPSK':
                        self.connect(self.source, self.fm_demod)
                        self.connect(self.source, self.resampler)

                self.unlock()
                self.log.info('CC Change %s' % self.control_channel)
                #self.decodequeue.flush()
                #cant figure out how to do this in zmq in the 30 seconds I looked, fixme
        def procHDU(self, frame):
                r = {'short':'HDU', 'long':'Header Data Unit'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['status_symbols'] = status_symbols
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:-10]
                bitframe = self.golay_18_6_8_decode(bitframe)
                bitframe = self.rs_36_20_17_decode(bitframe)
                r['mi']    = bitframe[:72]
                r['mfid']  = int(bitframe[72:80],2)
                r['algid'] = int(bitframe[80:88],2)
                r['kid']   = int(bitframe[88:104],2)
                r['tgid']  = int(bitframe[104:120],2)
                return r
        def procTnoLC(self, frame):
                r = {'short':'TnoLC', 'long':'Terminator without Link Control'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['status_symbols'] = status_symbols
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                return r
        def procLDU1(self, frame):
                r = {'short':'LDU1', 'long':'Logical Link Data Unit 1'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['status_symbols'] = status_symbols
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:]
                vc = [] #voice coding, 144 bits ea 88 digital voice imbe, 56 parity
                lc = '' #link control, 240 bits
                vc.append(bitframe[:144]) #vc1
                vc.append(bitframe[144:288]) #vc2
                lc += bitframe[288:328] #lc1-4
                vc.append(bitframe[328:472]) #vc3
                lc += bitframe[472:512] #lc5-8
                vc.append(bitframe[512:656]) #vc4
                lc += bitframe[656:696] #lc9-12
                vc.append(bitframe[696:840]) #vc5
                lc += bitframe[840:880] #lc13-16
                vc.append(bitframe[880:1024]) #vc6
                lc += bitframe[1024:1064] #lc17-20
                vc.append(bitframe[1064:1208]) #vc7
                lc += bitframe[1208:1248] #lc21-24
                vc.append(bitframe[1248:1392]) #vc8
                r['lsd'] = bitframe[1392:1424]
                vc.append(bitframe[1424:1568]) #vc9

                lc = self.hamming_10_6_3_decode(lc)
                r['lc'] = self.subprocLC(lc)
                return r
        def procTSDU(self,frame):
                r = {'short':'TSDU', 'long':'Trunking Signal Data Unit'}
                bitframe = self.bin_to_bit(frame)
                r['len'] = len(bitframe)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['status_symbols'] = status_symbols
                r['len2'] = len(bitframe)
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:]
                r['len3'] = len(bitframe)

                r['tsbk'] = []
                while(len(bitframe) >= 196):
                        r['tsbk'].append(self.subprocTSBK(bitframe[:196]))
                        bitframe = bitframe[196:]
                        if(bitframe[:1] == '1'):
                                break

                return r
        def procLDU2(self, frame):
                r = {'short' : 'LDU2', 'long': 'Logical Link Data Unit 2'}
                return r
        def procPDU(self, frame):
                r = {'short':'PDU', 'Long' : 'Packet Data Unit'}
                return r
        def procTLC(self, frame):
                r = {'short': 'TLC', 'Long' : 'Terminator with Link Control'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:-20]
                bitframe = self.golay_24_12_8_decode(bitframe)
                
                r['lc'] = self.subprocLC(bitframe)

                return r
        def subprocTSBK(self, bitframe):
                r = {}
                #sys.stderr.write('dibits: %i' % (len(dibits)))
                #print bitframe
                dibits = self.bits_to_dibit(bitframe)
                #print dibits
                dibits = self.data_deinterleave(dibits)
                #print dibits
                trellis_dibits = self.trellis_1_2_decode(dibits)
                bitframe = self.dibits_to_bit(trellis_dibits)
                #print bitframe
                #print hex(int(bitframe,2))
                if len(bitframe) < 96:
                        r['ERR'] = 'PACKET_LENGTH_SHORT'
                        return r
                if self.crc16(int(bitframe,2), 12) == 0:
                        r['crc'] = 0 # bitframe[:16]
                else:
                        r['crc'] = 1
                #sys.stderr.write('Bitframe: %i' % (len(bitframe)))
                r['lb'] = bitframe[:1] #Last block
                r['p'] = bitframe[1:2] #protected
                r['opcode'] = int(bitframe[2:8],2)
                r['mfid'] = int(bitframe[8:16],2)
                if r['mfid'] == 0x0 or r['mfid'] == 0x1: 
                        p = p25_cai()
                elif r['mfid'] == 0x90:
                        p = p25_moto()
                else:
                        r['name'] = 'UNKnOWN MFID'
                        r['data'] = hex(int(bitframe,2))
                        return r
                try:
                        r['name'] = p.tsbk_osp_single[r['opcode']]['name']
                except:
                        r['name'] = 'UNKNOWN OPCODE'
                        r['data'] = hex(int(bitframe,2))
                        return r
                if(len(bitframe[16:]) < 80): return r
                bitframe = bitframe[16:]
                for i in range(0, len(p.tsbk_osp_single[r['opcode']]['fields'])):
                        r[p.tsbk_osp_single[r['opcode']]['fields'][i]['name']] = int(bitframe[:p.tsbk_osp_single[r['opcode']]['fields'][i]['length']],2)
                        bitframe = bitframe[p.tsbk_osp_single[r['opcode']]['fields'][i]['length']:]
                return r
        def subprocLC(self, bitframe):
                bitframe = self.rs_24_12_13_decode(bitframe)
                r = {'short': 'LC', 'long': 'Link Control'}
                r['p'] = int(bitframe[0:1], 2)
                r['p'] = int(bitframe[1:2], 2)
                r['lcf'] = int(bitframe[2:8],2)
                r['mfid'] = int(bitframe[8:16],2)

                if(r['lcf'] == 0x0): #Group Voice Channel User (LCGVR)
                        r['lcf_long'] = 'Group Voice Channel User'
                        r['emergency'] = bitframe[16:17]
                        r['reserved'] = bitframe[17:32]
                        r['tgid'] = int(bitframe[32:48],2)
                        r['source_id'] = int(bitframe[48:72],2)
                        #print 'GV %s %s' %(r['tgid'], r['source_id'])
                elif(r['lcf'] == 0x15):        #Call Termination / Cancellation
                        r['lcf_long'] = 'Call Termination / Cancellation'
                        
                return r
        def procStatus(self, bitframe):
                r = []
                returnframe = ''
                for i in range(0, len(bitframe), 72):
                        r.append(int(bitframe[i+70:i+72],2))
                        returnframe += bitframe[i:i+70]
                        if(len(bitframe) < i+72): 
                                break

                return [returnframe, r]
        def crc16(self, dat,len):     # slow version
                poly = (1<<12) + (1<<5) + (1<<0)
                crc = 0
                for i in range(len):
                        bits = (dat >> (((len-1)-i)*8)) & 0xff
                        for j in range(8):
                                bit = (bits >> (7-j)) & 1
                                crc = ((crc << 1) | bit) & 0x1ffff
                                if crc & 0x10000:
                                        crc = (crc & 0xffff) ^ poly
                crc = crc ^ 0xffff
                return crc

        # fake (18,6,8) shortened Golay decoder, no error correction
        # TODO: make less fake
        # Pulled from Rev 88 of op25/trunk/python/c4fm_decode.py
        def golay_18_6_8_decode(self, input):
                output = ''
                for i in range(0,len(input),18):
                        codeword = input[i:i+18]
                        output +=codeword[:6]
                return output
        # fake (24,12,8) extended Golay decoder, no error correction
        # TODO: make less fake
        def golay_24_12_8_decode(self, input):
                output = ''
                for i in range(0,len(input),24):
                        codeword = input[i:i+24]
                        output += codeword[:12]
                return output

        # fake (36,20,17) Reed-Solomon decoder, no error correction
        def rs_36_20_17_decode(self, input):
                return input[:-96]

        # fake (24,12,13) Reed-Solomon decoder, no error correction
        def rs_24_12_13_decode(self, input):
                return input[:-72]

        # fake (24,16,9) Reed-Solomon decoder, no error correction
        def rs_24_16_9_decode(self,input):
                return input[:-48]
        # fake (10,6,3) shortened Hamming decoder, no error correction
        def hamming_10_6_3_decode(self, input):
                output = ''
                for i in range(0,len(input),10):
                         codeword = input[i:i+10]
                         output += codeword[:6]
                return output
        def trellis_test(self, input):
                output = []
                state = 0
                previous_match = True
                fsm_table = (
                        (0x0, 0xF, 0xC, 0x3),
                        (0x4, 0xB, 0x8, 0x7),
                        (0xD, 0x2, 0x1, 0xE),
                        (0x9, 0x6, 0x5, 0xA)
                        )
                dibit_table = (
                        (11, 12, 0, 7),
                        (14, 9, 5, 2),
                        (10, 13, 1, 6),
                        (15, 8, 4, 3)
                        )
                for i in range(0, len(input)-2, 2):
                        x = input[i]
                        y = input[i+1]
                        C = dibit_table[x][y]
                        #print codeword
                        min_distance = 100
                        min_distance_k = -1
                        for K in range(4):
                                distance = abs(fsm_table[state][K]-C)
                                if distance < min_distance:
                                        min_distance = distance
                                        min_distance_k = K
                        
                        c = fsm_table[state][min_distance_k]
                        
                        if c == C: 
                                match = True
                        else:
                                match = False
                        if not match and not previous_match:
                                #print "Trellis failure at length: %i" % len(output)
                                self.log.warning('Trellis failure at length %i' % len(output))
                                #raise Exception('Irrecoverable error in Trellis encoding.')
                                return output
                                        
                        output.append(min_distance_k)
                        FSMState = min_distance_k
                        previous_match = match

                return output
        def trellis_1_2_decode(self, input):
                output = []
                error_count = 0
                # state transition table, including constellation to dibit pair mapping
                next_words = (
                        (0x2, 0xC, 0x1, 0xF),
                        (0xE, 0x0, 0xD, 0x3),
                        (0x9, 0x7, 0xA, 0x4),
                        (0x5, 0xB, 0x6, 0x8))
                state = 0
                # cycle through 2 symbol codewords in input
                for i in range(0,len(input),2):
                        codeword = self.dibits_to_integer(input[i:i+2])
                        similarity = [0, 0, 0, 0]
                        # compare codeword against each of four candidates for the current state
                        for candidate in range(4):
                                # increment similarity result for each bit in codeword that matches candidate
                                for bit in range(4):
                                        if ((~codeword ^ next_words[state][candidate]) & (1 << bit)) > 0:
                                                similarity[candidate] += 1
                        # find the dibit that matches all four codeword bits
                        if similarity.count(4) == 1:
                                state = similarity.index(4)
                        # otherwise find the dibit that matches three codeword bits
                        elif similarity.count(3) == 1:
                                state = similarity.index(3)
                                # We may have corrected the error, so count only a partial error.
                                error_count += 0.01
                        else:
                                # We probably can't correct this error, but we can take our best guess.
                                for j in range(3,-1,-1):
                                        if similarity.count(j) > 0:
                                                state = similarity.index(j)
                                                error_count += 1
                                                break
                        output.append(state)
                # Even if we have a terrible string of errors, we return our best guess and report the error count.
                #if error_count > 0:
                #        sys.stderr.write("Trellis decoding error count: %.2f\n" % error_count)
                return output[:48]

        def data_deinterleave(self, input):
                output = []
                for i in range(0,23,2):
                        for j in (0, 26, 50, 74):
                                output.extend(input[i+j:i+j+2])
                output.extend(input[24:26])
                return output
        # return integer represented by sequence of dibits
        def dibits_to_integer(self, dibits):
                integer = 0
                for dibit in dibits:
                        integer = integer << 2
                        integer += int(dibit)
                return integer
        def bin_to_bit(self, input):
                output = ''
                for i in range(0, len(input)):
                        output += bin(input[i])[2:].zfill(8)
                return output
        def int_to_bit(self, input):
                output = ''
                #print input
                for i in range(0, len(input)):
                        output += bin(input[i])[2:].zfill(8)
                return output
                
        def dibits_to_bit(self, input):
                output = ''
                for j in range(0, len(input)):
                        output += bin(input[int(j)])[2:].zfill(2)
                return output
        def bits_to_dibit(self, input):
                output = []
                for i in range(0, len(input), 2):
                        output.append(int(input[i:i+2],2))
                return output
        def get_channel_detail(self, channel):
                chan_ident = (channel & 0xf000)>>12
                chan_number = channel & 0x0fff
                try:
                        base_freq = self.channel_identifier_table[chan_ident]['Base Frequency']
                        chan_spacing = self.channel_identifier_table[chan_ident]['Channel Spacing']/1000
                        slots = self.channel_identifier_table[chan_ident]['Slots']
                except KeyError:
                        return False, False, False
                chan_freq = ((chan_number/slots)*chan_spacing)
                slot_number = (chan_number % slots)
                channel_frequency = floor((base_freq + chan_freq)*1000000)
                channel_bandwidth = self.channel_identifier_table[chan_ident]['BW']*1000

                return channel_frequency, channel_bandwidth, slot_number

        def receive_engine(self):
                self.log.info('receive_engine() initializing')
                buf = b''
                data_unit_ids = {
                                0x0: 'Header Data Unit',
                                0x3: 'Terminator without Link Control',
                                0x5: 'Logical Link Data Unit 1',
                                0x7: 'Trunking Signaling Data Unit',
                                0xA: 'Logical Link Data Unit 2',
                                0xC: 'Packet Data Unit',
                                0xF: 'Terminator with Link Control'
                                }


                loop_start = time()
                loops_locked = 0
                wrong_duid_count = 0
                no_flow = 0

                while self.keep_running:
                        if loops_locked < -50 and time()-loop_start > 10:
                                if len(self.system['channels']) > 1:
                                        self.log.warning('Unable to lock control channel on %s' % self.control_channel)
                                        self.tune_next_control_channel()

                                loops_locked = 0
                                loop_start = time()
                        if loops_locked > 500:
                                self.is_locked = True
                        else:
                                if self.is_locked == True:
                                        self.site_detail = {}
                                        self.site_detail['WACN ID'] = None
                                        self.site_detail['System ID'] = None
                                        self.site_detail['Control Channel'] = None
                                        self.site_detail['System Service Class'] = None
                                        self.site_detail['Site ID'] = None
                                        self.site_detail['RF Sub-system ID'] = None
                                        self.site_detail['RFSS Network Connection'] = None
                                        self.site_detail['NAC'] = None
                                        self.is_locked = False
                        pkt = b''
                        try:
                            pkt = self.zmq_socket.recv(flags=zmq.NOBLOCK)
                        except Exception as e:
                            pass
                        if len(pkt) > 0: #self.decodequeue.count(): #fixme
                                buf += pkt
                                no_flow = 0
                        else:
                                no_flow = no_flow + 1
                                if no_flow % 100 == 0 and self.is_locked:
                                        self.log.error('extended no flow event')
                                if no_flow > 1000:
                                        self.log.error('No flow retune')
                                        self.tune_next_control_channel()
                                        no_flow = 0
                                sleep(0.007) #avg time between packets is 0.007s

                        fsoffset = buf.find(binascii.unhexlify('5575f5ff77ff'))
                        fsnext   = buf.find(binascii.unhexlify('5575f5ff77ff'), fsoffset+6)
                        if(fsoffset != -1 and fsnext != -1):
                                if(loops_locked < 1000):
                                        loops_locked = loops_locked + 100

                                frame = buf[fsoffset:fsnext]
                                buf = buf[fsnext:]
                                if len(frame) < 10: continue
                                frame_sync = binascii.hexlify(frame[0:6])
                                duid = int.from_bytes(frame[7:8], "big") & 0xf
                                nac = (int.from_bytes(frame[6:7], "big")<<4) +((int.from_bytes(frame[7:8],"big")&0xf0)>>4)
                                
                                #print('DUID: %s NAC: %s' % (duid, nac))
                                self.total_messages = self.total_messages + 3
                                #print 'FSO:%s FSN:%s BS:%s FL:%s - %s - %s' % (fsoffset, fsnext, len(buf), (fsnext-fsoffset), frame_sync, data_unit_ids[duid])
                                if duid != 0x7:
                                        wrong_duid_count = wrong_duid_count +1
                                        if wrong_duid_count > 10:
                                                self.log.warning('Hit wrong DUID count on control channel')
                                                if len(self.system['channels']) > 1:
                                                        self.tune_next_control_channel()

                                                loop_start = time()
                                                loops_locked = 0
                                                wrong_duid_count = 0
                                elif duid == 0x7:
                                        wrong_duid_count = 0

                                try:
                                        if duid == 0x0:
                                                r = self.procHDU(frame)
                                        elif duid == 0x3:
                                                r = self.procTnoLC(frame)
                                        elif duid == 0x5:
                                                r = self.procLDU1(frame)
                                        elif duid == 0x7:
                                                r = self.procTSDU(frame)
                                        elif duid == 0xA:
                                                r = self.procLDU2(frame)
                                        elif duid == 0xC:
                                                r = self.procPDU(frame)
                                        elif duid == 0xF: 
                                                r = self.procTLC(frame)
                                        else:
                                                pass
                                except Exception as e:
                                        self.log.info('%s' % e)
                                        self.bad_messages = self.bad_messages + 3
                                        continue
                                if len(self.system['channels']) == 1:
                                        self.log.info('%s' % r)
                                try:
                                        r['tsbk']
                                except:
                                        self.bad_messages = self.bad_messages + 3
                                        continue
                                for i in range(0, len(r['tsbk'])):
                                        t = r['tsbk'][i]
                                        t['nac'] = nac
                                        try:
                                                t['name']
                                        except:
                                                t['name'] = 'INVALID'

                                        try:
                                                t['crc']
                                        except:
                                                self.bad_messages = self.bad_messages + 1
                                                continue

                                        if t['crc'] == 1:
                                                self.bad_messages = self.bad_messages + 1
                                                continue

                                        if t['name'] == 'IDEN_UP_VU':
                                                t['Base Frequency'] = t['Base Frequency']*0.000005
                                                
                                                if t['BW VU'] == 4:
                                                        t['BW VU'] = 6.25
                                                elif t['BW VU'] == 5:
                                                        t['BW VU'] = 12.5
                                                
                                                t['Channel Spacing'] = t['Channel Spacing']*0.125
                                                t['Transmit Offset VU'] = int(t['Transmit Offset VU'])
                                                sign = (t['Transmit Offset VU']&0x100>>8)
                                                if sign == 0: sign = -1
                
                                                t['Transmit Offset VU'] = sign*(t['Transmit Offset VU']&0xff)*0.250 


                                                self.channel_identifier_table[t['Identifier']] = {
                                                        'BW': t['BW VU'], 
                                                        'Base Frequency': t['Base Frequency'], 
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset VU'],
                                                        'Type': 'FDMA',
                                                        'Slots': 1,
                                                        }
                                        elif t['name'] == 'IDEN_UP':
                                                t['Base Frequency'] = t['Base Frequency']*0.000005
                                                t['BW'] = t['BW']*0.125
                                                t['Channel Spacing'] = t['Channel Spacing']*0.125
                                                t['Transmit Offset'] = int(t['Transmit Offset'])
                                                sign = (t['Transmit Offset']&0x100>>8)
                                                if sign == 0: sign = -1

                                                t['Transmit Offset'] = sign*(t['Transmit Offset']&0xff)*0.250

                                                self.channel_identifier_table[t['Identifier']] = {
                                                        'BW': t['BW'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset'],
                                                        'Type': 'FDMA',
                                                        'Slots': 1,
                                                        }
                                        elif t['name'] == 'IDEN_UP_TDMA':
                                                t['Base Frequency'] = t['Base Frequency']*0.000005
                                                t['Channel Spacing'] = t['Channel Spacing']*0.125
                                                t['Transmit Offset TDMA'] = int(t['Transmit Offset TDMA'])
                                                sign = (t['Transmit Offset TDMA']&0x100>>8)
                                                if sign == 0: sign = -1

                                                t['Transmit Offset TDMA'] = sign*(t['Transmit Offset TDMA']&0x1fff)

                                                if(t['Channel Type'] == 0 or t['Channel Type'] == 1 or t['Channel Type'] == 2):
                                                        t['Access Type'] = 'FDMA'
                                                        t['Slots'] = 1
                                                elif(t['Channel Type'] == 3 or t['Channel Type'] == 4 or t['Channel Type'] == 5):
                                                        t['Access Type'] = 'TDMA'
                                                        if(t['Channel Type'] == 3 or t['Channel Type'] == 5):
                                                                t['Slots'] = 2
                                                        elif(t['Channel Type'] == 4):
                                                                t['Slots'] = 4
                                                

                                                if(t['Channel Type'] == 0 or t['Channel Type'] == 1 or t['Channel Type'] == 3 or t['Channel Type'] == 5):
                                                        t['BW'] = 12.5
                                                elif(t['Channel Type'] == 2):
                                                        t['BW'] = 6.25
                                                elif(t['Channel Type'] == 4):
                                                        t['BW'] = 25
                                                try:
                                                        self.channel_identifier_table[t['Identifier']] = {
                                                        'BW': t['BW'],
                                                        'Base Frequency': t['Base Frequency'],
                                                        'Channel Spacing': t['Channel Spacing'],
                                                        'Transmit Offset': t['Transmit Offset TDMA'],
                                                        'Type': t['Access Type'],
                                                        'Slots': t['Slots'],
                                                        }
                                                except:
                                                        pass        
                                        elif t['name'] == 'GRP_V_CH_GRANT':
                                                if 'Source Address' in t and t['Source Address'] == 0:
                                                        #super hacky fix for DTRS weirdness when dispatch console has no source address (comes across as 0)
                                                        t['Source Address'] = 1
                                                pass
                                        elif t['name'] == 'GRP_V_CH_GRANT_UPDT':
                                                pass
                                        elif t['name'] == 'UU_V_CH_GRANT':
                                                pass
                                        elif t['name'] == 'UU_ANS_REQ':
                                                pass
                                        elif t['name'] == 'GRP_V_CH_GRANT_UPDT_EXP':
                                                pass
                                        elif t['name'] == 'GRP_AFF_RSP':
                                                pass
                                        elif t['name'] == 'U_REG_RSP':
                                                pass
                                        elif t['name'] == 'NET_STS_BCST':
                                                self.site_detail['WACN ID'] = hex(int(t['WACN ID']))
                                                self.site_detail['System ID'] = hex(int(t['System ID']))
                                                self.site_detail['System Service Class'] = t['System Service Class']
                                                self.site_detail['Control Channel'], null, null = self.get_channel_detail(t['Channel'])
                                                self.site_detail['NAC'] = t['nac']
                                        elif t['name'] == 'RFSS_STS_BCST':
                                                self.site_detail['Site ID'] = t['Site ID']
                                                self.site_detail['RF Sub-system ID'] = t['RF Sub-system ID']
                                                self.site_detail['RFSS Network Connection'] = t['A']
                                        elif t['name'] == 'ADJ_STS_BCST':
                                                t['Channel'] = self.get_channel_detail(t['Channel'])
                                                del t['lb']
                                                del t['crc']
                                                del t['mfid']
                                                del t['opcode']
                                        try:
                                                packet_type = t['name']
                                        except:
                                                packet_type = 'invalid'

                                        self.client_redis.send_event_lazy('/topic/raw_control/%s' % (self.instance_uuid), t,{'packet_type': packet_type})
                                        self.protocol_log.info(t)
                        else:
                                loops_locked = loops_locked - 1
        def quality_check(self):
                desired_quality = 400.0 # approx 40 tsbk per sec

                logger = logging.getLogger('overseer.quality.%s' % self.instance_uuid)
                bad_messages = self.bad_messages
                total_messages = self.total_messages
                last_total = 0
                last_bad = 0
                while True:
                        sleep(10); #only check messages once per 10second
                        sid = '%s %s-%s %s-%s' % (self.system['id'], self.site_detail['System ID'], self.site_detail['WACN ID'], self.site_detail['RF Sub-system ID'], self.site_detail['Site ID'])
                        
                        current_packets = self.total_messages-last_total
                        current_packets_bad = self.bad_messages-last_bad

                        logger.info('System Status: %s (%s/%s) (%s/%s) CC: %s' % (sid, current_packets, current_packets_bad, self.total_messages, self.bad_messages, self.control_channel))
                        
                        if len(self.quality) >= 60:
                                self.quality.pop(0)

                        self.quality.append((current_packets-current_packets_bad)/desired_quality)
                        last_total = self.total_messages
                        last_bad = self.bad_messages

# Demodulator frequency tracker
#
class demod_watcher(threading.Thread):

    def __init__(self, tb):
        threading.Thread.__init__ (self)
        self.setDaemon(1)
        self.tb = tb
        self.keep_running = True
        self.start()

    def run(self):
        sleep(1)
        while(self.keep_running):
                if(self.tb.is_locked and self.tb.modulation == 'C4FM'):
                        #print 'Probe: %s' % self.tb.probe.level()
                        if self.tb.modulation == 'C4FM':
                                offset = self.tb.probe.level()
                                self.tb.connector.report_offset(offset)
                sleep(0.5)

if __name__ == '__main__':
        with open('config.logging.json', 'rt') as f:
            config = json.load(f)

        logging.config.dictConfig(config)
        system_config = { 
                'type': 'p25',
                'id': 0,
                'default_control_channel': 0,
                'channels': {
                        0: 851312500,
                }
        }
        main = p25_control_demod(system_config, uuid.uuid4(), uuid.uuid4())
