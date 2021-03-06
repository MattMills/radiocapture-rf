#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

import json
import threading
import time
import redis

import logging
import logging.config

class redis_demod_publisher():
        def __init__(self, host=None, port=None, parent_demod=None):
                self.log = logging.getLogger('redis_demod_publisher')

                if(host != None):
                        self.host = host
                else:
                        self.host = '127.0.0.1' #manually set here until there is a better place
                if(port != None):
                        self.port = port
                else:
                        self.port = 6379 #manually set here until there is a better place

                if(parent_demod == None):
                        raise Exception('parent_demod cannot be null')

                self.parent_demod = parent_demod

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
                while self.continue_running:
                        system_type = self.parent_demod.system['type']
                        try:
                                system_uuid = self.parent_demod.system['system_uuid']
                        except:
                                system_uuid = 'unknown'
                        try:
                                transmit_site_uuid = self.parent_demod.system['transmit_site_uuid']
                        except:
                                transmit_site_uuid = 'unknown'

                        publish_data = {
                                'instance_uuid': self.parent_demod.instance_uuid,
                                'site_uuid': self.parent_demod.site_uuid,
                                'system_uuid': system_uuid,
                                'transmit_site_uuid': transmit_site_uuid,
                                'overseer_uuid': self.parent_demod.overseer_uuid,
                                'site_detail': self.parent_demod.site_detail,
                                'site_status': self.parent_demod.quality,
                                'auto_capture': True,
                                'frequency': self.parent_demod.control_channel,
                                'timestamp': time.time(),
                        }
                        
                        try:
                                publish_data['system_modulation'] = self.parent_demod.modulation
                        except:
                                pass

                        
                        pipe = self.client.pipeline()
                        pipe.sadd('demod:%s' % system_type, self.parent_demod.instance_uuid)
                        pipe.set(self.parent_demod.instance_uuid, json.dumps(publish_data))
                        try:
                                result = pipe.execute()
                        except Exception as e:
                            self.log.error('Exception submitting redis demod publish: %s' % e)
                        time.sleep(1)
                        
