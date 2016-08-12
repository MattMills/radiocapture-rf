#!/usr/bin/env python
from edacs_control_demod import edacs_control_demod
from p25_control_demod import p25_control_demod
from moto_control_demod import moto_control_demod

from config import rc_config
import uuid


from frontend_connector import frontend_connector


overseer_uuid = '%s' % uuid.uuid4()
site_uuid = '876c1a54-8183-4134-a41c-67a5b6121fcd'

config = rc_config()                           

demods = []
for x in range(-40, 40):
    offset = x*12500

#    edacs_thread_no_esk = edacs_control_demod({
#        'type': 'edacs',
#        'id': 'edacs_no_esk',
#        'symbol_rate': 9600.0,
#        'esk': False,
#        'channels': { 0:offset, 1:offset} ,
#                                      
#    }, site_uuid, overseer_uuid)
#
#    edacs_thread_esk = edacs_control_demod({
#        'type': 'edacs',
#        'id': 'edacs_esk',
#        'symbol_rate': 9600.0,
#        'esk': True,
#        'channels': { 0:offset, 1:offset} ,
#                                      
#    }, site_uuid, overseer_uuid)
#
#
#    moto_thread = moto_control_demod({
#        'type': 'moto',
#        'id': 'moto',
#        'channels': { 0:offset, 1:offset },
#    }, site_uuid, overseer_uuid)
#
#
#    p25_thread_cqpsk = p25_control_demod({
#        'type': 'p25',
#        'id': 'cqpsk',
#        'modulation': 'CQPSK',
#        'default_control_channel': 0,
#        'channels': { 0: offset, 1:offset },
#    }, site_uuid, overseer_uuid)

    p25_thread_c4fm = p25_control_demod({
        'type': 'p25',
        'id': 'c4fm',
        'modulation': 'C4FM',
        'default_control_channel': 0,
        'channels': { 0: offset, 1: offset },
    }, site_uuid, overseer_uuid)



    #edacs_thread_no_esk.start()
    #edacs_thread_esk.start()
    #moto_thread.start()
    #p25_thread_cqpsk.start()
    p25_thread_c4fm.start()

    #demods.append(edacs_thread)
    #demods.append(edacs_thread_no_esk)
    #demods.append(moto_thread)
    #demods.append(p25_thread_cqpsk)
    demods.append(p25_thread_c4fm)

		
connector = frontend_connector()
with open('scan.output', 'w') as f:
    pass

import time
for mhz in range(850, 863):
    for x in (-5, -2.5, 0, 2.5, 5):
        offset = x*1000 
        connector.scan_mode_set_freq((mhz*1000000)+offset)
	time.sleep(5)
        for thread in demods:
            if thread.is_locked == True:
                    if thread.system['type'] == 'p25':
                        detail = sid = '%s %s-%s %s-%s' % (thread.site_detail['Control Channel'], thread.site_detail['System ID'], thread.site_detail['WACN ID'], thread.site_detail['RF Sub-system ID'], thread.site_detail['Site ID'])
                    else:
                        detail = thread.site_detail

                    with open('scan.output', 'a') as f:           
                        f.write('%s: System locked: Type: %s, detail: %s\n' % (((mhz*1000000)+offset+thread.control_channel), thread.system['type'], detail))
    print 'Scan complete: %s Mhz' % mhz