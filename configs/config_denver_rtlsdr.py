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
				'args': 'rtl=4-0,buffers=4',
				'offset': 307,
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 855050000,
				'samp_rate': self.samp_rate
			},
			1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-1,buffers=4',
				'offset': 290,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 857450000,
                                'samp_rate': self.samp_rate
                        },
                        2:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-2,buffers=4',
				'offset': 377,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 859850000,
                                'samp_rate': self.samp_rate
                        },
                        3:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-3,buffers=4',
				'offset': 647,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 852200000,
                                'samp_rate': self.samp_rate
                        },
                        4:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-4,buffers=4',
				'offset': -80,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 853850000,
                                'samp_rate': self.samp_rate
                        },
			5:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-5,buffers=4',
                                'offset': 231,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 407500000,
                                'samp_rate': self.samp_rate
                        },
			6:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-6,buffers=4',
                                'offset': 303,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 409500000,
                                'samp_rate': self.samp_rate
                        },
			7:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-7,buffers=4',
                                'offset': 170,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 770000000,
				'samp_rate': self.samp_rate
                        },
			8:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-8,buffers=4',
                                'offset': 444,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 772000000,
				'samp_rate': self.samp_rate
                        },
			9:{
				'type': 'rtlsdr',
				'args': 'rtl=4-9,buffers=4',
				'offset': 612,
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 774000000,
				'samp_rate': self.samp_rate
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
                        7: { #Adams County Simulcast (FRCC)
                                'type': 'p25',
                                'id': 7,
                                'default_control_channel': 0,
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
					11: 772993750
                                }
                        },
                        8: { #Arapahoe Admin (Denver Metro)	1	1
                                'type': 'p25',
                                'id': 8,
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
                                'id': 9,
				'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', #DTRS
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
                                'id': 10,
                                'default_control_channel': 0,
                                'channels': {
					0: 769256250,
					1: 771556250,
					2: 772006250,
					3: 772818750,
					4: 773131250,
					5: 773681250,
					6: 851787500,
					16: 852175000,
					17: 852600000,
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
                                'id': 11,
				'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', #DTRS
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
                        13: { #Fort Lupton (FRCC)
                                'type': 'p25',
                                'id': 13,
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
                                'id': 14,
				'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', #DTRS
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
                                'id': 15,
				'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', #DTRS
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
			16: { #MARC 1-001
				'type': 'p25',
                                'id': 16,
				'system_uuid': 'bfd7943c-2aa8-4b6c-a09f-0e6ddb25f034',  #MARC
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
			17: {	#MARC 2-002
                                'type': 'p25',
                                'id': 17,
				'system_uuid': 'bfd7943c-2aa8-4b6c-a09f-0e6ddb25f034',  #MARC
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
			18: { #MARC - 6-006
                                'type': 'p25',
                                'id': 18,
				'system_uuid': 'bfd7943c-2aa8-4b6c-a09f-0e6ddb25f034',  #MARC
                                'default_control_channel': 0,
                                'channels': {
					0: 851562500,
					8: 852125000,
					1: 852375000,
					2: 852775000,
					9: 853062500,
					3: 853150000,
					4: 853275000,
					5: 853425000,
					6: 853725000,
					7: 853862500,
					10: 857062500,
					11: 858137500,
					12: 859612500
				}
			},
			19: {

                                'type': 'p25',
                                'id': 19,
				'system_uuid': '31a2cf3a-5529-4a1b-8905-089c2a8feec8',  #Westminster P25
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
                        },
			20: { #City and Coutny of Denver - P25
				'type': 'p25',
                                'id': 20,
                                'default_control_channel': 0,
                                'channels': {
                                        0: 853862500,
                                        1: 853725000,
                                        2: 853425000,
                                        3: 853275000,
                                        4: 853150000,
					7: 852775000,
                                        5: 852375000,
                                        6: 851562500
				}
			},
			21: { #DTRS - 1-002
				'type': 'p25',
                                'id': 21,
                                'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', 
                                'default_control_channel': 0,
                                'channels': {
					0: 851350000,
					1: 851600000,
					2: 851925000,
					3: 852175000,
					4: 852587500,
					5: 852737500,
					6: 853175000,
					7: 853337500,
					8: 853587500,
					9: 853912500,
					10: 854137500,
					11: 854762500,
					12: 856912500,
					13: 857162500,
					14: 858012500,
				}
			},
			22: { #DTRS - 1-005
                                'type': 'p25',
                                'id': 22,
                                'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', 
                                'default_control_channel': 0,
                                'channels': {
					0: 851125000,
					1: 851625000,
					2: 851800000,
					3: 852087500,
					4: 852237500,
					5: 852662500,
					6: 852987500,
					7: 853162500,
					8: 853337500,
					9: 853550000,
					10: 853975000,
					11: 854712500,
					12: 855587500,
					13: 856012500,
                                }
                        },
			24: { #DTRS - 1-006
                                'type': 'p25',
                                'id': 24,
                                'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', 
                                'default_control_channel': 0,
                                'channels': {
					0: 851162500,
					1: 851475000,
					2: 851637500,
					3: 851862500,
					4: 852187500,
					5: 852450000,
					6: 852625000,
					7: 852950000,
					8: 853112500,
					9: 853450000,
					10: 853612500,
					11: 853850000,
					12: 854812500,
					13: 855612500,
					14: 856562500,
					15: 857612500,
                                }
                        },
			25: { #DTRS - 1-007
                                'type': 'p25',
                                'id': 25,
                                'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540',
                                'default_control_channel': 0,
                                'channels': {
					0: 851112500,
					1: 851275000,
					2: 851450000,
					3: 851737500,
					4: 852150000,
					5: 852287500,
					6: 852475000,
					7: 852712500,
					8: 853175000,
					9: 853400000,
					10: 853625000,
					11: 853875000,
					12: 857037500,
					13: 857512500,
					14: 769581250,
					15: 770856250,
					16: 771856250,
					17: 772756250,
					18: 773668750,
                                }
                        },
			26: { #DTRS - 1-052
                                'type': 'p25',
                                'id': 26,
                                'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', 
                                'default_control_channel': 0,
                                'channels': {
					0: 851300000,
					1: 851825000,
					2: 852387500,
					3: 852925000,
					4: 853525000,
					5: 853900000,
					6: 855312500,
					7: 857337500,
					8: 857587500,
					9: 858587500,
					10: 859337500,
					11: 859687500,
                                }
                        },
			27: { #DTRS - 1-068
                                'type': 'p25',
                                'id': 27,
                                'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', 
                                'default_control_channel': 0,
                                'channels': {
					0: 770593750,
					1: 771287500,
					2: 771718750,
					3: 772143750,
					4: 772406250,
					5: 773493750,
		
                                }
                        },
			28: { #DTRS - 1-069
                                'type': 'p25',
                                'id': 28,
                                'system_uuid': '4ec04aaa-a534-49ff-bc7c-79917487d540', 
                                'default_control_channel': 0,
                                'channels': {
					0: 771206250,
					1: 771468750,
					2: 772131250,
					3: 772418750,
					4: 773243750,
					5: 773693750,
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

		
