#!/usr/bin/env python2

""" Python implementation of Arcfour encryption algorithm.

This code is in the public domain.

"""

##  Arcfour
##
class Arcfour(object):

    """
    >>> Arcfour('Key').process('Plaintext').encode('hex')
    'bbf316e8d940af0ad3'
    >>> Arcfour('Wiki').process('pedia').encode('hex')
    '1021bf0420'
    >>> Arcfour('Secret').process('Attack at dawn').encode('hex')
    '45a01f645fc35b383552544b9bf5'
    """

    def __init__(self, key):
        s = range(256)
        j = 0
        klen = len(key)
        for i in xrange(256):
            j = (j + s[i] + ord(key[i % klen])) % 256
            (s[i], s[j]) = (s[j], s[i])
        self.s = s
        (self.i, self.j) = (0, 0)
        return

    def process(self, data):
        (i, j) = (self.i, self.j)
        s = self.s
        r = ''
        for c in data:
            i = (i+1) % 256
            j = (j+s[i]) % 256
            (s[i], s[j]) = (s[j], s[i])
            k = s[(s[i]+s[j]) % 256]
            r += chr(ord(c) ^ k)
        (self.i, self.j) = (i, j)
        return r

# test
if __name__ == '__main__':
    import doctest
    doctest.testmod()
