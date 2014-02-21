#!/usr/env/python

from gnuradio import gr, blocks, analog, filter, fft
try:
	from gnuradio.gr import firdes
except:
	from gnuradio.filter import firdes

import time, datetime
import os
import threading
import uuid
import math


class logging_receiver(gr.top_block):
	def __init__(self, port):
		self.audio_capture = True;

		gr.top_block.__init__(self, "logging_receiver")

		self.channel_id = None
		self.rlock = threading.RLock()

		self.audio_rate = 12500
		self.filter_rate = 12500
		
		self.thread_id = 'logr-' + str(uuid.uuid4())

		self.filename = "/dev/null"
		self.filepath = "/dev/null"

		self.source = blocks.udp_source(gr.sizeof_gr_complex*1, "0.0.0.0", port, 1472, True)
		self.sink = blocks.file_sink(gr.sizeof_gr_complex*1, self.filename)

		self.demod = analog.quadrature_demod_cf(1)
		self.goe_low = fft.goertzel_fc(self.audio_rate*2, 100, 1500)
		self.goe_high = fft.goertzel_fc(self.audio_rate*2, 100, 3000)
		self.probe_low = blocks.probe_signal_c()
		self.probe_high = blocks.probe_signal_c()

		self.connect(self.source, self.sink)
		self.connect(self.source, self.demod)
		self.connect(self.demod, self.goe_low, self.probe_low)
		self.connect(self.demod, self.goe_high, self.probe_high)

		self.cdr = {}
		self.time_open = 0
		self.time_activity = 0
		self.time_last_use = time.time()
		self.uuid = ''
		self.freq = 0
		self.center_freq = 0

		self.source_id = -1


		self.in_use = False
		self.codec_provoice = False
		self.codec_p25 = False
	
		self.lock_id = False
		p25_sensor = threading.Thread(target=self.p25_sensor)
                p25_sensor.daemon = True
                p25_sensor.start()
	def p25_sensor(self):
	
		while(True):
			time.sleep(0.1)
			if not self.codec_p25 or not self.in_use:
				continue
			l = math.fabs(self.probe_low.level())
			h = math.fabs(self.probe_high.level())

			print '%s %s' % (l, h)
			if(l > (h*1.3)):
				#self.activity()
				print 'active'
		
	def set_samp_rate(self, samp_rate):
		self.samp_rate = samp_rate
		self.goe_low.set_rate(samp_rate)
		self.goe_high.set_rate(samp_rate)
        def upload_and_cleanup(self, filename, time_open, uuid, cdr, filepath, patches, codec_provoice, codec_p25):
		if(time_open == 0): raise RuntimeError("upload_and_cleanup() with time_open == 0")
		
		time.sleep(2)
		if codec_provoice:
			os.system('nice -n 19 ./file_to_wav.py -i %s -p -v -100 -r %s -c %s 2>&1 >/dev/null' % (filename, self.audio_rate*2, self.audio_rate))
		elif codec_p25:
			os.system('nice -n 19 ./file_to_wav.py -i %s -5 -v -100 -r %s -c %s 2>&1 >/dev/null' % (filename, self.audio_rate*2, self.audio_rate))
		else:
			os.system('nice -n 19 ./file_to_wav.py -i %s -r %s -c %s -s -70 -v -100 2>&1 >/dev/null' % (filename, self.audio_rate*2, self.audio_rate))
                os.system('nice -n 19 lame -b 32 -q2 --silent ' + filename[:-4] + '.wav' + ' 2>&1 >/dev/null')
		try:
                	os.makedirs('/nfs/%s' % (filepath, ))
                except:
                        pass
		filename = '%s' % (filepath + uuid + '.mp3', )
		tags = {}
		tags['TIT2'] = '%s %s' % (cdr['type'],cdr['system_group_local'])
		tags['TPE1'] = '%s' %(cdr['system_user_local'])
		tags['TALB'] = '%s' % (cdr['system_id'])
		
		if(cdr['system_group_local'] in patches):
			groups = []
		        for group in patches[cdr['system_group_local']]:
		        	groups.append(group)
			tags['COMM'] = '%s,%s,%s' %(cdr['system_channel_local'],cdr['timestamp'], groups)
		else:
			tags['COMM'] = '%s,%s,%s' % (cdr['system_channel_local'],cdr['timestamp'], [])
		tags['COMM'] = tags['COMM'].replace(':', '|')
		os.system('id3v2 -2 --TIT2 "%s" --TPE1 "%s" --TALB "%s" -c "RC":"%s":"English" %s' % (tags['TIT2'], tags['TPE1'], tags['TALB'], tags['COMM'], filename))




		try:
		        os.remove(filename[:-4] + '.dat')
			pass
		except:
			print 'Error removing ' + filename[:-4] + '.dat'
		try: 
			os.remove(filename[:-4] + '.wav')
			pass
		except:
			print 'error removing ' + filename[:-4] + '.wav'

	def close(self, patches, upload=True, emergency=False):
		if(not self.in_use): raise RuntimeError('attempted to close() a logging receiver not in_use')
		print "(%s) %s %s" %(time.time(), "Close ", str(self.cdr))
		self.cdr['time_open'] = self.time_open
		self.cdr['time_close'] = time.time()
		self.source.disconnect()

		if(self.audio_capture):
			self.sink.close()

			if(upload):
				_thread_0 = threading.Thread(target=self.upload_and_cleanup,args=[self.filename, self.time_open, self.uuid, self.cdr, self.filepath, patches, self.codec_provoice, self.codec_p25])
	        		_thread_0.daemon = True
			        _thread_0.start()
			else:
				try:
					os.remove(self.filename)
					pass
				except:
					print 'Error removing ' +self.filename
		self.time_open = 0
		self.time_last_use = time.time()
		self.uuid =''
		self.cdr = {}
		self.in_use = False
	def open(self, cdr, audio_rate):
		if(self.in_use != False): raise RuntimeError("open() without close() of logging receiver")
		self.in_use = True
                self.cdr = cdr
		if(audio_rate != self.audio_rate):
			print 'System: Adjusting audio rate %s' % (audio_rate)
			self.audio_rate = audio_rate
			self.set_samp_rate(audio_rate*2)
			#channel_rate = (audio_rate*1.4)*2
			#self.audiotaps = gr.firdes.low_pass( 1.0, self.samp_rate, (self.audio_rate), (self.audio_rate*0.6), firdes.WIN_HAMMING)
			#self.prefilter_decim = int(self.samp_rate/audio_rate)
	                #self.prefilter.set_decim(self.prefilter_decim)
			#self.prefilter.set_taps(self.audiotaps)
			#self.lock()

			#self.disconnect(self, self.prefilter)
			#self.disconnect(self.prefilter, (self.valve, 0))
			
			#self.disconnect((self.valve,1), self.prefilter)
			#self.disconnect(self.prefilter, self.sink)
			#self.prefilter = gr.freq_xlating_fir_filter_ccc(self.prefilter_decim, self.audiotaps, 0, self.samp_rate)
			#self.connect((self.valve, 1), self.prefilter, self.sink)

                        #self.connect(self, self.prefilter)
                        #self.connect(self.prefilter, (self.valve, 0))

			#self.unlock()


		self.uuid = cdr['uuid'] = str(uuid.uuid4())


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

		self.time_open = cdr['timestamp'] =  time.time()
		self.activity()
	def set_codec_provoice(self,input):
		self.codec_provoice = input
	def set_codec_p25(self, input):
		self.codec_p25 = input
	def getfreq(self):
		return self.freq
	def activity(self):
		self.time_activity = time.time()
		self.time_last_use = time.time()
	def acquire_lock(self, lock_id):
		print '%s attempt lock acquire %s' % (self.thread_id, lock_id)
		if self.lock_id == False:
			self.lock_id = lock_id
			return True
		else:
			return False

if __name__ == '__main__':
	tb = logging_receiver(49999)
	cdr = {
		'type': 'group',
		'system_group_local': 0,
		'system_id': 0
		}
	tb.open(cdr, 12500)
	time.sleep(5)
	tb.wait()
	tb.close({})
