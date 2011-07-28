#!/usr/bin/env python2

""" Python implementation of ASCII85/ASCIIHex decoder (Adobe version).

This code is in the public domain.

"""

import re
import struct

# ascii85decode(data)
def ascii85decode(data):
    """
    In ASCII85 encoding, every four bytes are encoded with five ASCII
    letters, using 85 different types of characters (as 256**4 < 85**5).
    When the length of the original bytes is not a multiple of 4, a special
    rule is used for round up.
    
    The Adobe's ASCII85 implementation is slightly different from
    its original in handling the last characters.
    
    The sample string is taken from:
      http://en.wikipedia.org/w/index.php?title=Ascii85
    
    >>> ascii85decode('9jqo^BlbD-BleB1DJ+*+F(f,q')
    'Man is distinguished'
    >>> ascii85decode('E,9)oF*2M7/c~>')
    'pleasure.'
    """
    n = b = 0
    out = ''
    for c in data:
        if '!' <= c and c <= 'u':
            n += 1
            b = b*85+(ord(c)-33)
            if n == 5:
                out += struct.pack('>L',b)
                n = b = 0
        elif c == 'z':
            assert n == 0
            out += '\0\0\0\0'
        elif c == '~':
            if n:
                for _ in range(5-n):
                    b = b*85+84
                out += struct.pack('>L',b)[:n-1]
            break
    return out

# asciihexdecode(data)
hex_re = re.compile(r'([a-f\d]{2})', re.IGNORECASE)
trail_re = re.compile(r'^(?:[a-f\d]{2}|\s)*([a-f\d])[\s>]*$', re.IGNORECASE)
def asciihexdecode(data):
    """
    ASCIIHexDecode filter: PDFReference v1.4 section 3.3.1
    For each pair of ASCII hexadecimal digits (0-9 and A-F or a-f), the
    ASCIIHexDecode filter produces one byte of binary data. All white-space
    characters are ignored. A right angle bracket character (>) indicates
    EOD. Any other characters will cause an error. If the filter encounters
    the EOD marker after reading an odd number of hexadecimal digits, it
    will behave as if a 0 followed the last digit.
    
    >>> asciihexdecode('61 62 2e6364   65')
    'ab.cde'
    >>> asciihexdecode('61 62 2e6364   657>')
    'ab.cdep'
    >>> asciihexdecode('7>')
    'p'
    """
    decode = (lambda hx: chr(int(hx, 16)))
    out = map(decode, hex_re.findall(data))
    m = trail_re.search(data)
    if m:
        out.append(decode("%c0" % m.group(1)))
    return ''.join(out)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
