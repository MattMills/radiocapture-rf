#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):

                self.sources = {
                        0:{
                                'type': 'usrp2x',
                                #'device_addr': "recv_frame_size=49152,num_recv_frames=512,serial=E2R10Z3B1",
                                'device_addr': "fpga=/usr/local/share/uhd/images/usrp_b100_fpga_2rx.bin,recv_frame_size=49152,num_recv_frames=512,serial=EDR11Y7B1",
                                'otw_format': 'sc8',
                                'args': 'peak=0.35',
                                'center_freq': 864700000,
                                'samp_rate': 8000000,
                                'rf_gain': 7
                        },
                        1:{
                                'type': 'usrp2xb',
                                'center_freq': 858000000,
                                'samp_rate': 8000000,
                                'rf_gain': 7
                        }
                }


		self.systems = {
			0:{#San Diego - South Zone (1)
                                'type': 'moto',
                                'id': 0x470f,
                                'channels' : {
		                        0x259: 866037500,
		                        0x25d: 866137500,
		                        0x268: 866412500,
		                        0x269: 866437500,
		                        0x271: 866637500,
		                        0x27b: 866887500,
		                        0x27c: 866912500,
		                        0x282: 867062500,
		                        0x285: 867137500,
		                        0x28f: 867387500,
		                        0x290: 867412500,
		                        0x298: 867612500,
		                        0x299: 867637500,
		                        0x2a4: 867912500,
		                        #0x: 868075000, #doesnt show up on unitrunker list
		                        0x2ad: 868137500,
		                        0x2b8: 868412500,
		                        0x2b9: 868437500#,
		                        #868600000 #this either
                                }
                        },
			1:{#San Diego City - Site 1
				'type': 'moto',
                                'id': 0x2b2e,
                                'channels' : {
		                        0xc9: 856025000,
		                        0xca: 856050000,
		                        0xcb: 856075000,
		                        0xf0: 857000000,
		                        0xf1: 857025000,
		                        0xf2: 857050000,
		                        0x118: 858000000,
		                        0x119: 858025000,
		                        0x11a: 858050000,
		                        0x140: 859000000,
		                        0x141: 859025000,
		                        0x141: 859050000,
		                        0x168: 860000000,
		                        0x169: 860025000,
		                        0x16a: 860050000,
		                        0x1ba: 862050000,
		                        0x1bc: 862100000,
		                        0x1e2: 863050000,
		                        0x20a: 864050000,
		                        0x232: 865050000
	
				}
			}
		}


