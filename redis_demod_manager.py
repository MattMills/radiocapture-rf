#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

import json
import threading
import time
import redis

import logging
import logging.config

class redis_demod_manager():
        def __init__(self, parent_call_manager, host=None, port=None):
                self.log = logging.getLogger('redis_demod_manager')

                if(host != None):
                        self.host = host
                else:
                        self.host = '127.0.0.1' #manually set here until there is a better place
                if(port != None):
                        self.port = port
                else:
                        self.port = 6379 #manually set here until there is a better place


                self.parent_call_manager = parent_call_manager

                self.client = None
                self.continue_running = True
                
                self.demods = {}

                self.init_connection()

                manager_loop = threading.Thread(target=self.manager_loop)
                manager_loop.daemon = True
                manager_loop.start()
        def init_connection(self):
                self.client = redis.StrictRedis(host=self.host, port=self.port, db=0)
        def publish_call_table(self, instance_uuid, call_table):
                pipe = self.client.pipeline()
                pipe.set('call_table:%s' % instance_uuid, json.dumps(call_table))
                pipe.expire('call_table:%s' % instance_uuid, 300)
                result = pipe.execute()
        def get_instance(self, instance_id):
                for demod_type in self.demods:
                        if instance_id in self.demods[demod_type]:
                                return self.demods[demod_type][instance_id]
                return False
        def manager_loop(self):
                self.log.info('manager_loop() startup')
                time.sleep(0.1)
                while self.continue_running:
                        if self.parent_call_manager.demod_type == 'all':
                                demod_types = ['p25', 'edacs', 'moto']
                        else:
                                demod_types = [self.parent_call_manager.demod_type,]
                        

                        for demod_type in demod_types:
                                if demod_type not in self.demods:
                                        self.demods[demod_type] = {}
                                demods = {}
                                try:
                                    instances = self.client.smembers('demod:%s' % demod_type)
                                except Exception as e:
                                    self.log.error('Unable to get demod instances for demod_type: %s Exception: %s' % (demod_type, e))
                                    instances = {}

                                for instance_uuid in instances:
                                        try:
                                                data = self.client.get(instance_uuid)
                                                demods[instance_uuid.decode('utf-8')] = json.loads(data)
                                        except Exception as e:
                                                self.log.error('Error %s while processing instance %s %s' % (e, instance_uuid, demod_type))
                        
                                deletions = []
                                for demod in demods:
                                        if demod not in self.demods[demod_type]:
                                                self.parent_call_manager.notify_demod_new(demod)

                                        timestamp = demods[demod]['timestamp']
                                        if(timestamp < time.time()-5):
                                                self.client.srem('demod:%s' % demod_type, demod)
                                                self.client.delete(demod)
                                                deletions.append(demod)
                                                
                                                self.parent_call_manager.notify_demod_expire(demod)
                                                
                                
                                for deletion in deletions:
                                        del demods[deletion]

                                self.demods[demod_type] = demods

                        time.sleep(5)
                        
