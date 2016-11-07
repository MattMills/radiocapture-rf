""" 
    This function exports only two functions.
    
    - encode_lc() for the encoding of Golay code (24,12,8).
    - decode_lc() for the decoding of Golay code (24,12,8). 

"""

class Codec:
    """ 
        A private class for encoding and decoding Golay code (24,12,8).
    """

    # The number of bits in the message.
    message_length = 24
    # The number of data bits in the message.
    data_length = 12
    # The number of parity bits in the message.
    parity_length= 12
    # The minimum Hamming distance for the Hamming code.
    minimum_hamming_distance = 8

    # The generator polynomial for Hamming code (24,12,8).
    generator_polynomial = 0b110001110101

    # The generator matrix for Hamming code (24,12,8).
    generator_matrix = [0 for i in range(12)]
    codeword = 0x800
    for i in range(12):
        if codeword & 0x800:
            codeword ^= generator_polynomial
        
        bits = 0
        for j in range(11):
            if codeword & (1 << (10 - j)):
                generator_matrix[j] |=  (1 << i )
                bits+=1

        if not bits % 2:
            generator_matrix[11] |=  (1 << i)
        codeword <<=1
    # Prefix the identity matrix.
    generator_matrix = [ (1 << i) for i  in range(11, -1, -1)] + generator_matrix

    del codeword, bits, i,j

    def bitcount(self,value): 
        """ 
            Calculate the number of bits.
        """
        count = 0
        while(value):
            if 0x01 & value:
                count+=1
            value>>=1
        return count

    def xor(self,value): 
        """ 
            Calculate the XOR of the bits.
        """
        result = 0
        while(value):
            result ^= (0x01 & value)
            value>>=1
        return result

    def rotate_left(self,value, length, bits):
        """ 
            Rotate the bits left.
        """
        value = ~(-1 << length) & value
        return  ( (value & ~(-1 << (length - bits) ) ) << bits ) | ( (value >> (length - bits) ) & ~(-1 << bits))


    def rotate_right(self,value, length, bits):
        """ 
            Rotate the bits right.
        """
        value = ~(-1 << length) & value
        return (value >> bits) | ( (value & ~(-1 << bits)) << (length - bits) )

    def encode(self, data):
        """
            Encodes data into a message by adding the parity to the data.
            Args:
                data (int) - An integer with 12 bits of data.
            Return:
                int - An integer with 12 bits of data followed by 12 bits 
                of parity.
        """
        gm = self.generator_matrix
        k = self.data_length
        msg = ~(-1 << k) & data
        # Generate the parity
        for c in gm[k:]:
            msg <<= 1
            if self.xor(c & data):
                msg |= 1
        return msg

    def decode(self, msg, correct = True):
        """
            Decodes data from a message.
            Args:
                data (int) - An integer with 12 bits of data followed by 
                    12 bits of parity.
                correct(bool) - True to perform error correction.
            Return:
                int - An integer with 12 bits of data. 
                None - Message cannot be decoded.
        """
        n = self.message_length
        k = self.data_length
        p = self.parity_length
        gp = self.generator_polynomial

        msg =  ~(-1 << n) & msg
        data = msg >> p
        encoded = self.encode(data)

        if encoded == msg:
            return data
        elif not correct:
            return None
 
        cyclic = msg >> 1
        # Systematic Search
        # Ref: Error Control Coding; Fundamentals and Applications by Shu Lin
        # and Daniel J. Costello. Page 138
        for i in range(n-1):
            current = self.rotate_left(cyclic, (n-1), i)
            syndrome = current
            for j in range(k):
                if  (1 << (n-2-j)) & syndrome:
                    syndrome ^= (gp << (k-1-j))

            if self.bitcount(syndrome) <= 3:
                current ^= syndrome
                current = self.rotate_right(current, (n-1), i)
                return (current >> (p -1))

        for h in range(k):
            # Toogle a data bit.
            toggled = (1 << n-2-h ) ^ cyclic
            for i in range(n-1):
                current = toggled
                current = self.rotate_left(current, (n-1), i)
                syndrome = current
                for j in range(k):
                    if  (1 << (n-2-j)) & syndrome:
                        syndrome ^= (gp << (k-1-j))

                if self.bitcount(syndrome) <= 2:
                    current ^= syndrome
                    current = self.rotate_right(current, (n-1), i)
                    return (current >> (p-1))

        return None


codec_lc = Codec()

def encode_lc(data):
    return codec_lc.encode(data)


def decode_lc(msg,correct=True):
    return codec_lc.decode(msg,correct)


