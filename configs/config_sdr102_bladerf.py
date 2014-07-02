#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):
		self.receiver_split2 = True	#Does the frontend receiver split each inbound source by 1/2

                self.frontend_ip = '127.0.0.1'
                self.backend_ip = '127.0.0.1'


		self.sources = {
			0:{
				'type': 'bladerf',
				'args': 'numchan=1 bladerf=0,fpga=/home/mmills/build/hostedx40.rbf,buffers=4096,buflen=65536,transfers=15,stream_timeout_ms=30000,verbosity=debug',
				#'center_freq': 476812500,
				#'samp_rate': 16000000,
				'center_freq': 467060500,
				'samp_rate': 32000000,
				#'center_freq': 470050000,
				#'samp_rate': 400000,
				'rf_gain': 0,
				'bb_gain': 15
			},
			1:{
                                'type': 'bladerf',
                                'args': 'numchan=1 bladerf=1,fpga=/home/mmills/build/hostedx40.rbf,buffers=4096,buflen=65536,transfers=15,stream_timeout_ms=30000,verbosity=debug',
                                'center_freq': 457975000,
                                'samp_rate': 16000000,
                                'rf_gain': 4,
                                'bb_gain': 9
                        }
		}
		del self.sources[1]

		self.systems = {
			2: { #ICIS P25 RFSS1 SITE10 - Pasadena
                                'type': 'p25',
                                'id': 1010,
                                'default_control_channel': 0,
				'modulation': 'CQPSK',
                                'channels': {
                                        0: 477012500,
                                        1: 477112500,
                                        2: 477162500,
                                        3: 477212500,
                                        4: 477262500,
                                        5: 477312500,
                                        6: 477362500,
                                        7: 477412500,
                                        8: 477462500,
                                        9: 477512500,
                                        10: 477562500,
                                        11: 477612500,
					12: 477662500,
					13: 477712500,
					14: 477812500
                                },
			},
			1: { #ICIS P25 RFSS1 SITE11 - Glendale
                                'type': 'p25',
                                'id': 1011,
                                'default_control_channel': 0,
                                'modulation': 'CQPSK',
                                'channels': {
                                        0: 470262500,
                                        1: 482187500,
                                        2: 482237500,
                                        3: 482287500,
                                        4: 484187500
                                },
                        
                  	},
			0: { #ICIS P25 RFSS1 SITE15 - Pomona
                                'type': 'p25',
                                'id': 1015,
                                'default_control_channel': 0,
                                'modulation': 'CQPSK',
                                'channels': {
                                        0: 470025000,
                                        1: 470050000,
                                        2: 470100000,
                                        3: 470162500,
                                        4: 482162500,
					5: 482362500
                                },

                        },
			3: { #ICIS P25 RFSS1 SITE16 - Beverly Hills
                                'type': 'p25',
                                'id': 1016,
                                'default_control_channel': 0,
                                'modulation': 'CQPSK',
                                'channels': {
                                        0: 482125000,
                                        1: 482200000,
                                        2: 482225000,
                                        3: 482400000,
                                        4: 482625000
                                },

                        },
			4: { #ICIS P25 RFSS1 SITE19 - Glendora
                                'type': 'p25',
                                'id': 1019,
                                'default_control_channel': 0,
                                'modulation': 'CQPSK',
                                'channels': {
                                        0: 451175000,
					1: 451350000,
					2: 451425000,
					3: 451600000,
					4: 451787500,
					5: 451837500,
					6: 451900000,
					7: 451937500,
					8: 452150000,
					9: 452800000,
					10: 461487500,
					11: 463237500
                                },

                        },
			5: {
				'type': 'scanner',
				'id': '12345',
				'default_control_channel': 0,
				'modulation': 'analog',
				'threshold': -30,
				'channels': {
					0: 470537500
				}
			},
			6: {   
                                'type': 'scanner',
                                'id': '12345',
                                'default_control_channel': 0,
                                'modulation': 'analog',
                                'threshold': -30,
                                'channels': {
                                        0: 470412500
                                }
                        },
			7: {
                                'type': 'scanner',
                                'id': '12346',
                                'default_control_channel': 0,
                                'modulation': 'p25',
                                'threshold': -30,
                                'channels': {
                                        0: 451812500
                                }
                        },
		}
		del self.systems[1]
		del self.systems[2]
		del self.systems[3]

		del self.systems[0]
		del self.systems[4]

		del self.systems[5]
		del self.systems[6]
		self.blacklists = {}

