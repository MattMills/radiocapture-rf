#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com


import zmq
import random
import threading
import time
import logging
import uuid

class frontend_connector():
        def __init__(self, parent_instance_uuid, redis_channelizer_manager):
                #temp hack until I have auto-frontend figured out

                self.log = logging.getLogger('%s.frontend_connector' % (str(uuid.uuid4())))
        
                self.thread_lock = threading.Lock()
                self.send_lock = threading.Lock()

                #self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #self.s.connect((host,port))
                self.log.debug('Initializing Frontend Connector')

                self.continue_running = True
                self.redis_channelizer_manager = redis_channelizer_manager
                self.channel_port = 0
                self.host = None
                
                self.context = None
                self.socket = None
                self.my_client_id = None
                self.channel_id = None
                self.frequency = None
                self.last_create_channel = None

                connection_handler = threading.Thread(target=self.connection_handler, name='connection_handler')
                connection_handler.daemon = True
                connection_handler.start()
        def connection_init(self, frequency):
                self.context = zmq.Context()
                self.socket = self.context.socket(zmq.REQ)
                self.socket.setsockopt(zmq.RCVTIMEO, 1000) 
                self.socket.setsockopt(zmq.SNDTIMEO, 1000)
                self.socket.setsockopt(zmq.LINGER, 0)

                host, port = self.redis_channelizer_manager.get_channelizer_for_frequency(frequency)
                self.host = host
                self.log.info('Attempting ZMQ socket connection to tcp://%s:%s' % (host, port))
                try:
                    self.socket.connect("tcp://%s:%s" % (host, port))
                except Exception as e:
                    self.log.error('ZMQ connection failed to tcp://%s:%s Exception: (%s) %s' % (host, port, type(e), e))
                    raise e

                self.log.info('Successful ZMQ socket connection to tcp://%s:%s' % (host, port))
                self.my_client_id = None
                self.channel_id = None
                self.channel_port = 0
        def connection_teardown(self):
            try:
                self.socket.close()
            except: 
                pass
            try:
                self.context.term()
            except:
                pass
            try:
                self.context.destroy()
            except: 
                pass

        def send(self, data):
            tries = 0
            sent = False
            while tries < 5 and not sent:
                try:
                    with self.send_lock:
                        self.socket.send_string(data)
                        sent = True
                except Exception as e:
                    self.log.error('Exception in frontend_connector.send(): %s %s' % (type(e), e))
                    tries += 1
            while tries < 5:
                try:
                    with self.send_lock:
                        response = self.socket.recv_string()
                        response = response.split(',')
                        return response
                except Exception as e:
                    self.log.error('Exception in frontend_connector.recv(): %s %s' % (type(e), e))
                    tries += 1

            return None

        def connect(self):
                self.log.debug('Sending connect command')
                self.log.debug('RECVTIMEO: %s SENDTIMEO: %s' % (self.socket.getsockopt(zmq.RCVTIMEO), self.socket.getsockopt(zmq.SNDTIMEO)))
                data = self.send('connect')

                if data == None:
                        return None
                self.my_client_id = int(data[1])
                self.log.debug('Received client ID %s' % self.my_client_id)
        def __exit__(self):
                try:
                        aself.send('quit,%s' % self.my_client_id)
                except:
                        pass

        def set_port(self, port):
                self.log.debug('Setting port to %s' % port)
                self.current_port = port
        def scan_mode_set_freq(self, freq):
                self.log.debug('scan_mode_set_freq(freq = %s)' % freq)
                with self.thread_lock:
                    data = self.send('scan_mode_set_freq,%s' % (freq))

                
                if data == 'success':
                    return True
                else:
                    return False

        def create_channel(self, channel_rate, freq):
                self.last_create_channel = time.time()
                self.frequency = freq
                self.connection_init(freq)
                self.connect()
                self.thread_lock.acquire()
                
                self.log.debug('create_channel(channel_rate = %s, freq = %s)' % (channel_rate, freq))
                data = self.send('create,%s,%s,%s' % (self.my_client_id, channel_rate, freq))

                if data == None or data[0] == 'na': #failed
                        self.thread_lock.release()
                        self.log.error('Failed to create channel')
                        return False, False
                elif data[0] == 'create': #succeeded
                        channel_id = data[1]
                        port = data[2]
                        self.channel_port = port
                        self.channel_id = channel_id

                        self.thread_lock.release()
                        return channel_id, port
                else:
                        self.thread_lock.release()
                        return False, False
                        
        def release_channel(self):
                self.thread_lock.acquire()
                if self.channel_id == None:
                        self.thread_lock.release()
                        return False
                #if we dont have a port set, we can't have a channel.

                self.log.debug('release_channel()')
                data = self.send('release,%s,%s' % (self.my_client_id, self.channel_id))
                
                self.frequency = None

                if data == None or  data[0] == 'na': #failed
                        self.log.error('Failed to release channel, probably leaking channels')
                        self.thread_lock.release()
                        return False
                elif data[0] == 'release': #succeeded
                        channel_id = data[1]

                        self.channel_id = None
                        self.thread_lock.release()
                        return channel_id
                else:
                        self.thread_lock.release()
                        return False
        def report_offset(self, offset):
                self.thread_lock.acquire()
                if self.channel_id == None:
                        self.thread_lock.release()
                        return False #We're not running, cant change offset
                self.log.debug('report_offset(%s)' % offset)
                data = self.send('offset,%s,%s,%s' % (self.my_client_id, self.channel_id, offset))

                if data == None or data[0] == 'na': #failed
                        self.log.error('Failed to set offset')
                        self.thread_lock.release()
                        return False
                elif data[0] == 'offset': #success
                        self.thread_lock.release()
                        return True
        def exit(self):
                self.log.debug('exit() called')
                self.continue_running = False

        def connection_handler(self):
                self.log.debug('connection_handler() init')
                time.sleep(0.1)
                while self.continue_running == True:
                        if self.context == None or self.host == None:
                            #we haven't initialized yet
                            time.sleep(0.01)
                            continue
                        if self.last_create_channel != None and self.frequency == None and time.time()-self.last_create_channel > 120:
                            self.log.warning('Idle frontend connector detected idle time: %s' % (time.time()-self.last_create_channel))
                        self.thread_lock.acquire()
                        self.log.debug('Sending heartbeat')
                        try:
                                data = self.send('hb,%s' % self.my_client_id)

                                if data == None or data[0] == 'fail':
                                        self.log.error('Failed to heartbeat')
                                        self.connection_teardown()
                                        self.connection_init(self.frequency)
                                        self.connect()
                        except Exception as e:
                                self.log.error('Failed to heartbeat: %s' % e)
                        self.thread_lock.release()
                        time.sleep(0.25)
                
                self.thread_lock.acquire()
                self.log.debug('Sending quit command to ZMQ socket')
                self.send('quit,%s' % self.my_client_id)
                self.socket.close()
                self.context.destroy()
                
                self.thread_lock.release()
                self.log.debug('connection_handler() exit')
                        

if __name__ == '__main__':
        test = frontend_connector()
        channel_id = test.create_channel(25000, 855000000)
        if channel_id == False:
                raise Exception('test failed: create')
        if test.release_channel(channel_id) == False:
                raise Exception('test failed: release')

        print('function test pass')

        channels = []
        start = time.time()
        for i in range(0,100):
                channels.append(test.create_channel(25000, 855000000))

        for i in channels:
                test.release_channel(i)
        end = time.time()

        print('speed test %s' % (end-start))
