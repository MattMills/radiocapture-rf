#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

import json
import threading
import time
import uuid
import sys
import signal
import math
import logging
import traceback
import redis
import queue as Queue

class client_redis():
        def __init__(self, worker_threads=2):
                self.log = logging.getLogger('client_redis')
                self.log.debug('Initializing client_redis')

                self.host = '127.0.0.1' #manually set here until there is a better place
                self.port = 6379 #manually set here until there is a better place
                self.worker_threads = worker_threads

                self.redis = None
                self.pubsub = None

                self.connection_issue = True
                self.continue_running = True
                self.subscriptions = {}
                self.outbound_msg_queue = []
                self.outbound_msg_queue_lazy = []


                self.threads = []
                self.work_queue = Queue.Queue()

                connection_handler = threading.Thread(target=self.connection_handler)
                connection_handler.daemon = True
                connection_handler.start()
        
                send_event_hopeful_thread = threading.Thread(target=self.send_event_hopeful_thread)
                send_event_hopeful_thread.daemon = True
                send_event_hopeful_thread.start()
        
                send_event_lazy_thread = threading.Thread(target=self.send_event_lazy_thread)
                send_event_lazy_thread.daemon = True
                send_event_lazy_thread.start()


                publish_loop = threading.Thread(target=self.publish_loop)
                publish_loop.daemon = True
                publish_loop.start()




        def init_connection(self):
                self.redis = redis.Redis(host=self.host, port=self.port, db=0)
                self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
                self.pubsub.subscribe('default_channel')
        def build_worker_pool(self, capacity):
                for thread in self.threads:
                        if thread.is_alive() == False:
                                self.threads.remove(thread)

                while len(self.threads) < capacity:
                        t = threading.Thread(target=self.worker, args=(self.work_queue,))
                        t.daemon = True
                        t.start()
                        self.threads.append(t)
        def connection_handler(self):
                #This func will just try to reconnect repeatedly in a thread if we're flagged as having an issue.
                while(True):
                        if(self.connection_issue == True):
                                try:
                                        self.init_connection()
                                        self.connection_issue = False
                                        time.sleep(0.1)
                                        for subscription in self.subscriptions:
                                                self.log.info('Re-subscribing upon reconnection: %s' % subscription)
                                                self.subscribe(subscription, self.subscriptions[subscription]['callback_class'], self.subscriptions[subscription]['callback'], True)
                                                
                                except Exception as e:
                                        self.log.critical('Except: %s' % e)
                        self.build_worker_pool(self.worker_threads)
                        time.sleep(10)
        def subscribe(self, queue, callback_class, callback, resub=False):
                #This needs to exist so we can keep track of what subs we have and re-sub on reconnect
                if queue in self.subscriptions and not resub:
                        self.log.info('Ignoring existing subscription %s' % queue)
                        return True #we're already subscribed

                this_uuid = '%s' % uuid.uuid4()
                if(self.connection_issue == True):
                        self.log.info('Cannot process subscription request as were not properly connected')
                        self.subscriptions[queue] = {'uuid': this_uuid, 'callback': callback, 'callback_class': callback_class}
                        return None
                self.log.info('subscribe(%s %s %s %s)' %( queue, callback_class, callback, resub))
        
                try:
                        self.subscriptions[queue] = {'uuid': this_uuid, 'callback': callback, 'callback_class': callback_class}
                        self.pubsub.subscribe(queue)
                except Exception as e:
                        self.log.fatal('%s' % e)
                        self.connection_issue = True

        def unsubscribe(self, queue):
                if queue not in self.subscriptions:
                        return False #cant unsubscribe, we're not subscribed


                if(self.connection_issue == True):
                        del self.subscriptions[queue]
                        return None
                try:
                        self.pubsub.unsubscribe(queue)
                        del self.subscriptions[queue]
                except Exception as e:
                        self.log.error('%s' % e)
                        self.log.error('%s' % traceback.format_exc())
                        sys.exc_clear()
                        self.connection_issue = True
        def send_event_lazy(self, destination, body, headers = {}, persistent = False):
                headers['time_queued'] = time.time()
                self.outbound_msg_queue_lazy.append({'destination': destination, 'body': body, 'headers': headers, 'persistent': persistent})

        def send_event_lazy_thread(self):
                while self.continue_running:
                        time.sleep(0.010)
                        #If it gets there, then great, if not, well we tried!
                        if(self.connection_issue == True):
                                continue
                        while len(self.outbound_msg_queue_lazy) > 0 and self.connection_issue == False:
                                try:
                                        item = self.outbound_msg_queue_lazy.pop(0)
                                        if item['persistent'] == True:
                                                item['headers']['persistent'] = 'true'
                                        else:
                                                item['headers']['persistent'] = 'false'
                                        item['headers']['time_sent'] = time.time()
                                        self.redis.publish(item['destination'], json.dumps(item['body']))
                                except Exception as e:
                                        self.log.critical('Except: %s' % e)
                                        self.outbound_msg_queue_lazy.insert(0,item)
                                        self.connection_issue = True

        def send_event_hopeful(self, destination, body, persist):
                self.outbound_msg_queue.append({'destination': destination, 'body': body})

        def send_event_hopeful_thread(self):

                while self.continue_running:
                        time.sleep(0.010)
                        if(self.connection_issue == True):
                                continue
                        while len(self.outbound_msg_queue) > 0 and self.connection_issue == False:
                                try:
                                        item = self.outbound_msg_queue.pop(0)
                                        self.redis.publish(item['destination'], json.dumps(item['body']))
                                        
                                except Exception as e:
                                        self.log.critical('Except: %s' % e)
                                        self.outbound_msg_queue.insert(0,item)
                                        self.connection_issue = True
        def worker(self, queue):
                while self.continue_running:
                        try:
                                item = queue.get()
                                for x in 1,2,3:
                                        try:
                                                item['callback'](item['callback_class'], item['data'], item['headers'])
                                                break
                                        except Exception as e:
                                                self.log.error('Exception in worker thread: %s' % e)
                                                traceback.print_exc()
                                                sys.exc_clear()
                                                time.sleep(0.01)
                                
                                
                                queue.task_done()        
                        except:
                                time.sleep(0.01)
                                pass

        def publish_loop(self):
                self.log.debug('publish_loop() init')
                time.sleep(0.2)
                while self.continue_running:
                        if self.connection_issue == False:
                                try:
                                        try:
                                                message = self.pubsub.get_message()
                                                if not message:
                                                    time.sleep(0.010)
                                                    continue
                                                data = json.loads(message['data'])
                                                queue = message['channel'].decode('utf-8')
                                                #try:
                                                #        time_sent = float(frame.headers['time_sent'])
                                                #        time_queued = float(frame.headers['time_queued'])
                                                #        send_latency = (time.time()-time_sent)
                                                #        queue_latency = (time_sent-time_queued)
                                                #        if queue_latency > 0.1:
                                                #                print 'Queue Latency: %s' % (queue_latency)
                                                #        if send_latency > 0.1:
                                                #                print 'Send Latency: %s' % (send_latency)
                                                #except:
                                                #        pass
                                                self.work_queue.put({
                                                                'callback': self.subscriptions[queue]['callback'],
                                                                'callback_class':self.subscriptions[queue]['callback_class'],
                                                                'data': data,
                                                                'headers': {'destination': queue},
                                                                })
                                                #self.client.ack(frame)
                                        except Exception as e:
                                                raise
                                                self.log.critical('Except: %s' % e)
                                                #self.client.nack(frame)
                                except Exception as e:
                                        self.log.fatal('except: %s %s' % (type(e), e))
                                        self.connection_issue = True

                
