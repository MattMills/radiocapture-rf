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


		self.sources = {
			0:{
                                'type': 'bladerf',
				'args': 'numchan=1 bladerf,fpga=/home/mmills/hostedx40.rbf',
                                'center_freq': 855175000,
                                'samp_rate': 12000000,
                                'rf_gain': 2,
				'bb_gain': 33
                        }
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
		}
