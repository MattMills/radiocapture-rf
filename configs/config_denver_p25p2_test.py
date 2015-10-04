#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):
                self.receiver_split2 = False    #Does the frontend receiver split each inbound source by 1/2
		self.frontend_mode = 'xlat'

                self.frontend_ip = '127.0.0.1'
                self.backend_ip = '127.0.0.1'



		self.samp_rate = 2400000
		self.gain = 32
		self.if_gain = 0

		self.sources = {
			0:{
				'type': 'rtlsdr', 
				'args': 'rtl=10,buffers=4',
				'offset': 1280,
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 772050000,
				'samp_rate': self.samp_rate
			},
			1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=11,buffers=4',
				'offset': 880,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 770450000,
                                'samp_rate': self.samp_rate
                        },
                        2:{
                                'type': 'rtlsdr',
                                'args': 'rtl=12,buffers=4',
				'offset': 1110,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 859850000,
                                'samp_rate': self.samp_rate
                        },
                        3:{
                                'type': 'rtlsdr',
                                'args': 'rtl=13,buffers=4',
				'offset': 1190,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 852200000,
                                'samp_rate': self.samp_rate
                        },
                        4:{
                                'type': 'rtlsdr',
                                'args': 'rtl=14,buffers=4',
				'offset': 1000,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 853850000,
                                'samp_rate': self.samp_rate
                        },
			

		}
		self.sources = {
			0:{
                                'type': 'bladerf',
                                'args': 'numchan=1 bladerf,fpga=/home/mmills/build/hostedx40.rbf,num_samples=1048576,num_transfers=65536,num_buffers=65536',
                                'center_freq': 770175000,
                                'samp_rate': 12000000,
                                'rf_gain': 2,
                                'bb_gain': 20
                        }
		}


		self.systems = {
                         99: { #ICIS P25 RFSS1 SITE10 - Pasadena
                                'type': 'p25',
                                'id': 99,
                                'default_control_channel': 10,
                                'modulation': 'CQPSK',
                                'channels': {
                                        0: 770106250,
					1: 770356250,
					2: 770606250,
					3: 771106250,
					4: 771481250,
					5: 771731250,
					6: 772156250,
					7: 772481250,
					8: 772731250,
					9: 772743750,
					10: 772981250,
					11: 772993750,
                                },
                        },
		}

		
