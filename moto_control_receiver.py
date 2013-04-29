#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Moto Smartzone Test1
# Generated: Thu Oct  4 23:49:39 2012
##################################################

from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr, blocks
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.gr import firdes
from optparse import OptionParser

import binascii
#import baz
import time
import threading

from logging_receiver import logging_receiver

class moto_control_receiver(gr.hier_block2):

	def __init__(self, system, samp_rate, sources, top_block, block_id):

                gr.hier_block2.__init__(self, "moto_control_receiver",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
                                gr.io_signature(0, 0, 0)) # Output signature

		##################################################
		# Variables
		##################################################
		self.tb = top_block
		self.packets = 0
		self.packets_bad = 0
		self.symbol_rate = symbol_rate = 3600.0
		self.samp_rate = samp_rate
		self.control_source = 0
		self.block_id = block_id
		
		self.offset = offset = 0
		self.is_locked = False

		self.system = system
		print system
		self.system_id = system['id']
		self.sources = sources
		self.channels = system['channels']
		self.channels_list = self.channels.keys()

		self.thread_id = '%s-%s' % (self.system['type'], self.system_id)


		print self.channels
		print self.channels_list

		self.control_channel_key = 0
		self.control_channel = control_channel = self.channels[self.channels_list[0]]

		##################################################
		# Message Queues
		##################################################
		self.control_msg_sink_msgq = gr.msg_queue(1024)

		##################################################
		# Threads
		##################################################

		receive_engine = threading.Thread(target=self.receive_engine)
		receive_engine.daemon = True
		receive_engine.start()

                quality_check = threading.Thread(target=self.quality_check)
                quality_check.daemon = True
                quality_check.start()

		##################################################
		# Blocks
		##################################################

		self.source = self

		control_sample_rate = 10000
		channel_rate = control_sample_rate*3
		self.f1d = f1d = int(samp_rate/channel_rate) #filter 1 decimation
		#self.set_max_output_buffer(100000)
		self.control_prefilter_taps = firdes.low_pass(5,samp_rate,(control_sample_rate/2), (control_sample_rate*0.5))
		self.control_prefilter = gr.freq_xlating_fir_filter_ccc(f1d, (self.control_prefilter_taps), 100000, samp_rate)
		self.control_quad_demod = gr.quadrature_demod_cf(0.1)
		#(omega, gain_omega, mu, gain_mu, omega_relative_limit)
		#(samp_rate/f1d/symbol_rate, 1.4395919, 0.5, 0.05, 0.005)
		#(samp_rate/f1d/symbol_rate, 0.000025, 0.5, 0.01, 0.3)
		moving_sum = gr.moving_average_ff(1000, 1, 4000)
		#subtract = blocks.sub_ff(1)
		divide_const = blocks.multiply_const_vff((0.001, ))
		self.probe = gr.probe_signal_f()


		self.control_clock_recovery = digital.clock_recovery_mm_ff(samp_rate/f1d/symbol_rate, 1.4395919, 0.5, 0.05, 0.005)
		self.control_binary_slicer = digital.binary_slicer_fb()
		self.control_byte_pack = gr.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
		self.control_msg_sink = gr.message_sink(gr.sizeof_char*1, self.control_msg_sink_msgq, True)
		self.udp = gr.udp_sink(gr.sizeof_gr_complex*1, "127.0.0.1", self.system_id, 1472, True)
	
		##################################################
		# Connections
		##################################################
		self.connect(self.control_quad_demod, moving_sum, divide_const, self.probe)

		self.connect(self.control_prefilter, self.control_quad_demod, self.control_clock_recovery)
		self.connect(self.control_clock_recovery, self.control_binary_slicer, self.control_byte_pack, self.control_msg_sink)
		self.connect(self.control_prefilter, self.udp)
		
		self.connect(self.source, self.control_prefilter)

	def get_msgq(self):
		return self.control_msg_sink_msgq.delete_head().to_string()
	def tune_next_control(self):
                self.control_channel_key += 1
                if(self.control_channel_key >= len(self.channels_list)):
                        self.control_channel_key = 0
                self.control_channel = self.channels[self.channels_list[self.control_channel_key]]

		self.control_source = self.tb.retune_control(self.block_id, self.control_channel)
		self.control_prefilter.set_center_freq(self.sources[self.control_source]['center_freq']-self.control_channel)

		print 'CC Change - %s - %s - %s' % (self.control_channel, self.sources[self.control_source]['center_freq'], self.sources[self.control_source]['center_freq']-self.control_channel)
		self.control_msg_sink_msgq.flush()
		time.sleep(0.1)

        def quality_check(self):
                #global bad_messages, total_messages
                bad_messages = self.packets_bad
                total_messages = self.packets
                #dbc = query_handler()
                last_total = 0
                last_bad = 0
                while True:
                        time.sleep(10); #only check messages once per 10second
			#if self.packets_bad-last_bad >= 30: #Testing, if greater than 30 corrupt packets change to next cc
				#print '!!!!!!!!!!!!! CC CORRUPTION !!!!!!!!!!!!!!!'
				#self.tune_next_control()
				#time.sleep(5)
				#self.lock()
				#time.sleep(2)
				#self.unlock()
                        sid = self.system['id']
                        print 'System: ' + str(sid) + ' (' + str(self.packets-last_total) + '/' + str(self.packets_bad-last_bad) + ')' + ' (' +str(self.packets) + '/'+ str(self.packets_bad) + ') CC: ' + str(self.control_channel) + ' AR: ' + str(len(self.tb.active_receivers))
                        last_total = self.packets
                        last_bad = self.packets_bad

###################################################################################################
	def deinterleave(self, data):
		output = []
		if(len(data) != 76):
			return output
		for x in range(0, 19):
			for y in [0, 19, 38, 57]:
				output.append(int(data[x+y]))
		return output
	def checkEqual(self, iterator):
	      try:
	         iterator = iter(iterator)
	         first = next(iterator)
	         return all(first == rest for rest in iterator)
	      except StopIteration:
	         return True
####################################################################################################
	def receive_engine(self):
		print self.thread_id + ': receive_engine() startup'
		time.sleep(1)
		import sys

		

		frame_len = 76 #bits
		frame_sync = '10101100'
		fs_len = 8 #frame sync length in bits

		buf = ''
		#packets = tb.packets
		#packets_bad = tb.packets_bad
		sync_loops = 0
		locked = 0
		last_cmd = 0x0
		last_i = 0x0
		last_data = 0x0

		while 1:
			if(sync_loops < -200):
				print 'NO LOCK MAX SYNC LOOPS %s %s' % (self.channels_list[self.control_channel_key], self.channels[self.channels_list[self.control_channel_key]])
				#print 'b/p: %s %s' % (packets, packets_bad)
				sync_loops = 0
				self.tune_next_control()
				locked = 0
			data = self.get_msgq()
			for byte in data:
				buf = buf + str("{0:08b}" . format(ord(byte)))
			if len(buf) > frame_len*3:
				
				fs_loc = buf.find(frame_sync)
				fs_next_loc = buf[fs_loc+fs_len:].find(frame_sync)+fs_loc+fs_len
				if locked > 2 or (fs_loc > -1 and fs_next_loc > -1 and fs_next_loc-fs_loc == frame_len+fs_len):
					if fs_loc != 0:
						print 'Packet jump %s - %s' % (fs_loc, buf[:fs_loc])
						locked -= 1
					elif locked < 5:
						locked += 1
					
					if locked >= 5:
						self.is_locked = True
					else:
						self.is_locked = False

					self.packets += 1
					if sync_loops < 1000:
						sync_loops += 50
					if locked > 2:
						pkt = buf[fs_len:fs_len+frame_len]
						buf = buf[fs_len+frame_len:]
					else:
						print '--- no lock ---'
						pkt = buf[fs_loc+fs_len:fs_loc+fs_len+frame_len]
						buf = buf[fs_loc+fs_len+frame_len:]

					pkt = self.deinterleave(pkt)

					data = []
					parity = []
					dsyn = [] #data syndrome
					psyn = [] #parity syndrome
					for x in range(0, len(pkt), 2):
						data.append(pkt[x])
						parity.append(pkt[x+1])

					expected_parity = []
					last_bit = 0
					for x in range(0, len(data)):
						expected_parity.append(last_bit^data[x])
						last_bit = data[x]

					expected_pkt = []
					for x in range(0, len(data)):
						expected_pkt.append(data[x])
						expected_pkt.append(expected_parity[x])

					#syndrome = [a^b for a,b in pkt,expected_pkt]
					syndrome = []
					for x in range(0, len(pkt)):
						syndrome.append(pkt[x] ^ expected_pkt[x])
					if(self.checkEqual(syndrome) == False):
						self.packets_bad += 1
						for x in range(0, len(syndrome), 2):
							dsyn.append(syndrome[x])
							psyn.append(syndrome[x+1])

						for x in range(0, len(psyn)-1):
							if psyn[x] == psyn[x+1] == 1:
								if data[x] == 0:
									data[x] = 1
								else:
									data[x] = 0
					elif fs_loc != 0:
						locked += 1
					

					pkt = ''.join(map(str, data))
					if(len(pkt) > 1):
						lid = int(pkt[:16],2)^0xcc38# ^ 0x33c7
						tg = lid & 0xfff0
						status = lid & 0xf
						individual = int(pkt[16:17])
						ind_l = 'G' if int(pkt[16:17]) == 1 else 'I'
						cmd = int(pkt[17:27],2)^0xd5# ^ 0x32a
						#3bf == network status
						#3c0 == System info
						#308 == affiliation
						#310 == aff 2
						#320 == Network info
						#
						if last_cmd == 0x304 or last_cmd == 0x308 or last_cmd == 0x309: 
							dual = True
						else:
							dual = False
						if   not dual and cmd == 0x2f8:
							print '%s: %s %s %s - IDLE ' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif              cmd == 0x300: #s/d
							print '%s: %s %s %s - Group and PC1 busy' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif not dual and cmd == 0x301: #s
							print '%s: %s %s %s - Interconnect busy' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif              cmd == 0x302: #s/d
							print '%s: %s %s %s - Private call busy' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif              cmd == 0x303: #s/d
							print '%s: %s %s %s - Emergency busy' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif              cmd == 0x304: #f
							print '%s: %s %s %s - First-word of coded PC grant' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif              cmd == 0x308: #f
							print '%s: %s %s %s - First-word normal' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif              cmd == 0x309: #f
							print '%s: %s %s %s - First-word TY2 aliased to TY1' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x30a: #d
							print '%s: %s %s %s - TY2 dynamic regrouping' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x30b: #d
							print '%s: %s %s %s - Extended function' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif not dual and cmd == 0x30c: #s
							print '%s: %s %s %s - TY1 phone status' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x30d: #d
							print '%s: %s %s %s - Affiliation functions' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif not dual and cmd == 0x30f: #s
							print '%s: %s %s %s - TY1 Phone disconnect' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif not dual and cmd == 0x310: #s
							print '%s: %s %s %s - TY1 status value 1' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x310: #d
							print '%s: %s %s %s - Affiliation - (Radio: %s, TG: %s)' % (time.time(), hex(cmd), ind_l, hex(lid), last_data, lid)
                                                elif not dual and cmd == 0x311: #s
                                                        print '%s: %s %s %s - TY1 status value 2' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x311: #d
							print '%s: %s %s %s - TY2 messages' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x312: #s
                                                        print '%s: %s %s %s - TY1 status value 3' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x313: #s
                                                        print '%s: %s %s %s - TY1 status value 4' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x314: #s
                                                        print '%s: %s %s %s - TY1 status value 5' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x315: #s
                                                        print '%s: %s %s %s - TY1 status value 6' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x315: #d
							print '%s: %s %s %s - PC coded ring' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x316: #s
                                                        print '%s: %s %s %s - TY1 status value 7' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x317: #s
                                                        print '%s: %s %s %s - TY1 status value 8' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x317: #d
                                                        print '%s: %s %s %s - PC clear ring' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x318: #s
							print '%s: %s %s %s - TY1 Call Alert' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x318: #d
							print '%s: %s %s %s - TY2 PC Ring Ack' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x319: #s
							print '%s: %s %s %s - TY1 Emergency alarm' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x319: #d
							print '%s: %s %s %s - TY2 Call Alert' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x31a:
							print '%s: %s %s %s - TY2 Call Alert Ack' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x31b:
							print '%s: %s %s %s - Tresspass permitted [AVL indiv high prior grant]' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x31c:
							print '%s: %s %s %s - [AVL indiv low prior grant]' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x31d:
							print '%s: %s %s %s - [AVL group high prior grant]' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x324: #s
                                                        print '%s: %s %s %s - TY2 Interconnect reject' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x325: #s
                                                        print '%s: %s %s %s - TY2 Interconnect transpond' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x326: #s
                                                        print '%s: %s %s %s - TY2 Interconnect ring' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x32a: #s
                                                        print '%s: %s %s %s - Send affiliation request' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x32b: #s
                                                        print '%s: %s %s %s - Scan marker' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x32d: #s
                                                        print '%s: %s %s %s - TY1 System wide announcement' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x32e: #d
							print '%s: %s %s %s - \033[93m Emergency PTT announcement \033[0m' % (time.time(), hex(cmd), ind_l, hex(lid))
						elif     dual and cmd == 0x340: #d
							pass #print '%s: %s %s %s - TY1 regrouping sizecode A' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x341: #d
                                                        pass #print '%s: %s %s %s - TY1 regrouping sizecode B' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x342: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode C' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x343: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode D' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x344: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode E' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x345: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode F' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x346: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode G' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x347: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode H' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x348: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode I' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x349: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode J' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x34a: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode K' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x34c: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode M' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x34e: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode O' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif     dual and cmd == 0x350: #d
                                                        print '%s: %s %s %s - TY1 regrouping sizecode Q' % (time.time(), hex(cmd), ind_l, hex(lid))

                                                elif not dual and cmd >= 0x360 and cmd <= 0x39F:
                                                        print '%s: %s %s %s - AMSS site ID' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x3a0: #s
                                                        print '%s: %s %s %s - System diagnostic or BSI' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x3a8: #s
                                                        print '%s: %s %s %s - System test' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and cmd == 0x3b0: #s
                                                        print '%s: %s %s %s - CSC version number' % (time.time(), hex(cmd), ind_l, hex(lid))
                                                elif not dual and (cmd == 0x3bf or cmd == 0x3c0):
							r = {}
							r['opcode'] = 			(lid & 0xe000) >> 13 #3 bits
							if r['opcode'] == 1:
								
								r['power'] = 			(lid & 0x1000) >> 12 #1 bit
								r['dispatch_timeout'] = 	(lid & 0xe00) >> 9 #3 bits
								r['connect_tone'] = 		(lid & 0x1e0) >> 5 #4 bits
								r['interconnect_timeout'] = 	(lid & 0x1f)+individual #6 bits
							elif r['opcode'] == 2:
                                                                r['b'] = (lid & 0x1000) >> 12
                                                                r['c'] = (lid & 0x800) >> 11
                                                                r['d'] = (lid & 0x400) >> 10
                                                                r['e'] = (lid & 0x200) >> 9
                                                                r['f'] = (lid & 0x100) >> 8
                                                                r['g'] = (lid & 0x80) >> 7
                                                                r['h'] = (lid & 0x40) >> 6
								r['i'] = (lid & 0x20) >> 5
								r['j'] = (lid & 0x10) >> 4
								r['k'] = (lid & 0x8) >> 3

                                                        #print '%s: %s %s %s - System status - %s' % (time.time(), hex(cmd), ind_l, hex(lid), r)

						elif self.channels.has_key(cmd) and lid != self.system_id and tg != 0x1ff0:
							if dual:
								print '%s: Call  %s %s %s %s %s %s' % (time.time(), hex(lid), tg, status, individual, hex(cmd), last_data)
							#else:
							#	print '%s: Call  %s %s %s %s %s' % (time.time(), hex(lid), tg, status, individual, hex(cmd))
							#print 'b/p: %s %s' % (packets, packets_bad)
							allocated_receiver = False
							self.tb.ar_lock.acquire()
							for receiver in self.tb.active_receivers: #find any active channels and mark them as progressing
								if receiver.cdr != {} and receiver.cdr['system_channel_local'] == cmd and receiver.cdr['system_id'] == self.system['id']:
									if dual and receiver.cdr['system_user_local'] != last_data:
										#existing call but user LID does not match!
										receiver.close({}, True, True)
										allocated_receiver = receiver
										center = receiver.center_freq
									else:
										receiver.activity()
										allocated_receiver = -1
										break
							
							if allocated_receiver != -1:
								for receiver in self.tb.active_receivers: #look for an empty channel
									if receiver.in_use == False and abs(receiver.center_freq-self.channels[cmd]) < (self.samp_rate/2):
										allocated_receiver = receiver
										center = receiver.center_freq
										break
							
								if allocated_receiver == False: #or create a new one if there arent any empty channels
									allocated_receiver = logging_receiver(self.samp_rate)
									center = self.tb.connect_channel(self.channels[cmd], allocated_receiver)
									self.tb.active_receivers.append(allocated_receiver)
								

								allocated_receiver.tuneoffset(self.channels[cmd], center)
								#if tg > 32000:
								allocated_receiver.set_codec_p25(False)
								#else:
								#	allocated_receiver.set_codec_p25(False)
								allocated_receiver.set_codec_provoice(False)
								user_local = last_data if dual else 0
								cdr = {
									'system_id': self.system['id'], 
									'system_group_local': tg, 
									'system_user_local': user_local,
									'system_channel_local': cmd, 
									'type': 'group', 
									'center_freq': center}
								print 
								allocated_receiver.open(cdr, 25000.0)
							self.tb.ar_lock.release()
										
							#elif cmd == 0x1c:
							#	print '%s: Grant %s %s %s %s %s' % (time.time(), hex(lid), tg, status, individual, hex(cmd))
							#elif cmd == 0x308:
							#	print '%s: AFF1  %s %s %s %s %s' % (time.time(), hex(lid), tg, status, individual, hex(cmd))
							#elif cmd == 0x310:
							#	print '%s: AFF2  %s %s %s %s %s' % (time.time(), hex(lid), tg, status, individual, hex(cmd))
							#else:
							#	print '%s:       %s %s %s %s %s' % (time.time(), hex(lid), tg, status, individual, hex(cmd))
						else:
							print '%s: %s %s %s - Unknown OSW' % (time.time(), hex(cmd), ind_l, hex(lid))
						last_cmd = cmd
						last_i = individual
						last_data = lid
				else:
					buf = buf[fs_loc+fs_len:]
			
			else:
				sync_loops -= 1
				#time.sleep(0.01)

