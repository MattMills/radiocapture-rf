#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

import json
import threading
import time
import redis

import logging
import logging.config

import random

try:
    from config import rc_config
except:
    pass

class redis_channelizer_manager():
        def __init__(self, index=None):
                self.log = logging.getLogger('redis_channelizer_manager')

                self.clients = []
                self.continue_running = True
                self.index=index

                self.channelizers = {}

                self.init_connection()

                manager_loop = threading.Thread(target=self.manager_loop)
                manager_loop.daemon = True
                manager_loop.start()
        def init_connection(self):
            try:
                rc_config().redis_servers
            except Exception as e:
                self.log.error('Exception loading redis config: (%s) %s' % (type(e), e))
                self.log.error('No redis servers defined in config, failing back to localhost config')
                self.clients.append(redis.StrictRedis(host='127.0.0.1', port='6379', db=0))
                return

            for server in rc_config().redis_servers:
                self.log.info('New Redis connection: %s:%s' % server)
                self.clients.append(redis.StrictRedis(host=server[0], port=server[1], db=0))

        def get_instance(self, instance_id):
            if instance_id in self.channelizers:
                return self.channelizers[instance_id]
            return False
        def get_channelizer_for_frequency(self, frequency):
            if self.clients == []:
                time.sleep(0.1)
            self.log.info('get_channelizer_for_frequency(%s)' % frequency)
            options = {}

            smallest_offset = None

            for channelizer in self.channelizers:
                for source in self.channelizers[channelizer]['sources']:
                    if abs(source[0]-frequency) < source[1]/2:
                        if smallest_offset == None or (abs(source[0]-frequency) < smallest_offset):
                            smallest_offset = abs(source[0]-frequency)
                        if abs(source[0]-frequency) not in options:
                            options[abs(source[0]-frequency)] = []
                        options[abs(source[0]-frequency)].append(channelizer)

            #fixme: get operational status of each option, if one is drainstop (or pre-start) eliminate, else randomly pick between options
            self.log.info('channelizer result: %s' % options)
            try:
                channelizer = random.choice(options[smallest_offset])
                return (self.channelizers[channelizer]['address'], self.channelizers[channelizer]['port'])
            except Exception as e:
                self.log.error("Exception in rcm.get_channelizer_for_frequency(%s): %s" % (frequency, e))
                return (None, None)

        def manager_loop(self):
                self.log.info('manager_loop() startup')
                while self.continue_running:
                    for client in self.clients:
                        try:
                            instances = client.smembers('channelizers')
                        except Exception as e:
                            self.log.error('Unable to get channelizer instances Exception: (%s) %s' % (type(e), e))
                            instances = {}

                        channelizers = {}
                        for instance_uuid in instances:
                                try:
                                        data = client.get(instance_uuid)
                                        if data != None:
                                            channelizer = json.loads(data)
                                        if self.index == None or int(channelizer['index']) == self.index:
                                            channelizers[instance_uuid.decode('utf-8')] = channelizer
                                except Exception as e:
                                        self.log.error('Exception (%s) %s while loading channelizer instance %s from redis' % (type(e), e, instance_uuid))
                
                        deletions = []
                        for channelizer in channelizers:
                                if channelizer not in self.channelizers:
                                        #self.parent_frontend_connector.notify_channelizer_new(channelizer)
                                        #fixme: do something else with this data, we need to aggregate all channelizer data here
                                        pass

                                timestamp = channelizers[channelizer]['current_time']
                                if(timestamp < time.time()-5):
                                        client.srem('channelizers', channelizer)
                                        client.delete(channelizer)
                                        deletions.append(channelizer)
                                        
                                        #self.parent_frontend_connector.notify_channelizer_expire(channelizer)
                                        #fixme same as above
                                        
                        
                        for deletion in deletions:
                            try:
                                del channelizer[deletion]
                            except:
                                pass

                        self.channelizers = channelizers

                    time.sleep(0.5)
                    
