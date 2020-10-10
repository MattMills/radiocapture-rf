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

from client_activemq import client_activemq
import rs64
import golay
import hamming
import util


class logging_receiver(gr.top_block):
        def __init__(self, cdr, client_activemq, client_redis):
                self.thread_lock = threading.Lock()
                self.thread_lock.acquire()
                self.audio_capture = True

                gr.top_block.__init__(self, "logging_receiver")

                self.cdr = cdr
                self.in_use = False
                self.client_activemq = client_activemq
                self.client_redis = client_redis
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

                self.log = logging.getLogger('overseer.logging_receiver')
                self.log.debug('Initializing call_recorder')

                #debug = threading.Thread(target=self.debug, name='logging_receiver_debug')
                #debug.daemon = True
                #debug.[tart()

                #Setup connector
                self.connector = frontend_connector()
                for retry in 1,2,3,4,5:
                        try:
                                channel_id, port = self.connector.create_channel(int(self.cdr['channel_bandwidth']), int(self.cdr['frequency']))
                                self.source = zeromq.sub_source(gr.sizeof_gr_complex*1, 1, 'tcp://%s:%s' % (self.connector.host, port))
                                break
                        except:
                                pass
                if self.source == None:
                        self.connector.exit()
                        return False

                if self.log_dat:
                        self.dat_sink = blocks.file_sink(gr.sizeof_gr_complex*1, self.filename)
                        self.connect(self.source, self.dat_sink)


                self.set_rate(int(self.cdr['channel_bandwidth']*2))
                self.configure_blocks(self.cdr['modulation_type'])
                if self.cdr['modulation_type'] == 'p25_tdma' or self.cdr['modulation_type'] == 'p25_cqpsk_tdma' :
                        try:
                                self.set_p25_xor_chars(p25p2_lfsr(int(self.cdr['p25_nac']),int(self.cdr['p25_system_id'],0),int(self.cdr['p25_wacn'],0)).xor_chars)
                        except:
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
                        self.disconnect(self.source, self.resampler, self.agc, self.symbol_filter_c, self.clock, self.diffdec, self.to_float, self.rescale, self.slicer, self.decoder2, self.qsink)#, (self.subtract,0))
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
                
                        self.prefilter = filter.freq_xlating_fir_filter_ccc(1, (1,), 0, self.input_rate)
        
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

                        
                        self.decoder  = repeater.p25_frame_assembler('', 0, 0, True, True, False, decodequeue2, True, (True if protocol == 'p25_tdma' else False))
                        self.decoder2 = repeater.p25_frame_assembler('', 0, 0, False, True, False, decodequeue3, False, False)

                        self.qsink = blocks.message_sink(gr.sizeof_char, self.decodequeue, False)
                        
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
                        self.decoder  = repeater.p25_frame_assembler('', 0, 0, True, True, False, decodequeue2, True, (False if protocol == 'p25_cqpsk' else True))
                        self.decoder2 = repeater.p25_frame_assembler('', 0, 0, False, True, True, decodequeue3, False, False)

                        #temp for debug
                        #self.debug_sink = blocks.file_sink(1, '/dev/null')
                        #self.connect(self.slicer, self.debug_sink)

                        self.qsink = blocks.message_sink(gr.sizeof_char, self.decodequeue, False)

                        self.float_conversion = blocks.short_to_float(1, 8192)

                        self.connect(self.source, self.resampler, self.agc, self.symbol_filter_c, self.clock, self.diffdec, self.to_float, self.rescale, self.slicer, self.decoder2, self.qsink)#, (self.subtract,0))
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
                        if tb.decodequeue.count():
                                pkt = tb.decodequeue.delete_head().to_string()
                                buf += pkt

                        fsoffset = buf.find(binascii.unhexlify('5575f5ff77ff'))
                        fsnext   = buf.find(binascii.unhexlify('5575f5ff77ff'), fsoffset+6)
                        if(fsoffset != -1 and fsnext != -1):
                                frame = buf[fsoffset:fsnext]
                                buf = buf[fsnext:]

                                if len(frame) < 10: continue
                                frame_sync = binascii.hexlify(frame[0:6])
                                duid = int(ord(frame[7:8])&0xf)
                                nac = int(ord(frame[6:7]) +ord(frame[7:8])&0xf0)

                                if duid == 0x5 or duid == 0xa:
                                        self.activity()
                                #if self.in_use and (duid == 0x3 or duid == 0xF) and (last_duid == 0x3 or last_duid == 0xF):
                                #        self.close({})
                                #print '%s %s' % (hex(duid), hex(nac))
                                last_duid = duid
                                r = {}
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
                        except:
                                self.log.info('error removing ' + filename[:-4] + '.wav')
                        try:
                                if not self.log_wav:
                                        os.remove(filename[:-4] + '-sox.wav')
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
                        except e:
                                self.log.error('Exception calling decoder.get_errors(): ' %s)
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
                                self.decodequeue2.insert_tail(gr.message(0, 0, 0, 0))
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
                try:
                        self.decodequeue.flush()
                except:
                        pass
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
#Stuff pulled from p25
        def bin_to_bit(self, input):
                output = ''
                for i in range(0, len(input)):
                        output += bin(ord(input[i]))[2:].zfill(8)
                return output
        def procStatus(self, bitframe):
                r = []
                returnframe = ''
                for i in range(0, len(bitframe), 72):
                        r.append(int(bitframe[i+70:i+72],2))
                        returnframe += bitframe[i:i+70]
                        if(len(bitframe) < i+72):
                                break
                return [returnframe, r]
        # fake (10,6,3) shortened Hamming decoder, no error correction
        def hamming_10_6_3_decode(self, input):
                rs_code  = bytearray(24)
                rs_erasures = []
                for i in range(24):
                        hamming_code = int(input[i*10: (i+1)*10],2)
                        hamming_decoded = hamming.decode_lc(hamming_code)
                        if hamming_decoded is None:
                                rs_code[i] =  (hamming_code >> 4)
                                rs_erasures.append(i)
                        else:
                                rs_code[i] =  hamming_decoded        
                return rs_code, rs_erasures
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

                rs_code, rs_erasures = self.hamming_10_6_3_decode(lc)
                r['lc'] = self.subprocLC(rs_code, rs_erasures)

                return r
        def subprocLC(self, rs_code, rs_erasures):
                bitframe = self.rs_24_12_13_decode(rs_code, rs_erasures)
                r = {'short': 'LC', 'long': 'Link Control'}
                if bitframe == False:
                        return r #Uncorrectable decode
                r['p'] = int(bitframe[0:1], 2)
                r['sf'] = int(bitframe[1:2], 2)
                r['lcf'] = int(bitframe[2:8],2)

                if r['p'] == 1:
                        return r
                if r['sf'] == 0:
                        r['mfid'] = int(bitframe[8:16], 2)
                        bitframe = bitframe[16:]
                else:
                        r['mfid'] = 0
                        bitframe = bitframe[8:]

                if r['mfid'] != 0:
                        r['data'] = bitframe
                        return r

                if(r['lcf'] == 0): #Group Voice Channel User (LCGVR)
                        r['lcf_long'] = 'Group Voice Channel User'
                        r['service options'] = int(bitframe[0:8],2)
                        r['reserved'] = bitframe[8:15]
                        r['explicit'] = int(bitframe[15:16],2)
                        r['tgid'] = int(bitframe[16:32],2)
                        r['source_id'] = int(bitframe[32:56],2)
                        if self.cdr['system_user_local'] == 0:
                                self.cdr['system_user_local'] = r['source_id']
                        #print 'GV %s %s' %(r['tgid'], r['source_id'])
                elif r['lcf'] == 2:
                        r['lcf_long'] = 'Group Voice Channel Update'
                        r['channel_a'] = int(bitframe[0:16],2)
                        r['channel_a_group'] = int(bitframe[16:32], 2)
                        r['channel_b'] = int(bitframe[32:48], 2)
                        r['channel_b_group'] = int(bitframe[48:64], 2)
                elif r['lcf'] == 3:
                        r['lcf_long'] = 'Unit to Unit Voice Channel User'
                        r['service options'] = int(bitframe[0:8],2)
                        r['source_address'] = int(bitframe[8:32],2)
                        r['target_address'] = int(bitframe[32:56],2)
                elif r['lcf'] == 4:
                        r['lcf_long'] = 'Group Voice Channel Update - Explicit'
                        r['reserved'] = bitframe[0:8]
                        r['service_options'] = int(bitframe[8:16],2)
                        r['group_address'] = int(bitframe[16:32],2)
                        r['channel_transmit'] = int(bitframe[32:48],2)
                        r['chanenl_receive'] = int(bitframe[48:64], 2)
                elif r['lcf'] == 5:
                        r['lcf_long'] = 'Unit to Unit Answer Request'
                        r['service options'] = int(bitframe[0:8],2)
                        r['reserved'] = bitframe[8:15]
                        r['explicit'] = int(bitframe[15:16],2)
                        r['target_address'] = int(bitframe[16:40],2)
                        r['source_address'] = int(bitframe[40:64],2)
                elif r['lcf'] == 6:
                        r['lcf_long'] = 'Telephone Interconnect Voice Channel User'
                        r['reserved'] = bitframe[0:8]
                        r['service options'] = int(bitframe[8:16],2)
                        r['reserved2'] = bitframe[16:24]
                        r['call_timer'] = int(bitframe[24:40], 2)
                        r['target_adddress'] = int(bitframe[40:64],2)
                elif r['lcf'] == 7:
                        r['lcf_long'] = 'Telephone Interconnect Answer Request'
                        r['digit_1'] = int(bitframe[8:12],2)
                        r['digit_2'] = int(bitframe[12:16],2)
                        r['digit_3'] = int(bitframe[16:20],2)
                        r['digit_4'] = int(bitframe[20:24],2)
                        r['digit_5'] = int(bitframe[24:28],2)
                        r['digit_6'] = int(bitframe[28:32],2)
                        r['digit_7'] = int(bitframe[32:36],2)
                        r['digit_8'] = int(bitframe[36:40],2)
                        r['digit_9'] = int(bitframe[40:44],2)
                        r['digit_10'] = int(bitframe[44:48],2)
                        r['target_address'] = int(bitframe[48:64], 2)
                elif(r['lcf'] == 15): #Call Termination / Cancellation
                        r['lcf_long'] = 'Call Termination / Cancellation'
                        r['reserved'] = bitframe[0:40]
                        r['target_address'] = int(bitframe[40:64], 2)
                elif r['lcf'] == 16:
                        r['lcf_long'] = 'Group Affiliation Query'
                        r['reserved'] = bitframe[0:16]
                        r['target_address'] = int(bitframe[16:40], 2)
                        r['source_address'] = int(bitframe[40:64], 2)
                elif r['lcf'] == 17:
                        r['lcf_long'] = 'Unit Registration Command'
                        r['network_id'] = int(bitframe[0:12], 2)
                        r['system_id'] = int(bitframe[12:24], 2)
                        r['target_id'] = int(bitframe[24:48], 2)
                        r['reserved'] = bitframe[48:64]
                return r
        def golay_24_12_8_decode(self, input):
                rs_code = bytearray(24)
                rs_erasures = []
        
                for i in range(12):
                        golay_code = int(input[i*24: (i+1)*24],2)
                        golay_decoded= golay.decode_lc(golay_code)
                        if golay_decoded is None:
                                rs_code[2*i]   = (golay_code >>18 ) & 0x3F
                                rs_code[2*i+1] = (golay_code >>12 ) & 0x3F
                                rs_erasures.append(2*i)
                                rs_erasures.append(2*i+1)
                        else:
                                rs_code[2*i]   = (golay_decoded>> 6) & 0x3F
                                rs_code[2*i+1] = (golay_decoded) & 0x3F

                return rs_code, rs_erasures

        def procTLC(self, frame):
                r = {'short': 'TLC', 'Long' : 'Terminator with Link Control'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:-20]


                rs_code, rs_erasures = self.golay_24_12_8_decode(bitframe)
                r['lc'] = self.subprocLC(rs_code, rs_erasures)

                return r
        def rs_24_12_13_decode(self, rs_code, rs_erasures):
                data = rs64.decode_lc(rs_code, rs_erasures)

                if data:
                        return util.bytes_to_binary_str(data)
                else:
                        return False

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
