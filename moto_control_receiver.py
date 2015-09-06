#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Moto Smartzone Test1
# Generated: Thu Oct  4 23:49:39 2012
##################################################

from gnuradio import digital, blocks, analog, filter
from gnuradio.filter import firdes
from gnuradio import gr

import time
import threading

from logging_receiver import logging_receiver
from backend_event_publisher import backend_event_publisher

class moto_control_receiver(gr.hier_block2):

	def __init__(self, system, top_block, block_id):

                gr.hier_block2.__init__(self, "moto_control_receiver",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
                                gr.io_signature(0, 0, 0)) # Output signature

		##################################################
		# Variables
		##################################################
		self.tb = top_block
		self.channel_rate = 12500
		self.hang_time = 0.5
		self.packets = 0
		self.packets_bad = 0
	
		self.quality = []

		self.symbol_rate = symbol_rate = 3600.0
		self.control_source = 0
		self.block_id = block_id

		
		self.offset = offset = 0
		self.is_locked = False

		self.system = system

		self.system_id = system['id']
		self.channels = system['channels']
		self.channels_list = self.channels.keys()

		self.thread_id = '%s-%s' % (self.system['type'], self.system_id)

		self.control_channel_key = 0
		self.control_channel = control_channel = self.channels[self.channels_list[0]]

		self.option_dc_offset = False
		self.option_udp_sink = False
		self.option_logging_receivers = True

		self.enable_capture = True
		self.keep_running = True

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

		control_sample_rate = 12500
		channel_rate = control_sample_rate*2

		self.control_quad_demod = analog.quadrature_demod_cf(0.1)

		if(self.option_dc_offset):
			moving_sum = blocks.moving_average_ff(1000, 1, 4000)
			divide_const = blocks.multiply_const_vff((0.001, ))
			self.probe = blocks.probe_signal_f()


		self.control_clock_recovery = digital.clock_recovery_mm_ff(channel_rate/symbol_rate, 1.4395919, 0.5, 0.05, 0.005)
		self.control_binary_slicer = digital.binary_slicer_fb()
		self.control_byte_pack = blocks.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
		self.control_msg_sink = blocks.message_sink(gr.sizeof_char*1, self.control_msg_sink_msgq, True)

		if(self.option_udp_sink):
			self.udp = blocks.udp_sink(gr.sizeof_gr_complex*1, "127.0.0.1", self.system_id, 1472, True)
	
		##################################################
		# Connections
		##################################################

		self.connect(self, self.control_quad_demod, self.control_clock_recovery)
                self.connect(self.control_clock_recovery, self.control_binary_slicer, self.control_byte_pack, self.control_msg_sink)

		if(self.option_dc_offset):
			self.connect(self.control_quad_demod, moving_sum, divide_const, self.probe)

		if(self.option_udp_sink):
			self.connect(self.control_prefilter, self.udp)
		self.backend_event_publisher = backend_event_publisher()
		
	def get_msgq(self):
		return self.control_msg_sink_msgq.delete_head().to_string()
	def tune_next_control(self):
                self.control_channel_key += 1
                if(self.control_channel_key >= len(self.channels)):
                        self.control_channel_key = 0
                self.control_channel = self.channels[self.channels_list[self.control_channel_key]]

		self.control_source = self.tb.retune_control(self.block_id, self.control_channel)

		print 'CC Change - %s' % (self.control_channel)
		self.control_msg_sink_msgq.flush()
		time.sleep(0.1)

        def quality_check(self):

		desired_quality = 429.0 # approx 42.9 packets per sec

                #global bad_messages, total_messages
                bad_messages = self.packets_bad
                total_messages = self.packets
                #dbc = query_handler()
                last_total = 0
                last_bad = 0
                while self.keep_running:
                        time.sleep(10); #only check messages once per 10second

                        sid = self.system['id']
			current_packets = self.packets-last_total
			current_packets_bad = self.packets_bad-last_bad
                        print 'System: ' + str(sid) + ' (' + str(current_packets) + '/' + str(current_packets_bad) + ')' + ' (' +str(self.packets) + '/'+ str(self.packets_bad) + ') CC: ' + str(self.control_channel) + ' AR: ' + str(len(self.tb.active_receivers))

			if len(self.quality) >= 60:
				self.quality.pop(0)

			self.quality.append((current_packets-current_packets_bad)/desired_quality)

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

		frame_len = 76 #bits
		frame_sync = '10101100'
		fs_len = 8 #frame sync length in bits

		buf = ''
		sync_loops = 0
		locked = 0
		last_cmd = 0x0
		last_i = 0x0
		last_data = 0x0

		while self.keep_running:
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

						p = {
							'sys': self.system_id,
							'cmd': hex(cmd),
							'ind': ind_l,
							'lid': hex(lid)
						}

						if last_cmd == 0x304 or last_cmd == 0x308 or last_cmd == 0x309 or last_cmd == 0x321: 
							p['dual'] = True
							dual = True
						else:
							p['dual'] = False
							dual = False
						if   not dual and cmd == 0x2f8:
							p['type'] = 'IDLE'
						elif              cmd == 0x300: #s/d
                                                        p['type'] = 'Group and PC1 busy'
						elif not dual and cmd == 0x301: #s
                                                        p['type'] = 'Interconnect Busy'
						elif              cmd == 0x302: #s/d
                                                        p['type'] = 'Private call busy'
						elif              cmd == 0x303: #s/d
                                                        p['type'] = 'Emergency busy'
						elif              cmd == 0x304: #f
                                                        p['type'] = 'First-word of coded PC grant'
						elif              cmd == 0x308: #f
                                                        p['type'] = 'First-word normal'
						elif              cmd == 0x309: #f
                                                        p['type'] = 'First-word TY2 aliased to TY1'
						elif     dual and cmd == 0x30a: #d
                                                        p['type'] = 'TY2 dynamic regrouping'
						elif     dual and cmd == 0x30b: #d
                                                        p['type'] = 'Extended function'
						elif not dual and cmd == 0x30c: #s
                                                        p['type'] = 'TY1 Phone status'
						elif     dual and cmd == 0x30d: #d
                                                        p['type'] = 'Affiliation functions'
						elif not dual and cmd == 0x30f: #s
                                                        p['type'] = 'TY1 Phone disconnect'
						elif not dual and cmd == 0x310: #s
                                                        p['type'] = 'TY1 status value 1'
						elif     dual and cmd == 0x310: #d
                                                        p['type'] = 'Affiliation'
							p['radio_id'] = last_data
							p['tgid'] = lid
                                                elif not dual and cmd == 0x311: #s
                                                        p['type'] = 'TY1 status value 2'
						elif     dual and cmd == 0x311: #d
                                                        p['type'] = 'TY2 messages'
                                                elif not dual and cmd == 0x312: #s
                                                        p['type'] = 'TY1 status value 3'
                                                elif not dual and cmd == 0x313: #s
                                                        p['type'] = 'TY1 status value 4'
                                                elif not dual and cmd == 0x314: #s
                                                        p['type'] = 'TY1 status value 5'
                                                elif not dual and cmd == 0x315: #s
                                                        p['type'] = 'TY1 status value 6'
						elif     dual and cmd == 0x315: #d
                                                        p['type'] = 'PC coded ring'
                                                elif not dual and cmd == 0x316: #s
                                                        p['type'] = 'TY1 status value 7'
                                                elif not dual and cmd == 0x317: #s
                                                        p['type'] = 'TY1 status value 8'
                                                elif     dual and cmd == 0x317: #d
                                                        p['type'] = 'PC clear ring'
                                                elif not dual and cmd == 0x318: #s
                                                        p['type'] = 'TY1 Call Alert'
						elif     dual and cmd == 0x318: #d
                                                        p['type'] = 'TY2 PC Ring Ack'
                                                elif not dual and cmd == 0x319: #s
                                                        p['type'] = 'TY1 Emergency alarm'
						elif     dual and cmd == 0x319: #d
                                                        p['type'] = 'TY2 Call Alert'
						elif     dual and cmd == 0x31a:
                                                        p['type'] = 'TY2 Call Alert Ack'
						elif     dual and cmd == 0x31b:
                                                        p['type'] = 'Tresspass permitted [AVL indiv high prior grant]'
						elif     dual and cmd == 0x31c:
                                                        p['type'] = '[AVL indiv low prior grant]'
						elif     dual and cmd == 0x31d:
                                                        p['type'] = '[AVL group high prior grant]'
						elif		  cmd == 0x321:
                                                        p['type'] = 'Digital call word1'
                                                elif not dual and cmd == 0x324: #s
                                                        p['type'] = 'TY2 Interconnect reject'
                                                elif not dual and cmd == 0x325: #s
                                                        p['type'] = 'TY2 Interconnect transpond'
                                                elif not dual and cmd == 0x326: #s
                                                        p['type'] = 'TY2 Interconnect ring'
                                                elif not dual and cmd == 0x32a: #s
                                                        p['type'] = 'Send affiliation request'
                                                elif not dual and cmd == 0x32b: #s
                                                        p['type'] = 'Scan marker'
                                                elif not dual and cmd == 0x32d: #s
                                                        p['type'] = 'TY1 System wide announcement'
						elif     dual and cmd == 0x32e: #d
                                                        p['type'] = 'Emergency PTT announcement'
						elif     dual and cmd == 0x340: #d
                                                        p['type'] = 'TY1 regrouping sizecode A'
                                                elif     dual and cmd == 0x341: #d
                                                        p['type'] = 'TY1 regrouping sizecode B'
                                                elif     dual and cmd == 0x342: #d
                                                        p['type'] = 'TY1 regrouping sizecode C'
                                                elif     dual and cmd == 0x343: #d
                                                        p['type'] = 'TY1 regrouping sizecode D'
                                                elif     dual and cmd == 0x344: #d
                                                        p['type'] = 'TY1 regrouping sizecode E'
                                                elif     dual and cmd == 0x345: #d
                                                        p['type'] = 'TY1 regrouping sizecode F'
                                                elif     dual and cmd == 0x346: #d
                                                        p['type'] = 'TY1 regrouping sizecode G'
                                                elif     dual and cmd == 0x347: #d
                                                        p['type'] = 'TY1 regrouping sizecode H'
                                                elif     dual and cmd == 0x348: #d
                                                        p['type'] = 'TY1 regrouping sizecode I'
                                                elif     dual and cmd == 0x349: #d
                                                        p['type'] = 'TY1 regrouping sizecode J'
                                                elif     dual and cmd == 0x34a: #d
                                                        p['type'] = 'TY1 regrouping sizecode K'
                                                elif     dual and cmd == 0x34c: #d
                                                        p['type'] = 'TY1 regrouping sizecode M'
                                                elif     dual and cmd == 0x34e: #d
                                                        p['type'] = 'TY1 regrouping sizecode O'
                                                elif     dual and cmd == 0x350: #d
                                                        p['type'] = 'TY1 regrouping sizecode Q'
                                                elif not dual and cmd >= 0x360 and cmd <= 0x39F:
                                                        p['type'] = 'AMSS site ID'
                                                elif not dual and cmd == 0x3a0: #s
                                                        p['type'] = 'System diagnostic or BSI'
                                                elif not dual and cmd == 0x3a8: #s
                                                        p['type'] = 'System test'
                                                elif not dual and cmd == 0x3b0: #s
                                                        p['type'] = 'CSC version number'
                                                elif not dual and (cmd == 0x3bf or cmd == 0x3c0):
							p['opcode'] = 			(lid & 0xe000) >> 13 #3 bits
							if p['opcode'] == 1:
								
								p['power'] = 			(lid & 0x1000) >> 12 #1 bit
								p['dispatch_timeout'] = 	(lid & 0xe00) >> 9 #3 bits
								p['connect_tone'] = 		(lid & 0x1e0) >> 5 #4 bits
								p['interconnect_timeout'] = 	(lid & 0x1f)+individual #6 bits
							elif p['opcode'] == 2:
                                                                p['b'] = (lid & 0x1000) >> 12
                                                                p['c'] = (lid & 0x800) >> 11
                                                                p['d'] = (lid & 0x400) >> 10
                                                                p['e'] = (lid & 0x200) >> 9
                                                                p['f'] = (lid & 0x100) >> 8
                                                                p['g'] = (lid & 0x80) >> 7
                                                                p['h'] = (lid & 0x40) >> 6
								p['i'] = (lid & 0x20) >> 5
								p['j'] = (lid & 0x10) >> 4
								p['k'] = (lid & 0x8) >> 3
                                                        p['type'] = 'System status'
						elif self.channels.has_key(cmd) and lid != self.system_id and tg != 0x1ff0:
							if 'offset' in self.system.keys() and last_cmd == cmd-self.system['offset']:
								dual = True
							if dual and last_cmd == 0x308:
	                                                        p['type'] = 'Analog Call'
								call_type = 'a'
							elif dual and last_cmd == 0x321:
	                                                        p['type'] = 'Digital Call'
								call_type = 'd'
							else:
	                                                        p['type'] = 'Call Continuation'
								call_type = 'u'

							if 'force_p25' in self.system.keys() and self.system['force_p25']:
								call_type = 'd'

							if(self.option_logging_receivers):
								if self.channels[cmd] == self.control_channel:
									continue
								#This allows the upstream control to disable capture during receiver handoff.
								if not self.enable_capture:
									continue 
							
								allocated_receiver = False
								self.tb.ar_lock.acquire()
								for receiver in self.tb.active_receivers: #find any active channels and mark them as progressing
									if receiver.cdr != {} and receiver.cdr['system_channel_local'] == cmd and receiver.cdr['system_id'] == self.system['id']:
										if dual and receiver.cdr['system_user_local'] != last_data:
											#existing call but user LID does not match!
											self.tb.connector.release_channel(receiver.channel_id)
											receiver.close({})
											allocated_receiver = receiver
										else:
											receiver.activity()
											allocated_receiver = -1
											break
								
								if allocated_receiver != -1:
									#for receiver in self.tb.active_receivers: #look for an empty channel
									#	if receiver.in_use == False and abs(receiver.center_freq-self.channels[cmd]) < (self.samp_rate/2):
									#		allocated_receiver = receiver
									#		center = receiver.center_freq
									#		break
								
									#if allocated_receiver == False: #or create a new one if there arent any empty channels
									#	allocated_receiver = logging_receiver(self.samp_rate)
									#	center = self.tb.connect_channel(self.channels[cmd], allocated_receiver)
									#	self.tb.active_receivers.append(allocated_receiver)

									if(call_type == 'd'):
										bandwidth = 12500
									else:
										bandwidth = 12500

									try:
						                                allocated_receiver = self.tb.connect_channel(self.channels[cmd], bandwidth)
					        	                except:
										self.tb.ar_lock.release()
					                	                continue
								
									#allocated_receiver.tuneoffset(self.channels[cmd], center)
									if(call_type == 'd'):
										allocated_receiver.configure_blocks('p25')
									else:
										 allocated_receiver.configure_blocks('analog')
									user_local = last_data if dual else 0
									cdr = {
										'system_id': self.system['id'], 
										'system_group_local': tg, 
										'system_user_local': user_local,
										'system_channel_local': cmd, 
										'type': 'group', 
									}
									allocated_receiver.set_rate(bandwidth)
									allocated_receiver.open(cdr)
								self.tb.ar_lock.release()
										
						else:
                                                        p['type'] = 'Unknown OSW'

						if p['type'] != 'System status':
							print '%s:	%s %s %s %s' % (time.time(), p['cmd'],p['ind'] , p['lid'], p['type'])

						self.backend_event_publisher.publish_raw_control('test', self.system_id, p)
						last_cmd = cmd
						last_i = individual
						last_data = lid
				else:
					buf = buf[fs_loc+fs_len:]
			
			else:
				sync_loops -= 1

