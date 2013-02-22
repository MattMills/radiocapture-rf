#!/usr/env/python

from gnuradio import blks2, gr
from gnuradio.gr import firdes
from grc_gnuradio import blks2 as grc_blks2
#import gnuradio.blocks as gr_blocks

import string
import time, datetime
import os
import random
import threading
import uuid

import gnuradio.extras as gr_extras

#from ID3 import *

class logging_receiver(gr.hier_block2):
	def __init__(self, samp_rate):
		self.audio_capture = True;

		gr.hier_block2.__init__(self, "logging_receiver",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
                                gr.io_signature(0, 0, 0)) # Output signature

		self.samp_rate = samp_rate
		self.audio_rate = 12500
		
		self.audiotaps = gr.firdes.low_pass( 1.0, self.samp_rate, (self.audio_rate/2), ((self.audio_rate/2)*0.2), firdes.WIN_HAMMING)
		self.prefilter_decim = int(self.samp_rate/self.audio_rate)
		self.prefilter = gr.freq_xlating_fir_filter_ccc(self.prefilter_decim, self.audiotaps, 0, self.samp_rate)

		self.valve = gr_extras.stream_selector(gr.io_signature(1, 1, gr.sizeof_gr_complex), gr.io_signature(2, 2, gr.sizeof_gr_complex), )
		self.null = gr.null_sink(gr.sizeof_gr_complex)

		self.filename = "/dev/null"
		self.filepath = "/dev/null"
		self.sink = gr.file_sink(gr.sizeof_gr_complex*1, self.filename)

		self.connect((self.valve,0), self.null)
		self.connect(self, (self.valve, 0))
		self.connect((self.valve, 1), self.prefilter, self.sink)

		self.cdr = {}
		self.time_open = 0
		self.time_activity = 0
		self.uuid = ''
		self.freq = 0
		self.center_freq = 0

		self.muted = False
		self.mute()

		self.in_use = False
		self.codec_provoice = False
		self.codec_p25 = False
        def upload_and_cleanup(self, filename, time_open, uuid, cdr, filepath, codec_provoice, codec_p25):
		if(time_open == 0): raise RuntimeError("upload_and_cleanup() with time_open == 0")
		
		time.sleep(2)
		if codec_provoice:
			os.system('nice -n 19 ./file_to_wav.py -i '+ filename + ' -p 2>&1 >/dev/null')
		elif codec_p25:
			os.system('nice -n 19 ./file_to_wav.py -i '+ filename + ' -5 2>&1 >/dev/null')
		else:
			os.system('nice -n 19 ./file_to_wav.py -i '+ filename + ' -r ' + str(int(25000)) + ' 2>&1 >/dev/null')
                os.system('nice -n 19 lame -b 32 -q2 --silent ' + filename[:-4] + '.wav' + ' 2>&1 >/dev/null')
		try:
                	os.makedirs('/nfs/%s' % (filepath, ))
                except:
                        pass
		#try:
		#	id3info = ID3('%s' % (filepath + uuid + '.mp3', ))
		#	id3info['TITLE'] = str(cdr['type']) + ' ' + str(cdr['system_group_local'])
		#	id3info['ARTIST'] = str(cdr['system_user_local'])
		#	id3info['ALBUM'] = str(cdr['system'])
		#	id3info['COMMENT'] = '%s,%s' % (cdr['system_frequency'],cdr['timestamp'])
		#	id3info.write()
		#except InvalidTagError, msg:
		#	print "Invalid ID3 tag:", msg
		now = datetime.datetime.now()
		#try:
		#        os.remove(filename)
		#except:
		#	print 'Error removing ' + filename
		try: 
			os.remove(filename[:-4] + '.wav')
		except:
			print 'error removing '
	def close(self, upload=True, emergency=False):
		if(not self.in_use): raise RuntimeError('attempted to close() a logging receiver not in_use')
		print "(%s) %s %s" %(time.time(), "Close ", str(self.cdr))
		self.cdr['time_open'] = self.time_open
		self.cdr['time_close'] = time.time()

		self.mute()
		if(self.audio_capture):
			self.sink.close()

			if(upload):
				_thread_0 = threading.Thread(target=self.upload_and_cleanup,args=[self.filename, self.time_open, self.uuid, self.cdr, self.filepath, self.codec_provoice, self.codec_p25])
	        		_thread_0.daemon = True
			        _thread_0.start()
			else:
				try:
					os.remove(self.filename)
				except:
					print 'Error removing ' +self.filename

		#self.set_tgid(0)
		#self.call_id = 0
		self.time_open = 0
		self.in_use = False
		self.uuid =''
		self.cdr = {}
	def open(self, cdr, audio_rate):
		if(self.in_use != False): raise RuntimeError("open() without close() of logging receiver")

		if(audio_rate != self.audio_rate):
			self.audio_rate = audio_rate
			channel_rate = audio_rate*1.4
			self.audiotaps = gr.firdes.low_pass( 1.0, self.samp_rate, (self.audio_rate/2), ((self.audio_rate/2)*0.2), firdes.WIN_HAMMING)
			#self.prefilter_decim = int(self.samp_rate/audio_rate)
	                #self.prefilter.set_decim(self.prefilter_decim)
			#self.prefilter.set_taps(self.audiotaps)
			self.lock()
			self.disconnect((self.valve,1), self.prefilter)
			self.disconnect(self.prefilter, self.sink)
			self.prefilter = gr.freq_xlating_fir_filter_ccc(self.prefilter_decim, self.audiotaps, 0, self.samp_rate)
			self.connect((self.valve, 1), self.prefilter, self.sink)
			self.unlock()


		self.uuid = cdr['uuid'] = str(uuid.uuid4())

		self.in_use = True
		self.cdr = cdr

		print "(%s) %s %s" %(time.time(), "Open ", str(self.cdr))
		now = datetime.datetime.utcnow()

		if(self.cdr['type'] == 'group'):
			self.filepath = filepath = "%s/%s/%s/%s/%s/%s/%s/" % ('audio', now.year, now.month, now.day, now.hour, self.cdr['system_id'], self.cdr['system_group_local'])
		elif(self.cdr['type'] == 'individual'):
			self.filepath = filepath = "%s/%s/%s/%s/%s/%s/%s/" % ('audio', now.year, now.month, now.day, now.hour, self.cdr['system_id'], 'individual')
		try: 
			os.makedirs(filepath)
		except:
			pass
		self.filename = "%s/%s.dat" % (filepath, self.uuid)

		if(self.audio_capture):
			self.sink.open(self.filename)
			self.unmute()

		self.time_open = time.time()
		self.activity()
	def tuneoffset(self, target_freq, rffreq):
		print "Tuning to %s, center %s, offset %s" % (target_freq, rffreq, (rffreq-target_freq))
		self.prefilter.set_center_freq(rffreq-target_freq)
		self.freq = target_freq
		self.center_freq = rffreq
	def set_codec_provoice(self,input):
		self.codec_provoice = input
	def set_codec_p25(self, input):
		self.codec_p25 = input
	def getfreq(self):
		return self.freq
	def mute(self):
		self.valve.set_paths((0, ))
		self.muted = True
	def unmute(self):
		self.valve.set_paths((1, ))
		self.muted = False
	def is_muted(self):
		return self.muted
	def activity(self):
		self.time_activity = time.time()
