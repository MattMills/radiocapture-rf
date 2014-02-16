#!/usr/bin/env python

#(C) 2012 - Matt Mills
#P25 Protocol Definitions
#Changes:
#9/9/12 - Added tsbk_osp packet definitions (Single Message only)
class p25_cai:
 tsbk_osp_single =  {
  #Dictionary of single message OSPs

  #VOICE SERVICE OSPs
  0b000000 : 
  { 
   'name' : 'GRP_V_CH_GRANT', 
   'long_name' : 'Group Voice Channel Grant', 
   'fields' : 
   [ 
    {
     'name'  : 'Service Options',
     'length' : 8
    },
    {
     'name'  : 'Channel',
     'length' : 16
    },
    {
     'name'  : 'Group Address',
     'length' : 16
    },
    {
     'name'  : 'Source Address',
     'length' : 24
    }
   ]
  },

  0b000010 : 
  {
   'name' : 'GRP_V_CH_GRANT_UPDT', 
   'long_name' : 'Group Voice Channel Grant Update', 
   'fields' : 
   [
    {
     'name'   : 'Channel 0', #Name Modified from "Channel"
     'length' : 16
    },
    {
     'name'   : 'Group Address 0', #Name Modified from "Group Address"
     'length' : 16
    },
    {
     'name'   : 'Channel 1', #Name Modified from "Channel"
     'length' : 16
    },
    {
     'name'   : 'Group Address 1', #Name Modified from "Group Address"
     'length' : 16
    }
   ]

  },

  0b000011 :
  {
   'name' : 'GRP_V_CH_GRANT_UPDT_EXP',
   'long_name' : 'Group Voice Channel Update-Explicit',
   'fields' :
   [
    {
     'name'   : 'Service Options',
     'length' : 8
    },
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'Channel (T)',
     'length' : 16
    },
    {
     'name'   : 'Channel (R)',
     'length' : 16
    },
    {
     'name'   : 'Group Address',
     'length' : 16
    }
   ]
  },

  0b000100 : 
  {
   'name' : 'UU_V_CH_GRANT', 
   'long_name' : 'Unit To Unit Voice Channel Grant', 
   'fields' : 
   [
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },

  0b000101 : 
  {
   'name' : 'UU_ANS_REQ', 
   'long_name' : 'Unit To Unit Answer Request', 
   'fields' : 
   [
    {
     'name'   : 'Service Options',
     'length' : 8
    },
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    },
    {
     'name'   : 'Source ID',
     'length' : 24
    }
   ]
  },
  0b000110 :
  {
   'name' : 'UU_V_CH_GRANT_UPDT',
   'long_name' : 'Unit to Unit Voice Channel Grant Update',
   'fields' :
   [
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b001000 :
  {
   'name' : 'TELE_INT_CH_GRANT',
   'long_name' : 'Telephone Interconnect Voice Channel Grant',
   'fields' :
   [
    {
     'name'   : 'Service Options',
     'length' : 8
    },
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'Call Timer',
     'length' : 16
    },
    {
     'name'   : 'Source Address / Target Address',
     'length' : 24
    },
   ]
  },
  0b001001 :
  {
   'name' : 'TELE_INT_CH_GRANT_UPDT',
   'long_name' : 'Telephone Interconnect Voice Channel Grant Update',
   'fields' :
   [
    {
     'name'   : 'Service Options',
     'length' : 8
    },
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'Call Timer',
     'length' : 16
    },
    {
     'name'   : 'Source Address / Target Address',
     'length' : 24
    }
   ]
  },
  0b001010 :
  {
   'name' : 'TELE_INT_ANS_REQ',
   'long_name' : 'Telephone Interconnect Answer Request',
   'fields' :
   [
    {
     'name'   : 'Digit 1',
     'length' : 4
    },
    {
     'name'   : 'Digit 2',
     'length' : 4
    },
    {
     'name'   : 'Digit 3',
     'length' : 4
    },
    {
     'name'   : 'Digit 4',
     'length' : 4
    },
    {
     'name'   : 'Digit 5',
     'length' : 4
    },
    {
     'name'   : 'Digit 6',
     'length' : 4
    },
    {
     'name'   : 'Digit 7',
     'length' : 4
    },
    {
     'name'   : 'Digit 8',
     'length' : 4
    },
    {
     'name'   : 'Digit 9',
     'length' : 4
    },
    {
     'name'   : 'Digit 10',
     'length' : 4
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },

  #Data Service OSPs
  0b010000 :
  {
   'name' : 'IND_DATA_CH_GRANT',
   'long_name' : 'Individual Data Channel Grant (OBSOLETE)',
   'fields' :
   [
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b010001 :
  {
   'name' : 'GRP_DATA_CH_GRANT',
   'long_name' : 'Group Data Channel Grant (OBSOLETE)',
   'fields' :
   [
    {
     'name'   : 'Service Options',
     'length' : 8
    },
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'Group Address',
     'length' : 16
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b010010 :
  {
   'name' : 'GRP_DATA_CH_ANN',
   'long_name' : 'Group Data Channel Announcement (OBSOLETE)',
   'fields' :
   [
    {
     'name'   : 'Channel 0', #Name Modified from "Channel"
     'length' : 16
    },
    {
     'name'   : 'Group Address 0', #Name Modified from "Group Address"
     'length' : 16
    },
    {
     'name'   : 'Channel 1', #Name Modified from "Channel"
     'length' : 16
    },
    {
     'name'   : 'Group Address 1', #Name modified from "Group Address"
     'length' : 16
    }
   ]
  },
  0b010011 :
  {
   'name' : 'GRP_DATA_CH_ANN_EXP',
   'long_name' : 'Group Data Channel Announcement Explicit (OBSOLETE)',
   'fields' :
   [
    {
     'name'   : 'Service Options',
     'length' : 8
    },
    {
     'name'   : 'Reserved',
     'length' : 8
    },
    {
     'name'   : 'Channel (T)',
     'length' : 16
    },
    {
     'name'   : 'Channel (R)',
     'length' : 16
    },
    {
     'name'   : 'Group Address',
     'length' : 16
    }
   ]
  },
  0b010100 :
  {
   'name' : 'SN-DATA_CHN_GNT',
   'long_name' : 'SNDCP Data Channel Grant',
   'fields' :
   [
    {
     'name'   : 'Data Service Options',
     'length' : 8
    },
    {
     'name'   : 'Channel (T)',
     'length' : 16
    },
    {
     'name'   : 'Channel (R)',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },
  0b010101 :
  {
   'name' : 'SN-DATA_PAGE_REQ',
   'long_name' : 'SNDCP Data Page Request',
   'fields' :
   [
    {
     'name'   : 'Data Service Options',
     'length' : 8
    },
    {
     'name'   : 'reserved',
     'length' : 16
    },
    {
     'name'   : 'Data Access Control',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },
  0b010110 :
  {
   'name' : 'SN-DATA_CHN_ANN_EXP',
   'long_name' : 'SNDCP Data Channel Announcement - Explicit',
   'fields' : 
   [
    {
     'name'   : 'Data Service Options',
     'length' : 8
    },
    {
     'name'   : 'AA',
     'length' : 1
    },
    {
     'name'   : 'RA',
     'length' : 1
    },
    {
     'name'   : 'reserved',
     'length' : 6
    },
    {
     'name'   : 'Channel (T)',
     'length' : 16
    },
    {
     'name'   : 'Channel (R)',
     'length' : 16
    },
    {
     'name'   : 'Data Access Control',
     'length' : 16
    }
   ]
  },

  #Control and Status OSPs
  0b011000 :
  {
   'name' : 'STS_UPDT',
   'long_name' : 'Status Update',
   'fields' :
   [
    {
     'name'   : 'Status',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24 
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b011010 :
  {
   'name' : 'STS_Q',
   'long_name' : 'Status Query',
   'fields' :
   [
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b011100 :
  {
   'name' : 'MSG_UPDT',
   'long_name' : 'Message Update',
   'fields' :
   [
    {
     'name'   : 'Message',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b011101 :
  {
   'name' : 'RAD_MON_CMD',
   'long_name' : 'Radio Unit Monitor Command',
   'fields' :
   [
    {
     'name'   : 'TX Time',
     'length' : 8
    },
    {
     'name'   : 'SM',
     'length' : 1
    },
    {
     'name'   : 'Reserved',
     'length' : 5
    },
    {
     'name'   : 'TX Multiplier',
     'length' : 2
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },

  #RAD_MON_ENH_CMD has been removed as its "abbreviated" structure is multi-packet
  #0b011110 :
  #{a
  # 'name' : 'RAD_MON_ENH_CMD',
  # 'long_name' : 'Radio Unit Monitor Enhanced Command',
  # 'fields' :
  # [
  #  {
  #   'name'   : '',
  #   'length' : 
  #  },
  # ]
  #},
  0b011111 :
  {
   'name' : 'CALL_ALRT',
   'long_name' : 'Call Alert',
   'fields' :
   [
    {
     'name'   : 'reserved',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b100000 :
  {
   'name' : 'ACK_RSP_FNE',
   'long_name' : 'Acknowledge Response - FNE',
   'fields' :
   [
    {
     'name'   : 'AIV',
     'length' : 1
    },
    {
     'name'   : 'EX',
     'length' : 1
    },
    {
     'name'   : 'Service Type',
     'length' : 6
    },
    {
     'name'   : 'Additional Information',
     'length' : 32
    },
    {
     'name'   : 'Target Address / ID',
     'length' : 24
    }
   ]
  },
  0b100001 :
  {
   'name' : 'QUE_RSP',
   'long_name' : 'Queued Response',
   'fields' :
   [
    {
     'name'   : 'AIV',
     'length' : 1
    },
    {
     'name'   : '0',
     'length' : 1
    },
    {
     'name'   : 'Service Type',
     'length' : 6
    },
    {
     'name'   : 'Reason Code',
     'length' : 8
    },
    {
     'name'   : 'Additional Information',
     'length' : 24
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },
  0b100100 :
  {
   'name' : 'EXT_FNCT_CMD',
   'long_name' : 'Extended Function Command',
   'fields' :
   [
    {
     'name'   : 'Extended Function',
     'length' : 40
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },
  0b100111 :
  {
   'name' : 'DENY_RSP',
   'long_name' : 'Deny Response',
   'fields' :
   [
    {
     'name'   : 'AIV',
     'length' : 1
    },
    {
     'name'   : '0',
     'length' : 1
    },
    {
     'name'   : 'Service Type',
     'length' : 6
    },
    {
     'name'   : 'Reason Code',
     'length' : 8
    },
    {
     'name'   : 'Additional Information',
     'length' : 24
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },
  0b101000 :
  {
   'name' : 'GRP_AFF_RSP',
   'long_name' : 'Group Affiliation Response',
   'fields' :
   [
    {
     'name'   : 'LG',
     'length' : 1
    },
    {
     'name'   : 'Reserved',
     'length' : 5
    },
    {
     'name'   : 'GAV',
     'length' : 2
    },
    {
     'name'   : 'Announcement Group Address',
     'length' : 16
    },
    {
     'name'   : 'Group Address',
     'length' : 16
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },
  0b101001 :
  {
   'name' : 'SCCB_EXP',
   'long_name' : 'Secondary Control Channel Broadcast - Explicit',
   'fields' :
   [
    {
     'name'   : 'RF Sub-system ID',
     'length' : 8
    },
    {
     'name'   : 'Site ID',
     'length' : 8
    },
    {
     'name'   : 'Channel (T)',
     'length' : 16
    },
    {
     'name'   : 'Reserved',
     'length' : 8
    },
    {
     'name'   : 'Channel (R)',
     'length' : 16
    },
    {
     'name'   : 'System Service Class',
     'length' : 8
    }
   ]
  },
  0b101010 :
  {
   'name' : 'GRP_AFF_Q',
   'long_name' : 'Group Affiliation Query',
   'fields' :
   [
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b101011 :
  {
   'name' : 'LOC_REG_RSP',
   'long_name' : 'Location Registration Response',
   'fields' :
   [
    {
     'name'   : 'Reserved',
     'length' :  6
    },
    {
     'name'   : 'RV',
     'length' : 2
    },
    {
     'name'   : 'Group Address',
     'length' : 16
    },
    {
     'name'   : 'RF Subsystem ID',
     'length' : 8
    },
    {
     'name'   : 'Site ID',
     'length' : 8
    },
    {
     'name'   : 'Target Address',
     'length' : 24
    }
   ]
  },
  0b101100 :
  {
   'name' : 'U_REG_RSP',
   'long_name' : 'Unit Registration Response',
   'fields' :
   [
    {
     'name'   : 'reserved',
     'length' :  2
    },
    {
     'name'   : 'RV',
     'length' : 2
    },
    {
     'name'   : 'System ID',
     'length' : 12
    },
    {
     'name'   : 'Source ID',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b101101 :
  {
   'name' : 'U_REG_CMD',
   'long_name' : 'Unite Registration Command',
   'fields' :
   [
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'Target ID',
     'length' : 24
    },
    {
     'name'   : 'Source Address',
     'length' : 24
    }
   ]
  },
  0b101111 :
  {
   'name' : 'U_DE_REG_ACK',
   'long_name' : 'De-Registration Acknowledgement',
   'fields' :
   [
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'WACN ID',
     'length' : 20
    },
    {
     'name'   : 'System ID',
     'length' : 12
    },
    {
     'name'   : 'Source ID',
     'length' : 24
    }
   ]
  },
  0b110000 :
  {
   'name' : 'SYNC_BCST',
   'long_name' : 'Sync Broadcast',
   'fields' :
   [
    {
     'name'   : 'reserved',
     'length' : 8
    },
    {
     'name'   : 'reserved',
     'length' : 5
    },
    {
     'name'   : 'IST',
     'length' : 1
    },
    {
     'name'   : 'MMU',
     'length' : 1
    },
    {
     'name'   : 'MC',
     'length' : 2
    },
    {
     'name'   : 'VL',
     'length' : 1
    },
    {
     'name'   : 'Local Time Offset',
     'length' : 6
    },
    {
     'name'   : 'Year',
     'length' : 7
    },
    {
     'name'   : 'Month',
     'length' : 4
    },
    {
     'name'   : 'Day',
     'length' : 5
    },
    {
     'name'   : 'Hours',
     'length' : 5
    },
    {
     'name'   : 'Minutes',
     'length' : 6
    },
    {
     'name'   : 'Micro Slots',
     'length' : 13
    }
   ]
  },
  # Multi packet message
  #0b110001 :
  #{
  # 'name' : 'AUTH_DMD',
  # 'long_name' : 'Authentication Demand',
  # 'fields' :
  # [
  #  {
  #   'name'   : '',
  #   'length' : 
  #  },
  # ]
  #},
  0b110010 :
  {
   'name' : 'AUTH_FNE_RESP',
   'long_name' : 'Authentication FNE Response',
   'fields' :
   [
    {
     'name'   : 'Reserved',
     'length' : 8
    },
    {
     'name'   : 'RES2(3)',
     'length' : 8
    },
    {
     'name'   : 'RES2(2)',
     'length' : 8
    },
    {
     'name'   : 'RES2(1)',
     'length' : 8
    },
    {
     'name'   : 'RES2(0)',
     'length' : 8
    },
    {
     'name'   : 'Target ID',
     'length' : 24
    }
   ]
  },
  0b110011 :
  {
   'name' : 'IDEN_UP_TDMA',
   'long_name' : 'Identifier Update for TDMA',
   'fields' :
   [
    {
     'name'   : 'Identifier',
     'length' : 4
    },
    {
     'name'   : 'Channel Type',
     'length' : 4
    },
    {
     'name'   : 'Transmit Offset TDMA',
     'length' : 14
    },
    {
     'name'   : 'Channel Spacing',
     'length' : 10
    },
    {
     'name'   : 'Base Frequency',
     'length' : 32
    }
   ]
  },
  0b110100 :
  {
   'name' : 'IDEN_UP_VU',
   'long_name' : 'Identifier Update for VHF/UHF Bands',
   'fields' :
   [
    {
     'name'   : 'Identifier',
     'length' : 4
    },
    {
     'name'   : 'BW VU',
     'length' : 4
    },
    {
     'name'   : 'Transmit Offset VU',
     'length' : 14
    },
    {
     'name'   : 'Channel Spacing',
     'length' : 10
    },
    {
     'name'   : 'Base Frequency',
     'length' : 32
    }
   ]
  },
  0b110101 :
  {
   'name' : 'TIME_DATE_ANN',
   'long_name' : 'Time and Date Announcement',
   'fields' :
   [
    {
     'name'   : 'VD',
     'length' : 1
    },
    {
     'name'   : 'VT',
     'length' : 1
    },
    {
     'name'   : 'VL',
     'length' : 1
    },
    {
     'name'   : 'reserved',
     'length' : 1
    },
    {
     'name'   : 'Local Time Offset',
     'length' : 12
    },
    {
     'name'   : 'Date',
     'length' : 24
    },
    {
     'name'   : 'Time',
     'length' : 24
    }
   ]
  },
  0b110110 :
  {
   'name' : 'ROAM_ADDR_CMD',
   'long_name' : 'Roaming Address Command',
   'fields' :
   [
    {
     'name'   : 'Stack Operation',
     'length' : 8
    },
    {
     'name'   : 'WACN ID',
     'length' : 20
    },
    {
     'name'   : 'System ID',
     'length' : 12
    },
    {
     'name'   : 'Target ID',
     'length' : 24
    }
   ]
  },
  #Multi-packet message removed.
  #0b110111 :
  #{
  # 'name' : 'ROAM_ADDR_UPDT',
  # 'long_name' : 'Roaming Address Update',
  # 'fields' :
  # [
  #  {
  #   'name'   : '',
  #   'length' : 
  #  },
  # ]
  #},

  0b111000 :
  {
   'name' : 'SYS_SRV_BCST',
   'long_name' : 'System Service Broadcast',
   'fields' :
   [
    {
     'name'   : 'Twuid_validity',
     'length' : 8
    },
    {
     'name'   : 'System Services Available',
     'length' : 24
    },
    {
     'name'   : 'System Services Supported',
     'length' : 24
    },
    {
     'name'   : 'Request Priority Level',
     'length' : 8
    }
   ]
  },
  0b111001 :
  {
   'name' : 'SCCB',
   'long_name' : 'Secondary Control Channel Broadcast',
   'fields' :
   [
    {
     'name'   : 'RF Sub-System ID',
     'length' : 8
    },
    {
     'name'   : 'Site ID',
     'length' : 8
    },
    {
     'name'   : 'unlabeled', #This field was unlabeled (blank) in spec
     'length' : 8
    },
    {
     'name'   : 'Channel System Service Class 0', #Relabeled from Channel System Service Class
     'length' : 16
    },
    {
     'name'   : 'Channel System Service Class 1', #Relabeled from Channel System Service Class
     'length' : 16
    }
   ]
  },
  0b111010 :
  {
   'name' : 'RFSS_STS_BCST',
   'long_name' : 'RFSS Status Broadcast',
   'fields' :
   [
    {
     'name'   : 'LRA',
     'length' : 8
    },
    {
     'name'   : 'reserved',
     'length' : 2
    },
    {
     'name'   : 'R',
     'length' : 1
    },
    {
     'name'   : 'A',
     'length' : 1
    },
    {
     'name'   : 'System ID',
     'length' : 12
    },
    {
     'name'   : 'RF Sub-system ID',
     'length' : 8
    },
    {
     'name'   : 'Site ID',
     'length' : 8
    },
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'System Service Class',
     'length' : 8
    }
   ]
  },
  0b111011 :
  {
   'name' : 'NET_STS_BCST',
   'long_name' : 'Network Status Broadcast',
   'fields' :
   [
    {
     'name'   : 'LRA',
     'length' : 8
    },
    {
     'name'   : 'WACN ID',
     'length' : 20
    },
    {
     'name'   : 'System ID',
     'length' : 12
    },
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'System Service Class',
     'length' : 8
    }
   ]
  },
  0b111100 :
  {
   'name' : 'ADJ_STS_BCST',
   'long_name' : 'Adjacent Status Broadcast',
   'fields' :
   [
    {
     'name'   : 'LRA',
     'length' : 8
    },
    {
     'name'   : 'C',
     'length' : 1
    },
    {
     'name'   : 'F',
     'length' : 1
    },
    {
     'name'   : 'V',
     'length' : 1
    },
    {
     'name'   : 'A',
     'length' : 1
    },
    {
     'name'   : 'System ID',
     'length' : 12
    },
    {
     'name'   : 'RF Sub-system ID',
     'length' : 8
    },
    {
     'name'   : 'Site ID',
     'length' : 8
    },
    {
     'name'   : 'Channel',
     'length' : 16
    },
    {
     'name'   : 'System Service Class',
     'length' : 8
    }
   ]
  },
  0b111101 :
  {
   'name' : 'IDEN_UP',
   'long_name' : 'Identifier Update',
   'fields' :
   [
    {
     'name'   : 'Identifier',
     'length' : 4
    },
    {
     'name'   : 'BW',
     'length' : 9
    },
    {
     'name'   : 'Transmit Offset',
     'length' : 9
    },
    {
     'name'   : 'Channel Spacing',
     'length' : 10
    },
    {
     'name'   : 'Base Frequency',
     'length' : 32
    }
   ]
  }
 }

  #Opcode definition template
  #0b :
  #{
  # 'name' : '',
  # 'long_name' : '',
  # 'fields' :
  # [
  #  {
  #   'name'   : '',
  #   'length' : 
  #  },
  # ]
  #},







if '__main__' == __name__:

 p = p25_cai()
 for i in p.tsbk_osp_single.keys():
	suma = 0
	for x in range(0, len(p.tsbk_osp_single[i]['fields'])):
		suma += p.tsbk_osp_single[i]['fields'][x]['length']
	if suma > 64:
		print 'Packet length overflow: %s ' % (i)


