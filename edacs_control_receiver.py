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

class edacs_control_receiver(gr.hier_block2):
	def __init__(self, system, samp_rate, sources, top_block, block_id):
		gr.hier_block2.__init__(self, "edacs_control_receiver",
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
		self.control_channel_key = 8
                self.control_channel = control_channel = self.channels[self.channels_list[0]]
		self.control_source = 0

		self.thread_id = '%s-%s' % (self.system['type'], self.system['id'])

		#self.control_lcn = control_lcn = 1
		self.bad_messages = 0
		self.total_messages = 0

		self.is_locked = False

		#self.control_lcn_alt.insert(0, self.control_lcn) # add primary LCN to end of alternate list

		################################################
		# Blocks
		################################################
	

		control_samp_rate = 12500
		control_channel_rate = control_samp_rate*3 #Channel rate must be higher for clock recovery
		decimation_s1 = int(samp_rate/control_channel_rate)
		post_decimation_samp_rate = int(samp_rate/decimation_s1)

		print 'Decimation: %s' % (decimation_s1)

		self.taps = taps = firdes.low_pass(5, samp_rate, control_channel_rate/2, control_channel_rate/2*0.55, firdes.WIN_HAMMING)

		#self.set_max_output_buffer(100000)
        	self.control_prefilter = filter.freq_xlating_fir_filter_ccc(decimation_s1, (taps), 0, samp_rate)
		try:
			self.control_quad_demod = gr.quadrature_demod_cf(5)
		except:
			self.control_quad_demod = analog.quadrature_demod_cf(5)
		self.control_clock_recovery = digital.clock_recovery_mm_ff(samp_rate/decimation_s1/symbol_rate, 1.4395919, 0.5, 0.05, 0.005)
                self.control_binary_slicer = digital.binary_slicer_fb()
		try:
			self.control_unpacked_to_packed = gr.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
		except:
			self.control_unpacked_to_packed = blocks.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
		self.control_msg_queue = gr.msg_queue(1024)
		try:
			self.control_msg_sink = gr.message_sink(gr.sizeof_char, self.control_msg_queue,True)
		except:
			self.control_msg_sink = blocks.message_sink(gr.sizeof_char, self.control_msg_queue,True)

		#offset measurement
                #moving_sum = gr.moving_average_ff(10000, 1, 40000)
                #subtract = blocks.sub_ff(1)
                #divide_const = blocks.multiply_const_vff((0.0001, ))
                #self.probe = gr.probe_signal_f()

		#Local websocket output
		#self.websocket_sink = gr.udp_sink(gr.sizeof_char, "127.0.0.1", (10000+self.system['id']), 1472, True)
		#self.connect(self.control_unpacked_to_packed, self.websocket_sink)

		#self.connect(self.control_freq_xlating_fir_filter, self.udp_sink)
	
		#self.null_sink0 = gr.null_sink(gr.sizeof_gr_complex*1)
                #self.null_sink1 = gr.null_sink(gr.sizeof_gr_complex*1)

		self.source = self
		################################################
		# Connections
		################################################
	
		self.connect(   (self.source, self.control_source),
                                self.control_prefilter,
                                self.control_quad_demod,
                                self.control_clock_recovery,
                                self.control_binary_slicer,
                                self.control_unpacked_to_packed,
				self.control_msg_sink)

		#self.connect(self.control_quad_demod, moving_sum, divide_const, self.probe)
		
		#self.connect((self.source,0), self.null_sink0)
                #self.connect((self.source,1), self.null_sink1)

		###############################################
		self.patches = {}
		self.patch_timeout = 3 #seconds

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

        def message_election(self, m1, m2, m3):
                words = [m1, m2, m3]
                decoded = [self.bch_decode('00000000'+x) for x in words]

                dm1 = decoded[0][0][8:]
                dm2 = decoded[1][0][8:]
                dm3 = decoded[2][0][8:]

                if(dm1 == dm2 == dm3 == ''): return -1
                if(dm1 == dm2 == '' and dm3 != ''): return dm3
                if(dm1 == dm3 == '' and dm2 != ''): return dm2
                if(dm2 == dm3 == '' and dm1 != ''): return dm1

                if(dm1 == dm2 or dm1 == dm3):
                        return dm1
                elif(dm2 == dm3):
                        return dm2
                return -1
        def proc_cmd(self, system, m1, m2 = -1):
                r = {}
                m = ''

                mta = m1[:3]
                #if(mta == '010'):
                #       if(m1 == -1 or m2 == -1): return False
                #       r['logical_id'] = int(m1[3:10] + m2[3:10], 2)
                #       r['channel'] = int(m1[11:16],2)
                #       r['tx_trunked'] = int(m1[16:17],2)
                #       r['group'] = int(m1[17:28])
                #       
                #       print 'Chan Assignment - Group Voice - ' + str(r)
                #elif(mta == '011'):
                #       if(m1 == -1 or m2 == -1): return False
                #       r['logical_id'] = int(m1[3:10] + m2[3:10], 2)
                #       r['channel'] = int(m1[11:16],2)
                #       r['tx_trunked'] = int(m1[16:17],2)
                #       r['group'] = int(m1[17:28])
                #
                #       print 'Chan Assignment - Emergency Group Voice - ' + str(r)
                if(mta=='000' or mta == '010' or mta == '011' or mta == '101'):
                        if(m1 == -1 or m2 == -1): return False
                        r['logical_id'] = int(m1[3:10] + m2[4:11], 2)
                        r['channel'] = int(m1[11:16],2)
                        r['tx_trunked'] = bool(int(m1[16:17],2))
                        r['group'] = int(m1[17:28],2 )

                        m = 'Chan Assignment - Data - ' + str(r)
                        if( r['channel'] in system['channels'].keys() and r['channel'] != self.control_lcn): # nd r['group'] == 609): #and r['channel'] in self.wav_sinks):
                                self.new_call_group(system, r['channel'], r['group'], r['logical_id'], r['tx_trunked'])
                elif(mta == '111'):
                        mtb = m1[3:6]
                        if(mtb == '010'):
                                r = r
                                m = 'Unknown MTB 010'
                                #unknown
                        elif(mtb == '011'): #Channel Update
                                r['mtc'] = int(m1[6:8], 2)
                                r['channel'] = int(m1[8:13],2)
                                r['individual'] = int(m1[13:14],2)
                                r['id'] = int(m1[14:28],2)

                                #if(r['channel'] in active_channels):
                                channel_matched = False
                                for v in self.tb.active_receivers:
                                        if(v.cdr != {} and v.in_use and v.cdr['system_id'] == system['id'] and v.cdr['system_channel_local'] == r['channel']):
                                                v.activity()
                                                channel_matched = True

                                if(not channel_matched and r['mtc'] != 1 and r['mtc'] != 0):
                                        if( r['channel'] in system['channels'].keys() and r['channel'] != self.control_lcn):
                                                if(r['individual'] == 0):
                                                        if(r['mtc'] == 3):
                                                                self.new_call_group(system, r['channel'],r['id'], 0, False, True)
                                                        else:
                                                                self.new_call_group(system, r['channel'],r['id'], 0, False)

                                                else:
							pass
                                                        #self.new_call_individual(system, r['channel'] ,0, r['id'], False)

                                        #active_channels[r['channel']] = time()
                                m = 'Channel Update - ' + str(r)
                        elif(mtb == '100'):
                                r['sgid'] = int(m1[6:17],2)
                                r['group'] = int(m1[17:28], 2)

                                m = 'Patch - ' + str(r)
				if(r['sgid'] in self.patches):
					self.patches[r['sgid']][r['group']] = time.time()
				else:
					self.patches[r['sgid']] = {r['group']: time.time()}
						
                        elif(mtb == '101'): #Individual call channel assignment
                                if(m1 == -1 or m2 == -1): return False
                                r['tx_trunked'] = True if m1[6:7] == '1' else False
                                r['channel'] = int(m1[8:13], 2)
                                r['call_type'] = 'Voice' if m1[13:14] == '1' else 'UNKNOWN'
                                r['callee_logical_id'] = int(m1[14:28], 2)
                                r['caller_logical_id'] = int(m2[14:28], 2)

                                m = 'iCall - ' + str(r)
                                if( r['channel'] in system['channels'].keys() and r['channel'] != self.control_lcn): # nd r['group'] == 609): #and r['channel'] in self.wav_sinks):
                                        #check if channel is already tuned to
					pass
                                        #self.new_call_individual(system, r['channel'], r['callee_logical_id'], r['caller_logical_id'], r['tx_trunked'])
                        elif(mtb == '110'):
                                r['drop'] = True if m1[8:9] == '1' else False
                                r['unkey'] = True if m1[8:9] == '0' else False
                                r['channel'] = int(m1[9:14], 2)

                                m = 'Channel unkey/drop - ' + str(r)
                        elif(mtb == '111'):
                                mtd = m1[6:11]
                                if(mtd == '00001'): #adjacent site control channel
                                        r['ccaddr'] = int(m1[11:16],2)
                                        r['index'] = int(m1[16:19], 2)
                                        r['site_id'] = int(m1[19:22],2)

                                        #m = 'Adjacent site control channel - ' + str(r)
                                elif(mtd == '00010'): #extended site options
                                        r['messageno'] = int(m1[12:15], 2)
                                        r['data'] = int(m1[15:28],2)

                                        #m = 'Extended site options - ' +str(r)
                                elif(mtd == '00100'): #System dynamic regroup plan bitmap
                                        r['bank'] = int(m1[11:12], 2)
                                        r['residency'] = int(m1[12:20], 2)
                                        r['active'] = int(m1[20:28], 2)

                                        m = 'System dynamic regroup plan bitmap - ' +str(r)
                                elif(mtd == '00111'): #Unit disable/enable
                                        r['qualifier'] = int(m1[12:14], 2)
                                        r['logical_id'] = int(m1[14:28], 2)

                                        m = 'Unit disable/enable - ' + str(r)
                                elif(mtd[:3] == '010'): #SiteID (MTD = 010xx)
                                        r['delay'] = int(m1[9:11],2)
                                        r['channel'] = int(m1[11:16],2)
                                        r['priority'] = int(m1[16:19], 2)
                                        r['trunking'] = int(m1[20:21], 2)
                                        r['failsoft'] = int(m1[21:22], 2)
                                        r['auxmain'] = int(m1[22:23], 2)
                                        r['site_id'] = int(m1[23:28], 2)

                                        #m = 'SiteID - ' + str(r)
                                elif(mtd[:1] == '1'):   #Dynamic regroup
                                        if(m1 == -1 or m2 == -1): return False
                                        r['fleet_bits'] = m1[11:14]
                                        r['logical_id'] = int(m1[14:28], 2)
                                        r['plan_number'] = int(m2[7:11], 2)
                                        r['regroup_type'] = int(m2[11:13], 2)
                                        r['knob_setting'] = int(m2[13:16], 2)
                                        r['callee_logical_id'] = int(m2[17:28], 2)
                                        m = 'Dynamic regroup - ' + str(r)
                                else:
                                        m = 'unknown MTD ' + mtd
                        else:
                                m= 'Unknown MTB' + mtb
                else:
                        m= 'Unknown MTA ' + mta
                if(m2 == -1 and m != ''):
                        print "(%s)[%s] %s" %(time.time(),hex(int(m1, 2)), m)
                elif( m != ''):
                        print "(%s)[%s][%s] %s" %(time.time(),hex(int(m1, 2)), hex(int(m2,2)), m)
        def is_double_message(self, m1):
                if(m1 == -1): return True
                mta = m1[:3]
                if( mta == '000' or mta == '010' or mta == '011' or mta == '101'):
                        return True
                elif(mta == '111'):
                        mtb = m1[3:6]
                        if(mtb == '011' or mtb == '101'):
                                return True
                        elif(mtb == '111'):
                                mtd = m1[6:11]
                                if(mtd[:1] == '1'):
                                        return True

                return False
        def quality_check(self):
                #global bad_messages, total_messages
		bad_messages = self.bad_messages
		total_messages = self.total_messages
                #dbc = query_handler()
                last_total = 0
                last_bad = 0
                while True:
                        time.sleep(10); #only check messages once per 10second
                        sid = self.system['id']
                        print 'System: ' + str(sid) + ' (' + str(self.total_messages-last_total) + '/' + str(self.bad_messages-last_bad) + ')' + ' (' +str(self.total_messages) + '/'+ str(self.bad_messages) + ') CC: ' + str(self.control_channel) + ' AR: ' + str(len(self.tb.active_receivers))
                        #dbc.query('insert into signal_record (total, bad, timestamp, system) values (%s, %s, CURRENT_TIMESTAMP, %s)' % ((total_messages[sid]-last_total[sid]), (bad_messages[sid]-last_bad[sid]), sid))
                        last_total = self.total_messages
                        last_bad = self.bad_messages

        def new_call_group(self, system, channel, group, logical_id, tx_trunked, provoice = False):
		self.tb.ar_lock.acquire()
		receiver = False
		while receiver == False:# or receiver.get_lock() != self.thread_id:
	                (receiver,center) = self.get_receiver(system, channel)
                #receiver.set_call_details_group(system, logical_id, channel, tx_trunked, group)
                print 'Tuning new group call - %s %s' % ( system['channels'][channel], center)
                receiver.tuneoffset(system['channels'][channel], center)
                receiver.set_codec_provoice(provoice)
		receiver.set_codec_p25(False)
		cdr = {
			'system_id': self.system['id'], 
			'system_type': self.system['type'],
			'system_group_local': group,
			'system_user_local': logical_id,
			'system_channel_local': channel,
			'type': 'group',
			'center_freq': center
		}
		receiver.open(cdr, self.audio_rate)
		self.tb.ar_lock.release()
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

        def packet_framer(self, system, frame, bad_messages, total_messages):
                m1_1 = frame[0:40]
                m1_2 = self.binary_invert(frame[40:80])
                m1_3 = frame[80:120]
                m2_1 = frame[120:160]
                m2_2 = self.binary_invert(frame[160:200])
                m2_3 = frame[200:240]

                total_messages = total_messages + 2;
                if(len(m1_1) != 40 or len(m1_2) != 40 or len(m1_3) != 40):
                        bad_messages = bad_messages + 1
                        m1_1 = m1_2 = m1_3 = '0000000000000000000000000000000000000000'
                if(len(m2_1) != 40 or len(m2_2) != 40 or len(m2_3) != 40):
                        bad_messages = bad_messages + 1
                        m2_1 = m2_2 = m2_3 = '0000000000000000000000000000000000000000'

                m1 = self.message_election(m1_1, m1_2, m1_3)
                m2 = self.message_election(m2_1, m2_2, m2_3)

                if(system['esk']):
                        if(m1 != -1): m1 = str("{0:04b}" . format(int(m1[:4], 2)|0xA)) + m1[4:]
                        if(m2 != -1): m2 = str("{0:04b}" . format(int(m2[:4], 2)|0xA)) + m2[4:]
                return (m1, m2, bad_messages, total_messages)
        def get_next_frame(self, system, buf):
		failed_loops = self.failed_loops
		loop_start = self.loop_start
		framesync = self.framesync

                find_fs = buf.find(framesync)
                find_fsi = buf.find(self.binary_invert(framesync));
                if(find_fsi > -1):
                        frame = self.binary_invert(buf[find_fsi+48:find_fsi+48+240])
                        buf = buf[find_fsi+288:]
                elif(find_fs > -1):
                        frame = buf[find_fs+48:find_fs+48+240]
                        buf = buf[find_fs+288:]
                else:
                        self.failed_loops = self.failed_loops + 1
                        buf = buf[288:]
                        if(self.failed_loops > 100 and loop_start+2 < time.time()):
                                #print 'Failed loops: ' + str(self.failed_loops)

                                self.failed_loops = 0
                                self.loop_start = time.time()

                                print 'Cant get framesync lock, SYS: %s trying next control ' % (self.system['id'])
				self.is_locked = False
                                self.tune_next_control_channel()
                                buf = ''
                        return (buf, False)
                if(len(frame) < 240):
                        print 'Buffer Underrun in Framer: ' + str(len(frame))
                if(self.failed_loops > -1000):
                        self.failed_loops = self.failed_loops - 10
		else: # if their have been >100 non failed loops we should signify a signal lock for freq tuning
			self.is_locked = True
                loop_start = time.time()
                return (buf, frame)
        def process_commands(self, m1, m2, bad_messages):
                if((m1 == -1 or m2 == -1) and  self.is_double_message(m1) == True):
                        bad_messages = bad_messages + 2
                elif(self.is_double_message(m1) == True):
                        self.proc_cmd(self.system, m1, m2)
                else:
                        if(m1 == -1): bad_messages = bad_messages + 1
                        else: self.proc_cmd(self.system, m1)

                        if(m2 == -1): bad_messages = bad_messages + 1
                        else: self.proc_cmd(self.system, m2)
                return bad_messages
###########################################
# bch
###########################################
        _M, _N, _L, _K,  = 6, 63, 48, 36

        _GF_ALPHA = [1,2,4,8,16,32,3,6,12,24,48,35,5,10,20,40,19,38,15,30,60,59,53,41,17,34,7,14,28,56,51,37,9,18,36,11,22,44,27,54,47,29,58,55,45,25,50,39,13,26,52,43,21,42,23,46,31,62,63,61,57,49,33,0]
        _GF_IDX = [-1,0,1,6,2,12,7,26,3,32,13,35,8,48,27,18,4,24,33,16,14,52,36,54,9,45,49,38,28,41,19,56,5,62,25,11,34,31,17,47,15,23,53,51,37,44,55,40,10,61,46,30,50,22,39,43,29,60,42,21,20,59,57,58]

        def bch_decode(self, recd):
  	  _M, _N, _L, _K,  = 6, 63, 48, 36

          _GF_ALPHA = [1,2,4,8,16,32,3,6,12,24,48,35,5,10,20,40,19,38,15,30,60,59,53,41,17,34,7,14,28,56,51,37,9,18,36,11,22,44,27,54,47,29,58,55,45,25,50,39,13,26,52,43,21,42,23,46,31,62,63,61,57,49,33,0]
          _GF_IDX = [-1,0,1,6,2,12,7,26,3,32,13,35,8,48,27,18,4,24,33,16,14,52,36,54,9,45,49,38,28,41,19,56,5,62,25,11,34,31,17,47,15,23,53,51,37,44,55,40,10,61,46,30,50,22,39,43,29,60,42,21,20,59,57,58]
          """decode BCH(48,36,5), return tuple(decoded 36 bits, (err locations)).
             @recd - the received 48 bit, ordered by: 8_bit_COLOR_0, 28_bit_MSG, 12_bit_parity.     
             @return - check if the decoded msg is empty firstly!! you may use only data[8:8+28] slice.
             @return - error location is described as in the @recd 48 bit range! 
          """
          syn_err = False
          s = [0,0,0,0,0]
          s3 = 0
          elp = [0,0,0]
          loc = []
          reg = [0,0,0]

          #validate the input: string of 48 '0'|'1'.
          if len(recd)!=48 or [x for x in recd if (x!='0' and x!='1')] : return ('', loc)

          data = [int(x) for x in recd[::-1]]+[0]*15
          #print "data:", "".join([str(x) for x in data])

          for i in range(1, 5):
             s[i] = 0
             for j in [x for x in range(0, _L) if data[x]==1]:
                s[i] ^= _GF_ALPHA[(i*j) % _N]
             if s[i]!=0 : syn_err = True
             s[i] = _GF_IDX[s[i]];

          #print "s", s[1:]

          if not syn_err:   return (''.join(str(x) for x in data[47::-1]), loc)

          if s[1] != -1:
             s3 = (s[1]*3)%_N
             if s[3]==s3:
                data[s[1]] ^= 1
                loc += [s[1]]
             else:
                if s[3]==-1:
                   aux = _GF_ALPHA[s3]
                else :
                   aux = _GF_ALPHA[s3]^_GF_ALPHA[s[3]]
                #print "s3=", s3," ", "aux=",aux
                elp[0], elp[1], elp[2] =  0, (s[2]-_GF_IDX[aux]+_N)%_N, (s[1]-_GF_IDX[aux]+_N)%_N
                #print "elp/sigma=",elp
                reg[1], reg[2] = elp[1], elp[2]
                for i in range(1,64):
                   q = 1
                   for j in range(1,3):
                       if reg[j] != -1:
                          reg[j] = (reg[j]+j)%_N
                          q ^= _GF_ALPHA[reg[j]];
                   if q==0:  loc += [i%_N]
                if len(loc) == 2 : data[loc[0]],data[loc[1]] = data[loc[0]]^1, data[loc[1]] ^ 1
                else:
                   data = ()
                   loc = [-100]
                   #print "incomplete decoded."
          elif s[2]!=-1:
              data = ()
              loc += [-200]
              #print "incomplete decoded."

          if [x for x in loc if x>_L-1]: data = ()

          return (''.join(str(x) for x in data[47::-1]), [i if i<0 else _L-i-1   for i in loc   ])
############################################################################################################

	def control_decode(self):
		print self.thread_id + ': control_decode() start'
	        self.framesync = framesync = '010101010101010101010111000100100101010101010101'
	        self.buf = buf = ''
		self.total_messages = total_messages = 0
		self.bad_messages = bad_messages =  0
		self.failed_loops = failed_loops =  0
	        self.loop_start = loop_start = time.time()
		system = self.system

	        while(1):
			for patch in self.patches:
				deletes = []
				for group in self.patches[patch]:
					if ((time.time()-self.patches[patch][group]) > self.patch_timeout):
						#del newpatches[patch][group]
						deletes.append(group)
				for group in deletes:
					del self.patches[patch][group]
		
			deletes = []
			for patch in self.patches:
				if len(self.patches[patch]) == 0:
					deletes.append(patch)

			for patch in deletes:
				print 'Patch closed ' + str(patch)
				del self.patches[patch]

                        pkt = self.recv_pkt()
                        for b in pkt:
                                buf = buf + str("{0:08b}" . format(ord(b)))
                        if(len(buf) > 288*4):
                                print 'Buffer Overflow ' + str(len(buf))
                        while(len(buf) > 288*3): #frame+framesync len in binary is 288; buffer 4 frames
                                buf, frame = self.get_next_frame(system, buf)
                                if(frame == False): continue #Failed to get packet
                                m1, m2, self.bad_messages, self.total_messages = self.packet_framer(system, frame, self.bad_messages, self.total_messages)
                                self.bad_messages = self.process_commands(m1, m2, self.bad_messages)
