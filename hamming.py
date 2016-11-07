""" 
    This function exports only two functions.
    
    - encode_lc() for the encoding of Hamming code (10,6,3).
    - decode_lc() for the decoding of Hamming code (10,6,3). 

"""

class Codec:
    """ 
        A private class for encoding and decoding Hamming code (10,6,3).
    """
    # The number of bits in the message.
    message_length = 10
    # The number of data bits in the message.
    data_length = 6
    # The number of parity bits in the message.
    parity_length = 4
    # The minimum Hamming distance for the Hamming code.
    minimum_hamming_distance = 3
    # The generator polynomial for Hamming code (10,6,3).
    generator_polynomial = 0b10011

    # Ref: Table 5-4 of TIA-102.BAAA-A
    # Let G be the Generator Matrix.
    #        1 0 0 0 0 0  1 1 1 0
    #        0 1 0 0 0 0  1 1 0 1
    #  G = [ 0 0 1 0 0 0  1 0 1 1 ]
    #        0 0 0 1 0 0  0 1 1 1
    #        0 0 0 0 1 0  0 0 1 1
    #        0 0 0 0 0 1  1 1 0 0
    #
    generator_matrix = [
        0b100000, 
        0b010000, 
        0b001000, 
        0b000100, 
        0b000010, 
        0b000001, 
        0b111001, 
        0b110101,
        0b101110, 
        0b011110,   
    ]

    # Let H be the Parity Check Matrix.
    # H is obtained by transposing the parity columns of G (the last 4 columns) 
    # and appending an Identity Matrix and transposing the whole thing again. 
    # H = ( P^T | I )^T
    #        1 1 1 0  
    #        1 1 0 1  
    #        1 0 1 1  
    #        0 1 1 1  
    #  H = [ 0 0 1 1 ]
    #        1 1 0 0
    #        1 0 0 0  
    #        0 1 0 0  
    #        0 0 1 0  
    #        0 0 0 1  
    # 
    parity_check_matrix = [
        0b1110011000,   
        0b1101010100,   
        0b1011100010,   
        0b0111100001,   
    ]

    # The syndrome table is just the transpose of H. 
    # The index of the syndrome in the table is the position of the error bit.
    syndrome_table = [
        0b1110,   
        0b1101,   
        0b1011,   
        0b0111,   
        0b0011,   
        0b1100,   
        0b1000,   
        0b0100,   
        0b0010,   
        0b0001,   
       ]

    def xor(self,value): 
        """ 
            Calculate the XOR of the bits.
        """
        result = 0
        while(value):
            result ^= (0x01 & value)
            value>>=1
        return result 

    def encode(self, data):
        """
            Encodes data into a message by adding the parity to the data.
            Args:
                data (int) - An integer with 6 bits of data.
            Return:
                int - An integer with 6 bits of data followed by 4 bits 
                of parity.
        """
        gm = self.generator_matrix
        k = self.data_length
        msg = ~(-1 << k) & data
        # Caculate the parity bits.
        for  c in gm[k:]:
            msg <<=1
            if(self.xor( c & data) ):
                msg |= 1
        return msg

    def decode(self, msg, correct = False):
        """
            Decodes data from a message.
            Args:
                data (int) - An integer with 6 bits of data followed by 
                    4 bits of parity.
                correct(bool) - True to perform error correction.
            Return:
                int - An integer with 6 bits of data. 
                None - Message cannot be decoded.
        """
        pcm = self.parity_check_matrix
        st = self.syndrome_table
        n = self.message_length
        p = self.parity_length

        msg =  ~(-1 << n) & msg
        # Calculate the syndrome.
        syndrome = 0;
        for c in pcm:
            syndrome <<= 1
            if( self.xor(c & msg ) ):
                syndrome |= 1
    
        if not syndrome:
            return msg>>p
        elif not correct:
            return None

        # Looks up the syndrome in the syndrome table
        if syndrome in st:
            # Apply 1-bit correction.
            msg ^= ( 1 << (n - 1 - st.index(syndrome)))
            # Recalculate the syndrome bits.
            for c in pcm:
                if(self.xor(c & msg )):
                    return None
            return msg >> p
        return None

codec = Codec()

def encode_lc(data):
    """
        Encodes data into a message by adding the parity to the data.
        Args:
            data (int) - An integer with 6 bits of data.
        Return:
            int - An integer with 6 bits of data followed by 4 bits 
            of parity.
    """
    return codec.encode(data)

    
def decode_lc(msg, correct=False):
    """
        Decodes data from a message.
        Args:
            data (int) - An integer with 6 bits of data followed by 
                4 bits of parity.
            correct(bool) - True to perform error correction.
        Return:
            int - An integer with 6 bits of data. 
            None - Message cannot be decoded.
    """
    return codec.decode(msg, correct)



