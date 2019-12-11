# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

""" 
    This function exports only two functions.
    
    - encode_lc() for the encoding of Reed-Solomon code (24,12,13).
    - decode_lc() for the decoding of Reed-Solomon code (24,12,13). 

"""

class Codec:
    """ 
        A private class for encoding and decoding Reed-Solomon codes (n k,d) 
        in Galois field (2^6). 

    """
    alpha = 2 
    # Sentinal value for log(0).
    sentinal_value = 255 
    # The primitive characteristic polynomial used for generating the Galois field (2^6).
    primative_characteristic_polynomial = 0b1000011 
    # The exponentiation lookup table for the Galois field
    exponentiation_table = bytearray(63)
    exponentiation_table[0]  = 1
    # The logarithm lookup table for the Galois field
    logarithm_table = bytearray(64) 
    logarithm_table[0] = sentinal_value
    logarithm_table[1] = 0

    # Generate the exponentiation and logarithm tables.
    for s in range(1,63):
        exponentiation_table[s] = exponentiation_table[s-1] * alpha
        if exponentiation_table[s] & 0x40 :
            exponentiation_table[s] ^= primative_characteristic_polynomial
        # Save the logarithm.
        logarithm_table[exponentiation_table[s]] = s
    del s

    def __init__(self, hamming_distance):
        """ 
            Constructor for the Codec class. 
            Args:
                hamming_distance (int)- the minimum Hamming distance between 
                codewords of the RS code to create.

        """
        d = hamming_distance
        # Full message length of the RS code.
        n = 63 
        # Data length of the full RS code
        k = n - d + 1

        log = self.logarithm_table
        exp= self.exponentiation_table
        sv = self.sentinal_value

        # Calculate the generator polynomial from the minimum Hamming distance.
        gp = bytearray(d)
        gp[0] = 1
        gp[1] = exp[1]
        
        for i in range(1, d-1):
            for j in range(i + 1, 0, -1):
                if gp[j -1]:
                    gp[j] ^= exp[(log[gp[j-1]] + i + 1) % 63]
        
        # Cache the generator polynomial in logarithmic form.
        gpl = bytearray(d)
        for i in range(d):
            gpl[i] = log[gp[i]]

        # Calculate the generator matrix from the generator polynomial
        gm = []
        msg = bytearray(n)
        for i in range(k):
            msg[i] = 1
            for j in range(i+1, n):
                msg[j] = 0

            for j in range(i, k):
                if msg[j]:
                    c = log[msg[j]]
                    for h in range(d):
                        if gpl[h] != sv: 
                            msg[j+h] ^= exp[ (gpl[h] + c) % 63]
            gm.append(msg[k:n])
            
        # Cache the generator matrix in logarithmic form
        gml = []
        for r in gm:
            parity = bytearray(d-1)
            for i in range(d-1):
                parity[i] = log[r[i]]
            gml.append(parity)
    
        self.hamming_distance =  d
        self.generator_polynomial = gp
        self.generator_polynomial_logarithmic = gpl
        self.generator_matrix = gm
        self.generator_matrix_logarithmic  = gml



    def calculate_syndrome(self, msg):
        """ 
            Calculate the syndrome with roots alpha^1 to alpha^(2t) 

        """
        d = self.hamming_distance
        n = len(msg)
        k = n - d + 1
        exp = self.exponentiation_table
        log = self.logarithm_table
        
        syndrome = bytearray(d-1)
        for s in range(d-1):
            for t in range(n):
                if msg[t]:
                    syndrome[s] ^= exp[(log[msg[t]] + (d-1-s)*(n-1-t)) % 63]

        return syndrome


    def find_locator(self, msg, syndrome, erasures = []):
        """ 
            Find the error locator polynomial with the Berlekamp-Massey 
            algorithm.

            Ref: https://en.wikipedia.org/wiki/Berlekamp%E2%80%93Massey_algorithm
            Ref: Error Control Coding; Fundamentals and Applications by Shu Lin
            and Daniel J. Costello. Page 209-215
        """
        log = self.logarithm_table
        exp = self.exponentiation_table

        d = self.hamming_distance
        n = len(msg)
        k = n - d + 1

        t = len(syndrome) // 2
        s = syndrome[:2*t]

        # Form the erasure polynomial from known positions of error
        if len(erasures):
            e = bytearray( len(erasures) + 1)
            e[-1] = 1
            for i in range(len(erasures)):
                c = (63 - erasures[i]) % 63
                for j in range(-2-i, -1, 1):
                    if e[j+1]:
                        e[j] ^= exp[(log[e[j+1] ] + c)% 63 ]
        else:
            e = bytearray([1])

        a1 = bytearray(e) # current
        a2 = bytearray(e) # previous

        for i in range(2*t - len(erasures)):
            delta = s[i]
            for j in range(1, len(a1)):
                if  a1[-1-j] and s[i-j] :
                    delta ^= exp[ (  log[ a1[-1-j] ] + log[ s[i - j] ]) % 63 ]

            # Left shift
            a2 += bytearray([0])

            if delta:
                # Swap for the longer polynomial
                if len(a2)  > len(a1):
                    a1, a2 = a2, a1

                     # Let a1 be  a2 * delta
                    for j in range(len(a1)):
                        if a1[j]:
                            a1[j] = exp[ (log[ a1[j] ] + log[delta]) % 63 ]

                     # Let a2 be  a1/delta.
                    for j in range(len(a2)):
                        if a2[j]:
                            a2[j] = exp[ (log[ a2[j] ] + 63 -  log[delta]) % 63 ]

                # let a1 = a1 + a2*delta
                c = len(a1) - len(a2)    
                for j in range(len(a2)):
                    if a2[j]:
                        a1[c + j ] ^=  exp[(log[a2[j]] + log[delta]) % 63]

        locator = a1

        # Reverse the locator and trim starting and ending zeros.
        h = 0
        while len(locator) and not locator[h]:
            h+=1

        locator = locator[h::][::-1]
    
        h = 0
        while len(locator) and not locator[h]:
            h+=1

        return locator[h::]

    def find_upper(self,syndrome, locator):
        """ Find the coefficients of  syndrome * locator for 0 to t-1 """  
        log = self.logarithm_table
        exp = self.exponentiation_table
        d = self.hamming_distance
        t = d // 2
        a = locator
        s = syndrome

        upper = bytearray(2*t)
        for i in range(2*t):
            for j in range(i+1):
                if j <len(a)  and  s[-1-i+j] and a[-1-j]:
                    upper[-1-i] ^= exp[(log[s[-1-i+j]] + log[a[-1-j]]) % 63]

        return upper

    def find_lower(self, locator):
        """ Differentiate the locator polynomial """  
        lower = bytearray(len(locator) - 1)
        for i in range(1,len(locator), 2 ):
            lower[-i] = locator[-1 -i]
        return lower
        

    def decode(self, msg, erasures = [], correct=True):
        """
            Decodes a message containing a RS code word.
            Args:
                msg (bytearray) - A bytearray of n bytes with k data bytes 
                followed by d-1 parity bytes. Each byte holds six bits.
                erasures (list) - The indices of the errors in msg.
                correct (bool): True to correct detected errors.
            Return:
                bytearray - Message decoded. A bytearray with 
                    k data bytes. Each byte holds 6 bits.
                None - Message cannot be decoded.
            
        """

        log = self.logarithm_table
        exp = self.exponentiation_table
        d = self.hamming_distance
        n = len(msg)
        k = n - d + 1
        t = d // 2
        
        if (len(erasures) and not correct) or (len(erasures) > 2*t and correct):
            return None
            
        for i in range(len(erasures)):
            erasures[i] = n -1 - erasures[i]
        
        # Calculate the syndrome
        syndrome =  self.calculate_syndrome(msg)

        # Return the data bytes if the syndrome is all zeros.
        if not max(syndrome):
            return msg[:k]
        elif not correct:
            return None

        # Find the error locator polynomial.
        locator = self.find_locator(msg, syndrome, erasures)

        # Search for the locations of the errors
        locations = []
        for i in range(0, n):    
            ii = (63 - i) % 63
            r = 0 
            for j in range(len(locator)):
                if locator[j]:
                    r ^=exp[(log[locator[j]] + ( len(locator) -1-j) * ii) % 63]
            if not r:
                locations.append(i)
        
        if not len(locations):
            return None
    
        # Find the magnitude of the errors with Forney algorithm.
        # Ref: https://en.wikipedia.org/wiki/Forney_algorithm
        # Ref: Error Control Coding; Fundamentals and Applications by Shu Lin
        # and Daniel J. Costello. Page 245-247

        lower= self.find_lower(locator)
        upper = self.find_upper(syndrome, locator)

        for i in locations:
            ii =  (63 - i) % 63

            # Find the denominator of the error evaluator.
            denominator = 0
            for j in range(len(lower)):
                if lower[j]:
                    denominator ^=   exp[(log[lower[j]] + (len(lower) -1 - j ) * ii) % 63 ]


            # Find the numerator of the error evaluator.
            if denominator:
                numerator = 0
                for j in range(len(upper)):
                    if upper[j]:
                        numerator ^=  exp[(log[upper[j]] + (len(upper) -1 - j ) * ii) % 63 ]

                # Find the magnitude of the error and correct the message.
                if numerator:
                    magnitude = exp[ (log[numerator] + 63 - log[denominator]) % 63]
                    msg[-1-i] ^= magnitude

        # Check the the message is correct.
        syndrome =  self.calculate_syndrome(msg)

        if not max(self.calculate_syndrome(msg)):
            return msg[:k]

        return None

    def encode(self,msg):
        """
            Encodes a message by adding the parity of the data to the data.
            Args:
                msg (bytearray) - A byte array of n bytes with k data bytes 
                followed by d-1 parity bytes. Each byte holds 6 bits.

        """
        d = self.hamming_distance
        n = len(msg)
        k = n - d + 1
        exp = self.exponentiation_table
        log = self.logarithm_table
        gml = self.generator_matrix_logarithmic
        sv = self.sentinal_value

        # Adds the parity of the data to the message from the generator maxtix.
        for i in range(k):
            if msg[i]:
                c = log[msg[i]]
                r = gml[63 - n + i] 
                for j in range(d-1):
                    if r[j] != sv:
                         msg[k+j] ^= exp[(r[j] + c) % 63]


codec_lc = Codec(13)

def encode_lc(data):
    """
        Encodes data into a message.

        Arg:
            data (bytearray): A bytearray of 12 bytes containing data, 
            Each byte holds 6 bits.
        Return: 
            bytearray: A bytearray of 24 bytes containing 12 bytes of data
            followed by with 12 bytes of parity. Each byte holds 6 bits.

    """
    msg = data[:12] + bytearray(12)
    codec_lc.encode(msg)
    return msg

def decode_lc(msg, erasures=[], correct=True):
    """
        Decodes data from a message.

        Arg:
            msg (bytearray): A bytearray of 24 bytes containing 12 bytes of 
                data followed by 12 bytes of parity. Each byte holds 6 bits.
            erasures (list): The indices of the errors in message.
            correct (bool): True to correct detected errors.
        Return: 
            bytearray - Message decoded. A bytearray with 
                k data bytes. Each byte holds 6 bits.
            None - Message cannot be decoded.

    """
    return codec_lc.decode(msg, erasures, correct)


  
