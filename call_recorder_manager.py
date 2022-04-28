#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

import json
import threading
import time
import sys
import math
import logging
import logging.config
import multiprocessing
import os
import setproctitle

from redis_demod_manager import redis_demod_manager

from call_recorder import call_recorder

class call_recorder_manager():
        def __init__(self):
                self.log = logging.getLogger('overseer.call_recorder_manager')
                self.log.debug('Initializing call_recorder_manager')

                self.demod_type = 'all'
                setproctitle.setproctitle('%s - %s_call_recorder_manager' % (setproctitle.getproctitle(),  self.demod_type))
                self.redis_demod_manager = redis_demod_manager(self)

                self.call_recorders = {}
        def notify_demod_new(self, demod_instance_uuid):
                self.log.info('Notified of new demod %s' % (demod_instance_uuid))
                if demod_instance_uuid not in self.call_recorders:
                        keep_running = multiprocessing.Value('b')
                        keep_running.value = True
                        cr = multiprocessing.Process(target=self.worker, args=(call_recorder,demod_instance_uuid, keep_running ))
                        cr.start()
                        self.call_recorders[demod_instance_uuid] = {'object': cr, 'keep_running': keep_running }
                else:
                    self.log.warning('Received duplicate notification of new demod %s' % (demod_instance_uuid))
        def notify_demod_expire(self, demod_instance_uuid):
                self.log.info('Notified of expired demod %s' % (demod_instance_uuid))
                if demod_instance_uuid in self.call_recorders:
                        self.call_recorders[demod_instance_uuid]['keep_running'].value = False
                        self.call_recorders[demod_instance_uuid]['object'].join()
                        self.call_recorders[demod_instance_uuid]['object'].close()

                        del self.call_recorders[demod_instance_uuid]
                else:
                    self.log.warning('Received notification of expired demod %s but demod not in call recorder table' % (demod_instance_uuid, ))
        def worker(self, func, *args, **kwargs):
                self.log.info('THREADSTATE worker spawn: %s %s' % (os.getpid(), threading.get_native_id()))
                new_process = func(*args, **kwargs)
                try:
                    while(new_process.keep_running.value == True):
                        time.sleep(0.001)
                finally:
                    new_process.keep_running.value = False
                    new_process.shutdown()
                    self.log.fatal('call_recorder EXIT args (%s) pid %s' % (args, os.getpid()))
                    self.log.info('THREADSTATE worker EXIT: %s %s' % (os.getpid(), threading.get_native_id()))
                    return

if __name__ == '__main__':
        with open('config.logging.json', 'rt') as f:
            config = json.load(f)

        logging.config.dictConfig(config)

        main = call_recorder_manager()
        while True:
                time.sleep(1)
