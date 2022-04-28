#!/usr/bin/env python3

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

from edacs_control_demod import edacs_control_demod
from p25_control_demod import p25_control_demod
from moto_control_demod import moto_control_demod

from p25_call_manager import p25_call_manager
from moto_call_manager import moto_call_manager
from edacs_call_manager import edacs_call_manager

from call_recorder_manager import call_recorder_manager

from p25_metadata_agent import p25_metadata_agent

from config import rc_config
import uuid
import logging
import logging.config
import json
import multiprocessing
import sys
import os
import time
import manhole

def tb_worker(func, *args, **kwargs):
        #multiprocessing.Process(target=tb_worker, args=())
        new_process = func(*args, **kwargs)
        new_process.start()
        manhole.install(locals=locals())
        while(new_process.keep_running):
                time.sleep(1)

def worker(func, *args, **kwargs):
        #multiprocessing.Process(target=worker, args=())
        new_process = func(*args, **kwargs)
        manhole.install(locals=locals())
        while(True):
                time.sleep(1)
def excepthook(exctype, value, traceback):
    for p in multiprocessing.active_children():
            p.terminate()
    raise

sys.excepthook = excepthook


with open('config.logging.json', 'rt') as f:
    config = json.load(f)

logging.config.dictConfig(config)

import multiprocessing_logging
multiprocessing_logging.install_mp_handler()
multiprocessing_logging.install_mp_handler(logging.getLogger('overseer.quality'))
multiprocessing_logging.install_mp_handler(logging.getLogger('protocol'))

logger = logging.getLogger('overseer')

config = rc_config()       
overseer_uuid = '%s' % uuid.uuid4()
site_uuid = config.site_uuid


logger.info('Overseer %s initializing' % (overseer_uuid))
logger.info('Site UUID: %s' % site_uuid)


demods = {}
for x in config.systems:
        logger.info('Initializing %s demodulator. System configuration: %s' % (config.systems[x]['type'], config.systems[x]))
        if config.systems[x]['type'] == 'edacs':
                demods[x] = multiprocessing.Process(name='demod_edacs_%s' % (x, ), target=tb_worker, args=(edacs_control_demod, config.systems[x], site_uuid, overseer_uuid))
        elif config.systems[x]['type'] == 'moto':
                demods[x] = multiprocessing.Process(name='demod_moto_%s' % (x, ), target=tb_worker, args=(moto_control_demod, config.systems[x], site_uuid, overseer_uuid))
        elif config.systems[x]['type'] == 'p25':
                demods[x] = multiprocessing.Process(name='demod_p25_%s' % (x, ), target=tb_worker, args=(p25_control_demod, config.systems[x], site_uuid, overseer_uuid))
                
        demods[x].start()
        logger.info('demodulator %s pid: %s' % (x, demods[x].pid))

import time

logger.info('Initializing call managers')
p25_cm = multiprocessing.Process(name='p25_cm', target=worker, args=(p25_call_manager,))
p25_cm.start()
logger.info('p25_cm pid  %s' % p25_cm.pid)
moto_cm = multiprocessing.Process(name='moto_cm', target=worker, args=(moto_call_manager,))
moto_cm.start()
logger.info('moto_cm pid  %s' % moto_cm.pid)
edacs_cm = multiprocessing.Process(name='edacs_cm', target=worker, args=(edacs_call_manager,))
edacs_cm.start()
logger.info('edacs_cm pid  %s' % edacs_cm.pid)

#p25_md_agent = multiprocessing.Process(target=worker, args=(p25_metadata_agent,))
#p25_md_agent.start()

logger.info('Initializing call recorder manager')


call_recorder = multiprocessing.Process(name='call_recorder', target=worker, args=(call_recorder_manager,))
call_recorder.start()
logger.info('call_recorder pid  %s' % call_recorder.pid)

logger.info('Overseer %s initialization complete' % overseer_uuid)
while 1:
        for demod in demods.keys():
            logger.info('Overseer thread status (demod, %s %s): is_alive(%s)' % (demod, demods[demod].pid, demods[demod].is_alive()))
        logger.info('Overseer thread status (p25_cm, %s): is_alive(%s)' % (p25_cm.is_alive(),p25_cm.pid))
        logger.info('Overseer thread status (moto_cm, %s): is_alive(%s)' % (moto_cm.is_alive(), moto_cm.pid))
        logger.info('Overseer thread status (edacs_cm, %s): is_alive(%s)' % (edacs_cm.is_alive(), edacs_cm.pid))
        logger.info('Overseer thread status (call_recorder_manager, %s): is_alive(%s)' % (call_recorder.is_alive(), call_recorder.pid))

        time.sleep(5)
