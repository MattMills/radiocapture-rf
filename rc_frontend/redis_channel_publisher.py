#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

import json
import threading
import time
import redis
import uuid
import os

import logging
import logging.config
import zmq
import socket

from urllib.parse import urlparse


class redis_channel_publisher():
        def __init__(self, host=None, port=None, sources=None, channels=None, zmq_socket=None):
                self.log = logging.getLogger('redis_channel_publisher')

                if(host != None):
                        self.host = host
                else:
                        self.host = '127.0.0.1' #manually set here until there is a better place
                if(port != None):
                        self.port = port
                else:
                        self.port = 6379 #manually set here until there is a better place

                if sources == None:
                    raise Exception('Sources must be provided at initialization')
                if channels == None: 
                    raise Exception('Channels must be provided at initialization')
                if zmq_socket == None:
                    raise Exception('ZMQ Socket must be provided at initialization')

                self.start_time = time.time()

                self.sources = sources
                self.channels = channels
                self.zmq_socket = zmq_socket
                self.instance_uuid = str(uuid.uuid4())

                self.client = None
                self.continue_running = True

                self.init_connection()

                publish_loop = threading.Thread(target=self.publish_loop)
                publish_loop.daemon = True
                publish_loop.start()
        def init_connection(self):
                self.client = redis.StrictRedis(host=self.host, port=self.port, db=0)

        def publish_loop(self):
                self.log.info('publish_loop() startup')
                time.sleep(0.5)
                while self.continue_running:
                        publish_data = {
                                'instance_uuid': self.instance_uuid,
                                'start_time': self.start_time,
                                'current_time': time.time(),
                                'hostname': socket.gethostname(),
                                'pid': os.getpid(),
                                'address': socket.gethostbyname(socket.gethostname()),
                                'port': urlparse(self.zmq_socket.getsockopt(zmq.LAST_ENDPOINT).decode('utf-8')).port,
                                'channel_count': len(self.channels),
                                'source_count': len(self.sources),
                                'sources': [],
                                }



                        for source_id in self.sources:
                            source = self.sources[source_id]

                            publish_data['sources'].append((source['center_freq'], source['samp_rate']))

                        pipe = self.client.pipeline()
                        pipe.sadd('channelizers', self.instance_uuid)
                        pipe.set(self.instance_uuid, json.dumps(publish_data))
                        #expire handled in manager
                        #pipe.expire(self.instance_uuid, 60)
                        try:
                                result = pipe.execute()
                        except Exception as e:
                            self.log.error('Exception submitting redis demod publish: %s' % e)
                        time.sleep(1)
                        
