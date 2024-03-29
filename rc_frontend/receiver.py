#!/usr/bin/python3

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

from gnuradio import gr, filter
from gnuradio import blocks, zeromq
from gnuradio.filter import pfb, firdes
import gnuradio.filter.optfir as optfir

import time
import sys
import threading
import math
import os
import random
import json
import uuid
import logging
import logging.config
import argparse

import channel
import copy
from config import rc_config

import zmq
from redis_channel_publisher import redis_channel_publisher

class receiver(gr.top_block):
        def __init__(self, index):
                gr.top_block.__init__(self, 'receiver')

                if(index == None):
                    self.log = logging.getLogger('frontend')
                else:
                    self.log = logging.getLogger('frontend-%s' % (index, ))

                try:
                        gr.enable_realtime_scheduling()
                except:
                        pass


                self.zmq_context = zmq.Context()
                self.zmq_socket = self.zmq_context.socket(zmq.REP)
                self.zmq_socket.bind("tcp://0.0.0.0:0")

                self.access_lock = threading.RLock()
                self.access_lock.acquire()
                self.last_channel_cleanup = time.time()
                self.channel_idle_timeout = 10 #TEMPORARY CHANGE, fixme

        
                self.config = config = rc_config()

                try:
                    self.scan_mode = config.scan_mode
                except:
                    self.scan_mode = False

                self.realsources = config.sources

                self.sources = {}
                numsources = 0


                if index != None:
                    for i in list(self.realsources):
                        if i != int(index):
                            del self.realsources[i]
                self.log.info('Sources at init: %s %s' % (self.sources, self.realsources))

                for source in self.realsources:
                        if config.receiver_split2:
                                newsource1 = copy.copy(self.realsources[source])
                                newsource2 = copy.copy(self.realsources[source])
        
                                decim = 2
                                samp_rate = self.realsources[source]['samp_rate']
                                channel_rate = (samp_rate/decim)/2
                                transition = channel_rate*0.5
                                
                                taps = firdes.low_pass(1,samp_rate,channel_rate,transition)
        
                                filt1 = filter.freq_xlating_fir_filter_ccc(decim, (taps), -samp_rate/4, samp_rate)
                                filt2 = filter.freq_xlating_fir_filter_ccc(decim, (taps), samp_rate/4, samp_rate)

                        if self.realsources[source]['type'] == 'usrp':
                                from gnuradio import uhd

                                this_dev = uhd.usrp_source(
                                        device_addr=self.realsources[source]['device_addr'],
                                        stream_args=uhd.stream_args(
                                                cpu_format="fc32",
                                                otw_format=self.realsources[source]['otw_format'],
                                                args=self.realsources[source]['args'],
                                        ),
                                )
                                this_dev.set_samp_rate(self.realsources[source]['samp_rate'])
                                this_dev.set_center_freq(self.realsources[source]['center_freq'])
                                this_dev.set_gain(self.realsources[source]['rf_gain'])

                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect(this_dev, null_sink)

                                self.realsources[source]['block'] = this_dev
                        if self.realsources[source]['type'] == 'usrp2x':
                                from gnuradio import uhd

                                this_dev = uhd.usrp_source(
                                        device_addr=self.realsources[source]['device_addr'],
                                        stream_args=uhd.stream_args(
                                                cpu_format="fc32",
                                                otw_format=self.realsources[source]['otw_format'],
                                                args=self.realsources[source]['args'],
                                                channels=range(2),
                                        ),
                                )

                                this_dev.set_subdev_spec('A:RX1 A:RX2', 0)
                                this_dev.set_samp_rate(self.realsources[source]['samp_rate'])

                                this_dev.set_center_freq(self.realsources[source]['center_freq'], 0)
                                this_dev.set_center_freq(self.realsources[source+1]['center_freq'], 1)
                                this_dev.set_gain(self.realsources[source]['rf_gain'], 0)
                                this_dev.set_gain(self.realsources[source+1]['rf_gain'], 1)

                                multiply = blocks.multiply_const_vcc((1, ))
                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect((this_dev,0), multiply, null_sink)
                                self.realsources[source]['block'] = multiply

                                multiply = blocks.multiply_const_vcc((1, ))
                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect((this_dev,1), multiply, null_sink)
                                self.realsources[source+1]['block'] = multiply
                        if self.realsources[source]['type'] == 'bladerf':
                                import osmosdr

                                this_dev = osmosdr.source( args=self.realsources[source]['args'] )
                                this_dev.set_sample_rate(self.realsources[source]['samp_rate'])
                                this_dev.set_center_freq(self.realsources[source]['center_freq'], 0)
                                this_dev.set_freq_corr(0, 0)
                                #this_dev.set_dc_offset_mode(0, 0)
                                #this_dev.set_iq_balance_mode(0, 0)
                                this_dev.set_gain_mode(0, 0)
                                this_dev.set_gain(self.realsources[source]['rf_gain'], 0)
                                this_dev.set_if_gain(20, 0)
                                this_dev.set_bb_gain(self.realsources[source]['bb_gain'], 0)
                                this_dev.set_antenna("", 0)
                                this_dev.set_bandwidth(0, 0)


                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect(this_dev, null_sink)

                                self.realsources[source]['block'] = this_dev
                        if self.realsources[source]['type'] == 'rtlsdr':
                                import osmosdr

                                #process = os.popen('CellSearch -i '+ str(self.realsources[source]['serial']) +' -s 739e6 -e 739e6 -b | grep 739M | awk \'{sum+=$10} END { printf("%.10f", sum/NR)}\'')
                                #output = float(process.read())
                                #process.close()
                                #self.realsources[source]['offset'] = (1000000-(output*1000000))
                                #self.realsources[source]['offset'] = 0
                                #print 'Measured PPM - Dev#%s: %s' % (source, self.realsources[source]['offset'])

                                this_dev = osmosdr.source( args=self.realsources[source]['args'] )
                                this_dev.set_sample_rate(self.realsources[source]['samp_rate'])
                                this_dev.set_center_freq(self.realsources[source]['center_freq']+self.realsources[source]['offset'], 0)
                                #this_dev.set_freq_corr(self.realsources[source]['offset'], 0)
                                #this_dev.set_max_output_buffer(65535*64)

                                this_dev.set_dc_offset_mode(1, 0)
                                this_dev.set_iq_balance_mode(1, 0)
                                this_dev.set_gain_mode(False, 0)
                                this_dev.set_gain(self.realsources[source]['rf_gain'], 0)
                                this_dev.set_if_gain(30, 0)
                                this_dev.set_bb_gain(self.realsources[source]['bb_gain'], 0)


                                try:
                                        null_sink = gr.null_sink(gr.sizeof_gr_complex*1)
                                except:
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)

                                self.connect(this_dev, null_sink)

                                zmq_sink = self.realsources[source]['zmq_sink'] = zeromq.pub_sink(gr.sizeof_gr_complex, 1, 'ipc:///tmp/rx_source_%s' % (source), 100, False, -1)
                                self.connect(this_dev, zmq_sink)

                                self.realsources[source]['block'] = this_dev
                        if config.receiver_split2:
                                newsource1 = copy.copy(self.realsources[source])
                                newsource2 = copy.copy(self.realsources[source])

                                decim = 2
                                samp_rate = self.realsources[source]['samp_rate']
                                channel_rate = (samp_rate/decim)/2
                                transition = channel_rate*0.5

                                taps = firdes.low_pass(1,samp_rate,channel_rate,transition)

                                filt1 = filter.freq_xlating_fir_filter_ccc(decim, (taps), -samp_rate/4, samp_rate)
                                filt2 = filter.freq_xlating_fir_filter_ccc(decim, (taps), samp_rate/4, samp_rate)

                                null_sink1 = blocks.null_sink(gr.sizeof_gr_complex*1)
                                null_sink2 = blocks.null_sink(gr.sizeof_gr_complex*1)

                                self.connect(self.realsources[source]['block'], filt1, null_sink1)
                                self.connect(self.realsources[source]['block'], filt2, null_sink2)
                        
                                newsource1['block'] = filt1
                                newsource1['center_freq'] = self.realsources[source]['center_freq']-self.realsources[source]['samp_rate']/4
                                newsource1['samp_rate'] = newsource1['samp_rate']/decim
                                newsource2['block'] = filt2
                                newsource2['center_freq'] = self.realsources[source]['center_freq']+self.realsources[source]['samp_rate']/4
                                newsource2['samp_rate'] = newsource2['samp_rate']/decim
                
                                
                
                                self.sources[numsources] = newsource1
                                numsources = numsources+1
                                self.sources[numsources] = newsource2
                                numsources = numsources+1
                        else:
                                self.sources[numsources] = self.realsources[source]
                                self.sources[numsources]['source_id'] = source
                                numsources = numsources+1
                if self.config.frontend_mode == 'pfb':
                        for source in self.sources:
                                self.target_size = target_size = 400000
                                if(self.sources[source]['samp_rate']%target_size):
                                        raise Exception('samp_rate not round enough')
        
                                num_channels = int(math.ceil(self.sources[source]['samp_rate']/target_size))
                                self.sources[source]['pfb'] = pfb.channelizer_ccf(
                                  num_channels,
                                  (optfir.low_pass(1,num_channels,0.5, 0.5+0.2, 0.1, 80)),
                                  1.0,
                                  100
                                )
                                self.sources[source]['pfb'].set_channel_map(([]))
                                #null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                #self.connect((self.sources[source]['pfb'], 0), null_sink)
                                for x in range(0,num_channels):
                                        null_sink = blocks.null_sink(gr.sizeof_gr_complex*1)
                                        self.connect((self.sources[source]['pfb'], x), null_sink)
                                self.connect(self.sources[source]['block'], self.sources[source]['pfb'])

                self.log.info('Sources after init: %s %s' % (self.sources, self.realsources))
                self.channels = {}
                #for i in self.sources.keys():
                #        self.channels[i] = []

                self.redis_channel_publisher = redis_channel_publisher(sources=self.sources, channels=self.channels, zmq_socket=self.zmq_socket, index=index)


                self.start()
                self.access_lock.release()
        def connect_channel(self, channel_rate, freq):

                if self.config.frontend_mode == 'pfb':
                        return self.connect_channel_pfb(channel_rate, freq)
                elif self.config.frontend_mode == 'xlat':
                        return self.connect_channel_xlat(channel_rate, freq)
                else:
                        raise Exception('No frontend_mode selected')

        def connect_channel_xlat(self, channel_rate, freq):
                source_id = None
                source_distance = None

                if self.scan_mode == False:
                    for i in list(self.sources):
                        if abs(freq-self.sources[i]['center_freq']) < self.sources[i]['samp_rate']/2:
                                if source_distance == None or abs(freq-self.sources[i]['center_freq']) < source_distance:
                                        source_id = i
                                        source_distance = abs(freq-self.sources[i]['center_freq'])
    
                    if source_id == None:
                            raise Exception('Unable to find source for frequency %s' % freq)
                else:
                    source_id = 0
                
                source_center_freq = self.sources[source_id]['center_freq']
                source_samp_rate = self.sources[source_id]['samp_rate']
                source = self.sources[source_id]['block']
                real_source_id = self.sources[source_id]['source_id']

                offset = freq-source_center_freq
                if freq < 10000000:
                   offset = freq #scan mode, relative freq 

                #We have all our parameters, lets see if we can re-use an idling channel
                self.access_lock.acquire()
                block = None

                for c in list(self.channels):
                        if self.channels[c].source_id == source_id and self.channels[c].channel_rate == channel_rate and self.channels[c].in_use == False:
                                block = self.channels[c]
                                block_id = block.block_id
                                port = block.port
                                block.set_offset(offset)
                                block.channel_close_time = 0
                                #TODO: move UDP output
                                break

                if block == None:
                        for x in range(0, 3):
                                port = random.randint(10000,60000)
                                try:
                                    block = channel.channel('ipc:///tmp/rx_source_%s' % (real_source_id), port, channel_rate,(source_samp_rate), offset)
                                    break
                                except RuntimeError as err:
                                        self.log.error('Failed to build channel on port: %s attempt: %s' % (port, x))
                                        return False, False

                        block.source_id = source_id
                        block_id = '%s' % uuid.uuid4()
                        self.channels[block_id] = block
                        block.block_id = block_id

                        block.start()

                block.in_use = True

                self.access_lock.release()
                return block.block_id, port

        def connect_channel_pfb(self, channel_rate, freq):
        
                source_id = None

                if self.scan_mode == False:
                    for i in list(self.sources):
                        if abs(freq-self.sources[i]['center_freq']) < self.sources[i]['samp_rate']/2:
                                source_id = i
                                break

                    if source_id == None:
                        raise Exception('Unable to find source for frequency %s' % freq)

                source_center_freq = self.sources[source_id]['center_freq']
                source_samp_rate = self.sources[source_id]['samp_rate']
                source = self.sources[source_id]['block']

                offset = freq-source_center_freq

                if freq < 10000000:
                    offset = freq #scan mode, relative freq

                pfb = self.sources[source_id]['pfb']

                pfb_samp_rate = self.target_size #1000000
                pfb_center_freq = source_center_freq - (pfb_samp_rate/2)

                num_channels = source_samp_rate/pfb_samp_rate

                offset = freq - source_center_freq
                chan = int(round(offset/float(pfb_samp_rate)))
                if chan < 0:
                        chan = chan + num_channels

                pfb_offset = offset-(chan*(pfb_samp_rate))

                pfb_id = chan

                

                if pfb_offset < (-1*(pfb_samp_rate/2))+(channel_rate/2) or pfb_offset > (pfb_samp_rate/2)-(channel_rate/2):
                        self.log.warning('warning: %s edge boundary' % freq)
                #We have all our parameters, lets see if we can re-use an idling channel
                self.access_lock.acquire()

                block = None        

                for c in list(self.channels):
                        if self.channels[c].source_id == source_id and self.channels[c].pfb_id == pfb_id and self.channels[c].in_use == False:
                                block = self.channels[c]
                                block_id = self.channels[c].block_id
                                block.set_offset(pfb_offset)
                                block.channel_close_time = 0
                                #TODO: move UDP output
                                break

                if block == None:
                        for x in range(0, 3):
                                port = random.randint(10000,60000)
                                try:
                                        block = channel.channel(port, channel_rate,(pfb_samp_rate), pfb_offset)
                                except RuntimeError as err:
                                        self.log.error('Failed to build channel on port: %s attempt: %s' % (port, x))
                                        pass

                        block.source_id = source_id
                        block.pfb_id = pfb_id

                        self.channels[port] = block
                        block_id = '%s' % uuid.uuid4()
                        block.block_id = block_id

                        self.lock()
                        self.connect((pfb,pfb_id), block)
                        self.unlock()

                block.in_use = True

                self.access_lock.release()

                return block.block_id, port
        def release_channel(self, block_id):
                self.access_lock.acquire()
                if block_id not in self.channels:
                        return True
                
                self.channels[block_id].in_use = False
                self.channels[block_id].channel_close_time = time.time()

                #TODO: move UDP output
                
                self.access_lock.release()
                return True
        def source_offset(self, block_id, offset):
                if self.scan_mode:
                        return False
                try:
                        center_freq = self.sources[self.channels[block_id].source_id]['center_freq']
                except:
                        return False
                try:
                        accumulated_offset = self.sources[self.channels[block_id].source_id]['accumulated_offset']
                except:
                        accumulated_offset = 0
                        
                try:
                        base_offset = self.sources[self.channels[block_id].source_id]['offset']
                except:        
                        base_offset = 0

                if offset > 1 or offset < -1:
                        hz_offset = offset*50
                elif offset > 0.5 or offset < -0.5:
                        hz_offset = offset*10
                else:
                        hz_offset = offset*4
                self.log.debug('hz_offset: %s' % hz_offset)
                if hz_offset < 5 and hz_offset > -5:
                        return True

                total_offset = accumulated_offset+hz_offset
                if abs(total_offset) > self.channels[block_id].channel_rate/2:
                        #if we've gone further than 1/2 of our channel width something is clearly wrong, lets try inverting our offset, but /2 so we don't immediately trip this again.
                        total_offset = (total_offset/2)*-1

                new_center_freq = center_freq+total_offset
                
                self.log.info('Source %s New Center freq %s %s' % (self.channels[block_id].source_id, new_center_freq, total_offset))
                self.access_lock.acquire()
                self.sources[self.channels[block_id].source_id]['block'].set_center_freq(new_center_freq+base_offset,0)
                self.sources[self.channels[block_id].source_id]['accumulated_offset'] = total_offset
                self.access_lock.release()
                return True

if __name__ == '__main__':
        with open('config.logging.json', 'rt') as f:
            config = json.load(f)


        parser = argparse.ArgumentParser()
        parser.add_argument('-i', '--index', help="Device config index, if specified, all other configured sources will be deleted")
        args = parser.parse_args()

        logging.config.dictConfig(config)
        if(args.index == None):
            log = logging.getLogger('frontend')
        else:
            log = logging.getLogger('frontend-%s' % (args.index, ))


        tb = receiver(args.index)
        #print len(tb.channels)
        #tb.wait()
        import time
        import sys
        import os 
        clients = {}
        client_hb = {}
        client_num = 0

        def handler(msg, tb):
                global clients
                global client_hb
                #if not data: 
                #        for x in my_channels:
                #               tb.release_channel(x)
                #        break
                data = msg.strip().split(',')
                if data[0] == 'create':
                        c = int(data[1])
                        channel_rate = int(data[2])
                        freq = int(data[3])
                        try:
                                block_id, port = tb.connect_channel(channel_rate, freq)
                        except Exception as e:
                                block_id = -1
                                log.error('Exception: %s' % e)

                        if block_id == -1 or block_id == False:
                                #Channel failed to create, probably freq out of range
                                log.error('failed to create channel %s' % freq)
                                return 'na,%s' % freq
                        else:
                                log.info('%s Created channel ar: %s %s %s %s %s %s' % ( time.time(), len(tb.channels), channel_rate, freq, port, block_id, c))
                                try:
                                        clients[c].append(block_id)
                                except Exception as e:
                                        print(clients)
                                        log.error('Exception in channel creation %s' % e)
                                        tb.release_channel(block_id)
                                        return 'na,%s' % freq
                                return 'create,%s,%s' % (block_id, port)
                elif data[0] ==  'release':
                        try:
                                c = int(data[1])
                                block_id = data[2]
                                result = tb.release_channel(block_id)
                                
                                if result == -1:
                                        #Channel failed to release
                                        log.error('failed to release %s %s' % (block_id, c))
                                        return 'na,%s' % block_id
                                else:
                                        log.info('Released channel %s %s' % ( block_id,c))
                                        try:
                                                clients[c].remove(block_id)
                                        except ValueError as e:
                                                pass
                                        return 'release,%s' % block_id
                        except Exception as e:
                                return 'na\n'
                elif data[0] == 'scan_mode_set_freq':
                    freq = int(data[1])
                    try:
                        log.info('attempting to set center freq to %s' % freq)
                        if 'offset' in tb.realsources[0]:
                            tb.realsources[0]['block'].set_center_freq(freq+tb.realsources[0]['offset'], 0)
                        else:
                            tb.realsources[0]['block'].set_center_freq(freq, 0)
                        log.info('success set center freq')
                        return 'success'
                    except:
                        raise
                        return 'fail'

                elif data[0] == 'quit':
                        c = int(data[1])
                        log.info('quit received from client %s' % c)
                        try:
                                for x in clients[c]:
                                        tb.release_channel(x)
                        except KeyError as e:
                                pass
                        except:
                                raise
                        finally:

                                try:
                                    del client_hb[c]
                                except:
                                    pass
                                try:
                                    del clients[c]
                                except:
                                    pass

                        return 'quit,%s' % c
                elif data[0] == 'connect':
                        global client_num
                        c = client_num
                        client_num = client_num + 1
                        clients[c] = []
                        client_hb[c] = time.time()
                        log.info('connect received from %s' % c)
                        return 'connect,%s' % c
                elif data[0] == 'hb':
                        try:
                            c = int(data[1])
                        except:
                            return 'fail,0'
                        if c not in client_hb:
                                return 'fail,%s' % c
                        client_hb[c] = time.time()
                        return 'hb,%s' % c
                elif data[0] == 'offset':
                        client_id = int(data[1])
                        block_id = data[2]
                        offset = float(data[3])
        
                        tb.source_offset(block_id, offset)
                        
                        return 'offset,%s' % client_id

        context = tb.zmq_context
        socket = tb.zmq_socket
        start_time = time.time()
        last_status = time.time()

        while 1:
                if time.time()-last_status > 10:
                        log.info('Frontend Status: client: %s client_hb: %s channels: %s uptime: %s' % (len(clients), len(client_hb), len(tb.channels), int(time.time()-start_time)))
                        log.info('%s %s %s' % (clients, client_hb, tb.channels))
                        last_status = time.time()

                        #if int(time.time()-start_time) > 300 and len(tb.channels) < 5:
                        #        sys.exit(os.EX_SOFTWARE)
        
                        owned_channels = []
                        orphans = []
                        for client in clients:
                                for c in clients[client]:
                                        owned_channels.append(c)
                        if time.time()-tb.last_channel_cleanup > tb.channel_idle_timeout*2:
                                tb.last_channel_cleanup = time.time()
                                deletables = []
                                for c in list(tb.channels):
                                    if tb.channels[c].channel_close_time != 0 and time.time()-tb.channels[c].channel_close_time > tb.channel_idle_timeout:
                                        deletables.append(c)
                                if len(deletables) > 0:
                                        log.info('Channel cleanup initiated due to rf idle timeout')
                                        #tb.lock()
                                        for c in deletables:
                                                log.info('disconnecting channel %s' % tb.channels[c].block_id)
                                                #tb.disconnect(tb.sources[tb.channels[c].source_id]['block'], tb.channels[c])
                                                tb.channels[c].destroy()
                                                del tb.channels[c]
                                        #tb.unlock()

                deletions = []
                for client in list(client_hb):
                        try:
                            if time.time()-client_hb[client] > 5:
                                log.warning('Client heartbeat timeout %s' % client)
                                if client not in clients:
                                        log.warning('Cleaning up client_hb, as client has already quit')
                                        del client_hb[client]
                                for x in clients[client]:
                                        log.info('Attempting to release channel %s due to heartbeat timeout of client %s' % (x, client))
                                        tb.release_channel(x)
                                clients[client] = []

                                deletions.append(client)
                        except KeyError as e:
                                raise
                                pass
                        except:
                                raise
                                pass
                for c in deletions:
                        log.info('Deleting %s from client_hb and clients' % c)
                        try:
                                del client_hb[c]
                        except:
                                pass
                        try:
                                del clients[c]
                        except:
                                pass

                #try:
                #        msg = socket.recv()
                #        resp = handler(msg, tb)
                #        socket.send(resp)
                try:
                        msg = socket.recv_string(flags=zmq.NOBLOCK)
                        resp = handler(msg, tb)
                except zmq.Again:
                    time.sleep(0.001)
                    continue
                except Exception as e:
                        log.error('Exception in recv_string: (%s) %s' % (type(e), e))
                for t in range(3):
                    try:
                        socket.send_string(resp)
                        break
                    except Exception as e:
                        log.error('Exception in send_string: (%s) %s' % (type(e), e))
                #print(tb.channels)
