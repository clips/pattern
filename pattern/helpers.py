from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

#--- STRING FUNCTIONS ------------------------------------------------------------------------------
# Latin-1 (ISO-8859-1) encoding is identical to Windows-1252 except for the code points 128-159:
# Latin-1 assigns control codes in this range, Windows-1252 has characters, punctuation, symbols
# assigned to these code points.


def decode_string(v, encoding="utf-8"):
    """ Returns the given value as a Unicode string (if possible).
    """
    if isinstance(encoding, str):
        encoding = ((encoding,),) + (("windows-1252",), ("utf-8", "ignore"))
    if isinstance(v, bytes):
        for e in encoding:
            try:
                return v.decode(*e)
            except:
                pass
        return v
    return str(v)


def encode_string(v, encoding="utf-8"):
    """ Returns the given value as a Python byte string (if possible).
    """
    if isinstance(encoding, str):
        encoding = ((encoding,),) + (("windows-1252",), ("utf-8", "ignore"))
    if isinstance(v, str):
        for e in encoding:
            try:
                return v.encode(*e)
            except:
                pass
        return v
    return bytes(v)

decode_utf8 = decode_string
encode_utf8 = encode_string
