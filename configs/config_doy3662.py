#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):

		self.sources = {
                        0:{
                                'type': 'rtlsdr',
				'serial': '0',
                                'args': 'numchan=1 rtl=0',
                                'center_freq': 502000000,
                                'samp_rate': 2800000,
                                'rf_gain': 30,
                                'bb_gain': 31
                        }
                }

		self.systems = {
			0:{#Backs County - South Simulcast (Site 2)
                                'type': 'moto',
                                'id': 0x710b,
                                'channels' : {
					0x17c: 501037500, #0x17c  0x0
	                                0x182: 501187500, #0x182  0x6
	                                0x183: 501212500, #0x183  0x7
	                                0x184: 501237500, #0x184  0x8
	                                0x185: 501262500, #0x185  0x9
	                                0x18b: 501412500, #0x18b  0xf
	                                0x192: 501587500, #0x192  0x16
	                                0x195: 501662500, #0x195  0x19
	                                0x199: 501762500  #0x199  0x1d
                                }
                        },
			1:{ #Bucks county - North simulcast (site 1)
				'type': 'moto',
				'id': 0x710a,
				'channels': {
					0x181: 501162500,
					0x189: 501362500,
					0x18f: 501512500,
					0x191: 501562500,
					0x198: 501737500
				}
			}
		}
		del self.systems[0]
		self.blacklists = {}
