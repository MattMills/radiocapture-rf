#!/usr/bin/env python

#(C) 2013 - Matt Mills
#Configuration File Structure (channel definitions)
#Changes:
# 4/28/2013 - Initial Creation
class rc_config:
	def __init__(self):
		self.receiver_split2 = False	#Does the frontend receiver split each inbound source by 1/2
		self.frontend_mode = 'xlat'
		self.scan_mode = False

                self.frontend_ip = '127.0.0.1'
                self.backend_ip = '127.0.0.1'
		
		self.if_gain = 0
		self.gain = 45
		self.samp_rate = 2000000

		self.site_uuid = '0bc6e731-6328-4119-b2f7-7687d7502e83'

		self.sources = {
			0:{
                                'type': 'rtlsdr',
                                'args': 'rtl=2-1,buffers=4',
                                'offset': 1640,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 851018000,
                                'samp_rate': self.samp_rate
                        },
                        1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=2-2,buffers=4',
                                'offset': 1600,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 852518000,
                                'samp_rate': self.samp_rate
                        },
                        2:{
                                'type': 'rtlsdr',
                                'args': 'rtl=2-3,buffers=4',
                                'offset': 1800,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 854018000,
                                'samp_rate': self.samp_rate
                        },
                        3:{
                                'type': 'rtlsdr',
                                'args': 'rtl=2-4,buffers=4',
                                'offset': 1960,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 855518000,
                                'samp_rate': self.samp_rate
                        },
			4:{
                                'type': 'rtlsdr',
                                'args': 'rtl=2-5,buffers=4',
                                'offset': 2110,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 857018000,
                                'samp_rate': self.samp_rate
                        },
			5:{
                                'type': 'rtlsdr',
                                'args': 'rtl=2-6,buffers=4',
                                'offset': 946,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 858518000,
                                'samp_rate': self.samp_rate
                        },
			6:{
				'type': 'rtlsdr',
                                'args': 'rtl=2-7,buffers=4',
                                'offset': 1950,
                                'bb_gain': 15,
                                'rf_gain': 39,
                                'center_freq': 859918000,
                                'samp_rate': self.samp_rate
                        },
			7:{
                                'type': 'rtlsdr',
                                'args': 'rtl=2-8,buffers=4',
                                'offset': 1340,
                                'bb_gain': 15,
                                'rf_gain': 39,
                                'center_freq': 859918000,
                                'samp_rate': self.samp_rate
                        },
		}

		self.systems = {
			0: { #DTRS - Templeton Gap (04-22
                                'type': 'p25',
                                'id': '04022',
				'transmit_site_uuid': '',
				'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 6,
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
			6: { #DTRS - Fountain Valley - 04-011
                                'type': 'p25',
                                'id': '04011',
				'transmit_site_uuid': '',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 7,
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
				'transmit_site_uuid': '1b61e8b3-3a03-4c11-ae3c-2e6766da5906',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 0,
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
			8: { #DTRS - Peterson Air Force BAse - 04-017
				'type': 'p25',
				'id': '04017',
				'transmit_site_uuid': '869e44ae-27e1-4b8e-933d-00108f9270cd',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
				'default_control_channel': 0,
				'modulation': 'C4FM',
				'channels': {
					0: 852262500,
					1: 855487500,
					2: 855737500,
					3: 856487500,
					4: 856737500,
					5: 857237500,
					6: 857737500,
					7: 858237500,
					8: 859237500,
				},
			},
			10: { #DTRS - Cedar Heights - 04-024
                                'type': 'p25',
                                'id': '04024',
				'transmit_site_uuid': '',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 11,
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
				'transmit_site_uuid': '7caa9228-ff85-45ba-8842-1b009c9fe10f',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 10,
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
			12: { #DTRS - Cheyenne Mountain - 06-048
                                'type': 'p25',
                                'id': '06048',
				'transmit_site_uuid': '23ef7d94-9034-4cb8-be60-147078d696ca',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
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
			14: { #DTRS - col springs simulcast - 04-028
				'type': 'p25',
				'id': '04028',
				'transmit_site_uuid': '6a57d644-a5a9-4b5f-bcff-fb79b6939616',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
				'default_control_channel': 0,
				'modulation': 'CQPSK',
				'channels': {
					0: 851875000,
					1: 851900000,
					2: 852075000,
					3: 852337500,
					4: 852400000,
					5: 852612500,
					6: 852637500,
					7: 852762500,
					8: 852800000,
					9: 853362500,
					10: 853387500,
					11: 853562500,
					12: 853637500,
					13: 853712500,
					14: 853762500,
					15: 853887500,
					16: 854112500,
					17: 857012500,
					18: 858612500,
					19: 859012500,
				}
			},
			15: {
				'type': 'p25',
                                'id': '06060',
				'transmit_site_uuid': '98086b66-9865-45c3-9245-af580eed34c2',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 0,
                                'modulation': 'C4FM',
                                'channels': {
                                        0: 852600000,
                                }
			},
			16: {
                                'type': 'p25',
                                'id': '06039',
				'transmit_site_uuid': '76053b69-c8a7-44d2-98a0-4d910a4eb0b6',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 0,
                                'modulation': 'C4FM',
                                'channels': {
                                        0: 859837500,
                                }
                        },
			17: {
                                'type': 'p25',
                                'id': '06001',
				'transmit_site_uuid': 'f6fa9a93-aec9-4ed5-b511-e2aed9c94121',
                                'system_uuid': 'ff38e81a-6aa6-4279-85fd-4e3cc448e007',
                                'default_control_channel': 0,
                                'modulation': 'CQPSK',
                                'channels': {
                                        0: 853987500,
                                }
                        }
		}


                del self.systems[0]
                #del self.systems[8]
                del self.systems[6]
                del self.systems[7]
                del self.systems[10]
		del self.systems[11]

		self.blacklists = {}

