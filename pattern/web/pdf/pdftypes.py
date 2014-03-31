#!/usr/bin/env python2
import sys
import zlib
from lzw import lzwdecode
from ascii85 import ascii85decode, asciihexdecode
from runlength import rldecode
from psparser import PSException, PSObject
from psparser import LIT, KWD, STRICT

LITERAL_CRYPT = LIT('Crypt')

# Abbreviation of Filter names in PDF 4.8.6. "Inline Images"
LITERALS_FLATE_DECODE = (LIT('FlateDecode'), LIT('Fl'))
LITERALS_LZW_DECODE = (LIT('LZWDecode'), LIT('LZW'))
LITERALS_ASCII85_DECODE = (LIT('ASCII85Decode'), LIT('A85'))
LITERALS_ASCIIHEX_DECODE = (LIT('ASCIIHexDecode'), LIT('AHx'))
LITERALS_RUNLENGTH_DECODE = (LIT('RunLengthDecode'), LIT('RL'))
LITERALS_CCITTFAX_DECODE = (LIT('CCITTFaxDecode'), LIT('CCF'))
LITERALS_DCT_DECODE = (LIT('DCTDecode'), LIT('DCT'))


##  PDF Objects
##
class PDFObject(PSObject): pass

class PDFException(PSException): pass
class PDFTypeError(PDFException): pass
class PDFValueError(PDFException): pass
class PDFNotImplementedError(PSException): pass


##  PDFObjRef
##
class PDFObjRef(PDFObject):

    def __init__(self, doc, objid, _):
        if objid == 0:
            if STRICT:
                raise PDFValueError('PDF object id cannot be 0.')
        self.doc = doc
        self.objid = objid
        #self.genno = genno  # Never used.
        return

    def __repr__(self):
        return '<PDFObjRef:%d>' % (self.objid)

    def resolve(self):
        return self.doc.getobj(self.objid)


# resolve
def resolve1(x):
    """Resolves an object.

    If this is an array or dictionary, it may still contains
    some indirect objects inside.
    """
    while isinstance(x, PDFObjRef):
        x = x.resolve()
    return x

def resolve_all(x):
    """Recursively resolves the given object and all the internals.
    
    Make sure there is no indirect reference within the nested object.
    This procedure might be slow.
    """
    while isinstance(x, PDFObjRef):
        x = x.resolve()
    if isinstance(x, list):
        x = [ resolve_all(v) for v in x ]
    elif isinstance(x, dict):
        for (k,v) in x.iteritems():
            x[k] = resolve_all(v)
    return x

def decipher_all(decipher, objid, genno, x):
    """Recursively deciphers the given object.
    """
    if isinstance(x, str):
        return decipher(objid, genno, x)
    if isinstance(x, list):
        x = [ decipher_all(decipher, objid, genno, v) for v in x ]
    elif isinstance(x, dict):
        for (k,v) in x.iteritems():
            x[k] = decipher_all(decipher, objid, genno, v)
    return x

# Type cheking
def int_value(x):
    x = resolve1(x)
    if not isinstance(x, int):
        if STRICT:
            raise PDFTypeError('Integer required: %r' % x)
        return 0
    return x

def float_value(x):
    x = resolve1(x)
    if not isinstance(x, float):
        if STRICT:
            raise PDFTypeError('Float required: %r' % x)
        return 0.0
    return x

def num_value(x):
    x = resolve1(x)
    if not (isinstance(x, int) or isinstance(x, float)):
        if STRICT:
            raise PDFTypeError('Int or Float required: %r' % x)
        return 0
    return x

def str_value(x):
    x = resolve1(x)
    if not isinstance(x, str):
        if STRICT:
            raise PDFTypeError('String required: %r' % x)
        return ''
    return x

def list_value(x):
    x = resolve1(x)
    if not (isinstance(x, list) or isinstance(x, tuple)):
        if STRICT:
            raise PDFTypeError('List required: %r' % x)
        return []
    return x

def dict_value(x):
    x = resolve1(x)
    if not isinstance(x, dict):
        if STRICT:
            raise PDFTypeError('Dict required: %r' % x)
        return {}
    return x

def stream_value(x):
    x = resolve1(x)
    if not isinstance(x, PDFStream):
        if STRICT:
            raise PDFTypeError('PDFStream required: %r' % x)
        return PDFStream({}, '')
    return x


##  PDFStream type
##
class PDFStream(PDFObject):

    def __init__(self, attrs, rawdata, decipher=None):
        assert isinstance(attrs, dict)
        self.attrs = attrs
        self.rawdata = rawdata
        self.decipher = decipher
        self.data = None
        self.objid = None
        self.genno = None
        return

    def set_objid(self, objid, genno):
        self.objid = objid
        self.genno = genno
        return

    def __repr__(self):
        if self.data is None:
            assert self.rawdata is not None
            return '<PDFStream(%r): raw=%d, %r>' % (self.objid, len(self.rawdata), self.attrs)
        else:
            assert self.data is not None
            return '<PDFStream(%r): len=%d, %r>' % (self.objid, len(self.data), self.attrs)

    def __contains__(self, name):
        return name in self.attrs
    
    def __getitem__(self, name):
        return self.attrs[name]
    
    def get(self, name, default=None):
        return self.attrs.get(name, default)
    
    def get_any(self, names, default=None):
        for name in names:
            if name in self.attrs:
                return self.attrs[name]
        return default

    def get_filters(self):
        filters = self.get_any(('F', 'Filter'))
        if not filters: return []
        if isinstance(filters, list): return filters
        return [ filters ]

    def decode(self):
        assert self.data is None and self.rawdata != None
        data = self.rawdata
        if self.decipher:
            # Handle encryption
            data = self.decipher(self.objid, self.genno, data)
        filters = self.get_filters()
        if not filters:
            self.data = data
            self.rawdata = None
            return
        for f in filters:
            if f in LITERALS_FLATE_DECODE:
                # will get errors if the document is encrypted.
                try:
                    data = zlib.decompress(data)
                except zlib.error as e:
                    if STRICT:
                        raise PDFException('Invalid zlib bytes: %r, %r' % (e, data))
                    data = ''
            elif f in LITERALS_LZW_DECODE:
                data = lzwdecode(data)
            elif f in LITERALS_ASCII85_DECODE:
                data = ascii85decode(data)
            elif f in LITERALS_ASCIIHEX_DECODE:
                data = asciihexdecode(data)
            elif f in LITERALS_RUNLENGTH_DECODE:
                data = rldecode(data)
            elif f in LITERALS_CCITTFAX_DECODE:
                #data = ccittfaxdecode(data)
                raise PDFNotImplementedError('Unsupported filter: %r' % f)
            elif f == LITERAL_CRYPT:
                # not yet..
                raise PDFNotImplementedError('/Crypt filter is unsupported')
            else:
                raise PDFNotImplementedError('Unsupported filter: %r' % f)
            # apply predictors
            params = self.get_any(('DP', 'DecodeParms', 'FDecodeParms'), {})
            if 'Predictor' in params and 'Columns' in params:
                pred = int_value(params['Predictor'])
                columns = int_value(params['Columns'])
                if pred:
                    if pred != 12:
                        raise PDFNotImplementedError('Unsupported predictor: %r' % pred)
                    buf = ''
                    ent0 = '\x00' * columns
                    for i in xrange(0, len(data), columns+1):
                        pred = data[i]
                        ent1 = data[i+1:i+1+columns]
                        if pred == '\x02':
                            ent1 = ''.join( chr((ord(a)+ord(b)) & 255) for (a,b) in zip(ent0,ent1) )
                        buf += ent1
                        ent0 = ent1
                    data = buf
        self.data = data
        self.rawdata = None
        return

    def get_data(self):
        if self.data is None:
            self.decode()
        return self.data

    def get_rawdata(self):
        return self.rawdata
