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
		self.gain = 28
		self.if_gain = 15 

		self.sources = {
			0:{
				'type': 'rtlsdr', 
				'args': 'rtl=10',
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 855050000,
				'samp_rate': self.samp_rate
			},
			1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=11',
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 857450000,
                                'samp_rate': self.samp_rate
                        },
                        2:{
                                'type': 'rtlsdr',
                                'args': 'rtl=12',
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 859850000,
                                'samp_rate': self.samp_rate
                        },
                        3:{
                                'type': 'rtlsdr',
                                'args': 'rtl=13',
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 852200000,
                                'samp_rate': self.samp_rate
                        },
                        4:{
                                'type': 'rtlsdr',
                                'args': 'rtl=14',
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 853850000,
                                'samp_rate': self.samp_rate
                        },
		}


		self.systems = {
			0: { #Denver Public Safety - EDACS
				'type': 'edacs',
				'id': 1,
				'symbol_rate': 9600.0,
				'esk': True,
				'channels': {
					1: 854987500,
	                                2: 855487500,
	                                3: 855987500,
	                                4: 856487500,
	                                5: 857237500,
	                                6: 857737500,
	                                7: 858487500,
	                                8: 859237500,
	                                9: 859737500,
	                                10: 854437500,
	                                11: 855237500,
	                                12: 855737500,
	                                13: 856237500,
	                                14: 856737500,
	                                15: 857487500,
	                                16: 858237500,
	                                17: 858737500,
	                                18: 859487500,
	                                19: 854062500,
	                                20: 854562500
				}
			},
			1: { #Aurora City - EDACS
				'type': 'edacs',
                                'id': 2,
                                'symbol_rate': 9600.0,
                                'esk': False,
                                'channels': {
	                                1: 856762500,
	                                2: 856937500,
	                                3: 856962500,
	                                4: 856987500,
	                                5: 857762500,
	                                6: 857937500,
	                                7: 857962500,
	                                8: 857987500,
	                                9: 858762500,
	                                10: 858937500,
	                                11: 858962500,
	                                12: 858987500,
	                                13: 859762500,
	                                14: 859937500,
	                                15: 859962500,
	                                16: 859987500,
	                                17: 860762500,
	                                18: 860937500,
	                                19: 860962500,
	                                20: 860987500
				}
			},
			2: { #DIA - EDACS
				'type': 'edacs',
                                'id': 3,
                                'symbol_rate': 9600.0,
                                'esk': False,
                                'channels': {
	                               1: 855212500,
	                               2: 855712500,
	                               3: 856462500,
	                               4: 857212500,
	                               5: 857712500,
	                               6: 851362500,
	                               7: 851662500,
	                               8: 851937500,
	                               9: 852537500,
	                               10: 852837500,
	                               11: 856437500,
	                               12: 857437500,
	                               13: 858437500,
	                               14: 859437500,
	                               15: 857637500
				}
			},
			3: { #Westerville / Arvada - EDACS
				'type': 'edacs',
                                'id': 4,
                                'symbol_rate': 9600.0,
                                'esk': False,
                                'channels': {
					1: 851062500,
		                        2: 851762500,
		                        3: 852062500,
		                        4: 852325000,
		                        5: 853925000,
		                        6: 851312500,
		                        7: 852162500,
		                        8: 852887500,
		                        9: 853350000,
		                        10: 853650000
				}
			}
		}

