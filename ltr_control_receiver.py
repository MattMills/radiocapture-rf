#!/usr/env/python

from gnuradio import gr, digital, blocks, filter, analog
try:
        from gnuradio.gr import firdes
except:
        from gnuradio.filter import firdes


import string
import time
import os
import random
import threading
from logging_receiver import logging_receiver

class ltr_control_receiver(gr.hier_block2):
	def __init__(self, system, samp_rate, sources, top_block, block_id):
		gr.hier_block2.__init__(self, "ltr_control_receiver",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
                                gr.io_signature(0, 0, 0)) # Output signature
	
		self.tb = top_block
		self.sources = sources
		self.system = system
		self.samp_rate = samp_rate
		self.block_id = block_id

		self.audio_rate = audio_rate = 12500
		self.symbol_rate = symbol_rate = system['symbol_rate']
		self.channels = channels = system['channels']
		self.channels_list = self.channels.keys()
		self.control_channel_key = 0
                self.control_channel = control_channel = self.channels[self.channels_list[0]]
		self.control_source = 0

		self.thread_id = '%s-%s' % (self.system['type'], self.system['id'])

		self.bad_messages = 0
		self.total_messages = 0

		self.is_locked = False


		################################################
		# Blocks
		################################################
	

		control_samp_rate = 12500
		control_channel_rate = control_samp_rate #Channel rate must be higher for clock recovery
		decimation_s1 = int(samp_rate/(control_samp_rate*1.5))
		post_decimation_samp_rate = int(samp_rate/decimation_s1)

		print 'Decimation: %s' % (decimation_s1)

		self.taps = taps = firdes.low_pass(1, samp_rate, control_channel_rate/2, (control_channel_rate/2)*0.25, firdes.WIN_HAMMING,6.76)

        	self.control_prefilter = filter.freq_xlating_fir_filter_ccc(decimation_s1, (taps), self.control_channel-self.sources[self.control_source]['center_freq'], samp_rate)
		self.control_squelch = analog.simple_squelch_cc(-63, 1)

		self.control_quad_demod = analog.quadrature_demod_cf(3)
		new_samp_rate = samp_rate/decimation_s1

		self.control_low_pass = filter.fir_filter_fff(1, firdes.low_pass(1, new_samp_rate, 425, 425*0.1, firdes.WIN_HAMMING, 6.76))
		self.control_add_const = blocks.add_const_vff((-0.25, ))
		self.control_clock_recovery = digital.clock_recovery_mm_ff(new_samp_rate/symbol_rate, 0.25*0.175*0.175, 0.5, 0.175, 0.005)
                self.control_binary_slicer = digital.binary_slicer_fb()
		self.control_unpacked_to_packed = blocks.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
		self.control_msg_queue = gr.msg_queue(1024)
		self.control_msg_sink = blocks.message_sink(gr.sizeof_char, self.control_msg_queue,True)

		self.source = self

		################################################
		# Connections
		################################################
	
		self.connect(   self.source,
                                self.control_prefilter,
				#self.control_squelch,
                                self.control_quad_demod,
				self.control_low_pass,
				self.control_add_const, #This is super hacky, I hate myself :(
                                self.control_clock_recovery,
                                self.control_binary_slicer,
                                self.control_unpacked_to_packed,
				self.control_msg_sink)


		###############################################
		control_decode_0 = threading.Thread(target=self.control_decode)
		control_decode_0.daemon = True
		control_decode_0.start()

                quality_check_0 = threading.Thread(target=self.quality_check)
                quality_check_0.daemon = True
                quality_check_0.start()



	def tune_next_control_channel(self):
                self.control_channel_key += 1
                if(self.control_channel_key >= len(self.channels_list)):
                        self.control_channel_key = 0

		self.control_lcn = self.control_channel_key
                self.control_channel = self.channels[self.channels_list[self.control_channel_key]]
		
		self.control_source = self.tb.retune_control(self.block_id, self.control_channel)
	
                self.control_prefilter.set_center_freq(self.control_channel-self.sources[self.control_source]['center_freq'])
                print 'CC Change - %s - %s - %s' % (self.control_channel, self.sources[self.control_source]['center_freq'], self.sources[self.control_source]['center_freq']-self.control_channel)
                self.control_msg_queue.flush()
                time.sleep(0.1)



		#self.tune_control_channel()

        def recv_pkt(self):
                return self.control_msg_queue.delete_head().to_string()
        def build_audio_channel(self, c):
		allocated_receiver = logging_receiver(self.samp_rate)
		center = self.tb.connect_channel(self.channels[c], allocated_receiver)
		self.tb.active_receivers.append(allocated_receiver)
		
		return (allocated_receiver, center)
		

        def binary_invert(self, s):
                r = ''
                for c in s:
                        if(c == '0'): r = r + '1'
                        else: r = r + '0'
                return r

        def quality_check(self):
		bad_messages = self.bad_messages
		total_messages = self.total_messages
                last_total = 0
                last_bad = 0
                while True:
                        time.sleep(10); #only check messages once per 10second
                        sid = self.system['id']
                        print 'System: %s (%s / %s) (%s / %s) CC: %s AR: %s' %(sid, (self.total_messages-last_total),(self.bad_messages-last_bad),self.total_messages,self.bad_messages,self.control_channel,len(self.tb.active_receivers))
                        last_total = self.total_messages
                        last_bad = self.bad_messages

        def new_call_individual(self, system, channel, callee_logical_id, caller_logical_id, tx_trunked, provoice = False):
		self.tb.ar_lock.acquire()
		reciever = False
		while receiver == False:# or receiver.get_lock() != self.thread_id:
	                (receiver,center) = self.get_receiver(system, channel)
                #receiver.set_call_details_individual(system, callee_logical_id, caller_logical_id, channel, tx_trunked)
                receiver.tuneoffset(system['channels'][channel], self.center_freq)
                receiver.set_codec_provoice(False)
		receiver.set_codec_p25(False)
                cdr = {
                        'system_id': self.system['id'],
			'system_type': self.system['type'],
                        'system_callee_local': callee_logical_id,
                        'system_caller_local': caller_logical_id,
                        'system_channel_local': channel,
                        'type': 'individual',
                        'center_freq': center
                }
		receiver.open(cdr, self.audio_rate)
		self.tb.ar_lock.release()
        def get_receiver(self, system, channel):
                free_al = []
                for v in self.tb.active_receivers:
                        if(v.in_use == False): free_al.append(v)
                        if(v.cdr != {} and v.cdr['system_id'] == system['id'] and v.cdr['system_channel_local'] == channel and v.in_use == True):
                                print 'emergency close of open audiologger for new traffic'
                                v.close(self.patches, True, True)
                                receiver = v
				center = receiver.center_freq
				return (receiver,center)
		for v in free_al:
			if abs(v.center_freq-system['channels'][channel]) < (self.samp_rate/2):
	                	receiver = v
				center = receiver.center_freq
				return (receiver,center)

		(receiver, center) = self.build_audio_channel(channel)
                return (receiver,center)
	def get_checksum(self, area, goto, home, group, free):
		checksum = 0
		
		if area == 1:
			checksum = checksum ^ 0x38

		if (goto & 0b10000) >> 4:
			checksum = checksum ^ 0x1c
		if (goto & 0b01000) >> 3:
                        checksum = checksum ^ 0x0e
		if (goto & 0b00100) >> 2:
                        checksum = checksum ^ 0x46
		if (goto & 0b00010) >> 1:
                        checksum = checksum ^ 0x23
		if (goto & 0b00001):
                        checksum = checksum ^ 0x51

		if (home & 0b10000) >> 4:
                        checksum = checksum ^ 0x68
                if (home & 0b01000) >> 3:
                        checksum = checksum ^ 0x75
                if (home & 0b00100) >> 2:
                        checksum = checksum ^ 0x7a
                if (home & 0b00010) >> 1:
                        checksum = checksum ^ 0x3d
                if (home & 0b00001):
                        checksum = checksum ^ 0x1f

		if (group & 0b10000000) >> 7:
                        checksum = checksum ^ 0x4f
		if (group & 0b01000000) >> 6:
                        checksum = checksum ^ 0x26
		if (group & 0b00100000) >> 5:
                        checksum = checksum ^ 0x52
		if (group & 0b00010000) >> 4:
                        checksum = checksum ^ 0x29
                if (group & 0b00001000) >> 3:
                        checksum = checksum ^ 0x15
                if (group & 0b00000100) >> 2:
                        checksum = checksum ^ 0x0b
                if (group & 0b00000010) >> 1:
                        checksum = checksum ^ 0x45
                if (group & 0b00000001):
                        checksum = checksum ^ 0x62

		if (free & 0b10000) >> 4:
                        checksum = checksum ^ 0x31
                if (free & 0b01000) >> 3:
                        checksum = checksum ^ 0x19
                if (free & 0b00100) >> 2:
                        checksum = checksum ^ 0x0d
                if (free & 0b00010) >> 1:
                        checksum = checksum ^ 0x07
                if (free & 0b00001):
                        checksum = checksum ^ 0x43
		
		return checksum

	def control_decode(self):
		print self.thread_id + ': control_decode() start'

	        self.buf = buf = ''
		self.total_messages = total_messages = 0
		self.bad_messages = bad_messages =  0
		self.failed_loops = failed_loops =  0
	        self.loop_start = loop_start = time.time()
		system = self.system

		fs = '101011000'

	        while(1):

                        pkt = self.recv_pkt()
                        for b in pkt:
                                buf = buf + str("{0:08b}" . format(ord(b)))
                        if(len(buf) > 40*4):
                                print 'Buffer Overflow ' + str(len(buf))
                        while(len(buf) > 40): #frame+framesync len in binary is 40
				find_fs = buf.find(fs)
				if find_fs == -1:
					buf = ''
				else:
					frame = buf[find_fs:find_fs+40]
					if len(frame) < 40: 
						break
					r = {}
					r['fs'] = int(frame[:9],2)
					r['area'] = int(frame[9:10],2)
					r['goto'] = int(frame[10:15],2)
					r['home'] = int(frame[15:20],2)
					r['group'] = int(frame[20:28],2)
					r['free'] = int(frame[28:33],2)
					r['crc'] = int(frame[33:40],2)
					
					buf = buf[find_fs+40:]

					checksum = self.get_checksum(r['area'], r['goto'], r['home'], r['group'], r['free'])

					GREEN = '\033[92m'
					RED = '\033[91m'
					ENDC = '\033[0m'

					if checksum == r['crc']:
						color = '%sPASS%s ' % (GREEN, ENDC)
					else:
						color = '%sFAIL%s ' % (RED, ENDC)

					if(r['group'] == 255):
						print 'OSW: %s %s %s %s %s %s %s - IDLE LCN=%s' % (color, r['area'], r['goto'], r['home'], r['group'], r['free'], hex(r['crc']), r['goto'])
					elif r['goto'] == 31:
						print 'OSW: %s %s %s %s %s %s %s - END LCN=%s' % (color, r['area'], r['goto'], r['home'], r['group'], r['free'], hex(r['crc']), r['goto'])
					else:
						print 'OSW: %s %s %s %s %s %s %s - ACTV GROUP=%s-%s-%s FREE=%s LCN=%s' % (color, r['area'], r['goto'], r['home'], r['group'], r['free'], hex(r['crc']), r['area'], r['home'], r['group'], r['free'], r['goto'])
				#print '%s' % fram
			
			
