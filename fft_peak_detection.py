#!/usr/bin/env python3

import numpy
from scipy import signal

from p25_control_demod import p25_control_demod
from moto_control_demod import moto_control_demod
from edacs_control_demod import edacs_control_demod
from redis_channelizer_manager import redis_channelizer_manager


from config import rc_config

import time
import uuid
import json
import logging
import argparse


with open('config.logging.json', 'rt') as f:
        config = json.load(f)

logging.config.dictConfig(config)

overseer_uuid = '%s' % str(uuid.uuid4())
site_uuid = '876c1a54-8183-4134-a41c-67a5b6121fcd'

config = rc_config()


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--index', help="Device config index, if specified, all other configured sources will be deleted", type=int)
args = parser.parse_args()


rcm = redis_channelizer_manager(index=args.index)
time.sleep(0.5)
with open('/tmp/fft_source_%s' % args.index, 'rb') as fh:
    data = numpy.fromfile(fh, numpy.float32) 

last_values = []
last_values_length = 2048


fft_width = 1024*16
bandwidth = config.sources[args.index]['samp_rate']
hz_per_bin = bandwidth/fft_width
center_freq = config.sources[args.index]['center_freq']

min_width_in_bins = 3000/hz_per_bin
max_width_in_bins = 30000/hz_per_bin

data_average = sum(data)/len(data)
data_min = min(data)
data_max = max(data)

for i in range(len(data)):
    data[i] = data[i]+abs(data_min)

data_average = sum(data)/len(data)
data_min = min(data)
data_max = max(data)

peaks = signal.find_peaks(data, width=[min_width_in_bins, max_width_in_bins], prominence=1)


demods = {}

for line in peaks[0]:
    if data[line] > data_average*2:
        frequency = int((line*hz_per_bin)-(bandwidth/2)+center_freq)
        print('Peak %s' % int(frequency))
        demods[frequency] = p25_control_demod({
                'type': 'p25',
                'id': 'p25',
                'modulation': 'C4FM',
                'default_control_channel': 0,
                'channels': { 0: frequency, 1:frequency},
            }, site_uuid, overseer_uuid, rcm=rcm)
        demods[frequency].start()

time.sleep(30)
offsets = []
for frequency in demods:
            thread = demods[frequency]
            if thread.is_locked == True:
                    if thread.system['type'] == 'p25':
                        detail = sid = '%s %s-%s %s-%s' % (thread.site_detail['Control Channel'], thread.site_detail['System ID'], thread.site_detail['WACN ID'], thread.site_detail['RF Sub-system ID'], thread.site_detail['Site ID'])
                    else:
                        detail = thread.site_detail
                    try:
                        offset = frequency-thread.site_detail['Control Channel']
                    except:
                        offset = None

                    if offset != None and offset < 5000 and offset > -5000:
                        offsets.append(offset)
                    print('%s %s %s' % (frequency, offset, detail))
                    with open('fft.scan.output', 'a') as f:
                        f.write('%s %s %s %s %s %s\n' % ( args.index, frequency, offset, detail, thread.quality, thread.bad_messages))
                    thread.keep_running = False


if len(offsets) > 0:
    print('offset average for %s: %s' % (args.index, sum(offsets)/len(offsets)))
#plt.plot(data)
#plt.axhline((data_average*2))
#plt.show()



