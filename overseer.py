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

with open('config.logging.json', 'rt') as f:
    config = json.load(f)

logging.config.dictConfig(config)


logger = logging.getLogger('overseer')

overseer_uuid = '%s' % uuid.uuid4()
site_uuid = '9218d5c0-98e5-4592-9859-f18acac2e639'

logger.info('Overseer %s initializing' % (overseer_uuid))
logger.info('Site UUID: %s' % site_uuid)
config = rc_config()       

demods = {}
for x in config.systems:
        logger.info('Initializing %s demodulator. System configuration: %s' % (config.systems[x]['type'], config.systems[x]))
	if config.systems[x]['type'] == 'edacs':
		demods[x] = edacs_control_demod(config.systems[x], site_uuid, overseer_uuid)
	elif config.systems[x]['type'] == 'moto':
		demods[x] = moto_control_demod(config.systems[x], site_uuid, overseer_uuid)
	elif config.systems[x]['type'] == 'p25':
		demods[x] = p25_control_demod(config.systems[x], site_uuid, overseer_uuid)
		
	demods[x].start()

import time

logger.info('Initializing call managers')
p25_cm = p25_call_manager()
#moto_cm = moto_call_manager()
#edacs_cm = edacs_call_manager()

p25_md_agent = p25_metadata_agent()

logger.info('Initializing call recorder')

call_recorder = call_recorder()

logger.info('Overseer %s initialization complete' % overseer_uuid)
while 1:
	time.sleep(1)
