#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):
                self.receiver_split2 = False    #Does the frontend receiver split each inbound source by 1/2
		self.frontend_mode = 'xlat'

                self.frontend_ip = '10.5.0.22'
                self.backend_ip = '10.5.0.23'

                self.site_uuid = 'f1877ce6-bfef-4c9e-b34d-014c24c974f2'

		self.samp_rate = 2400000
		self.gain = 28
		self.if_gain = 20

		self.sources = {
			0:{
				'type': 'rtlsdr', 
				'args': 'rtl=10,buffers=4',
				'offset': 1280,
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 855050000,
				'samp_rate': self.samp_rate
			},
			1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=11,buffers=4',
				'offset': 880,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 857450000,
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
			5:{
                                'type': 'rtlsdr',
                                'args': 'rtl=15,buffers=4',
                                'offset': 1000,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 407500000,
                                'samp_rate': self.samp_rate
                        },
			6:{
                                'type': 'rtlsdr',
                                'args': 'rtl=16,buffers=4',
                                'offset': 1080,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 409500000,
                                'samp_rate': self.samp_rate
                        },
			7:{
                                'type': 'rtlsdr',
                                'args': 'rtl=17,buffers=4',
                                'offset': 1400,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 770500000,
                                'samp_rate': 3200000
                        },
			8:{
                                'type': 'rtlsdr',
                                'args': 'rtl=18,buffers=4',
                                'offset': 1120,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 773500000,
                                'samp_rate': 3200000
                        },
			

		}


		self.systems = {
			0: { #Denver Public Safety - EDACS
				'type': 'edacs',
				'id': 0,
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
                                'id': 1,
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
                                'id': 2,
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
			3: { #Denver city services
                                'type': 'edacs',
                                'id': 3,
                                'symbol_rate': 9600.0,
                                'esk': False,
                                'channels': {
                                        1: 858462500,
                                        2: 859212500,
                                        3: 859462500,
                                        4: 856637500,
                                        5: 856137500,
                                        6: 855462500,
                                        7: 856212500,
                                        8: 856712500,
                                        9: 857462500,
                                        10: 858212500,
					11: 858712500,
					12: 859262500,
					13: 859712500,
					14: 854587500,
					15: 857137500
                                }
			},
			4: { #Lakewood Public Works - EDACS
				'type': 'edacs',
                                'id': 4,
                                'symbol_rate': 9600.0,
                                'esk': True,
                                'channels': {
					1: 853750000,
		                        2: 854387500,
		                        3: 854537500,
		                        4: 855137500,
		                        5: 856537500,
				}
			},
			5:{#United Airlines
                                'type': 'moto',
                                'id': 0x3b27,
                                'channels' : {
                                        0x1: 853462500,
					0x99: 854837500,
					0xe8: 856812500,
					0xeb: 856887500,
					0x113: 857887500,
					0x137: 858787500,
					0x13b: 858887500,
					0x163: 859887500,
					0x188: 860812500,
                                        0x18b: 860887500,
                                        0x18c: 860912500,
                                }
                        },
			6:{#Denver area federal / military - (2) Downtown Denver
				'type': 'moto',
                                'id': 0x8d34,
                                'channels' : {
                                        0x1ba: 406775000,
                                        0x1d6: 407125000,
                                        0x20d: 407812500,
                                        0x23e: 408425000,
                                        0x25a: 408775000,
                                }
                        },
                        7: { #Adams County Simulcast (Denver Metro)	3	22
                                'type': 'p25',
                                'id': 3022,
                                'default_control_channel': 0,
                                'channels': {
					0: 770106250,
					1: 770356250,
					2: 770606250,
					3: 771106250,
					4: 771481250,
					5: 771731250,
					6: 772156250,
					7: 772493750,
					8: 772731250,
					9: 772743750,
					10: 772981250,
					11: 772993750
                                }
                        },
                        8: { #Arapahoe Admin (Denver Metro)	1	1
                                'type': 'p25',
                                'id': 1001,
                                'default_control_channel': 0,
                                'channels': {
					0: 851225000,
					1: 851775000,
					2: 852100000,
					3: 852362500,
					4: 852937500,
					5: 853237500,
					6: 853437500,
					7: 853662500,
					8: 854862500,
					9: 856687500,
					10: 858387500

                                }
                        },
                        9: { #Auraria Campus (Denver Metro)	1	70
                                'type': 'p25',
                                'id': 1070,
                                'default_control_channel': 0,
                                'channels': {
					0: 769156250,
					1: 769406250,
					2: 769656250,
					3: 769906250,
					4: 770156250,
					5: 770406250,
					6: 770656250,
					7: 770906250,
					8: 773031250,
					9: 773281250,
					10: 773531250,
					11: 773781250

                                }
                        },
                        10: { #Chevron Plaza Tower (Denver Metro)	1	64
                                'type': 'p25',
                                'id': 1064,
                                'default_control_channel': 0,
                                'channels': {
					0: 769256250,
					1: 771556250,
					2: 772006250,
					3: 772818750,
					4: 773131250,
					5: 773681250,
					6: 851787500,
					7: 852875000,
					8: 853837500,
					9: 857687500,
					10: 858062500,
					11: 858512500,
					12: 858687500,
					13: 859037500,
					14: 859512500,
					15: 859912500

                                }
                        },
                        11: { #Denver TX (Denver Metro)	1	20
                                'type': 'p25',
                                'id': 1020,
                                'default_control_channel': 0,
                                'channels': {
					0: 770281250,
					1: 772556250,
					2: 773906250,
					3: 774306250,
					4: 774556250,
					5: 774806250,
					6: 851437500,
					7: 852362500,
					8: 852562500,
					9: 852812500,
					10: 853112500,
					11: 853700000

                                }
                        },
                        12: { #DRDC CF	1	9
                                'type': 'p25',
                                'id': 1009,
                                'default_control_channel': 0,
                                'channels': {
					0: 851150000,
					1: 851950000,
					2: 852700000,
					3: 853475000,
					4: 853675000,
					5: 853962500

                                }
                        },
                        13: { #Fort Lupton	3	55
                                'type': 'p25',
                                'id': 3055,
                                'default_control_channel': 0,
                                'channels': {
					0: 770256250,
					1: 771006250,
					2: 771256250,
					3: 771543750,
					4: 771843750,
					5: 772093750,
					6: 772393750,
					7: 773168750,
					8: 773418750

                                }
                        },
                        14: { #Lookout Mountain (Denver Metro)	1	8
                                'type': 'p25',
                                'id': 1008,
                                'default_control_channel': 0,
                                'channels': {
					0: 851112500,
					1: 851400000,
					2: 851487500,
					3: 851687500,
					4: 851987500,
					5: 852037500,
					6: 852200000,
					7: 852412500,
					8: 852487500,
					9: 853062500,
					10: 853412500,
					11: 853487500,
					12: 853775000,
					13: 854162500,
					14: 855437500,
					15: 855837500,
					16: 856062500,
					17: 856512500,
					18: 857787500
                                }
                        },
                        15: { #State Capitol (Denver Metro)	1	71
                                'type': 'p25',
                                'id': 1071,
                                'default_control_channel': 0,
                                'channels': {
					0: 769306250,
					1: 769531250,
					2: 769781250,
					3: 770581250,
					4: 771456250,
					5: 772206250,
					6: 773231250,
					7: 773481250,
					8: 774031250,
					9: 774281250,
					10: 774656250,
					11: 774906250
                                }
                        },
			16: {
				'type': 'p25',
                                'id': 10,
                                'default_control_channel': 0,
				'channels': {
					0: 851250000,
					1: 851712500,
					2: 851912500,
					3: 852225000,
					4: 852687500,
					5: 852912500,
					6: 853300000,
					7: 853537500
				}
			},
			17: {
                                'type': 'p25',
                                'id': 11,
                                'default_control_channel': 0,
                                'channels': {
					0: 851087500,
					1: 851337500,
					2: 852437500,
					3: 852750000,
					4: 853212500,
					5: 854637500,
					6: 855412500,
					7: 856612500
				}
			},
			18: {
                                'type': 'p25',
                                'id': 12,
                                'default_control_channel': 0,
                                'channels': {
					0: 851562500,
					1: 852375000,
					2: 852775000,
					3: 853150000,
					4: 853275000,
					5: 853425000,
					6: 853725000,
					7: 853862500
				}
			},
			19: {

                                'type': 'p25',
                                'id': 13,
                                'default_control_channel': 0,
                                'channels': {
					0: 851062500,
					1: 851762500,
					2: 852162500,
					3: 852887500,
					4: 853350000,
					5: 856037500,
					6: 859387500
                                }
                        }
		}
		#del self.systems[19]
		#del self.systems[18]
		#del self.systems[17]
		#del self.systems[16]
		#del self.systems[15]
		#del self.systems[14]
		#del self.systems[13]
		#del self.systems[12]
		#del self.systems[11]
		#del self.systems[10]
		#del self.systems[9]
		#del self.systems[8]
		#del self.systems[7]
	
		#del self.systems[6]
		#del self.systems[5]
		#del self.systems[4]
		#del self.systems[3]
		#del self.systems[2]
		#del self.systems[1]
		#del self.systems[0]

		
