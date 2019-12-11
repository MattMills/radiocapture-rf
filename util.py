
# Copyright 2019,2020 Radiocapture LLC - Radiocapture.com

def bytes_to_binary_str(ar, sep=""):
    """
        Converts a bytearray into a string of binary numbers.
        Each byte holds 6 bits.

        Args:
            ar (bytearray) - A bytearray.
            sep (str) - The string between every 6 bits.
        Return:
            string - The representation of the data.
    """
    output = ""
    for i in range(len(ar)):
        if output:
            output += sep

        for t in range(5, -1, -1 ):
            if ar[i] & (1 << t):
               output += str(1)
            else:
               output += str(0)
    return output

def bytes_to_octal_str(ar, sep=""):
    """
        Converts a bytearray into a string of octal numbers.
        Each byte holds 6 bits.

        Args:
            ar (bytearray) - A bytearray.
            sep (str) - The string between every 6 bits.
        Return:
        Return:
            string - The representation of the data.
    """
    output = ""
    for i in range(len(ar)):
        if output:
            output += sep
        output += str(ar[i] >> 3) + str(ar[i] & 0x7)
    return output  

def octal_str_to_bytes(ostr):
    """
        Converts an octal string into a bytearray. Each byte holds 6 bits.

        For a string "01157",
            bytearray[0] = 0o01,
            bytearray[1] = 0o15,
            bytearray[2] = 0o77,
        
        Args:
            bstr (str): An octal string. 
        Return: 
            bytearray: A bytearray containing the data. Each byte holds 6 bits.
    """
    ostr = ostr.replace(" ", "")

    ar = bytearray(len(ostr)//2)
    for i in range(0,len(ostr)//2):
        b = int(ostr[i*2: (i*+1)*2],8)
        if b:
            ar[i] = b
    return ar

def binary_str_to_bytes(bstr):
    """
        Converts a binary string into a bytearray. Each byte holds 6 bits.
        Each byte holds 6 bits.

        For a string "000001001101111111",
            bytearray[0] = 0o01,
            bytearray[1] = 0o15,
            bytearray[2] = 0o77,
        
        Args:
            bstr (str): A binary string. 
        Return: 
            bytearray: A bytearray containing the data.

    """
    bstr = bstr.replace(" ", "")
    ar = bytearray(len(bstr)//6)
    for i in range(len(ar)):
        ar[i]  = int(bstr[i*6:(i+1)*6],2)
    return ar



#def bstr_conv(bstr):
#    """
#        Converts a binary string into an integer. 
#        Args:
#            bstr (str): A binary string. 
#        Return: 
#            bytearray: An integer containing the data.
#
#    """
#    bstr = bstr.replace(" ", "")
#    value = 0
#    for i in range(len(bstr)):
#        value <<=1
#        if int(bstr[i],2):
#            value |= 1
#    return value



#def repr_bin(value, n):
#    """
#        Converts an integer into a string of binary numbers.
#
#        Args:
#            ar (bytearray) - A bytearray.
#            split (bool) - True to add a space between every 6 bits.
#        Return:
#            string - The representation of the data.
#    """
#    output = ""
#    for i in range(n):
#        if (1 << i) & value:
#           output += str(1)
#        else:
#           output += str(0)
#    return output
#
