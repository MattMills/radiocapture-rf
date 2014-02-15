#!/usr/bin/env python

import math
import os
import sys
import threading
import binascii
import uuid
import datetime

from gnuradio import gr, uhd, filter, analog,blocks
from gnuradio.filter import firdes
from math import pi
import op25_repeater as repeater
import op25
from time import sleep,time

from p25_cai import p25_cai
from logging_receiver import logging_receiver


# The P25 receiver
#
class p25_control_receiver (gr.hier_block2):
	def __init__(self, system, samp_rate, sources, top_block, block_id):
	#p25_control_receiver( self.systems[system], self.sources[0]['samp_rate'], self.sources, self, system)

		gr.hier_block2.__init__(self, "p25_control_receiver",
	        	gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
	                gr.io_signature(0, 0, 0)) # Output signature
	
		self.hang_time = 0.3 #300 ms hang time	

		#set globals
		self.tb = top_block
		self.system = system
		self.block_id = block_id
		self.sources = sources
		self.samp_rate = samp_rate

		self.control_channel = system['channels'][system['default_control_channel']]
		self.control_channel_i = system['default_control_channel']
		self.control_source = 0

		self.call_table = {}
		self.channel_identifier_table = {}

		self.thread_id = '%s-%s' % (self.system['type'], self.system['id'])

	        # Setup receiver attributes
	        channel_rate = 25000 #125000
	        symbol_rate = 4800

		self.bad_messages = 0
		self.total_messages = 0
	
	      
	        # channel filter
	        channel_decim = samp_rate // channel_rate
	        channel_rate = samp_rate // channel_decim
	        trans_width = 12.5e3 / 2;
	        trans_centre = trans_width + (trans_width / 2)
	        coeffs = firdes.low_pass(1.0, samp_rate, channel_rate/2, channel_rate/2*0.55, firdes.WIN_HANN)
	        self.control_prefilter = filter.freq_xlating_fir_filter_ccf(channel_decim, coeffs, self.control_channel, samp_rate)
	
	        # power squelch
	        #power_squelch = gr.pwr_squelch_cc(squelch, 1e-3, 0, True)
	        #self.connect(self.channel_filter, power_squelch)
	
	        # FM demodulator
	        self.symbol_deviation = 600.0
	        fm_demod_gain = channel_rate / (2.0 * pi * self.symbol_deviation)
	        fm_demod = analog.quadrature_demod_cf(fm_demod_gain)
	
	        # symbol filter        
	        symbol_decim = 1
	        samples_per_symbol = channel_rate // symbol_rate
	        symbol_coeffs = (1.0/samples_per_symbol,) * samples_per_symbol
	        symbol_filter = filter.fir_filter_fff(symbol_decim, symbol_coeffs)
	
	        # C4FM demodulator
	        autotuneq = gr.msg_queue(2)
	        self.demod_watcher = demod_watcher(autotuneq, self.adjust_channel_offset)
	        demod_fsk4 = op25.fsk4_demod_ff(autotuneq, channel_rate, symbol_rate)
	
	        # symbol slicer
	        levels = [ -2.0, 0.0, 2.0, 4.0 ]
	        slicer = op25.fsk4_slicer_fb(levels)
	
	        # frame decoder
		self.decodequeue = decodequeue = gr.msg_queue(1000)
		qsink = blocks.message_sink(gr.sizeof_char, self.decodequeue, False)
		self.decoder = decoder = repeater.p25_frame_assembler('', 0, 0, False, True, True, autotuneq)
	

	        self.connect(self, self.control_prefilter, fm_demod, symbol_filter, demod_fsk4, slicer, decoder, qsink)
	
                ##################################################
                # Threads
                ##################################################

                receive_engine = threading.Thread(target=self.receive_engine)
                receive_engine.daemon = True
                receive_engine.start()

                quality_check_0 = threading.Thread(target=self.quality_check)
                quality_check_0.daemon = True
                quality_check_0.start()
	    # Adjust the channel offset
	    #
	def adjust_channel_offset(self, delta_hz):
	        max_delta_hz = 12000.0
	        delta_hz *= self.symbol_deviation      
	        delta_hz = max(delta_hz, -max_delta_hz)
	        delta_hz = min(delta_hz, max_delta_hz)
	        self.control_prefilter.set_center_freq(self.control_channel - delta_hz)
        def tune_next_control_channel(self):
                self.control_channel_i += 1
                if(self.control_channel_i >= len(self.system['channels'])):
                        self.control_channel_i = 0

                self.control_channel = self.system['channels'][self.control_channel_i]

                self.control_source = self.tb.retune_control(self.block_id, self.control_channel)

                self.control_prefilter.set_center_freq(self.control_channel-self.sources[self.control_source]['center_freq'])
                print '%s: CC Change - %s - %s - %s' % (self.thread_id, self.control_channel, self.sources[self.control_source]['center_freq'], self.control_channel-self.sources[self.control_source]['center_freq'])
                self.decodequeue.flush()
                sleep(0.1)
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
		if r['mfid'] != 0x0 and r['mfid'] != 0x1: return r
		p = p25_cai()
                try:
                        r['name'] = p.tsbk_osp_single[r['opcode']]['name']
                except:
                        r['name'] = 'INVALID'
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
		r['lcf'] = int(bitframe[:8],2)
                r['mfid'] = int(bitframe[8:16],2)

		if(r['lcf'] == 0x0): #Group Voice Channel User (LCGVR)
			r['lcf_long'] = 'Group Voice Channel User'
			r['emergency'] = bitframe[16:17]
			r['reserved'] = bitframe[17:32]
			r['tgid'] = int(bitframe[32:48],2)
			r['source_id'] = int(bitframe[48:72],2)
			#print 'GV %s %s' %(r['tgid'], r['source_id'])
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
				print "Trellis failure at length: %i" % len(output)
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
		#	sys.stderr.write("Trellis decoding error count: %.2f\n" % error_count)
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
			output += bin(ord(input[i]))[2:].zfill(8)
		return output
	def int_to_bit(self, input):
		output = ''
		print input
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
	def new_call(self, channel, group, user):
		return False
		if(self.system['id'] in self.tb.blacklists.keys() and group in self.tb.blacklists[self.system['id']]):
			return False
			#Ignore blacklisted groups
		chan_ident = (channel & 0xf000)>>12
		chan_number = channel & 0x0fff
		try:
			base_freq = self.channel_identifier_table[chan_ident]['Base Frequency']
			chan_spacing = self.channel_identifier_table[chan_ident]['Channel Spacing']/1000
		except KeyError:
			print "%s: GRP_V_CH_GRANT on Channel plan that is undefined" % self.thread_id
			return False

		chan_freq = (chan_number*chan_spacing)
		channel_frequency = (base_freq + chan_freq)*1000000
		channel_bandwidth = self.channel_identifier_table[chan_ident]['BW']*1000
		
		self.tb.ar_lock.acquire()
		allocated_receiver = False

		for receiver in self.tb.active_receivers: #find any active channels and mark them as progressing
			#If we're on the same channel with a different group, close and reopen
			#If we're on the same group and channel mark as activity
			#If we're on the same group and different channel, ignore

			if receiver.cdr != {} and receiver.cdr['system_channel_local'] == channel and receiver.cdr['system_id'] == self.system['id']:
				if receiver.cdr['system_group_local'] != group or (receiver.cdr['system_user_local'] != user and user != 0):
					#Quick close, new user/group.
					old_cdr = receiver.cdr
					receiver.close({})
					receiver.set_codec_p25(True)
		                        receiver.set_codec_provoice(False)
		
		                        cdr = {
		                                'system_id': self.system['id'],
		                                'system_group_local': group,
		                                'system_user_local': user,
		                                'system_channel_local': channel,
		                                'type': 'group',
		                                'center_freq': old_cdr['center_freq'],
						'hang_time': self.hang_time
		                        }

		                        receiver.open(cdr, int(channel_bandwidth))
					allocated_receiver = receiver
				else:
			
					receiver.activity()
	                                allocated_receiver = receiver
                                break
		if allocated_receiver == False: #If not an existing call
			for receiver in self.tb.active_receivers: #look for an empty channel
				if receiver.in_use == False and abs(receiver.center_freq-channel_frequency) < (self.samp_rate/2):
					allocated_receiver = receiver
					center = receiver.center_freq
					break

			if allocated_receiver == False: #or create a new one if there arent any empty channels
				allocated_receiver = logging_receiver(self.samp_rate)
				try:
					center = self.tb.connect_channel(channel_frequency, allocated_receiver)
				except:
					self.tb.ar_lock.release()
					return False
				self.tb.active_receivers.append(allocated_receiver)
			
			allocated_receiver.tuneoffset(channel_frequency, center)
			allocated_receiver.set_codec_p25(True)
			allocated_receiver.set_codec_provoice(False)
			
			cdr = {
				'system_id': self.system['id'],
				'system_group_local': group,
				'system_user_local': user,
				'system_channel_local': channel,
				'type': 'group',
				'center_freq': center,
				'hang_time': self.hang_time
			}

			allocated_receiver.open(cdr, int(channel_bandwidth))
		self.tb.ar_lock.release()
		return allocated_receiver
	def progress_call(self, channel):
                for receiver in self.tb.active_receivers: #find any active channels and mark them as progressing
                        if receiver.cdr != {} and receiver.cdr['system_channel_local'] == channel and receiver.cdr['system_id'] == self.system['id']:
                                receiver.activity()
	def receive_engine(self):
		print '%s: Receive_engine() start' %self.thread_id
		buf = ''
		data_unit_ids = {
				0x0: 'Header Data Unit',
				0x3: 'Terminator without Link Control',
				0x5: 'Logical Link Data Unit 1',
				0x7: 'Trunking Signaling Data Unit',
				0xA: 'Logical Link Data Unit 2',
				0xC: 'Packet Data Unit',
				0xF: 'Terminator with Link Control'
				}

		channel_timeout = 0.5
		last_chan_status = 0

		loop_start = time()
		loops_locked = 0
		wrong_duid_count = 0

		while True:
			if loops_locked < -100 and time()-loop_start > 2:
				self.tune_next_control_channel()

				loops_locked = 0
				loop_start = time()
			if self.decodequeue.count():
				pkt = self.decodequeue.delete_head().to_string()
                                buf += pkt
			else:
				sleep(0.010) #avg time between packets is 0.007s

			fsoffset = buf.find(binascii.unhexlify('5575f5ff77ff'))
			fsnext   = buf.find(binascii.unhexlify('5575f5ff77ff'), fsoffset+6)
			if(fsoffset != -1 and fsnext != -1):
				if(loops_locked < 100):
					loops_locked = loops_locked + 100

				frame = buf[fsoffset:fsnext]
				buf = buf[fsnext:]
				if len(frame) < 10: continue
				frame_sync = binascii.hexlify(frame[0:6])
				duid = int(ord(frame[7:8])&0xf)
				nac = int(ord(frame[6:7]) +ord(frame[7:8])&0xf0)
				self.total_messages = self.total_messages + 1
				#print 'FSO:%s FSN:%s BS:%s FL:%s - %s - %s' % (fsoffset, fsnext, len(buf), (fsnext-fsoffset), frame_sync, data_unit_ids[duid])
				if duid != 0x7:
					wrong_duid_count = wrong_duid_count +1
					if wrong_duid_count > 50:
						self.tune_next_control_channel()

						loop_start = time()
				                loops_locked = 0
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
						print "%s: ERROR: Unknown DUID %s" % (self.thread_id, duid)
				except Exception as e:
					self.bad_messages = self.bad_messages + 3
					continue
				try:
					r['tsbk']
				except:
					self.bad_messages = self.bad_messages + 3
                                        continue
				for i in range(0, len(r['tsbk'])):
					t = r['tsbk'][i]
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

					if t['name'] == 'IDEN_UP':
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
							'Transmit Offset': t['Transmit Offset']
							}
					elif t['name'] == 'IDEN_UP_VU':
						print '%s: %s' % (self.thread_id, t)
					elif t['name'] == 'GRP_V_CH_GRANT':
						self.new_call(t['Channel'], t['Group Address'], t['Source Address'])
						print '[%s]%s: %s' % (time(), self.thread_id, t)
						pass
					elif t['name'] == 'GRP_V_CH_GRANT_UPDT':
						self.new_call(t['Channel 0'], t['Group Address 0'], 0)
						self.new_call(t['Channel 1'], t['Group Address 1'], 0)
						print '[%s]%s: %s' % (time(), self.thread_id, t)
						pass
					elif t['name'] == 'UU_V_CH_GRANT':
						print '%s: %s' % (self.thread_id, t)
					elif t['name'] == 'UU_ANS_REQ':
						print '%s: %s' % (self.thread_id, t)
					elif t['name'] == 'GRP_V_CH_GRANT_UPDT_EXP':
						print '%s: %s' % (self.thread_id, t)
					elif t['name'] == 'GRP_AFF_RSP':
						print '%s: %s' % (self.thread_id, t)
					elif t['name'] == 'U_REG_RSP':
						print '%s: %s' % (self.thread_id, t)
					#else:
						#print '%s: %s' % (self.thread_id, t)
			else:
				loops_locked = loops_locked - 1
        def quality_check(self):
                bad_messages = self.bad_messages
                total_messages = self.total_messages
                last_total = 0
                last_bad = 0
                while True:
                        sleep(10); #only check messages once per 10second
                        sid = self.system['id']
                        print 'System: ' + str(sid) + ' (' + str(self.total_messages-last_total) + '/' + str(self.bad_messages-last_bad) + ')' + ' (' +str(self.total_messages) + '/'+ str(self.bad_messages) + ') CC: ' + str(self.control_channel) + ' AR: ' + str(len(self.tb.active_receivers))
                        last_total = self.total_messages
                        last_bad = self.bad_messages

# Demodulator frequency tracker
#
class demod_watcher(threading.Thread):

    def __init__(self, msgq,  callback, **kwds):
        threading.Thread.__init__ (self, **kwds)
        self.setDaemon(1)
        self.msgq = msgq
        self.callback = callback
        self.keep_running = True
        #self.start()

    def run(self):
        while(self.keep_running):
            msg = self.msgq.delete_head()
            frequency_correction = msg.arg1()
            print 'Freq correction %s' % (frequency_correction)
            self.callback(frequency_correction)
