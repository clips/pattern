#!/usr/bin/env python2

import re
from psparser import PSLiteral
from glyphlist import glyphname2unicode
from latin_enc import ENCODING


##  name2unicode
##
STRIP_NAME = re.compile(r'[0-9]+')
def name2unicode(name):
    """Converts Adobe glyph names to Unicode numbers."""
    if name in glyphname2unicode:
        return glyphname2unicode[name]
    m = STRIP_NAME.search(name)
    if not m: raise KeyError(name)
    return unichr(int(m.group(0)))


##  EncodingDB
##
class EncodingDB(object):

    std2unicode = {}
    mac2unicode = {}
    win2unicode = {}
    pdf2unicode = {}
    for (name,std,mac,win,pdf) in ENCODING:
        c = name2unicode(name)
        if std: std2unicode[std] = c
        if mac: mac2unicode[mac] = c
        if win: win2unicode[win] = c
        if pdf: pdf2unicode[pdf] = c

    encodings = {
      'StandardEncoding': std2unicode,
      'MacRomanEncoding': mac2unicode,
      'WinAnsiEncoding': win2unicode,
      'PDFDocEncoding': pdf2unicode,
      }

    @classmethod
    def get_encoding(klass, name, diff=None):
        cid2unicode = klass.encodings.get(name, klass.std2unicode)
        if diff:
            cid2unicode = cid2unicode.copy()
            cid = 0
            for x in diff:
                if isinstance(x, int):
                    cid = x
                elif isinstance(x, PSLiteral):
                    try:
                        cid2unicode[cid] = name2unicode(x.name)
                    except KeyError:
                        pass
                    cid += 1
        return cid2unicode
