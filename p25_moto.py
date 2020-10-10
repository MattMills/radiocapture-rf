#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com
#P25 Protocol Definitions - MOTOROLA MFID
#Changes:
#4/23/2016 - Added tsbk_osp packet definitions (Single Message only)

class p25_moto:
 tsbk_osp_single =  {
  #Dictionary of single message OSPs

  #VOICE SERVICE OSPs
  0b000000 : 
  { 
   'name' : 'MOT_PAT_GRP_ADD_CMD', 
   'long_name' : 'Motorola Patch Group Add', 
   'fields' : 
   [ 
    {
     'name'  : 'Super Group',
     'length' : 16
    },
    {
     'name'  : 'Group 1',
     'length' : 16
    },
    {
     'name'  : 'Group 2',
     'length' : 16
    },
    {
     'name'  : 'Group 3',
     'length' : 16
    }
   ]
  },
  0b000001 :
  {
   'name' : 'MOT_PAT_GRP_DEL_CMD',
   'long_name' : 'Motorola Patch Group Delete', 
   'fields' :
   [
    {
     'name'  : 'Super Group',
     'length' : 16
    },
    {
     'name'  : 'Group 1',
     'length' : 16
    },
    {
     'name'  : 'Group 2',
     'length' : 16
    },
    {
     'name'  : 'Group 3',
     'length' : 16
    }
   ]
  },
  0b000010 :
  {
   'name' : 'MOT_PAT_GRP_VOICE_CHAN_GRANT',
   'long_name' : 'Motorola Patch Group Voice Channel Grant',
   'fields' :
   [
    {
     'name'  : 'unknown 0',
     'length' : 8
    },
    {
     'name'  : 'Channel',
     'length' : 16
    },
    {
     'name'  : 'Super Group',
     'length' : 16
    },
    {
     'name'  : 'Source Address',
     'length' : 24
    },
   ]
  },
  0b000011 :
  {
   'name' : 'MOT_PAT_GRP_VOICE_CHAN_GRANT_UPDT',
   'long_name' : 'Motorola Patch Group Voice Channel Grant Update',
   'fields' :
   [
    {
     'name'  : 'Channel 0',
     'length' : 16
    },
    {
     'name'  : 'Super Group 0',
     'length' : 16
    },
    {
     'name'  : 'Channel 1',
     'length' : 16
    },
    {
     'name'  : 'Super Group 1',
     'length' : 16
    },
   ]
  },



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

 p = p25_moto()
 for i in p.tsbk_osp_single.keys():
        suma = 0
        for x in range(0, len(p.tsbk_osp_single[i]['fields'])):
                suma += p.tsbk_osp_single[i]['fields'][x]['length']
        if suma > 64:
                print('Packet length overflow: %s ' % (i))

 print('complete')

