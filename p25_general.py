#!/usr/bin/env python

# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com


from p25_cai import p25_cai
from p25_moto import p25_moto


class p25_general():
        def __init__(self):
                self.data_unit_ids = {
                                0x0: 'Header Data Unit',
                                0x3: 'Terminator without Link Control',
                                0x5: 'Logical Link Data Unit 1',
                                0x7: 'Trunking Signaling Data Unit',
                                0xA: 'Logical Link Data Unit 2',
                                0xC: 'Packet Data Unit',
                                0xF: 'Terminator with Link Control'
                                }
        def procHDU(self, frame):
                r = {'short':'HDU', 'long':'Header Data Unit'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['status_symbols'] = status_symbols
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:-10]
                bitframe = self.golay_18_6_8_decode(bitframe)
                bitframe = self.rs_36_20_17_decode(bitframe)
                r['mi']    = bitframe[:72]
                r['mfid']  = int(bitframe[72:80],2)
                r['algid'] = int(bitframe[80:88],2)
                r['kid']   = int(bitframe[88:104],2)
                r['tgid']  = int(bitframe[104:120],2)
                return r
        def procTnoLC(self, frame):
                r = {'short':'TnoLC', 'long':'Terminator without Link Control'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['status_symbols'] = status_symbols
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                return r
        def procLDU1(self, frame):
                r = {'short':'LDU1', 'long':'Logical Link Data Unit 1'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['status_symbols'] = status_symbols
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:]
                vc = [] #voice coding, 144 bits ea 88 digital voice imbe, 56 parity
                lc = '' #link control, 240 bits
                vc.append(bitframe[:144]) #vc1
                vc.append(bitframe[144:288]) #vc2
                lc += bitframe[288:328] #lc1-4
                vc.append(bitframe[328:472]) #vc3
                lc += bitframe[472:512] #lc5-8
                vc.append(bitframe[512:656]) #vc4
                lc += bitframe[656:696] #lc9-12
                vc.append(bitframe[696:840]) #vc5
                lc += bitframe[840:880] #lc13-16
                vc.append(bitframe[880:1024]) #vc6
                lc += bitframe[1024:1064] #lc17-20
                vc.append(bitframe[1064:1208]) #vc7
                lc += bitframe[1208:1248] #lc21-24
                vc.append(bitframe[1248:1392]) #vc8
                r['lsd'] = bitframe[1392:1424]
                vc.append(bitframe[1424:1568]) #vc9

                lc = self.hamming_10_6_3_decode(lc)
                r['lc'] = self.subprocLC(lc)
                return r
        def procTSDU(self,frame):
                r = {'short':'TSDU', 'long':'Trunking Signal Data Unit'}
                bitframe = self.bin_to_bit(frame)
                r['len'] = len(bitframe)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['status_symbols'] = status_symbols
                r['len2'] = len(bitframe)
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:]
                r['len3'] = len(bitframe)

                r['tsbk'] = []
                while(len(bitframe) >= 196):
                        r['tsbk'].append(self.subprocTSBK(bitframe[:196]))
                        bitframe = bitframe[196:]
                        if(bitframe[:1] == '1'):
                                break

                return r
        def procLDU2(self, frame):
                r = {'short' : 'LDU2', 'long': 'Logical Link Data Unit 2'}
                return r
        def procPDU(self, frame):
                r = {'short':'PDU', 'Long' : 'Packet Data Unit'}
                return r
        def procTLC(self, frame):
                r = {'short': 'TLC', 'Long' : 'Terminator with Link Control'}
                bitframe = self.bin_to_bit(frame)
                [bitframe, status_symbols] = self.procStatus(bitframe)
                r['fs'] = hex(int(bitframe[:48],2))
                r['nid'] = hex(int(bitframe[48:112],2))
                bitframe = bitframe[112:-20]
                bitframe = self.golay_24_12_8_decode(bitframe)
                
                r['lc'] = self.subprocLC(bitframe)

                return r
        def subprocTSBK(self, bitframe):
                r = {}
                #print bitframe
                dibits = self.bits_to_dibit(bitframe)
                #print dibits
                dibits = self.data_deinterleave(dibits)
                #print dibits
                trellis_dibits = self.trellis_1_2_decode(dibits)
                bitframe = self.dibits_to_bit(trellis_dibits)
                #print bitframe
                #print hex(int(bitframe,2))
                if len(bitframe) < 96:
                        r['ERR'] = 'PACKET_LENGTH_SHORT'
                        return r
                if self.crc16(int(bitframe,2), 12) == 0:
                        r['crc'] = 0 # bitframe[:16]
                else:
                        r['crc'] = 1
                #sys.stderr.write('Bitframe: %i' % (len(bitframe)))
                r['lb'] = bitframe[:1] #Last block
                r['p'] = bitframe[1:2] #protected
                r['opcode'] = int(bitframe[2:8],2)
                r['mfid'] = int(bitframe[8:16],2)
                if r['mfid'] == 0x0 or r['mfid'] == 0x1: 
                        p = p25_cai()
                elif r['mfid'] == 0x90:
                        p = p25_moto()
                else:
                        r['name'] = 'UNKnOWN MFID'
                        r['data'] = hex(int(bitframe,2))
                        return r
                try:
                        r['name'] = p.tsbk_osp_single[r['opcode']]['name']
                except:
                        r['name'] = 'UNKNOWN OPCODE'
                        r['data'] = hex(int(bitframe,2))
                        return r
                if(len(bitframe[16:]) < 80): return r
                bitframe = bitframe[16:]
                for i in range(0, len(p.tsbk_osp_single[r['opcode']]['fields'])):
                        r[p.tsbk_osp_single[r['opcode']]['fields'][i]['name']] = int(bitframe[:p.tsbk_osp_single[r['opcode']]['fields'][i]['length']],2)
                        bitframe = bitframe[p.tsbk_osp_single[r['opcode']]['fields'][i]['length']:]
                return r
        def subprocLC(self, bitframe):
                bitframe = self.rs_24_12_13_decode(bitframe)
                r = {'short': 'LC', 'long': 'Link Control'}
                r['p'] = int(bitframe[0:1], 2)
                r['p'] = int(bitframe[1:2], 2)
                r['lcf'] = int(bitframe[2:8],2)
                r['mfid'] = int(bitframe[8:16],2)

                if(r['lcf'] == 0x0): #Group Voice Channel User (LCGVR)
                        r['lcf_long'] = 'Group Voice Channel User'
                        r['emergency'] = bitframe[16:17]
                        r['reserved'] = bitframe[17:32]
                        r['tgid'] = int(bitframe[32:48],2)
                        r['source_id'] = int(bitframe[48:72],2)
                        #print 'GV %s %s' %(r['tgid'], r['source_id'])
                elif(r['lcf'] == 0x15):        #Call Termination / Cancellation
                        r['lcf_long'] = 'Call Termination / Cancellation'
                        
                return r
        def procStatus(self, bitframe):
                r = []
                returnframe = ''
                for i in range(0, len(bitframe), 72):
                        r.append(int(bitframe[i+70:i+72],2))
                        returnframe += bitframe[i:i+70]
                        if(len(bitframe) < i+72): 
                                break

                return [returnframe, r]
        def crc16(self, dat,len):     # slow version
                poly = (1<<12) + (1<<5) + (1<<0)
                crc = 0
                for i in range(len):
                        bits = (dat >> (((len-1)-i)*8)) & 0xff
                        for j in range(8):
                                bit = (bits >> (7-j)) & 1
                                crc = ((crc << 1) | bit) & 0x1ffff
                                if crc & 0x10000:
                                        crc = (crc & 0xffff) ^ poly
                crc = crc ^ 0xffff
                return crc

        # fake (18,6,8) shortened Golay decoder, no error correction
        # TODO: make less fake
        # Pulled from Rev 88 of op25/trunk/python/c4fm_decode.py
        def golay_18_6_8_decode(self, input):
                output = ''
                for i in range(0,len(input),18):
                        codeword = input[i:i+18]
                        output +=codeword[:6]
                return output
        # fake (24,12,8) extended Golay decoder, no error correction
        # TODO: make less fake
        def golay_24_12_8_decode(self, input):
                output = ''
                for i in range(0,len(input),24):
                        codeword = input[i:i+24]
                        output += codeword[:12]
                return output

        # fake (36,20,17) Reed-Solomon decoder, no error correction
        def rs_36_20_17_decode(self, input):
                return input[:-96]

        # fake (24,12,13) Reed-Solomon decoder, no error correction
        def rs_24_12_13_decode(self, input):
                return input[:-72]

        # fake (24,16,9) Reed-Solomon decoder, no error correction
        def rs_24_16_9_decode(self,input):
                return input[:-48]
        # fake (10,6,3) shortened Hamming decoder, no error correction
        def hamming_10_6_3_decode(self, input):
                output = ''
                for i in range(0,len(input),10):
                         codeword = input[i:i+10]
                         output += codeword[:6]
                return output
        def trellis_1_2_decode(self, input):
                output = []
                error_count = 0
                # state transition table, including constellation to dibit pair mapping
                next_words = (
                        (0x2, 0xC, 0x1, 0xF),
                        (0xE, 0x0, 0xD, 0x3),
                        (0x9, 0x7, 0xA, 0x4),
                        (0x5, 0xB, 0x6, 0x8))
                state = 0
                # cycle through 2 symbol codewords in input
                for i in range(0,len(input),2):
                        codeword = self.dibits_to_integer(input[i:i+2])
                        similarity = [0, 0, 0, 0]
                        # compare codeword against each of four candidates for the current state
                        for candidate in range(4):
                                # increment similarity result for each bit in codeword that matches candidate
                                for bit in range(4):
                                        if ((~codeword ^ next_words[state][candidate]) & (1 << bit)) > 0:
                                                similarity[candidate] += 1
                        # find the dibit that matches all four codeword bits
                        if similarity.count(4) == 1:
                                state = similarity.index(4)
                        # otherwise find the dibit that matches three codeword bits
                        elif similarity.count(3) == 1:
                                state = similarity.index(3)
                                # We may have corrected the error, so count only a partial error.
                                error_count += 0.01
                        else:
                                # We probably can't correct this error, but we can take our best guess.
                                for j in range(3,-1,-1):
                                        if similarity.count(j) > 0:
                                                state = similarity.index(j)
                                                error_count += 1
                                                break
                        output.append(state)
                # Even if we have a terrible string of errors, we return our best guess and report the error count.
                #if error_count > 0:
                #        sys.stderr.write("Trellis decoding error count: %.2f\n" % error_count)
                return output[:48]

        def data_deinterleave(self, input):
                output = []
                for i in range(0,23,2):
                        for j in (0, 26, 50, 74):
                                output.extend(input[i+j:i+j+2])
                output.extend(input[24:26])
                return output
        # return integer represented by sequence of dibits
        def dibits_to_integer(self, dibits):
                integer = 0
                for dibit in dibits:
                        integer = integer << 2
                        integer += int(dibit)
                return integer
        def bin_to_bit(self, input):
                output = ''
                for i in range(0, len(input)):
                        output += bin(input[i])[2:].zfill(8)
                return output
        def int_to_bit(self, input):
                output = ''
                #print input
                for i in range(0, len(input)):
                        output += bin(input[i])[2:].zfill(8)
                return output
                
        def dibits_to_bit(self, input):
                output = ''
                for j in range(0, len(input)):
                        output += bin(input[int(j)])[2:].zfill(2)
                return output
        def bits_to_dibit(self, input):
                output = []
                for i in range(0, len(input), 2):
                        output.append(int(input[i:i+2],2))
                return output
