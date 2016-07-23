from edacs_control_demod import edacs_control_demod
from p25_control_demod import p25_control_demod
from moto_control_demod import moto_control_demod

from p25_call_manager import p25_call_manager
from moto_call_manager import moto_call_manager
from edacs_call_manager import edacs_call_manager

from call_recorder import call_recorder

from config import rc_config
import uuid

overseer_uuid = '%s' % uuid.uuid4()
site_uuid = '9218d5c0-98e5-4592-9859-f18acac2e639'

config = rc_config()                           

demods = {}
for x in config.systems:
	if config.systems[x]['type'] == 'edacs':
		demods[x] = edacs_control_demod(config.systems[x], site_uuid, overseer_uuid)
	elif config.systems[x]['type'] == 'moto':
		demods[x] = moto_control_demod(config.systems[x], site_uuid, overseer_uuid)
	elif config.systems[x]['type'] == 'p25':
		demods[x] = p25_control_demod(config.systems[x], site_uuid, overseer_uuid)
		
	demods[x].start()

import time

#p25_cm = p25_call_manager()
#moto_cm = moto_call_manager()
#edacs_cm = edacs_call_manager()

#call_recorder = call_recorder()
while 1:
	time.sleep(1)
