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
		self.gain = 20
		self.if_gain = 10

		self.sources = {
			0:{
				'type': 'rtlsdr', 
				'args': 'rtl=3-1,buffers=4',
				'offset': 1040,
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 770000000, 
				'samp_rate': self.samp_rate
			},
			1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-2,buffers=4',
				'offset': 1350,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 772000000,
                                'samp_rate': self.samp_rate
                        },
                        2:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-3,buffers=4',
				'offset': 827,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 774000000,
                                'samp_rate': self.samp_rate
                        },
			3:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-4,buffers=4',
                                'offset': 210,
                                'bb_gain': 20,
                                'rf_gain': 28,
                                'center_freq': 851200000,
                                'samp_rate': self.samp_rate
                        },
                        4:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-5,buffers=4',
                                'offset': 460,
                                'bb_gain': 20,
                                'rf_gain': 28,
                                'center_freq': 853400000,
                                'samp_rate': self.samp_rate
                        },
                        5:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-6,buffers=4',
                                'offset': 980,
                                'bb_gain': 20,
                                'rf_gain': 28,
                                'center_freq': 855600000,
                                'samp_rate': self.samp_rate
                        },
                        6:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-7,buffers=4',
                                'offset': 0,
                                'bb_gain': 20,
                                'rf_gain': 28,
                                'center_freq': 857800000,
                                'samp_rate': self.samp_rate
                        },
                        7:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-8,buffers=4',
                                'offset': 110,
                                'bb_gain': 20,
                                'rf_gain': 28,
                                'center_freq': 860000000,
                                'samp_rate': self.samp_rate
                        },
			

		}


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
			#1: {
			#	'type': 'moto',
			#	'id': 0xa812,
			#	'channels': {
			#		10: 851262500,
			#		25: 851637500,
			#		35: 851887500,
			#		50: 852262500,
			#		110: 853762500,
			#		#854962500
			#		169: 855237500,
			#		197: 855937500,
			#		229: 856737500,
			#		494: 852375000,
			#	}
			#}
			#1: {	#NJCIS, hunterdon Simulcast
			#	'type': 'p25',
			#	'id': 'ngcis',
			#	'modulation': 'C4FM',
			#	'default_control_channel': 0,
			#	'channels': {
			#		0: 769206250,
			#		1: 770193750,
			#		2: 773031250,
			#		3: 773593750,
			#		4: 773831250,
			#		5: 774818750,
			#	}
			#},
			2: {
				'type': 'p25',
				'id': 'peco',
				'modulation': 'C4FM',
				'default_control_channel': 0,
				'channels': {
					0: 854912500,
					1: 856162500,
					2: 857162500,
					3: 858162500,
					4: 859112500,
					5: 860537500,
				}
			},
			#3: {
			#	'type': 'moto',
			#	'id': 'nj-sp',
			#	'channels': {
			#		0: 851012500,
			#		48: 852212500,
			#		85: 853137500,
			#		228: 856712500,
			#		248: 857212500,
			#		268: 857717500,
			#		288: 858212500,
			#		308: 858712500,
			#		328: 859212500,
			#		348: 859712500,
			#		368: 860212500,
			#		388: 860712500,
			#	}
			#}
		}
