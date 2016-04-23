#!/usr/bin/env python


from stompest.config import StompConfig
from stompest.sync import Stomp
from stompest.protocol import StompSpec

import json
import threading
import time
import stompy

class p25_call_manager():
        def __init__(self, host=None, port=None):
		self.demod_type = 'p25'

		self.redis_demod_manager = redis_demod_manager(self)


                if(host != None):
                        self.host = host
                else:
                        self.host = '127.0.0.1' #manually set here until there is a better place
                if(port != None):
                        self.port = port
                else:
                        self.port = 61613 #manually set here until there is a better place

                self.client = None
                self.connection_issue = True

                connection_handler = threading.Thread(target=self.connection_handler)
                connection_handler.daemon = True
                connection_handler.start()

        def init_connection(self):
                if(self.client != None and self.client.session.state == 'connected'):
                        try:
                                self.client.disconnect()
                        except:
                                pass

                config = StompConfig('tcp://%s:%s' % (self.host, self.port), version=StompSpec.VERSION_1_1, check=True)
                self.client = Stomp(config)
                self.client.connect(heartBeats=(30000, 0), connectTimeout=1, connectedTimeout=1)

        def connection_handler(self):
                #This func will just try to reconnect repeatedly in a thread if we're flagged as having an issue.
                while(True):
                        if(self.connection_issue == True):
                                try:
                                        self.init_connection()
                                        self.connection_issue = False
                                except:
                                        pass
                        time.sleep(1)

        def send_event_lazy(self, destination, body):
                #If it gets there, then great, if not, well we tried!
                if(self.connection_issue == True):
                        return None

                try:
                        self.client.send(destination, json.dumps(body))
                except:
                        self.connection_issue = True

	def publish_loop(self):
		print 'publish_loop()'
		while self.continue_running:

			publish_data = {
				'instance_uuid': self.parent_demod.instance_uuid,
				'site_uuid': self.parent_demod.site_uuid,
				'overseer_uuid': self.parent_demod.overseer_uuid,
				'site_detail': self.parent_demod.site_detail,
				'site_status': self.parent_demod.quality,
				'auto_capture': True,
				'frequency': self.parent_demod.control_channel,
				'timestamp': time.time(),
			}

			
			
			time.sleep(1)
