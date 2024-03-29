#!/usr/env/python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

from gnuradio import gr, blocks, analog, filter, fft, digital, zeromq
try:
        from gnuradio.gr import firdes
except:
        from gnuradio.filter import firdes

import time, datetime
import os
import threading
import uuid
import logging

try:
        import dsd
except:
        pass

from math import pi

import op25
import op25_repeater as repeater
from p25p2_lfsr import p25p2_lfsr

from p25_cai import p25_cai
from frontend_connector import frontend_connector
from p25_general import p25_general

from client_activemq import client_activemq
import rs64
import golay
import hamming
import util
import sys

import zmq
import traceback

class logging_receiver(gr.top_block):
        def __init__(self, cdr, client_activemq, client_redis, rcm):
                gr.top_block.__init__(self, "logging_receiver")

                self.log = logging.getLogger('overseer.logging_receiver')
                self.log.debug("logging_receiver().__init__(%s, %s, %s, %s, %s" % (self, cdr, client_activemq, client_redis, rcm))

                self.cdr = cdr
                self.client_activemq = client_activemq
                self.client_redis = client_redis
                self.rcm = rcm

                self.thread_lock = threading.Lock()
                self.thread_lock.acquire()
                self.audio_capture = True

                self.p25_general = p25_general()

                self.zmq_context = zmq.Context()
                self.zmq_socket = self.zmq_context.socket(zmq.SUB)
                self.zmq_socket.setsockopt(zmq.SUBSCRIBE, b"")

                self.in_use = False
                self.thread_id = 'logr-' + str(uuid.uuid4())

                self.filename = "/dev/null"
                self.filepath = "/dev/null"
                self.channel_rate = 0
                self.input_rate = 0
        
                #optionall log dat files
                self.log_dat = False

                #optionally keep wav files around
                self.log_wav = False

                self.sink = blocks.wavfile_sink(self.filepath, 1, 8000)

                self.protocol = None
                self.time_activity = 0

                self.codec_provoice = False
                self.codec_p25 = False
        
                self.destroyed = False


                #debug = threading.Thread(target=self.debug, name='logging_receiver_debug')
                #debug.daemon = True
                #debug.[tart()

                #Setup connector
                self.connector = frontend_connector(cdr['instance_uuid'], self.rcm)
                self.source = None
                for retry in 1,2,3,4,5:
                        try:
                                channel_id, port = self.connector.create_channel(int(self.cdr['channel_bandwidth']), int(self.cdr['frequency']))
                                self.source = zeromq.sub_source(gr.sizeof_gr_complex*1, 1, 'tcp://%s:%s' % (self.connector.host, port))
                                break
                        except:
                                pass
                if self.source == None:
                        self.connector.exit()
                        self.log.error("Failed to after five attempts connector.create_channel(%s, %s)" % (int(self.cdr['channel_bandwidth']), int(self.cdr['frequency'])))

                if self.log_dat:
                        self.dat_sink = blocks.file_sink(gr.sizeof_gr_complex*1, self.filename)
                        self.connect(self.source, self.dat_sink)


                self.set_rate(int(self.cdr['channel_bandwidth']*2))
                self.configure_blocks(self.cdr['modulation_type'])
                if self.cdr['modulation_type'] == 'p25_tdma' or self.cdr['modulation_type'] == 'p25_cqpsk_tdma' :
                        try:
                                self.set_p25_xor_chars(p25p2_lfsr(int(self.cdr['p25_nac']),int(self.cdr['p25_system_id'],0),int(self.cdr['p25_wacn'],0)).xor_chars)
                        except Exception as e:
                                traceback.print_exc()
                                self.log.error('Failed to set XOR chars %s %s %s' % (cdr['instance_uuid'], type(e), e))
                                pass
                        self.set_p25_tdma_slot(self.cdr['slot'])

                p25_sensor = threading.Thread(target=self.p25_sensor, name='p25_sensor', args=(self,))
                p25_sensor.daemon = True
                p25_sensor.start()


                self.open()
                self.start()
                self.thread_lock.release()
        def configure_blocks(self, protocol):
                if protocol == 'provoice' or protocol == 'analog_edacs': 
                        protocol = 'analog'
                self.log.debug('configure_blocks(%s)' % protocol)
                if not (protocol == 'p25' or protocol == 'p25_tdma' or protocol == 'p25_cqpsk' or protocol=='p25_cqpsk_tdma' or protocol == 'provoice' or protocol == 'dsd_p25' or protocol == 'analog' or protocol == 'none'):
                        raise Exception('Invalid protocol %s' % protocol)
                if self.protocol == protocol:
                        return True
                self.lock()
                if self.protocol == 'analog':
                        self.disconnect(self.source, self.signal_squelch, self.audiodemod, self.high_pass, self.resampler, self.sink)
                        self.signal_squelch = None
                        self.audiodemod = None
                        self.high_pass = None
                        self.resampler = None

                elif self.protocol == 'p25' or 'p25_tdma':
                        try:
                                self.disconnect(self.source, self.prefilter, self.fm_demod)#, (self.subtract,0))
                                self.disconnect(self.fm_demod, self.symbol_filter, self.demod_fsk4, self.slicer, self.decoder, self.float_conversion, self.sink)
                                self.disconnect(self.slicer, self.decoder2, self.qsink)
                                self.demod_watcher.keep_running = False

                        except:
                                pass
                        #self.disconnect(self.fm_demod, self.avg, self.mult, (self.subtract,1))

                        self.prefilter = None
                        self.fm_demod = None
                        #self.avg = None
                        #self.mult = None
                        #self.subtract = None
                        self.symbol_filter = None
                        self.demod_fsk4 = None
                        self.slicer = None
                        self.decoder = None
                        self.decoder2 = None
                        self.qsink = None
                        self.imbe = None
                        self.float_conversion = None
                        self.resampler = None
                elif self.protocol == 'p25_cqpsk' or self.protocol == 'p25_cqpsk_tdma':
                        self.disconnect(self.source, self.prefilter, self.resampler, self.agc, self.symbol_filter_c, self.clock, self.diffdec, self.to_float, self.rescale, self.slicer, self.decoder2, self.qsink)#, (self.subtract,0))
                        self.disconnect(self.slicer, self.decoder, self.float_conversion, self.sink)

                        self.prefilter = None
                        self.resampler = None
                        self.agc = None
                        self.symbol_filter_c = None
                        self.clock = None
                        self.diffdec = None
                        self.to_float = None
                        self.rescale = None
                        self.slicer = None

                        self.imbe = None
                        self.decodequeue3 = None
                        self.decodequeue2 = None
                        self.decodequeue = None

                        self.demod_watcher = None
                        self.decoder  = None
                        self.decoder2 = None
                        self.qsink = None
                        self.float_conversion = None

                elif self.protocol == 'provoice':
                        self.disconnect(self.source, self.fm_demod, self.resampler_in, self.dsd, self.out_squelch, self.sink)
                        self.fm_demod = None
                        self.resampler_in = None
                        self.dsd = None
                        self.out_squelch = None
                elif self.protocol == 'dsd_p25':
                        self.disconnect(self.source, self.fm_demod, self.resampler_in, self.dsd, self.sink)
                        self.fm_demod = None
                        self.resampler_in = None
                        self.dsd = None
                self.protocol = protocol
                        
                if protocol == 'analog':
                        self.signal_squelch = analog.pwr_squelch_cc(-100,0.01, 0, True)
                        #self.tone_squelch = gr.tone_squelch_ff(audiorate, 4800.0, 0.05, 300, 0, True)
                        #tone squelch is EDACS ONLY
                        self.audiodemod = analog.fm_demod_cf(channel_rate=self.input_rate, audio_decim=1, deviation=15000, audio_pass=(self.input_rate*0.25), audio_stop=((self.input_rate*0.25)+2000), gain=8, tau=75e-6)
                        self.high_pass = filter.fir_filter_fff(1, firdes.high_pass(1, self.input_rate, 300, 30, firdes.WIN_HAMMING, 6.76))
                        self.resampler = filter.rational_resampler_fff(
                                        interpolation=8000,
                                        decimation=self.input_rate,
                                        taps=None,
                                        fractional_bw=None,
                        )
                        self.connect(self.source, self.signal_squelch, self.audiodemod, self.high_pass, self.resampler, self.sink)
                elif protocol == 'p25' or protocol == 'p25_tdma':
                        self.symbol_deviation = symbol_deviation = 600.0
                        if protocol == 'p25_tdma':                        
                                symbol_rate = 6000
                        else:
                                symbol_rate = 4800
                        channel_rate = self.input_rate
                        taps = firdes.low_pass_2(1.0,channel_rate,self.channel_rate/2,500.0, 30.0, firdes.WIN_BLACKMAN)               
                        self.prefilter = filter.freq_xlating_fir_filter_ccc(1, taps, 0, self.input_rate)
        
                        fm_demod_gain = channel_rate / (2.0 * pi * symbol_deviation)
                        self.fm_demod = analog.quadrature_demod_cf(fm_demod_gain)
                        

                        #self.avg = blocks.moving_average_ff(1000, 1, 4000)
                        #self.mult = blocks.multiply_const_vff((0.001, ))
                        #self.subtract = blocks.sub_ff(1)

                        symbol_decim = 1
                        samples_per_symbol = channel_rate // symbol_rate
                        symbol_coeffs = (1.0/samples_per_symbol,) * samples_per_symbol
                        self.symbol_filter = filter.fir_filter_fff(symbol_decim, symbol_coeffs)

                        autotuneq = gr.msg_queue(2)
                        self.demod_fsk4 = op25.fsk4_demod_ff(autotuneq, channel_rate, symbol_rate)

                        # symbol slicer
                        levels = [ -2.0, 0.0, 2.0, 4.0 ]
                        self.slicer = op25.fsk4_slicer_fb(levels)
                        
                        self.imbe = repeater.vocoder(False, True, 0, "", 0, False)
                        self.decodequeue3 = decodequeue3 = gr.msg_queue(10000)
                        self.decodequeue2 = decodequeue2 = gr.msg_queue(10000)
                        self.decodequeue = decodequeue = gr.msg_queue(10000)

                        self.demod_watcher = None #demod_watcher(decodequeue2, self.adjust_channel_offset)

                        
                        try:
                            self.decoder  = repeater.p25_frame_assembler('127.0.0.1', 0, 0, True, True, False, decodequeue2, True, (True if protocol == 'p25_tdma' else False))
                            self.decoder2 = repeater.p25_frame_assembler('127.0.0.1', 0, 0, False, True, False, decodequeue3, False, False)
                        except:
                            self.decoder  = repeater.p25_frame_assembler('127.0.0.1', 0, 0, True, True, False, decodequeue2, True, (True if protocol == 'p25_tdma' else False), False)
                            self.decoder2 = repeater.p25_frame_assembler('127.0.0.1', 0, 0, False, True, False, decodequeue3, False, False, False)

                        self.qsink = qsink = zeromq.pub_sink(gr.sizeof_char, 1, 'tcp://127.0.0.1:*')
                        self.zmq_socket.connect(qsink.last_endpoint())
                        
                        self.float_conversion = blocks.short_to_float(1, 8192)
        
                        self.connect(self.source, self.prefilter, self.fm_demod)#, (self.subtract,0))
                        #self.connect(self.fm_demod, self.symbol_filter, self.demod_fsk4, self.slicer, self.decoder, self.imbe, self.float_conversion, self.sink)
                        self.connect(self.fm_demod, self.symbol_filter, self.demod_fsk4, self.slicer, self.decoder, self.float_conversion, self.sink)
                        self.connect(self.slicer,self.decoder2, self.qsink)
                        #self.connect(self.fm_demod, self.avg, self.mult, (self.subtract,1))
                elif protocol == 'p25_cqpsk' or protocol == 'p25_cqpsk_tdma':
                        self.symbol_deviation = symbol_deviation = 600.0
                        self.resampler = blocks.multiply_const_cc(1.0)
                        self.agc = analog.feedforward_agc_cc(1024,1.0)
                        self.symbol_filter_c = blocks.multiply_const_cc(1.0)

                        gain_mu= 0.025
                        if protocol == 'p25_cqpsk_tdma':
                                symbol_rate = 6000
                        else:
                                symbol_rate = 4800

                        taps = firdes.low_pass_2(1.0,self.channel_rate,self.channel_rate/2,500.0, 30.0, firdes.WIN_BLACKMAN)
                        self.prefilter = filter.freq_xlating_fir_filter_ccc(1, taps, 0, self.input_rate)

                        omega = float(self.input_rate) / float(symbol_rate)
                        gain_omega = 0.1  * gain_mu * gain_mu

                        alpha = 0.04
                        beta = 0.125 * alpha * alpha
                        fmax = 1200     # Hz
                        fmax = 2*pi * fmax / float(self.input_rate)

                        self.clock = repeater.gardner_costas_cc(omega, gain_mu, gain_omega, alpha,  beta, fmax, -fmax)
                        self.diffdec = digital.diff_phasor_cc()
                        self.to_float = blocks.complex_to_arg()
                        self.rescale = blocks.multiply_const_ff( (1 / (pi / 4)) )

                        # symbol slicer
                        levels = [ -2.0, 0.0, 2.0, 4.0 ]
                        self.slicer = op25.fsk4_slicer_fb(levels)

                        #self.imbe = repeater.vocoder(False, True, 0, "", 0, False)
                        self.decodequeue3 = decodequeue3 = gr.msg_queue(2)
                        self.decodequeue2 = decodequeue2 = gr.msg_queue(2)
                        self.decodequeue = decodequeue = gr.msg_queue(10000)

                        #self.demod_watcher = demod_watcher(decodequeue2, self.adjust_channel_offset)
                        try:
                            self.decoder  = repeater.p25_frame_assembler('127.0.0.1', 0, 0, True, True, False, decodequeue2, True, (False if protocol == 'p25_cqpsk' else True))
                            self.decoder2 = repeater.p25_frame_assembler('127.0.0.1', 0, 0, False, True, True, decodequeue3, False, False)
                        except:
                            self.decoder  = repeater.p25_frame_assembler('127.0.0.1', 0, 0, True, True, False, decodequeue2, True, (False if protocol == 'p25_cqpsk' else True), False)
                            self.decoder2 = repeater.p25_frame_assembler('127.0.0.1', 0, 0, False, True, True, decodequeue3, False, False, False)

                        #temp for debug
                        #self.debug_sink = blocks.file_sink(1, '/dev/null')
                        #self.connect(self.slicer, self.debug_sink)

                        self.qsink = qsink = zeromq.pub_sink(gr.sizeof_char, 1, 'tcp://127.0.0.1:*')
                        self.zmq_socket.connect(qsink.last_endpoint())

                        self.float_conversion = blocks.short_to_float(1, 8192)

                        self.connect(self.source, self.prefilter, self.resampler, self.agc, self.symbol_filter_c, self.clock, self.diffdec, self.to_float, self.rescale, self.slicer, self.decoder2, self.qsink)#, (self.subtract,0))
                        self.connect(self.slicer, self.decoder, self.float_conversion, self.sink)
                elif protocol == 'provoice':
                        fm_demod_gain = 0.6
                        self.fm_demod = analog.quadrature_demod_cf(fm_demod_gain)
                        
                        self.resampler_in = filter.rational_resampler_fff(interpolation=48000, decimation=self.input_rate, taps=None, fractional_bw=None, )
                        self.dsd = dsd.block_ff(dsd.dsd_FRAME_PROVOICE,dsd.dsd_MOD_AUTO_SELECT,3,0,False)
                        self.out_squelch = analog.pwr_squelch_ff(-100,0.01, 0, True)
                        
                        self.connect(self.source, self.fm_demod, self.resampler_in, self.dsd, self.out_squelch, self.sink)
                elif protocol == 'dsd_p25':
                        symbol_deviation = 600.0
                        fm_demod_gain = 0.4 #self.input_rate / (2.0 * pi * symbol_deviation)
                        self.fm_demod = analog.quadrature_demod_cf(fm_demod_gain)

                        self.resampler_in = filter.rational_resampler_fff(interpolation=48000, decimation=self.input_rate, taps=None, fractional_bw=None, )
                        self.dsd = dsd.block_ff(dsd.dsd_FRAME_P25_PHASE_1,dsd.dsd_MOD_AUTO_SELECT,3,3,False)

                        self.connect(self.source, self.fm_demod, self.resampler_in, self.dsd, self.sink)
                self.unlock()
        def set_p25_tdma_slot(self, slot):
                if self.protocol != 'p25_tdma' and self.protocol != 'p25_cqpsk_tdma':
                        return False

                self.decoder.set_slotid(slot)
                self.decoder2.set_slotid(slot)
        def set_p25_xor_chars(self, xor_chars):
                pass
                self.decoder.set_xormask(xor_chars)
                self.decoder2.set_xormask(xor_chars)
                #return False

        def adjust_channel_offset(self, delta_hz):
                pass
                self.log.debug('adjust channel offset: %s' % (delta_hz))

                max_delta_hz = 12000.0
                delta_hz *= self.symbol_deviation
                delta_hz = max(delta_hz, -max_delta_hz)
                delta_hz = min(delta_hz, max_delta_hz)
                if self.prefilter != None:
                        self.prefilter.set_center_freq(0 - delta_hz)

        def debug(self):
            while not self.destroyed:
                time.sleep(10)
                print('DEBUG: %s %s %s %s %s' % (time.time(), self.connector.my_client_id, self.cdr['call_uuid'], self.destroyed, self.in_use))

        def p25_sensor(self, tb):

                import binascii
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
                last_duid = None
                last_lc = None
                while(not self.destroyed):
                        #if self == None or self.destroyed != False:
                        if self.destroyed != False:
                                break

                        time.sleep(0.007)
                        if self.protocol != 'p25' and self.protocol != 'p25_cqpsk' and self.protocol != 'p25_tdma' and self.protocol != 'p25_cqpsk_tdma' :
                                continue
                
                        try:
                                self.decodequeue
                        except:
                                self.log.critical('NO DECODEQUEUE')
                                continue
                        pkt = b''
                        try:
                            pkt = self.zmq_socket.recv(flags=zmq.NOBLOCK)
                        except Exception as e:
                            pass

                        buf += pkt

                        fsoffset = buf.find(binascii.unhexlify('5575f5ff77ff'))
                        fsnext   = buf.find(binascii.unhexlify('5575f5ff77ff'), fsoffset+6)
                        if(fsoffset != -1 and fsnext != -1):
                                frame = buf[fsoffset:fsnext]
                                buf = buf[fsnext:]

                                if len(frame) < 10: continue
                                frame_sync = binascii.hexlify(frame[0:6])

                                duid = int.from_bytes(frame[7:8], "big") & 0xf
                                nac = (int.from_bytes(frame[6:7], "big")<<4) +((int.from_bytes(frame[7:8],"big")&0xf0)>>4)


                                if duid == 0x5 or duid == 0xa:
                                        self.activity()
                                #if self.in_use and (duid == 0x3 or duid == 0xF) and (last_duid == 0x3 or last_duid == 0xF):
                                #        self.close({})
                                #print '%s %s' % (hex(duid), hex(nac))
                                last_duid = duid
                                r = {}
                                try:
                                        if duid == 0x0:
                                                r = self.p25_general.procHDU(frame)
                                        elif duid == 0x3:
                                                r = self.p25_general.procTnoLC(frame)
                                        elif duid == 0x5:
                                                r = self.p25_general.procLDU1(frame)
                                        elif duid == 0x7:
                                                r = self.p25_general.procTSDU(frame)
                                        elif duid == 0xA:
                                                r = self.p25_general.procLDU2(frame)
                                        elif duid == 0xC:
                                                r = self.p25_general.procPDU(frame)
                                        elif duid == 0xF:
                                                r = self.p25_general.procTLC(frame)
                                        else:
                                                self.log.warning("%s: ERROR: Unknown DUID %s" % (self.thread_id, duid))
                                except Exception as e:
                                        if duid == 0x5 or duid == 0xf: pass #print e
                                        continue
                                        
                                body = {
                                        'packet': r,
                                        'instance_uuid': self.cdr['instance_uuid'],
                                        'call_uuid': self.cdr['call_uuid'],
                                        }
                                try:
                                        packet_type = r['lc']['lcf_long']
                                except:
                                        packet_type = 'invalid'
                                try:
                                        if last_lc != r['lc'] and r['lc']['lcf_long'] == 'Call Termination / Cancellation':
                                                self.client_redis.send_event_lazy('/topic/raw_voice/%s' %self.cdr['instance_uuid'] , body, {'packet_type': packet_type }, False)
                                        last_lc = r['lc']
                                except:
                                        pass
                                


        def upload_and_cleanup(self, filename, uuid, cdr, filepath, patches, emergency=False):
                        
                        #if not emergency:
                        self.destroy()
                        if cdr['modulation_type'] in ['p25', 'p25_cqpsk', 'p25_tdma', 'p25_cqpsk_tdma']:
                                os.system('nice -n 19 sox ' + filename[:-4] + '.wav ' + filename[:-4] +'-sox.wav gain -h equalizer 0.25k 0.5k -8 equalizer 0.75k 0.5k -6 equalizer 1.25k 0.5k -6  contrast loudness gain -n -6 dither')
                        elif cdr['modulation_type'] == 'analog_edacs':
                                os.system('nice -n 19 sox ' + filename[:-4] + '.wav ' + filename[:-4] +'-sox.wav gain -h trim 0.2 contrast loudness gain -n -6 dither')
                        else:
                                os.system('nice -n 19 sox ' + filename[:-4] + '.wav ' + filename[:-4] +'-sox.wav gain -h contrast loudness gain -n -6 dither')
                        os.system('nice -n 19 lame -b 32 -q2 --silent ' + filename[:-4] + '-sox.wav ' +filename[:-4] + '.mp3 2>&1 >/dev/null')

                        filename = filename[:-4] + '.mp3'
                        tags = {}
                        tags['TIT2'] = '%s %s' % (cdr['type'],cdr['system_group_local'])
                        tags['TPE1'] = '%s' %(cdr['system_user_local'])
                        tags['TALB'] = '%s' % (cdr['system_id'])
                        
                        groups = []
                        for patch_group in patches:
                                if(cdr['system_group_local'] in patches[patch_group] or cdr['system_group_local'] == patch_group):
                                        for group in patches[patch_group]:
                                                groups.append(group)
                                        groups.append(patch_group)
                        groups = list(set(groups))

                        tags['COMM'] = '%s,%s,%s' %(cdr['system_channel_local'],cdr['time_open'], groups)
                        tags['COMM'] = tags['COMM'].replace(':', '|')
                        os.system('id3v2 -2 --TIT2 "%s" --TPE1 "%s" --TALB "%s" -c "RC":"%s":"English" %s' % (tags['TIT2'], tags['TPE1'], tags['TALB'], tags['COMM'], filename))
                        #os.system('mp3gain -q -c -p %s' % (filename))
        
                        try: 
                                if not self.log_wav:
                                        os.remove(filename[:-4] + '.wav')
                                        self.log.info('Deleting %s wav file' % (cdr['uuid'],))
                        except:
                                self.log.info('error removing ' + filename[:-4] + '.wav')
                        try:
                                if not self.log_wav:
                                        
                                        os.remove(filename[:-4] + '-sox.wav')
                                        self.log.info('Deleting %s post sox wav file' % (cdr['uuid'],))
                        except:
                                pass

                        return filename

        def close(self, patches, send_event_func=False, emergency=False):
                self.thread_lock.acquire()
                self.thread_lock.release()
                if self.destroyed == True:
                        return True
                #print "(%s) %s %s" %(time.time(), "Close ", str(self.cdr))
                self.cdr['time_close'] = time.time()
                self.log.info('CLOSE %s %s' % (self.cdr['instance_uuid'], self.cdr['call_uuid']))

                if self.cdr['modulation_type'] in ['p25', 'p25_cqpsk', 'p25_tdma', 'p25_cqpsk_tdma']:
                        try:
                                self.cdr['errors'] = self.decoder.get_errors()
                        except Exception as e:
                                self.log.error('Exception calling decoder.get_errors(): %s %s' % (type(e), e))
                                self.cdr['errors'] = 9999999

                if(self.audio_capture):
                        self.stop()
                        try:
                                self.sink.close()
                        except:
                                print('%s' % self.sink)
                        #self.debug_sink.close()
                        if self.log_dat:
                                self.dat_sink.close()
                        filename = self.upload_and_cleanup(self.filename, self.uuid, self.cdr, self.filepath, patches, False)
                        self.client_activemq.send_event_hopeful('/queue/call_management/call_complete', {'cdr': self.cdr, 'filename': filename, 'uuid': self.uuid}, True)
                self.time_last_use = time.time()
                self.uuid =''
                self.in_use = False
        def destroy(self):
                if self.destroyed == True:
                    return True
                if self.protocol == 'p25' or self.protocol=='p25_cqpsk' or self.protocol == 'p25_tdma' or self.protocol == 'p25_cqpsk_tdma':
                        try:
                                self.demod_watcher.keep_running = False
                        except:
                                pass

                self.configure_blocks('none')
                self.connector.release_channel()

                self.connector.exit()

                self.source = None
                self.sink = None

                self.destroyed = True

        def set_rate(self, channel_rate):
                if(channel_rate != self.channel_rate):
                        self.log.debug('System: Adjusting audio rate %s' % (channel_rate))
                        self.channel_rate = channel_rate
                        self.input_rate = channel_rate
                        proto = self.protocol
                        if proto == None: return True
                        self.configure_blocks('none')
                        self.configure_blocks(proto)

        def open(self):
                if self.destroyed == True:
                        return False
                if(self.in_use != False): raise RuntimeError("open() without close() of logging receiver")
                self.in_use = True
                self.uuid = self.cdr['uuid'] = str(uuid.uuid4())


                self.log.info('OPEN %s %s %s' % (self.cdr['instance_uuid'], self.cdr['call_uuid'], self.cdr))
                now = datetime.datetime.utcnow()

                if(self.cdr['type'] == 'group'):
                        self.filepath = filepath = "%s/%s/%s/%s/%s/%s/%s" % ('audio', now.year, now.month, now.day, now.hour, self.cdr['instance_uuid'], self.cdr['system_group_local'])
                elif(self.cdr['type'] == 'individual'):
                        self.filepath = filepath = "%s/%s/%s/%s/%s/%s/%s" % ('audio', now.year, now.month, now.day, now.hour, '%s' % self.cdr['instance_uuid'], 'individual')
                try: 
                        os.makedirs(filepath)
                except:
                        pass
                self.filename = str("%s/%s.wav" % (filepath, self.uuid))

                if(self.audio_capture):
                        self.sink.open('%s' % self.filename)
                        #debug:
                        #self.debug_sink.open('%s.dat' % self.filename)
                        if self.log_dat:
                                self.dat_sink.open('%s/%s.dat' % (filepath, self.uuid))

                self.activity()
        def set_codec_provoice(self,input):
                self.codec_provoice = input
        def set_codec_p25(self, input):
                self.codec_p25 = input
        def getfreq(self):
                return self.freq
        def activity(self):
                self.time_activity = time.time()
                self.time_last_use = time.time()
        def acquire_lock(self, lock_id):
                self.log.debug('%s attempt lock acquire %s' % (self.thread_id, lock_id))
                if self.lock_id == False:
                        self.lock_id = lock_id
                        return True
                else:
                        return False
                return integer

# Demodulator frequency tracker
#
class demod_watcher(threading.Thread):

    def __init__(self, msgq,  callback, **kwds):
        threading.Thread.__init__ (self, **kwds)
        self.setDaemon(1)
        self.msgq = msgq
        self.callback = callback
        self.keep_running = True
        self.last_msg = None
        self.start()

    def run(self):
        while(self.keep_running):
                msg = self.msgq.delete_head()
                self.last_msg = msg
                frequency_correction = msg.arg1()
                self.log.info('Freq correction %s' % (frequency_correction))
                self.callback(frequency_correction)
                                                                 
if __name__ == '__main__':
        tb = logging_receiver(49999)
        cdr = {
                'type': 'group',
                'system_group_local': 0,
                'system_id': 0
                }
        tb.open(cdr, 12500)
        time.sleep(5)
        tb.wait()
        tb.close({})
