#!/usr/bin/env python

from edacs_control_demod import edacs_control_demod
from p25_control_demod import p25_control_demod
from moto_control_demod import moto_control_demod

from p25_call_manager import p25_call_manager
from moto_call_manager import moto_call_manager
from edacs_call_manager import edacs_call_manager

from call_recorder import call_recorder

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

def tb_worker(func, *args, **kwargs):
	#multiprocessing.Process(target=tb_worker, args=())
	new_process = func(*args, **kwargs)
	#new_process.run()

def worker(func, *args, **kwargs):
	#multiprocessing.Process(target=worker, args=())
	new_process = func(*args, **kwargs)
	while(True):
		time.sleep(3600)
def excepthook(exctype, value, traceback):
    for p in multiprocessing.active_children():
    	p.terminate()
    raise

sys.excepthook = excepthook


with open('config.logging.json', 'rt') as f:
    config = json.load(f)

logging.config.dictConfig(config)


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
		demods[x] = multiprocessing.Process(target=tb_worker, args=(edacs_control_demod, config.systems[x], site_uuid, overseer_uuid))
	elif config.systems[x]['type'] == 'moto':
		demods[x] = multiprocessing.Process(target=tb_worker, args=(moto_control_demod, config.systems[x], site_uuid, overseer_uuid))
	elif config.systems[x]['type'] == 'p25':
		demods[x] = multiprocessing.Process(target=tb_worker, args=(p25_control_demod, config.systems[x], site_uuid, overseer_uuid))
		
	demods[x].start()

import time

logger.info('Initializing call managers')
p25_cm = multiprocessing.Process(target=worker, args=(p25_call_manager,))
p25_cm.start()
moto_cm = multiprocessing.Process(target=worker, args=(moto_call_manager,))
moto_cm.start()
edacs_cm = multiprocessing.Process(target=worker, args=(edacs_call_manager,))
edacs_cm.start()

#p25_md_agent = multiprocessing.Process(target=worker, args=(p25_metadata_agent,))
#p25_md_agent.start()

logger.info('Initializing call recorder')

#call_recorder = multiprocessing.Process(target=worker, args=(call_recorder,))
#call_recorder.start()

logger.info('Overseer %s initialization complete' % overseer_uuid)
while 1:
	time.sleep(1)
