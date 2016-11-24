#!/usr/bin/env python
from edacs_control_demod import edacs_control_demod
from p25_control_demod import p25_control_demod
from moto_control_demod import moto_control_demod

from config import rc_config
import uuid

import logging
import logging.config
import json

from frontend_connector import frontend_connector

with open('config.logging.json', 'rt') as f:
    config = json.load(f)

logging.config.dictConfig(config)



overseer_uuid = '%s' % uuid.uuid4()
site_uuid = '876c1a54-8183-4134-a41c-67a5b6121fcd'

config = rc_config()                           


types = ['p25_c4fm']

demods = []
for x in range(-20, 20):
    offset = x*6250

    if 'edacs_no_esk' in types:
	    edacs_thread_no_esk = edacs_control_demod({
	        'type': 'edacs',
	        'id': 'edacs_no_esk',
	        'symbol_rate': 9600.0,
	        'esk': False,
	        'channels': { 0:offset} ,
	                                      
	    }, site_uuid, overseer_uuid)
	    edacs_thread_no_esk.start()
	    demods.append(edacs_thread_no_esk)

    if 'edacs_esk' in types:
	    edacs_thread_esk = edacs_control_demod({
	        'type': 'edacs',
	        'id': 'edacs_esk',
	        'symbol_rate': 9600.0,
	        'esk': True,
	        'channels': { 0:offset} ,
	                                      
	    }, site_uuid, overseer_uuid)
	    edacs_thread_esk.start()
	    demods.append(edacs_thread_esk)
    if 'moto' in types:
	    moto_thread = moto_control_demod({
	        'type': 'moto',
	        'id': 'moto',
	        'channels': { 0:offset, 1:offset },
	    }, site_uuid, overseer_uuid)
	    moto_thread.start()
	    demods.append(moto_thread)
	
    if 'p25_cqpsk' in types:
	    p25_thread_cqpsk = p25_control_demod({
	        'type': 'p25',
	        'id': 'cqpsk',
	        'modulation': 'CQPSK',
	        'default_control_channel': 0,
	        'channels': { 0: offset},
	    }, site_uuid, overseer_uuid)
	    p25_thread_cqpsk.start()
	    demods.append(p25_thread_cqpsk)
    if 'p25_c4fm' in types:
	    p25_thread_c4fm = p25_control_demod({
	        'type': 'p25',
	        'id': 'c4fm',
	        'modulation': 'C4FM',
	        'default_control_channel': 0,
	        'channels': { 0: offset},
	    }, site_uuid, overseer_uuid)
	    p25_thread_c4fm.start()
	    demods.append(p25_thread_c4fm)

		
connector = frontend_connector()
with open('scan.output', 'w') as f:
    pass

import time
import itertools
for mhz in itertools.chain(range(768, 775), range(850, 863)):
    for x in (-5, -2.5, 0, 2.5):
        offset = x*100000
        connector.scan_mode_set_freq(int((mhz*1000000)+offset))
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
