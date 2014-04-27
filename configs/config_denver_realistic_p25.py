#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):
                self.receiver_split2 = False    #Does the frontend receiver split each inbound source by 1/2
		self.sources = {
			0:{
                                'type': 'bladerf',
				'args': 'numchan=1 bladerf=0,fpga=/home/mmills/build/hostedx40.rbf,num_samples=1048576,num_transfers=65536,num_buffers=65536',
                                'center_freq': 771000000,#855500000,
                                'samp_rate': 12000000,
                                'rf_gain': 4,
				'bb_gain': 9
                        },
			1:{
				'type': 'bladerf',
				'args': 'numchan=1 bladerf=1,fpga=/home/mmills/build/hostedx40.rbf,num_samples=1048576,num_transfers=65536,num_buffers=65536',
                                'center_freq': 856000000,
                                'samp_rate': 12000000,
                                'rf_gain': 4,
                                'bb_gain': 9
                        }
		}
                self.systems = {
                        0: { #Adams County Simulcast (Denver Metro)	3	22
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
                        1: { #Arapahoe Admin (Denver Metro)	1	1
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
                        2: { #Auraria Campus (Denver Metro)	1	70
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
                        3: { #Chevron Plaza Tower (Denver Metro)	1	64
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
                        4: { #Denver TX (Denver Metro)	1	20
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
                        5: { #DRDC CF	1	9
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
                        6: { #Fort Lupton	3	55
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
                        7: { #Lookout Mountain (Denver Metro)	1	8
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
                        8: { #State Capitol (Denver Metro)	1	71
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
			10: {
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
			11: {
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
			12: {
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
			13: {

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
		self.blacklists = {
			0xbee07: [
997,
998,
999,
1000,
1433,
1435,
1437,
1439,
2308,
2309,
2311,
2313,
2315,
2317,
2463,
2465,
2467,
2469,
2471,
2473,
2491,
2492,
2493,
2494,
2495,
2496,
2497,
2498,
2502,
2503,
2504,
2505,
2506,
2507,
2508,
2509,
2510,
2511,
2512,
2513,
2514,
2515,
2516,
2517,
2518,
2818,
3050,
3088,
3091,
3092,
3093,
4131,
4132,
4133,
4141,
4143,
9018,
10004,
10005,
10006,
10007,
10008,
10041,
10042,
10043,
10044,
10072,
10088,
10089,
10094,
10095,
12002,
12003,
12004,
12016,
12018,
12019,
12020,
12026,
12027,
12028
			]
		}
		self.blacklists[3022] = self.blacklists[0xbee07]
		self.blacklists[1001] = self.blacklists[0xbee07]
		self.blacklists[1070] = self.blacklists[0xbee07]
		self.blacklists[1064] = self.blacklists[0xbee07]
		self.blacklists[1020] = self.blacklists[0xbee07]
		self.blacklists[1009] = self.blacklists[0xbee07]
		self.blacklists[3055] = self.blacklists[0xbee07]
		self.blacklists[1008] = self.blacklists[0xbee07]
		self.blacklists[1071] = self.blacklists[0xbee07]

		#del self.systems[0]
                

		#del self.systems[1]
                

		#del self.systems[2]
                #del self.systems[4]
                #del self.systems[6]
                #del self.systems[7]
                #del self.systems[8]

		#del self.systems[3]
		

		#del self.systems[5]
		#del self.systems[10]
		#del self.systems[11]
		#del self.systems[12]
		#del self.systems[13]
	
