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

                self.site_uuid = 'none'

		self.samp_rate = 2400000
		self.gain = 28
		self.if_gain = 20

		self.sources = {
			0:{
				'type': 'rtlsdr', 
				'args': 'rtl=3-1,buffers=4',
				'offset': 0,
				'bb_gain': self.if_gain,
				'rf_gain': self.gain,
				'center_freq': 770000000, 
				'samp_rate': self.samp_rate
			},
			1:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-2,buffers=4',
				'offset': 0,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 772000000,
                                'samp_rate': self.samp_rate
                        },
                        2:{
                                'type': 'rtlsdr',
                                'args': 'rtl=3-3,buffers=4',
				'offset': 0,
                                'bb_gain': self.if_gain,
                                'rf_gain': self.gain,
                                'center_freq': 774000000,
                                'samp_rate': self.samp_rate
                        },
			

		}


		self.systems = {
                        0: {
                                'type': 'p25',
                                'id': '1-001',
                                'default_control_channel': 0,
                                'channels': {
					0: 769256250,
					1: 769268750,
					2: 769506250,
					3: 769518750,
					4: 770556250,
					5: 770806250,
					6: 770818750,
					7: 771106250,
					8: 771118750,
					9: 771681250,
					10: 771693750,
					11: 771981250,
					12: 771993750,
					13: 772331250,
					14: 772343750,
					15: 772656250,
					16: 772981250,
					17: 772993750,
					18: 773231250,
					19: 773243750,
					20: 773881250,
					21: 773893750,
					22: 774656250,
					23: 774668750,
                                }
                        },
		}

		
