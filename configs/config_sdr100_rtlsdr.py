#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):
                self.receiver_split2 = False    #Does the frontend receiver split each inbound source by 1/2
		self.samp_rate = 2850000
		self.gain = 46
		self.if_gain = 15 

		self.sources = {
			0:{'serial': 0},
			1:{'serial': 1},
			2:{'serial': 2}
		}
		self.center_freq = {
			0: 867500000,
			1: 855825000,
			2: 858742500
		}


		self.systems = {
			0:{#San Bernadino County 06/7
				'type': 'moto',
				'id': 0x3c33,
				'channels' : {
	                                0x99: 854837500,
	                                0xa7: 855187500,
	                                0xb0: 855412500,
	                                0xb1: 855437500,
	                                0xb7: 855587500,
	                                0xb8: 855612500,
	                                0xba: 855662500,
	                                0xc2: 855862500,
	                                0xe8: 856812500,
	                                0x110: 857812500,
	                                0x161: 859837500,
	                                #0x188: 860812500,
	                                0x265: 866337500,
	                                0x267: 866387500,
	                                0x270: 866612500,
	                                0x279: 866837500,
	                                0x27b: 866887500,
	                                0x286: 867162500,
	                                0x28e: 867362500,
	                                0x290: 867412500,
	                                0x299: 867637500,
	                                0x29b: 867687500,
	                                0x2a3: 867887500,
	                                0x2ae: 868162500,
	                                0x2b5: 868337500,
	                                0x2b7: 868387500,
	                                0x2c0: 868612500,
	                                0x2c2: 868662500
				}
			},
			1:{#San Bernadino County 08
				'type': 'moto',
				'id': 0x363f,
				'channels' : {
	                                0xfe: 857362500,
	                                0x14f: 859387500,
	                                0x160: 859812500,
	                                #0x189: 860837500,
	                                0x25f: 866187500,
	                                0x273: 866687500,
	                                0x284: 867112500,
	                                0x28d: 867337500,
        	                        0x2a1: 867837500,
	                                0x2ac: 868112500,
	                                0x2c3: 868687500,
	                                0x2cc: 868912500
				}
			},
			2:{#San Bernadino County 09
				'type': 'moto',
				'id': 0x262c,
				'channels' : {
	                                #014x: 851500000, #Not valid standard, valid splinter
	                                #0x62: 853450000, #Not valid standard, valid splinter
        	                        0xd9: 856425000, #Not Valid standard, valid splinter
	                                0x25d: 866137500,
	                                0x25e: 866162500,
	                                0x266: 866362500,
	                                0x271: 866637500,
	                                0x27a: 866862500,
	                                0x27c: 866912500,
	                                0x285: 867137500,
	                                0x28f: 867387500,
	                                0x298: 867612500,
	                                0x29a: 867662500,
	                                0x2a2: 867862500,
	                                0x2a4: 867912500,
	                                0x2ad: 868137500,
	                                0x2af: 868187500,
	                                0x2b6: 868362500,
	                                0x2b8: 868412500,
	                                0x2c1: 868637500,
	                                0x2c9: 868837500#,
	                                #0x2cd: 868937500
				}
			},
			3:{# CCCS Countywide
				'type': 'moto',
                                'id': 0x6c3f,
				'channels' : {
	                                #0x??: 851062500,
	                               0xbc:  855712500,
	                               0xd0:  856212500,
	                               0xda:  856462500,
	                               0xe4:  856712500,
	                               0xee:  856962500,
	                               0xf8:  857212500,
	                               0x102: 857462500,
	                               0x10c: 857712500,
	                               0x116: 857962500,
	                               0x120: 858212500,
	                               0x12a: 858462500,
	                               0x134: 858712500,
	                               0x13e: 858962500,
	                               0x148: 859212500,
	                               0x152: 859462500,
	                               0x15c: 859712500,
	                               0x166: 859962500
	                               #0x170: 860212500,
	                               #0x17a: 860462500,
	                               #0x184: 860712500,
	                               #0x18e: 860962500
				}
			},
			4:{#Riverside EDACS - West site
				'type': 'edacs',
				'id': 1,
				'symbol_rate': 9600.0,
				'esk': False,
				'channels': {
	                                1: 866212500,
	                                2: 866262500,
	                                3: 866712500,
	                                4: 866762500,
	                                5: 867212500,
	                                6: 867712500,
	                                7: 868212500,
	                                8: 867262500,
	                                9: 868262500,
	                                10: 868712500,
	                                11: 867787500,
	                                12: 868787500
				}
			}
		}

		del self.systems[4]
