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

                self.site_uuid = 'none'

		self.samp_rate = 2400000
		self.gain = 40
		self.if_gain = 20

		self.sources = {
			0:{
				'type': 'rtlsdr', 
				'args': 'rtl=3-1,buffers=4',
				'offset': 1030,
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 770000000, 
				'samp_rate': self.samp_rate
			},
			1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-2,buffers=4',
				'offset': 1290,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 772010000,
                                'samp_rate': self.samp_rate
                        },
                        2:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-3,buffers=4',
				'offset': 639,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 774000000,
                                'samp_rate': self.samp_rate
                        },
			3:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-4,buffers=4',
                                'offset': 682,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 772000000,
                                'samp_rate': self.samp_rate
                        },
                        4:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-5,buffers=4',
                                'offset': 544,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 853400000,
                                'samp_rate': self.samp_rate
                        },
                        5:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-6,buffers=4',
                                'offset': 990,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 855600000,
                                'samp_rate': self.samp_rate
                        },
                        6:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-7,buffers=4',
                                'offset': 510,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 857800000,
                                'samp_rate': self.samp_rate
                        },
                        7:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-8,buffers=4',
                                'offset': 442,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 860000000,
                                'samp_rate': self.samp_rate
                        },
			

		}
		del self.sources[7]
		del self.sources[1]
		del self.sources[4]
		del self.sources[5]
		#self.sources[3]['center_freq'] = 770000000
		#self.sources[4]['center_freq'] = 772010000
		#self.sources[5]['center_freq'] = 774000000
		del self.sources[6]


		self.systems = { #Dtown Simulcast
                        0: {
                                'type': 'p25',
                                'id': '1-001',
				'modulation': 'CQPSK',
				'transmit_site_uuid': '30f9e95e-bfd9-4b65-9f4f-ec313859d693',
				'system_uuid': 'c4d894fb-99e4-4c12-aeae-3a1314690848',
                                'default_control_channel': 15,
                                'channels': {
					0: 769256250,
					1: 769268750,
					2: 769506250,
					3: 769518750,
					4: 770556250,
					5: 770806250,
					6: 770818750,
					7: 771106250,
					8: 771118750,
					9: 771681250,
					10: 771693750,
					11: 771981250,
					12: 771993750,
					13: 772331250,
					14: 772343750,
					15: 772656250,
					16: 772981250,
					17: 772993750,
					18: 773231250,
					19: 773243750,
					20: 773881250,
					21: 773893750,
					22: 774656250,
					23: 774668750,
                                }
                        },
			4: {
				'type': 'moto',
				'id': 'nj-sp',
				'channels': {
					0: 851012500,
					48: 852212500,
					85: 853137500,
					228: 856712500,
					248: 857212500,
					268: 857717500,
					288: 858212500,
					308: 858712500,
					328: 859212500,
					348: 859712500,
					368: 860212500,
					388: 860712500,
				}
			}
		}
