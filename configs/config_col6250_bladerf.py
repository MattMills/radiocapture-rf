#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):
		self.receiver_split2 = True	#Does the frontend receiver split each inbound source by 1/2
		self.frontend_mode = 'xlat'

                self.frontend_ip = '127.0.0.1'
                self.backend_ip = '127.0.0.1'


		self.sources = {
			0:{
				'type': 'bladerf',
				#'args': 'bladerf=0,fpga=/home/mmills/build/hostedx40.rbf,buffers=4096,buflen=65536,transfers=15,stream_timeout_ms=30000,verbosity=debug',
				'args': 'bladerf=0,fpga=/root/hostedx40.rbf,fpga-reload=1',
				'center_freq': 856000000,
				'samp_rate': 10000000,
				'rf_gain': 1,
				'bb_gain': 35
			},
		}

		self.systems = {
			0: { #DTRS - Templeton Gap (04-22
                                'type': 'p25',
                                'id': '04022',
                                'default_control_channel': 5,
				'modulation': 'C4FM',
                                'channels': {
                                        0: 852637500,
					1: 854112500,
					2: 854287500,
					3: 854462500,
					4: 855237500,
					5: 855937500,
					6: 856237500,
					7: 856462500,
					
                                },
			},
			#1: { #DTRS - Austin Bluffs - 4-016
                        #        'type': 'p25',
                        #        'id': '04016',
                        #        'default_control_channel': 0,
                        #        'modulation': 'C4FM',
                        #        'channels': {
                        #                0: 851075000,
			#		1: 852275000,
			#		2: 852337500,
			#		3: 852762500,
			#		4: 852800000,
			#		5: 853075000,
			#		6: 853362500,
			#		7: 853562500,
			#		8: 853637500,
			#		9: 853762500,
			#		10: 853887500,
                        #        },
                        #},
			#2: { #DTRS - Black Forest - 04-021
			#	'type': 'p25',
                        #        'id': '04021',
                        #        'default_control_channel': 0,
                        #        'modulation': 'C4FM',
                        #        'channels': {
                        #                0: 854262500,
			#		1: 855212500,
			#		2: 855712500,
			#		3: 856462500,
			#		4: 857212500,
			#		5: 858437500,
			#		6: 859437500,
                        #        },
			#},
			#3: { #DTRS - Calhan - 04-014
                        #        'type': 'p25',
                        #        'id': '04014',
                        #        'default_control_channel': 0,
                        #        'modulation': 'C4FM',
                        #        'channels': {
                        #                0: 851125000,
			#		1: 851700000,
			#		2: 852212500,
			#		3: 853125000,
			#		4: 853825000,
                        #        },
			#},
			#4: { #DTRS - Truckton - 04-019
                        #        'type': 'p25',
                        #        'id': '04019',
                        #        'default_control_channel': 0,
                        #        'modulation': 'C4FM',
                        #        'channels': {
                        #                0: 853800000,
			#		1: 857487500,
			#		2: 858487500,
			#		3: 859487500,
                        #        },
			#},
			5: { #DTRS - Airport - 04-017
                                'type': 'p25',
                                'id': '04017',
                                'default_control_channel': 8,
                                'modulation': 'C4FM',
                                'channels': {
                                        0: 852262500,
					1: 855485700,
					2: 855737500,
					3: 856487500,
					4: 856737500,
					5: 857237500,
					6: 857737500,
					7: 858237500,
					8: 859237500,
                                },
			},
			6: { #DTRS - Fountain Valley - 04-011
                                'type': 'p25',
                                'id': '04011',
                                'default_control_channel': 6,
                                'modulation': 'C4FM',
                                'channels': {
                                        0: 851375000,
					1: 852112500,
					2: 854712500,
					3: 856762500,
					4: 856987500,
					5: 857987500,
					6: 858987500,
					7: 859987500,
                                },
			},
			7: { #DTRS - Ski Summit - 04-013
                                'type': 'p25',
                                'id': '04013',
                                'default_control_channel': 13,
                                'modulation': 'C4FM',
                                'channels': {
                                        0: 854387500,
					1: 856012500,
					2: 856937500,
					3: 856962500,
					4: 857762500,
					5: 857937500,
					6: 857962500,
					7: 858612500,
					8: 858762500,
					9: 858937500,
					10: 858962500,
					11: 859762500,
					12: 859937500,
					13: 859962500,
                                },
			},
			8: { #DTRS - Cheyenne Mountain - 06-048
                                'type': 'p25',
                                'id': '06048',
                                'default_control_channel': 4,
                                'modulation': 'C4FM',
                                'channels': {
                                        0: 851050000,
					1: 851200000,
					2: 851387500,
					3: 851725000,
					4: 852787500,
					5: 853050000,
					6: 854362500,
					7: 854662500,
					8: 855287500,
					9: 856062500,
					10: 856662500,
					11: 856837500,
                                },
			},
			#9: { #DTRS - Mt Pittsburg - 04-018
                        #        'type': 'p25',
                        #        'id': '04018',
                        #        'default_control_channel': 0,
                        #        'modulation': 'C4FM',
                        #        'channels': {
                        #                0: 851287500,
			#		1: 852050000,
			#		2: 852637500,
			#		3: 853187500,
			#		4: 853662500,
			#		5: 853737500,
                        #        },
			#},
			10: { #DTRS - Cedar Heights - 04-024
                                'type': 'p25',
                                'id': '04024',
                                'default_control_channel': 10,
                                'modulation': 'C4FM',
                                'channels': {
                                        0: 851612500,
					1: 851900000,
					2: 854012500,
					3: 854162500,
					4: 854337500,
					5: 854487500,
					6: 855087500,
					7: 856812500,
					8: 857912500,
					9: 858812500,
					10: 859812500,
					11: 860812500,
                                },
			},
			11: { #DTRS - Stanley Canyon - 04-012
                                'type': 'p25',
                                'id': '04012',
                                'default_control_channel': 9,
                                'modulation': 'C4FM',
                                'channels': {
                                        0: 851550000,
					1: 851675000,
					2: 851875000,
					3: 852075000,
					4: 852400000,
					5: 852612500,
					6: 852850000,
					7: 853100000,
					8: 853387500,
					9: 853462500,
					10: 853712500,
                                },
			},
			#12: { #DTRS - Woodland Park - 04-015
                        #        'type': 'p25',
                        #        'id': '04015',
                        #        'default_control_channel': 0,
                        #        'modulation': 'C4FM',
                        #        'channels': {
                        #                0: 851575000,
			#		1: 851812500,
			#		2: 852425000,
			#		3: 852675000,
			#		4: 853262500,
			#		5: 859737500,
                        #        },
			#}
		}

		del self.systems[0]
		del self.systems[8]
		del self.systems[5]
		del self.systems[7]
		#del self.systems[10]
		#del self.systems[11]
		self.blacklists = {}

