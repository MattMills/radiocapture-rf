#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com


from stompest.config import StompConfig
from stompest.sync import Stomp
from stompest.protocol import StompSpec

import json
import threading
import time
import uuid
import sys
import signal
import math
import logging

from redis_demod_manager import redis_demod_manager
from client_redis import client_redis

class moto_call_manager():
        def __init__(self):
                self.log = logging.getLogger('overseer.moto_call_manager')
                self.log.info('Initializing moto_call_manager')
                self.demod_type = 'moto'

                self.redis_demod_manager = redis_demod_manager(self)

                self.instance_locks = {}
                self.amq_clients = {}

                self.continue_running = True

                self.hang_time = 1.0
                self.instance_metadata = {}
                self.system_metadata = {}
                
                periodic_timeout_thread = threading.Thread(target=self.periodic_timeout_thread)
                periodic_timeout_thread.daemon = True
                periodic_timeout_thread.start()

        def notify_demod_new(self, demod_instance_uuid):
                self.log.info('Notified of new demod %s' % (demod_instance_uuid))
                self.amq_clients[demod_instance_uuid] = client_redis(4)
                self.amq_clients[demod_instance_uuid].subscribe('/topic/raw_control/%s' % (demod_instance_uuid), self, self.process_raw_control.__func__, False)
                self.instance_locks[demod_instance_uuid] = threading.RLock()

        def notify_demod_expire(self, demod_instance_uuid):
                self.log.info('Notified of expired demod %s' % (demod_instance_uuid))
                if demod_instance_uuid in self.amq_clients:
                        self.amq_clients[demod_instance_uuid].unsubscribe('/topic/raw_control/%s' % (demod_instance_uuid))

        def get_system_from_instance(self, instance_uuid):
                try:
                        return self.redis_demod_manager.get_instance(instance_uuid)['system_uuid']
                except:
                        return False

        def call_user_to_group(self, instance_uuid, frequency, group_address, user_address=0, digital=False):
                with self.instance_locks[instance_uuid]:
                        system_uuid = self.get_system_from_instance(instance_uuid)
                        if system_uuid == False:
                                return False
        
                        sct = self.system_metadata[system_uuid]['call_table']
                        ict = self.instance_metadata[instance_uuid]['call_table']
                        call_uuid = None
                        for call in ict:
                                if ict[call]['system_channel_local'] == frequency and ict[call]['system_group_local'] == group_address and (user_address == 0 or ict[call]['system_user_local'] == user_address):
                                        ict[call]['time_activity'] = time.time()
                                        return True
                                                
                                
                        #Not a continuation, new call
                        for call in sct:
                                if sct[call]['system_group_local'] == group_address and (user_address == 0 or sct[call]['system_user_local'] == user_address) and time.time() - sct[call]['time_open'] < 1:
                                        call_uuid = sct[call]['call_uuid']
                                        break
        
                        if call_uuid == None:
                                #call is new systemwide, assign new UUID
                                call_uuid = '%s' % uuid.uuid4()
                        instance = self.redis_demod_manager.get_instance(instance_uuid)
                        cdr = {
                                'call_uuid': call_uuid,
                                'system_id': system_uuid,
                                'transmit_site_uuid': instance['transmit_site_uuid'],
                                'instance_uuid': instance_uuid,
                                'system_group_local': group_address,
                                'system_user_local': user_address,
                                'system_channel_local': frequency,
                                'type': 'group',
                                'frequency': frequency,
                                'channel_bandwidth': 12500,
                                'modulation_type': '%s' % ('p25' if digital == True else 'analog'),
                                'hang_time': self.hang_time,
                                'time_open': time.time(),
                                'time_activity': time.time(),
                                }
        
                        ict[call_uuid] = cdr
                        if call_uuid not in sct:
                                sct[call_uuid] = cdr
                                sct[call_uuid]['instances'] = {instance_uuid: True}
                        else:
                                sct[call_uuid]['instances'][instance_uuid] = True
                                
                        
        
                        #event call open to record subsys
                        self.amq_clients[instance_uuid].send_event_lazy('/topic/call_management/new_call/%s' % instance_uuid, cdr)
                        self.redis_demod_manager.publish_call_table(instance_uuid, ict)
                        self.log.info('OPEN: %s %s %s %s' % (cdr['instance_uuid'], cdr['call_uuid'], cdr['system_group_local'], cdr['system_user_local']) )
        
        def periodic_timeout_thread(self):
                self.log.info('periodic_timeout_thread()')
                while self.continue_running:
                        time.sleep(0.1)
                        for instance in list(self.instance_metadata):
                                with self.instance_locks[instance]:
                                        ict = self.instance_metadata[instance]['call_table']
                                        system_uuid = self.get_system_from_instance(instance)
                                        if system_uuid == False:
                                                continue
                                        sct = self.system_metadata[system_uuid]['call_table']

                                        closed_calls = []
                                        for call_uuid in ict:
                                                if time.time()-ict[call_uuid]['time_activity'] > ict[call_uuid]['hang_time']:
                                                        closed_calls.append(call_uuid)
                                                        #event call close to record subsys on call specific queue
                                                        self.amq_clients[instance].send_event_lazy('/topic/call_management/timeout/%s' % instance, {'call_uuid': call_uuid, 'instance_uuid': instance})                                                

                                                        self.log.info('%s CLOSE: %s' % (time.time(), ict[call_uuid]))
                                        for call_uuid in closed_calls:
                                                del ict[call_uuid]
                                                del sct[call_uuid]['instances'][instance]
                                                if len(sct[call_uuid]['instances']) == 0:
                                                        del sct[call_uuid]
                                        if len(closed_calls) > 0:
                                                self.redis_demod_manager.publish_call_table(instance, ict)
                                        


        def process_raw_control(self, t, headers):
                instance_uuid = headers['destination'].replace('/topic/raw_control/', '')
                instance = self.redis_demod_manager.get_instance(instance_uuid)
                system_uuid = self.get_system_from_instance(instance_uuid)

                if instance_uuid not in self.instance_metadata:
                        self.instance_metadata[instance_uuid] = {'channel_identifier_table': {}, 'patches': {}, 'call_table': {}}

                if system_uuid not in self.system_metadata:
                        self.system_metadata[system_uuid] = {'call_table': {}}

                #if 'crc' in t and t['crc'] != 0:
                #        continue #Don't bother trying to work with bad data
                with self.instance_locks[instance_uuid]:
                        if t['type'] == 'IDEN_UP_VU' and t['crc'] == 0:
                                try:
                                       self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                        'BW': t['BW VU'],
                                        'Base Frequency': t['Base Frequency'],
                                        'Channel Spacing': t['Channel Spacing'],
                                        'Transmit Offset': t['Transmit Offset VU'],
                                        'Type': 'FDMA',
                                        'Slots': 1,
                                        }
                                except:
                                        pass
                        elif t['type'] == 'IDEN_UP' and t['crc'] == 0:
                                try:
                                       self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                        'BW': t['BW'],
                                        'Base Frequency': t['Base Frequency'],
                                        'Channel Spacing': t['Channel Spacing'],
                                        'Transmit Offset': t['Transmit Offset'],
                                        'Type': 'FDMA',
                                        'Slots': 1,
                                        }
                                except:
                                        pass
                        elif t['type'] == 'IDEN_UP_TDMA' and t['crc'] == 0:
                                try:
                                        self.instance_metadata[instance_uuid]['channel_identifier_table'][t['Identifier']] = {
                                        'BW': t['BW'],
                                        'Base Frequency': t['Base Frequency'],
                                        'Channel Spacing': t['Channel Spacing'],
                                        'Transmit Offset': t['Transmit Offset TDMA'],
                                        'Type': t['Access Type'],
                                        'Slots': t['Slots'],
                                        }
                                except:
                                        pass
                        elif t['type'] == 'Analog Call' :
                                #{u'lid': u'0x510', u'status': 0, u'cmd': u'0x18c', u'sys': 15143, u'frequency': 860912500, u'system_type': u'moto', u'dual': True, u'ind': u'I', u'tg': 1296, u'type': u'Analog Call', u'user_local': 20974}
                                #{u'lid': u'0x5f0', u'status': 0, u'cmd': u'0x188', u'sys': 15143, u'frequency': 860812500, u'system_type': u'moto', u'dual': False, u'ind': u'I', u'tg': 1520, u'type': u'Call Continuation', u'user_local': 0}
                                self.log.debug('ANALOG CALL %s %s %s %s' % (instance_uuid, t['frequency'], t['tg'], t['user_local']))
                                self.call_user_to_group(instance_uuid, t['frequency'], t['tg'], t['user_local'])
                        elif t['type'] == 'Digital Call':
                                self.log.debug('DIGITAL CALL %s %s %s %s' % (instance_uuid, t['frequency'], t['tg'], t['user_local']))
                                self.call_user_to_group(instance_uuid, t['frequency'], t['tg'], t['user_local'], digital=True)
                        elif t['type'] == 'Call Continuation':
                                self.log.debug('Call Continuation %s %s %s %s' % (instance_uuid, t['frequency'], t['tg'], t['user_local']))
                                self.call_user_to_group(instance_uuid, t['frequency'], t['tg'], t['user_local'])

if __name__ == '__main__':

        main = moto_call_manager()
        while True:
                time.sleep(1)
