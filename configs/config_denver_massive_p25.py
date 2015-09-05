#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):
                self.receiver_split2 = False    #Does the frontend receiver split each inbound source by 1/2

                self.frontend_ip = '127.0.0.1'
                self.backend_ip = '127.0.0.1'


		self.sources = {
			0:{
                                'type': 'bladerf',
				'args': 'numchan=1 bladerf,fpga=/home/mmills/build/hostedx115.rbf,num_samples=1048576,num_transfers=65536,num_buffers=65536',
                                'center_freq': 855500000,
                                'samp_rate': 10666666,
                                'rf_gain': 2,
				'bb_gain': 18
                        },
			1:{
                                'type': 'usrp',
                                'device_addr': "recv_frame_size=24576,num_recv_frames=512,serial=E2R10Z3B1",
                                #'device_addr': "serial=E2R10Z3B1",
                                'otw_format': 'sc8',
                                'args': '',
                                'center_freq': 771500000,
                                'samp_rate': 10666666,
                                'rf_gain': 3
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
                        3: { #Betasso	3	32
                                'type': 'p25',
                                'id': 3032,
                                'default_control_channel': 0,
                                'channels': {
					0: 852137500,
					1: 852975000,
					2: 853250000,
					3: 853500000,
					4: 853950000

                                }
                        },
                        4: { #Byers	1	73
                                'type': 'p25',
                                'id': 1073,
                                'default_control_channel': 0,
                                'channels': {
					0: 769593750,
					1: 770293750,
					2: 771243750,
					3: 772318750,
					4: 773143750,
					5: 774493750

                                }
                        },
                        5: { #Chevron Plaza Tower (Denver Metro)	1	64
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
                        6: { #Denver TX (Denver Metro)	1	20
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
                        7: { #DRDC CF	1	9
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
                        8: { #Fort Lupton	3	55
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
                        9: { #FrankTown (Denver Metro)	1	10
                                'type': 'p25',
                                'id': 1010,
                                'default_control_channel': 0,
                                'channels': {
					0: 852137500,
					1: 852975000,
					2: 853250000,
					3: 853500000,
					4: 853950000

                                }
                        },
                        10: { #Gunbarrel	3	54
                                'type': 'p25',
                                'id': 3054,
                                'default_control_channel': 0,
                                'channels': {
					0: 769293750,
					1: 770306250,
					2: 771156250,
					3: 771406250,
					4: 771706250,
					5: 772031250,
					6: 772356250,
					7: 773881250,
					8: 774881250

                                }
                        },
                        11: { #Longmont	3	56
                                'type': 'p25',
                                'id': 3056,
                                'default_control_channel': 0,
                                'channels': {
					0: 769281250,
					1: 769556250,
					2: 771581250,
					3: 772656250,
					4: 772918750,
					5: 774206250
                                }
                        },
                        12: { #Lookout Mountain (Denver Metro)	1	8
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
                        13: { #Riley Peak (Denver Metro)	1	2
                                'type': 'p25',
                                'id': 1002,
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
					14: 858012500

                                }
                        },
                        14: { #Silver Heights (Denver Metro)	1	3
                                'type': 'p25',
                                'id': 1003,
                                'default_control_channel': 0,
                                'channels': {
					0: 851300000,
					1: 851825000,
					2: 852137500,
					3: 852387500,
					4: 852700000,
					5: 852925000,
					6: 853200000,
					7: 853525000
                                }
                        },
                        15: { #Smoky Hill (Denver Metro)	1	7
                                'type': 'p25',
                                'id': 1007,
                                'default_control_channel': 0,
                                'channels': {
					0: 769581250,
					1: 770856250,
					2: 771856250,
					3: 772756250,
					4: 773668750,
					5: 851112500,
					6: 851275000,
					7: 851450000,
					8: 851737500,
					9: 852150000,
					10: 852287500,
					11: 852475000,
					12: 852712500,
					13: 853175000,
					14: 853400000,
					15: 853625000,
					16: 853875000,
					17: 857037500,
					18: 857512500
                                }
                        },
                        16: { #Southeast Weld	3	58
                                'type': 'p25',
                                'id': 3058,
                                'default_control_channel': 0,
                                'channels': {
					0: 771531250,
					1: 771831250,
					2: 772081250,
					3: 772381250,
					4: 773156250,
					5: 773406250
                                }
                        },
                        17: { #State Capitol (Denver Metro)	1	71
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
                        18: { #Zap (Denver Metro)	1	47
                                'type': 'p25',
                                'id': 1047,
                                'default_control_channel': 0,
                                'channels': {
					0: 774306250,
					1: 774556250,
					2: 774806250,
					3: 851212500,
					4: 851537500,
					5: 852037500,
					6: 852350000,
					7: 852662500,
					8: 853512500

                                }
                        },

		}
		del self.systems[3]
		del self.systems[9]
		del self.systems[4]
		del self.systems[11]
		del self.systems[16]
		del self.systems[13]
		del self.systems[10]
		del self.systems[14]
		del self.systems[18]
		del self.systems[15]
