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

                self.site_uuid = 'd5bc103c-db78-4f16-a2da-d4bec23d7e72'

		self.samp_rate = 2400000
		self.gain = 30
		self.if_gain = 40

		self.sources = {
			0:{
				'type': 'rtlsdr', 
				'args': 'rtl=4-0,buffers=4',
				'offset': 100,
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 855050000,
				'samp_rate': self.samp_rate
			},
			1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-1,buffers=4',
				'offset': 130,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 857450000,
                                'samp_rate': self.samp_rate
                        },
                        2:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-2,buffers=4',
				'offset': 330,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 859850000,
                                'samp_rate': self.samp_rate
                        },
                        3:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-3,buffers=4',
				'offset': 540,
                                'bb_gain': self.if_gain,
                                'rf_gain': 36,
                                'center_freq': 852200000,
                                'samp_rate': self.samp_rate
                        },
                        4:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-4,buffers=4',
				'offset': -90,
                                'bb_gain': self.if_gain,
                                'rf_gain': 36,
                                'center_freq': 853850000,
                                'samp_rate': self.samp_rate
                        },
			5:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-5,buffers=4',
                                'offset': 180,
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
                                'rf_gain': 36,
                                'center_freq': 770000000,
				'samp_rate': self.samp_rate
                        },
			8:{
                                'type': 'rtlsdr',
                                'args': 'rtl=4-8,buffers=4',
                                'offset': 444,
                                'bb_gain': self.if_gain,
                                'rf_gain': 38,
                                'center_freq': 772000000,
				'samp_rate': self.samp_rate
                        },
			9:{
				'type': 'rtlsdr',
				'args': 'rtl=4-9,buffers=4',
				'offset': 612,
				'bb_gain': self.if_gain,
				'rf_gain': 38,
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
			1: { #DIA - EDACS
				'type': 'edacs',
                                'id': 1,
                                'symbol_rate': 9600.0,
				'transmit_site_uuid': 'd62895e9-f1b7-4149-8fbe-b46ef54fa950',
                                'system_uuid': 'c35c1083-c799-47d2-8f76-bcd313999bf4',
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
			2: { #Denver city services
                                'type': 'edacs',
                                'id': 2,
                                'symbol_rate': 9600.0,
				'transmit_site_uuid': 'dac3bed2-4f02-4f3f-a404-8735d6ddd5d7',
                                'system_uuid': 'afd4d02b-171c-4a97-806c-6c275dfcfbb2',
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
			4:{#United Airlines
                                'type': 'moto',
                                'id': 0x3b27,
                                'transmit_site_uuid': 'd04ba7d7-eb9b-4355-b617-b07034522276',
                                'system_uuid': '28d436b4-c9df-4787-a2ba-f5d27e0ab121',
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
			5:{#Denver area federal / military - (2) Downtown Denver
				'type': 'moto',
                                'id': 0x8d34,
                                'transmit_site_uuid': 'a265fea6-18a8-47cd-b5a5-5caccced460b',
                                'system_uuid': '8e5ceec8-2e4a-4cbb-aaa0-06a278874894',
                                'channels' : {
                                        0x1ba: 406775000,
                                        0x1d6: 407125000,
                                        0x20d: 407812500,
                                        0x23e: 408425000,
                                        0x25a: 408775000,
                                }
                        },
                        6: { #Adams County Simulcast (FRCC) 5-22
                                'type': 'p25',
                                'id': 6,
                                'default_control_channel': 0,
				'modulation': 'CQPSK',
                                'transmit_site_uuid': '125ca2a8-118e-4413-a0c6-ad24c0a0de98',
                                'system_uuid': '3fe357e7-5098-469f-89f1-15f67326b361',
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
                        7: { #DTRS 1-001
                                'type': 'p25',
                                'id': 7,
                                'default_control_channel': 0,
                                'transmit_site_uuid': 'e5434680-1b27-4b14-b8e3-5f4960eb21cc',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', #DTRS
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
                        8: { #DTRS 1-070
                                'type': 'p25',
                                'id': 8,
				'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', #DTRS
                                'transmit_site_uuid': '83592f32-550f-4417-9c77-57685e0619b6',
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
                        10: { #DTRS 1-064
                                'type': 'p25',
                                'id': 10,
                                'default_control_channel': 0,
                                'transmit_site_uuid': '43dc2da0-082d-4643-8793-2e77d3b12da8',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', #DTRS
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
                        11: { #DTRS 1-020
                                'type': 'p25',
                                'id': 11,
                                'transmit_site_uuid': '28ae194d-42a3-49b3-a387-ed039cf5a37c',
				'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', #DTRS
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
                        14: { #DTRS 1-008
                                'type': 'p25',
                                'id': 14,
                                'transmit_site_uuid': 'c91bb25c-09e0-49d8-bc11-9fdd6e10806d',
				'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', #DTRS
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
                        15: { #DTRS 1-071
                                'type': 'p25',
                                'id': 15,
                                'transmit_site_uuid': 'a9b8f3f0-042d-4f5d-bf0d-003c8eac4dc8',
				'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', #DTRS
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
                                'transmit_site_uuid': '8bebe35e-d316-4ecb-819c-dced718f0ce8',
				'system_uuid': '8bd8cbe3-ac9a-4808-b2e4-a8817b6a288f',  #MARC
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
                                'transmit_site_uuid': 'f1666ebb-08b2-4f28-af08-a3bf8aa82c7c',
				'system_uuid': '8bd8cbe3-ac9a-4808-b2e4-a8817b6a288f',  #MARC
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
                                'transmit_site_uuid': 'c1f3a4d6-d512-4a00-bb4b-ee6b44f9c2a6',
				'system_uuid': '8bd8cbe3-ac9a-4808-b2e4-a8817b6a288f',  #MARC
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
			22: { #DTRS - 1-005
                                'type': 'p25',
                                'id': 22,
                                'transmit_site_uuid': '5e738104-d9b5-42ef-b970-9e037fa5cefd',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 0,
				'modulation': 'C4FM',
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
                                'transmit_site_uuid': 'ba9e9cf8-c9d1-46be-8ddd-ee3c743a79af',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', 
                                'default_control_channel': 0,
				'modulation': 'C4FM',
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
                                'transmit_site_uuid': '658a2b18-3749-4316-a181-c8abd57144ec',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
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
                                'transmit_site_uuid': '788a3227-e1e2-43b5-8760-87730cc292ec',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
				'modulation': 'CQPSK',
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
                                'transmit_site_uuid': 'd532058c-cd1c-4937-8748-371015877b72',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', 
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
                                'transmit_site_uuid': '5cdcd394-f3f5-4bb4-b5a2-f08559dd6bd4',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007', 
                                'default_control_channel': 0,
                                'channels': {
					0: 771206250,
					1: 771468750,
					2: 772131250,
					3: 772418750,
					4: 773243750,
					5: 773693750,
                                }
                        },
			29: { #Aurora P25
				'type': 'p25',
				'id': 29,
				'system_uuid': 'unknown',
				'modulation': 'CQPSK',
				'default_control_channel': 0,
                                'transmit_site_uuid': 'b772c955-2e5a-4b34-aa49-c56d800f6cc6',
                                'system_uuid': 'd096d184-a844-4e25-9e4f-936ae3436e15',
				'channels': {
					0: 856762500,
					1: 856937500,
					2: 856962500,
					3: 856987500,
					4: 857762500,
					5: 857937500,
					6: 857962500,
					7: 857987500,
					8: 858762500,
					9: 858937500,
					10: 858962500,
					11: 858987500,
					12: 859762500,
					13: 859937500,
					14: 859962500,
					15: 859987500,
					16: 860762500,
					17: 860937500,
					18: 860962500,
					19: 860987500,


				}
			},
			30: { #DTRS 1-014
				'type': 'p25',
                                'id': 30,
                                'transmit_site_uuid': '4391a532-a156-46ff-b12a-61fe05dc632e',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
				'default_control_channel': 0,
				'modulation': 'CQPSK',
                                'channels': {
					0: 851975000,
                                        1: 852312500,
                                        2: 852900000,
                                        3: 853375000,
                                        4: 853937500,
                                        5: 856112500,
                                        6: 857187500,
                                        7: 858112500,
                                        8: 858537500,
                                        9: 859562500,
				}
			},
			31: { #MARC 3-003
				'type': 'p25',
                                'id': 31,
                                'transmit_site_uuid': '0f6e515e-08fc-4e74-a8ba-eb1ca23260be',
                                'system_uuid': '8bd8cbe3-ac9a-4808-b2e4-a8817b6a288f',  #MARC
                                'default_control_channel': 0,
                                'channels': {
					0: 852062500,
					1: 852325000,
					2: 853750000,
					3: 854187500,
					4: 854387500,
					5: 854612500,
					6: 855137500,
					7: 856537500,
				}
			},
			32: { #MARC 21-021
				'type': 'p25',
                                'id': 32,
                                'transmit_site_uuid': '3bf26f46-1261-47c4-b581-50e98816516e',
                                'system_uuid': '8bd8cbe3-ac9a-4808-b2e4-a8817b6a288f',  #MARC
                                'default_control_channel': 0,
                                'channels': {
					0: 851312500,
					1: 854737500,
					2: 856087500,
					3: 857537500,
					4: 858187500,
					5: 858562500,
					6: 859062500,
					7: 859537500
				}
			}
		}
	
		#del self.systems[32]
		#del self.systems[31]
		del self.systems[30]
		#del self.systems[29]
		del self.systems[28]
		del self.systems[27]
		del self.systems[26]
		del self.systems[25]
		del self.systems[24]

		del self.systems[22]



		#del self.systems[18]
		#del self.systems[17]
		#del self.systems[16]
		del self.systems[15]
		del self.systems[14]


		del self.systems[11]
		del self.systems[10]
		
		del self.systems[8]
		del self.systems[7]
		#del self.systems[6]

		del self.systems[5]
		del self.systems[4]

		#del self.systems[3]
		#del self.systems[2]
		#del self.systems[1]

		del self.systems[0]

		
