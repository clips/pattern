#!/usr/bin/env python2
import sys
import struct
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from cmapdb import CMapDB, CMapParser, FileUnicodeMap, CMap
from encodingdb import EncodingDB, name2unicode
from psparser import PSStackParser
from psparser import PSSyntaxError, PSEOF
from psparser import LIT, KWD, STRICT
from psparser import PSLiteral, literal_name
from pdftypes import PDFException, resolve1
from pdftypes import int_value, float_value, num_value
from pdftypes import str_value, list_value, dict_value, stream_value
from fontmetrics import FONT_METRICS
from utils import apply_matrix_norm, nunpack, choplist


def get_widths(seq):
    widths = {}
    r = []
    for v in seq:
        if isinstance(v, list):
            if r:
                char1 = r[-1]
                for (i,w) in enumerate(v):
                    widths[char1+i] = w
                r = []
        elif isinstance(v, int):
            r.append(v)
            if len(r) == 3:
                (char1,char2,w) = r
                for i in xrange(char1, char2+1):
                    widths[i] = w
                r = []
    return widths
#assert get_widths([1]) == {}
#assert get_widths([1,2,3]) == {1:3, 2:3}
#assert get_widths([1,[2,3],6,[7,8]]) == {1:2,2:3, 6:7,7:8}

def get_widths2(seq):
    widths = {}
    r = []
    for v in seq:
        if isinstance(v, list):
            if r:
                char1 = r[-1]
                for (i,(w,vx,vy)) in enumerate(choplist(3,v)):
                    widths[char1+i] = (w,(vx,vy))
                r = []
        elif isinstance(v, int):
            r.append(v)
            if len(r) == 5:
                (char1,char2,w,vx,vy) = r
                for i in xrange(char1, char2+1):
                    widths[i] = (w,(vx,vy))
                r = []
    return widths
#assert get_widths2([1]) == {}
#assert get_widths2([1,2,3,4,5]) == {1:(3,(4,5)), 2:(3,(4,5))}
#assert get_widths2([1,[2,3,4,5],6,[7,8,9]]) == {1:(2,(3,4)), 6:(7,(8,9))}


##  FontMetricsDB
##
class FontMetricsDB(object):

    @classmethod
    def get_metrics(klass, fontname):
        return FONT_METRICS[fontname]


##  Type1FontHeaderParser
##
class Type1FontHeaderParser(PSStackParser):

    KEYWORD_BEGIN = KWD('begin')
    KEYWORD_END = KWD('end')
    KEYWORD_DEF = KWD('def')
    KEYWORD_PUT = KWD('put')
    KEYWORD_DICT = KWD('dict')
    KEYWORD_ARRAY = KWD('array')
    KEYWORD_READONLY = KWD('readonly')
    KEYWORD_FOR = KWD('for')
    KEYWORD_FOR = KWD('for')

    def __init__(self, data):
        PSStackParser.__init__(self, data)
        self._cid2unicode = {}
        return

    def get_encoding(self):
        while 1:
            try:
                (cid,name) = self.nextobject()
            except PSEOF:
                break
            try:
                self._cid2unicode[cid] = name2unicode(name)
            except KeyError:
                pass
        return self._cid2unicode
    
    def do_keyword(self, pos, token):
        if token is self.KEYWORD_PUT:
            ((_,key),(_,value)) = self.pop(2)
            if (isinstance(key, int) and
                isinstance(value, PSLiteral)):
                self.add_results((key, literal_name(value)))
        return

    
##  CFFFont
##  (Format specified in Adobe Technical Note: #5176
##   "The Compact Font Format Specification")
##
NIBBLES = ('0','1','2','3','4','5','6','7','8','9','.','e','e-',None,'-')
def getdict(data):
    d = {}
    fp = StringIO(data)
    stack = []
    while 1:
        c = fp.read(1)
        if not c: break
        b0 = ord(c)
        if b0 <= 21:
            d[b0] = stack
            stack = []
            continue
        if b0 == 30:
            s = ''
            loop = True
            while loop:
                b = ord(fp.read(1))
                for n in (b >> 4, b & 15):
                    if n == 15:
                        loop = False
                    else:
                        s += NIBBLES[n]
            value = float(s)
        elif 32 <= b0 and b0 <= 246:
            value = b0-139
        else:
            b1 = ord(fp.read(1))
            if 247 <= b0 and b0 <= 250:
                value = ((b0-247)<<8)+b1+108
            elif 251 <= b0 and b0 <= 254:
                value = -((b0-251)<<8)-b1-108
            else:
                b2 = ord(fp.read(1))
                if 128 <= b1: b1 -= 256
                if b0 == 28:
                    value = b1<<8 | b2
                else:
                    value = b1<<24 | b2<<16 | struct.unpack('>H', fp.read(2))[0]
        stack.append(value)
    return d

class CFFFont(object):

    STANDARD_STRINGS = (
      '.notdef', 'space', 'exclam', 'quotedbl', 'numbersign',
      'dollar', 'percent', 'ampersand', 'quoteright', 'parenleft',
      'parenright', 'asterisk', 'plus', 'comma', 'hyphen', 'period',
      'slash', 'zero', 'one', 'two', 'three', 'four', 'five', 'six',
      'seven', 'eight', 'nine', 'colon', 'semicolon', 'less', 'equal',
      'greater', 'question', 'at', 'A', 'B', 'C', 'D', 'E', 'F', 'G',
      'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
      'U', 'V', 'W', 'X', 'Y', 'Z', 'bracketleft', 'backslash',
      'bracketright', 'asciicircum', 'underscore', 'quoteleft', 'a',
      'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
      'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
      'braceleft', 'bar', 'braceright', 'asciitilde', 'exclamdown',
      'cent', 'sterling', 'fraction', 'yen', 'florin', 'section',
      'currency', 'quotesingle', 'quotedblleft', 'guillemotleft',
      'guilsinglleft', 'guilsinglright', 'fi', 'fl', 'endash',
      'dagger', 'daggerdbl', 'periodcentered', 'paragraph', 'bullet',
      'quotesinglbase', 'quotedblbase', 'quotedblright',
      'guillemotright', 'ellipsis', 'perthousand', 'questiondown',
      'grave', 'acute', 'circumflex', 'tilde', 'macron', 'breve',
      'dotaccent', 'dieresis', 'ring', 'cedilla', 'hungarumlaut',
      'ogonek', 'caron', 'emdash', 'AE', 'ordfeminine', 'Lslash',
      'Oslash', 'OE', 'ordmasculine', 'ae', 'dotlessi', 'lslash',
      'oslash', 'oe', 'germandbls', 'onesuperior', 'logicalnot', 'mu',
      'trademark', 'Eth', 'onehalf', 'plusminus', 'Thorn',
      'onequarter', 'divide', 'brokenbar', 'degree', 'thorn',
      'threequarters', 'twosuperior', 'registered', 'minus', 'eth',
      'multiply', 'threesuperior', 'copyright', 'Aacute',
      'Acircumflex', 'Adieresis', 'Agrave', 'Aring', 'Atilde',
      'Ccedilla', 'Eacute', 'Ecircumflex', 'Edieresis', 'Egrave',
      'Iacute', 'Icircumflex', 'Idieresis', 'Igrave', 'Ntilde',
      'Oacute', 'Ocircumflex', 'Odieresis', 'Ograve', 'Otilde',
      'Scaron', 'Uacute', 'Ucircumflex', 'Udieresis', 'Ugrave',
      'Yacute', 'Ydieresis', 'Zcaron', 'aacute', 'acircumflex',
      'adieresis', 'agrave', 'aring', 'atilde', 'ccedilla', 'eacute',
      'ecircumflex', 'edieresis', 'egrave', 'iacute', 'icircumflex',
      'idieresis', 'igrave', 'ntilde', 'oacute', 'ocircumflex',
      'odieresis', 'ograve', 'otilde', 'scaron', 'uacute',
      'ucircumflex', 'udieresis', 'ugrave', 'yacute', 'ydieresis',
      'zcaron', 'exclamsmall', 'Hungarumlautsmall', 'dollaroldstyle',
      'dollarsuperior', 'ampersandsmall', 'Acutesmall',
      'parenleftsuperior', 'parenrightsuperior', 'twodotenleader',
      'onedotenleader', 'zerooldstyle', 'oneoldstyle', 'twooldstyle',
      'threeoldstyle', 'fouroldstyle', 'fiveoldstyle', 'sixoldstyle',
      'sevenoldstyle', 'eightoldstyle', 'nineoldstyle',
      'commasuperior', 'threequartersemdash', 'periodsuperior',
      'questionsmall', 'asuperior', 'bsuperior', 'centsuperior',
      'dsuperior', 'esuperior', 'isuperior', 'lsuperior', 'msuperior',
      'nsuperior', 'osuperior', 'rsuperior', 'ssuperior', 'tsuperior',
      'ff', 'ffi', 'ffl', 'parenleftinferior', 'parenrightinferior',
      'Circumflexsmall', 'hyphensuperior', 'Gravesmall', 'Asmall',
      'Bsmall', 'Csmall', 'Dsmall', 'Esmall', 'Fsmall', 'Gsmall',
      'Hsmall', 'Ismall', 'Jsmall', 'Ksmall', 'Lsmall', 'Msmall',
      'Nsmall', 'Osmall', 'Psmall', 'Qsmall', 'Rsmall', 'Ssmall',
      'Tsmall', 'Usmall', 'Vsmall', 'Wsmall', 'Xsmall', 'Ysmall',
      'Zsmall', 'colonmonetary', 'onefitted', 'rupiah', 'Tildesmall',
      'exclamdownsmall', 'centoldstyle', 'Lslashsmall', 'Scaronsmall',
      'Zcaronsmall', 'Dieresissmall', 'Brevesmall', 'Caronsmall',
      'Dotaccentsmall', 'Macronsmall', 'figuredash', 'hypheninferior',
      'Ogoneksmall', 'Ringsmall', 'Cedillasmall', 'questiondownsmall',
      'oneeighth', 'threeeighths', 'fiveeighths', 'seveneighths',
      'onethird', 'twothirds', 'zerosuperior', 'foursuperior',
      'fivesuperior', 'sixsuperior', 'sevensuperior', 'eightsuperior',
      'ninesuperior', 'zeroinferior', 'oneinferior', 'twoinferior',
      'threeinferior', 'fourinferior', 'fiveinferior', 'sixinferior',
      'seveninferior', 'eightinferior', 'nineinferior',
      'centinferior', 'dollarinferior', 'periodinferior',
      'commainferior', 'Agravesmall', 'Aacutesmall',
      'Acircumflexsmall', 'Atildesmall', 'Adieresissmall',
      'Aringsmall', 'AEsmall', 'Ccedillasmall', 'Egravesmall',
      'Eacutesmall', 'Ecircumflexsmall', 'Edieresissmall',
      'Igravesmall', 'Iacutesmall', 'Icircumflexsmall',
      'Idieresissmall', 'Ethsmall', 'Ntildesmall', 'Ogravesmall',
      'Oacutesmall', 'Ocircumflexsmall', 'Otildesmall',
      'Odieresissmall', 'OEsmall', 'Oslashsmall', 'Ugravesmall',
      'Uacutesmall', 'Ucircumflexsmall', 'Udieresissmall',
      'Yacutesmall', 'Thornsmall', 'Ydieresissmall', '001.000',
      '001.001', '001.002', '001.003', 'Black', 'Bold', 'Book',
      'Light', 'Medium', 'Regular', 'Roman', 'Semibold',
      )

    class INDEX(object):

        def __init__(self, fp):
            self.fp = fp
            self.offsets = []
            (count, offsize) = struct.unpack('>HB', self.fp.read(3))
            for i in xrange(count+1):
                self.offsets.append(nunpack(self.fp.read(offsize)))
            self.base = self.fp.tell()-1
            self.fp.seek(self.base+self.offsets[-1])
            return

        def __repr__(self):
            return '<INDEX: size=%d>' % len(self)

        def __len__(self):
            return len(self.offsets)-1

        def __getitem__(self, i):
            self.fp.seek(self.base+self.offsets[i])
            return self.fp.read(self.offsets[i+1]-self.offsets[i])

        def __iter__(self):
            return iter( self[i] for i in xrange(len(self)) )

    def __init__(self, name, fp):
        self.name = name
        self.fp = fp
        # Header
        (_major,_minor,hdrsize,offsize) = struct.unpack('BBBB', self.fp.read(4))
        self.fp.read(hdrsize-4)
        # Name INDEX
        self.name_index = self.INDEX(self.fp)
        # Top DICT INDEX
        self.dict_index = self.INDEX(self.fp)
        # String INDEX
        self.string_index = self.INDEX(self.fp)
        # Global Subr INDEX
        self.subr_index = self.INDEX(self.fp)
        # Top DICT DATA
        self.top_dict = getdict(self.dict_index[0])
        (charset_pos,) = self.top_dict.get(15, [0])
        (encoding_pos,) = self.top_dict.get(16, [0])
        (charstring_pos,) = self.top_dict.get(17, [0])
        # CharStrings
        self.fp.seek(charstring_pos)
        self.charstring = self.INDEX(self.fp)
        self.nglyphs = len(self.charstring)
        # Encodings
        self.code2gid = {}
        self.gid2code = {}
        self.fp.seek(encoding_pos)
        format = self.fp.read(1)
        if format == '\x00':
            # Format 0
            (n,) = struct.unpack('B', self.fp.read(1))
            for (code,gid) in enumerate(struct.unpack('B'*n, self.fp.read(n))):
                self.code2gid[code] = gid
                self.gid2code[gid] = code
        elif format == '\x01':
            # Format 1
            (n,) = struct.unpack('B', self.fp.read(1))
            code = 0
            for i in xrange(n):
                (first,nleft) = struct.unpack('BB', self.fp.read(2))
                for gid in xrange(first,first+nleft+1):
                    self.code2gid[code] = gid
                    self.gid2code[gid] = code
                    code += 1
        else:
            raise ValueError('unsupported encoding format: %r' % format)
        # Charsets
        self.name2gid = {}
        self.gid2name = {}
        self.fp.seek(charset_pos)
        format = self.fp.read(1)
        if format == '\x00':
            # Format 0
            n = self.nglyphs-1
            for (gid,sid) in enumerate(struct.unpack('>'+'H'*n, self.fp.read(2*n))):
                gid += 1
                name = self.getstr(sid)
                self.name2gid[name] = gid
                self.gid2name[gid] = name
        elif format == '\x01':
            # Format 1
            (n,) = struct.unpack('B', self.fp.read(1))
            sid = 0
            for i in xrange(n):
                (first,nleft) = struct.unpack('BB', self.fp.read(2))
                for gid in xrange(first,first+nleft+1):
                    name = self.getstr(sid)
                    self.name2gid[name] = gid
                    self.gid2name[gid] = name
                    sid += 1
        elif format == '\x02':
            # Format 2
            assert 0
        else:
            raise ValueError('unsupported charset format: %r' % format)
        #print self.code2gid
        #print self.name2gid
        #assert 0
        return

    def getstr(self, sid):
        if sid < len(self.STANDARD_STRINGS):
            return self.STANDARD_STRINGS[sid]
        return self.string_index[sid-len(self.STANDARD_STRINGS)]


##  TrueTypeFont
##
class TrueTypeFont(object):

    class CMapNotFound(Exception): pass

    def __init__(self, name, fp):
        self.name = name
        self.fp = fp
        self.tables = {}
        self.fonttype = fp.read(4)
        (ntables, _1, _2, _3) = struct.unpack('>HHHH', fp.read(8))
        for _ in xrange(ntables):
            (name, tsum, offset, length) = struct.unpack('>4sLLL', fp.read(16))
            self.tables[name] = (offset, length)
        return

    def create_unicode_map(self):
        if 'cmap' not in self.tables:
            raise TrueTypeFont.CMapNotFound
        (base_offset, length) = self.tables['cmap']
        fp = self.fp
        fp.seek(base_offset)
        (version, nsubtables) = struct.unpack('>HH', fp.read(4))
        subtables = []
        for i in xrange(nsubtables):
            subtables.append(struct.unpack('>HHL', fp.read(8)))
        char2gid = {}
        # Only supports subtable type 0, 2 and 4.
        for (_1, _2, st_offset) in subtables:
            fp.seek(base_offset+st_offset)
            (fmttype, fmtlen, fmtlang) = struct.unpack('>HHH', fp.read(6))
            if fmttype == 0:
                char2gid.update(enumerate(struct.unpack('>256B', fp.read(256))))
            elif fmttype == 2:
                subheaderkeys = struct.unpack('>256H', fp.read(512))
                firstbytes = [0]*8192
                for (i,k) in enumerate(subheaderkeys):
                    firstbytes[k/8] = i
                nhdrs = max(subheaderkeys)/8 + 1
                hdrs = []
                for i in xrange(nhdrs):
                    (firstcode,entcount,delta,offset) = struct.unpack('>HHhH', fp.read(8))
                    hdrs.append((i,firstcode,entcount,delta,fp.tell()-2+offset))
                for (i,firstcode,entcount,delta,pos) in hdrs:
                    if not entcount: continue
                    first = firstcode + (firstbytes[i] << 8)
                    fp.seek(pos)
                    for c in xrange(entcount):
                        gid = struct.unpack('>H', fp.read(2))
                        if gid:
                            gid += delta
                        char2gid[first+c] = gid
            elif fmttype == 4:
                (segcount, _1, _2, _3) = struct.unpack('>HHHH', fp.read(8))
                segcount /= 2
                ecs = struct.unpack('>%dH' % segcount, fp.read(2*segcount))
                fp.read(2)
                scs = struct.unpack('>%dH' % segcount, fp.read(2*segcount))
                idds = struct.unpack('>%dh' % segcount, fp.read(2*segcount))
                pos = fp.tell()
                idrs = struct.unpack('>%dH' % segcount, fp.read(2*segcount))
                for (ec,sc,idd,idr) in zip(ecs, scs, idds, idrs):
                    if idr:
                        fp.seek(pos+idr)
                        for c in xrange(sc, ec+1):
                            char2gid[c] = (struct.unpack('>H', fp.read(2))[0] + idd) & 0xffff
                    else:
                        for c in xrange(sc, ec+1):
                            char2gid[c] = (c + idd) & 0xffff
            else:
                assert 0
        # create unicode map
        unicode_map = FileUnicodeMap()
        for (char,gid) in char2gid.iteritems():
            unicode_map.add_cid2unichr(gid, char)
        return unicode_map


##  Fonts
##

class PDFFontError(PDFException): pass
class PDFUnicodeNotDefined(PDFFontError): pass

LITERAL_STANDARD_ENCODING = LIT('StandardEncoding')
LITERAL_TYPE1C = LIT('Type1C')


# PDFFont
class PDFFont(object):

    def __init__(self, descriptor, widths, default_width=None):
        self.descriptor = descriptor
        self.widths = widths
        self.fontname = resolve1(descriptor.get('FontName', 'unknown'))
        if isinstance(self.fontname, PSLiteral):
            self.fontname = literal_name(self.fontname)
        self.flags = int_value(descriptor.get('Flags', 0))
        self.ascent = num_value(descriptor.get('Ascent', 0))
        self.descent = num_value(descriptor.get('Descent', 0))
        self.italic_angle = num_value(descriptor.get('ItalicAngle', 0))
        self.default_width = default_width or num_value(descriptor.get('MissingWidth', 0))
        self.leading = num_value(descriptor.get('Leading', 0))
        self.bbox = list_value(descriptor.get('FontBBox', (0,0,0,0)))
        self.hscale = self.vscale = .001
        return

    def __repr__(self):
        return '<PDFFont>'

    def is_vertical(self):
        return False

    def is_multibyte(self):
        return False

    def decode(self, bytes):
        return map(ord, bytes)

    def get_ascent(self):
        return self.ascent * self.vscale
    def get_descent(self):
        return self.descent * self.vscale

    def get_width(self):
        w = self.bbox[2]-self.bbox[0]
        if w == 0:
            w = -self.default_width
        return w * self.hscale
    def get_height(self):
        h = self.bbox[3]-self.bbox[1]
        if h == 0:
            h = self.ascent - self.descent
        return h * self.vscale

    def char_width(self, cid):
        return self.widths.get(cid, self.default_width) * self.hscale

    def char_disp(self, cid):
        return 0

    def string_width(self, s):
        return sum( self.char_width(cid) for cid in self.decode(s) )


# PDFSimpleFont
class PDFSimpleFont(PDFFont):

    def __init__(self, descriptor, widths, spec):
        # Font encoding is specified either by a name of
        # built-in encoding or a dictionary that describes
        # the differences.
        if 'Encoding' in spec:
            encoding = resolve1(spec['Encoding'])
        else:
            encoding = LITERAL_STANDARD_ENCODING
        if isinstance(encoding, dict):
            name = literal_name(encoding.get('BaseEncoding', LITERAL_STANDARD_ENCODING))
            diff = list_value(encoding.get('Differences', None))
            self.cid2unicode = EncodingDB.get_encoding(name, diff)
        else:
            self.cid2unicode = EncodingDB.get_encoding(literal_name(encoding))
        self.unicode_map = None
        if 'ToUnicode' in spec:
            strm = stream_value(spec['ToUnicode'])
            self.unicode_map = FileUnicodeMap()
            CMapParser(self.unicode_map, StringIO(strm.get_data())).run()
        PDFFont.__init__(self, descriptor, widths)
        return

    def to_unichr(self, cid):
        if self.unicode_map:
            try:
                return self.unicode_map.get_unichr(cid)
            except KeyError:
                pass
        try:
            return self.cid2unicode[cid]
        except KeyError:
            raise PDFUnicodeNotDefined(None, cid)

# PDFType1Font
class PDFType1Font(PDFSimpleFont):

    def __init__(self, rsrcmgr, spec):
        try:
            self.basefont = literal_name(spec['BaseFont'])
        except KeyError:
            if STRICT:
                raise PDFFontError('BaseFont is missing')
            self.basefont = 'unknown'
        try:
            (descriptor, widths) = FontMetricsDB.get_metrics(self.basefont)
        except KeyError:
            descriptor = dict_value(spec.get('FontDescriptor', {}))
            firstchar = int_value(spec.get('FirstChar', 0))
            lastchar = int_value(spec.get('LastChar', 255))
            widths = list_value(spec.get('Widths', [0]*256))
            widths = dict( (i+firstchar,w) for (i,w) in enumerate(widths) )
        PDFSimpleFont.__init__(self, descriptor, widths, spec)
        if 'Encoding' not in spec and 'FontFile' in descriptor:
            # try to recover the missing encoding info from the font file.
            self.fontfile = stream_value(descriptor.get('FontFile'))
            length1 = int_value(self.fontfile['Length1'])
            data = self.fontfile.get_data()[:length1]
            parser = Type1FontHeaderParser(StringIO(data))
            self.cid2unicode = parser.get_encoding()
        return

    def __repr__(self):
        return '<PDFType1Font: basefont=%r>' % self.basefont

# PDFTrueTypeFont
class PDFTrueTypeFont(PDFType1Font):

    def __repr__(self):
        return '<PDFTrueTypeFont: basefont=%r>' % self.basefont

# PDFType3Font
class PDFType3Font(PDFSimpleFont):

    def __init__(self, rsrcmgr, spec):
        firstchar = int_value(spec.get('FirstChar', 0))
        lastchar = int_value(spec.get('LastChar', 0))
        widths = list_value(spec.get('Widths', [0]*256))
        widths = dict( (i+firstchar,w) for (i,w) in enumerate(widths))
        if 'FontDescriptor' in spec:
            descriptor = dict_value(spec['FontDescriptor'])
        else:
            descriptor = {'Ascent':0, 'Descent':0,
                          'FontBBox':spec['FontBBox']}
        PDFSimpleFont.__init__(self, descriptor, widths, spec)
        self.matrix = tuple(list_value(spec.get('FontMatrix')))
        (_,self.descent,_,self.ascent) = self.bbox
        (self.hscale,self.vscale) = apply_matrix_norm(self.matrix, (1,1))
        return

    def __repr__(self):
        return '<PDFType3Font>'


# PDFCIDFont
class PDFCIDFont(PDFFont):

    def __init__(self, rsrcmgr, spec):
        try:
            self.basefont = literal_name(spec['BaseFont'])
        except KeyError:
            if STRICT:
                raise PDFFontError('BaseFont is missing')
            self.basefont = 'unknown'
        self.cidsysteminfo = dict_value(spec.get('CIDSystemInfo', {}))
        self.cidcoding = '%s-%s' % (self.cidsysteminfo.get('Registry', 'unknown'),
                                    self.cidsysteminfo.get('Ordering', 'unknown'))
        try:
            name = literal_name(spec['Encoding'])
        except KeyError:
            if STRICT:
                raise PDFFontError('Encoding is unspecified')
            name = 'unknown'
        try:
            self.cmap = CMapDB.get_cmap(name)
        except CMapDB.CMapNotFound as e:
            if STRICT:
                raise PDFFontError(e)
            self.cmap = CMap()
        try:
            descriptor = dict_value(spec['FontDescriptor'])
        except KeyError:
            if STRICT:
                raise PDFFontError('FontDescriptor is missing')
            descriptor = {}
        ttf = None
        if 'FontFile2' in descriptor:
            self.fontfile = stream_value(descriptor.get('FontFile2'))
            ttf = TrueTypeFont(self.basefont,
                               StringIO(self.fontfile.get_data()))
        self.unicode_map = None
        if 'ToUnicode' in spec:
            strm = stream_value(spec['ToUnicode'])
            self.unicode_map = FileUnicodeMap()
            CMapParser(self.unicode_map, StringIO(strm.get_data())).run()
        elif self.cidcoding == 'Adobe-Identity':
            if ttf:
                try:
                    self.unicode_map = ttf.create_unicode_map()
                except TrueTypeFont.CMapNotFound:
                    pass
        else:
            try:
                self.unicode_map = CMapDB.get_unicode_map(self.cidcoding, self.cmap.is_vertical())
            except CMapDB.CMapNotFound as e:
                pass

        self.vertical = self.cmap.is_vertical()
        if self.vertical:
            # writing mode: vertical
            widths = get_widths2(list_value(spec.get('W2', [])))
            self.disps = dict( (cid,(vx,vy)) for (cid,(_,(vx,vy))) in widths.iteritems() )
            (vy,w) = spec.get('DW2', [880, -1000])
            self.default_disp = (None,vy)
            widths = dict( (cid,w) for (cid,(w,_)) in widths.iteritems() )
            default_width = w
        else:
            # writing mode: horizontal
            self.disps = {}
            self.default_disp = 0
            widths = get_widths(list_value(spec.get('W', [])))
            default_width = spec.get('DW', 1000)
        PDFFont.__init__(self, descriptor, widths, default_width=default_width)
        return

    def __repr__(self):
        return '<PDFCIDFont: basefont=%r, cidcoding=%r>' % (self.basefont, self.cidcoding)

    def is_vertical(self):
        return self.vertical

    def is_multibyte(self):
        return True

    def decode(self, bytes):
        return self.cmap.decode(bytes)

    def char_disp(self, cid):
        "Returns an integer for horizontal fonts, a tuple for vertical fonts."
        return self.disps.get(cid, self.default_disp)

    def to_unichr(self, cid):
        try:
            if not self.unicode_map: raise KeyError(cid)
            return self.unicode_map.get_unichr(cid)
        except KeyError:
            raise PDFUnicodeNotDefined(self.cidcoding, cid)


# main
def main(argv):
    for fname in argv[1:]:
        fp = file(fname, 'rb')
        #font = TrueTypeFont(fname, fp)
        font = CFFFont(fname, fp)
        print font
        fp.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
