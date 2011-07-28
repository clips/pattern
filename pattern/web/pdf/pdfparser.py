#!/usr/bin/env python2
import sys
import re
import struct
try:
    import hashlib as md5
except ImportError:
    import md5
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from psparser import PSStackParser
from psparser import PSSyntaxError, PSEOF
from psparser import literal_name
from psparser import LIT, KWD, STRICT
from pdftypes import PDFException, PDFTypeError, PDFNotImplementedError
from pdftypes import PDFStream, PDFObjRef
from pdftypes import resolve1, decipher_all
from pdftypes import int_value, float_value, num_value
from pdftypes import str_value, list_value, dict_value, stream_value
from arcfour import Arcfour
from utils import choplist, nunpack
from utils import decode_text, ObjIdRange


##  Exceptions
##
class PDFSyntaxError(PDFException): pass
class PDFNoValidXRef(PDFSyntaxError): pass
class PDFNoOutlines(PDFException): pass
class PDFDestinationNotFound(PDFException): pass
class PDFEncryptionError(PDFException): pass
class PDFPasswordIncorrect(PDFEncryptionError): pass

# some predefined literals and keywords.
LITERAL_OBJSTM = LIT('ObjStm')
LITERAL_XREF = LIT('XRef')
LITERAL_PAGE = LIT('Page')
LITERAL_PAGES = LIT('Pages')
LITERAL_CATALOG = LIT('Catalog')


##  XRefs
##
class PDFBaseXRef(object):

    def get_trailer(self):
        raise NotImplementedError

    def get_objids(self):
        return []

    def get_pos(self, objid):
        raise KeyError(objid)


##  PDFXRef
##
class PDFXRef(PDFBaseXRef):
    
    def __init__(self):
        self.offsets = {}
        self.trailer = {}
        return

    def load(self, parser, debug=0):
        while 1:
            try:
                (pos, line) = parser.nextline()
                if not line.strip(): continue
            except PSEOF:
                raise PDFNoValidXRef('Unexpected EOF - file corrupted?')
            if not line:
                raise PDFNoValidXRef('Premature eof: %r' % parser)
            if line.startswith('trailer'):
                parser.seek(pos)
                break
            f = line.strip().split(' ')
            if len(f) != 2:
                raise PDFNoValidXRef('Trailer not found: %r: line=%r' % (parser, line))
            try:
                (start, nobjs) = map(long, f)
            except ValueError:
                raise PDFNoValidXRef('Invalid line: %r: line=%r' % (parser, line))
            for objid in xrange(start, start+nobjs):
                try:
                    (_, line) = parser.nextline()
                except PSEOF:
                    raise PDFNoValidXRef('Unexpected EOF - file corrupted?')
                f = line.strip().split(' ')
                if len(f) != 3:
                    raise PDFNoValidXRef('Invalid XRef format: %r, line=%r' % (parser, line))
                (pos, genno, use) = f
                if use != 'n': continue
                self.offsets[objid] = (int(genno), long(pos))
        if 1 <= debug:
            print >>sys.stderr, 'xref objects:', self.offsets
        self.load_trailer(parser)
        return

    KEYWORD_TRAILER = KWD('trailer')
    def load_trailer(self, parser):
        try:
            (_,kwd) = parser.nexttoken()
            assert kwd is self.KEYWORD_TRAILER
            (_,dic) = parser.nextobject()
        except PSEOF:
            x = parser.pop(1)
            if not x:
                raise PDFNoValidXRef('Unexpected EOF - file corrupted')
            (_,dic) = x[0]
        self.trailer.update(dict_value(dic))
        return

    PDFOBJ_CUE = re.compile(r'^(\d+)\s+(\d+)\s+obj\b')
    def load_fallback(self, parser, debug=0):
        parser.seek(0)
        while 1:
            try:
                (pos, line) = parser.nextline()
            except PSEOF:
                break
            if line.startswith('trailer'):
                parser.seek(pos)
                self.load_trailer(parser)
                if 1 <= debug:
                    print >>sys.stderr, 'trailer: %r' % self.get_trailer()
                break
            m = self.PDFOBJ_CUE.match(line)
            if not m: continue
            (objid, genno) = m.groups()
            self.offsets[int(objid)] = (0, pos)
        return

    def get_trailer(self):
        return self.trailer

    def get_objids(self):
        return self.offsets.iterkeys()

    def get_pos(self, objid):
        try:
            (genno, pos) = self.offsets[objid]
        except KeyError:
            raise
        return (None, pos)


##  PDFXRefStream
##
class PDFXRefStream(PDFBaseXRef):

    def __init__(self):
        self.data = None
        self.entlen = None
        self.fl1 = self.fl2 = self.fl3 = None
        self.objid_ranges = []
        return

    def __repr__(self):
        return '<PDFXRefStream: fields=%d,%d,%d>' % (self.fl1, self.fl2, self.fl3)

    def load(self, parser, debug=0):
        (_,objid) = parser.nexttoken() # ignored
        (_,genno) = parser.nexttoken() # ignored
        (_,kwd) = parser.nexttoken()
        (_,stream) = parser.nextobject()
        if not isinstance(stream, PDFStream) or stream['Type'] is not LITERAL_XREF:
            raise PDFNoValidXRef('Invalid PDF stream spec.')
        size = stream['Size']
        index_array = stream.get('Index', (0,size))
        if len(index_array) % 2 != 0:
            raise PDFSyntaxError('Invalid index number')
        self.objid_ranges.extend( ObjIdRange(start, nobjs) 
                                  for (start,nobjs) in choplist(2, index_array) )
        (self.fl1, self.fl2, self.fl3) = stream['W']
        self.data = stream.get_data()
        self.entlen = self.fl1+self.fl2+self.fl3
        self.trailer = stream.attrs
        if 1 <= debug:
            print >>sys.stderr, ('xref stream: objid=%s, fields=%d,%d,%d' %
                             (', '.join(map(repr, self.objid_ranges)),
                              self.fl1, self.fl2, self.fl3))
        return

    def get_trailer(self):
        return self.trailer

    def get_objids(self):
        for objid_range in self.objid_ranges:
            for x in xrange(objid_range.get_start_id(), objid_range.get_end_id()+1):
                yield x
        return

    def get_pos(self, objid):
        offset = 0
        found = False
        for objid_range in self.objid_ranges:
            if objid >= objid_range.get_start_id() and objid <= objid_range.get_end_id():
                offset += objid - objid_range.get_start_id()
                found = True
                break
            else:
                offset += objid_range.get_nobjs()
        if not found: raise KeyError(objid)
        i = self.entlen * offset
        ent = self.data[i:i+self.entlen]
        f1 = nunpack(ent[:self.fl1], 1)
        if f1 == 1:
            pos = nunpack(ent[self.fl1:self.fl1+self.fl2])
            genno = nunpack(ent[self.fl1+self.fl2:])
            return (None, pos)
        elif f1 == 2:
            objid = nunpack(ent[self.fl1:self.fl1+self.fl2])
            index = nunpack(ent[self.fl1+self.fl2:])
            return (objid, index)
        # this is a free object
        raise KeyError(objid)


##  PDFPage
##
class PDFPage(object):

    """An object that holds the information about a page.

    A PDFPage object is merely a convenience class that has a set
    of keys and values, which describe the properties of a page
    and point to its contents.

    Attributes:
      doc: a PDFDocument object.
      pageid: any Python object that can uniquely identify the page.
      attrs: a dictionary of page attributes.
      contents: a list of PDFStream objects that represents the page content.
      lastmod: the last modified time of the page.
      resources: a list of resources used by the page.
      mediabox: the physical size of the page.
      cropbox: the crop rectangle of the page.
      rotate: the page rotation (in degree).
      annots: the page annotations.
      beads: a chain that represents natural reading order.
    """

    def __init__(self, doc, pageid, attrs):
        """Initialize a page object.
        
        doc: a PDFDocument object.
        pageid: any Python object that can uniquely identify the page.
        attrs: a dictionary of page attributes.
        """
        self.doc = doc
        self.pageid = pageid
        self.attrs = dict_value(attrs)
        self.lastmod = resolve1(self.attrs.get('LastModified'))
        self.resources = resolve1(self.attrs['Resources'])
        self.mediabox = resolve1(self.attrs['MediaBox'])
        if 'CropBox' in self.attrs:
            self.cropbox = resolve1(self.attrs['CropBox'])
        else:
            self.cropbox = self.mediabox
        self.rotate = (self.attrs.get('Rotate', 0)+360) % 360
        self.annots = self.attrs.get('Annots')
        self.beads = self.attrs.get('B')
        if 'Contents' in self.attrs:
            contents = resolve1(self.attrs['Contents'])
        else:
            contents = []
        if not isinstance(contents, list):
            contents = [ contents ]
        self.contents = contents
        return

    def __repr__(self):
        return '<PDFPage: Resources=%r, MediaBox=%r>' % (self.resources, self.mediabox)


##  PDFDocument
##
class PDFDocument(object):

    """PDFDocument object represents a PDF document.

    Since a PDF file can be very big, normally it is not loaded at
    once. So PDF document has to cooperate with a PDF parser in order to
    dynamically import the data as processing goes.

    Typical usage:
      doc = PDFDocument()
      doc.set_parser(parser)
      doc.initialize(password)
      obj = doc.getobj(objid)
    
    """

    debug = 0

    def __init__(self, caching=True):
        self.caching = caching
        self.xrefs = []
        self.info = []
        self.catalog = None
        self.encryption = None
        self.decipher = None
        self._parser = None
        self._cached_objs = {}
        self._parsed_objs = {}
        return

    def set_parser(self, parser):
        "Set the document to use a given PDFParser object."
        if self._parser: return
        self._parser = parser
        # Retrieve the information of each header that was appended
        # (maybe multiple times) at the end of the document.
        self.xrefs = parser.read_xref()
        for xref in self.xrefs:
            trailer = xref.get_trailer()
            if not trailer: continue
            # If there's an encryption info, remember it.
            if 'Encrypt' in trailer:
                #assert not self.encryption
                self.encryption = (list_value(trailer['ID']),
                                   dict_value(trailer['Encrypt']))
            if 'Info' in trailer:
                self.info.append(dict_value(trailer['Info']))
            if 'Root' in trailer:
                #  Every PDF file must have exactly one /Root dictionary.
                self.catalog = dict_value(trailer['Root'])
                break
        else:
            raise PDFSyntaxError('No /Root object! - Is this really a PDF?')
        if self.catalog.get('Type') is not LITERAL_CATALOG:
            if STRICT:
                raise PDFSyntaxError('Catalog not found!')
        return

    # initialize(password='')
    #   Perform the initialization with a given password.
    #   This step is mandatory even if there's no password associated
    #   with the document.
    PASSWORD_PADDING = '(\xbfN^Nu\x8aAd\x00NV\xff\xfa\x01\x08..\x00\xb6\xd0h>\x80/\x0c\xa9\xfedSiz'
    def initialize(self, password=''):
        if not self.encryption:
            self.is_printable = self.is_modifiable = self.is_extractable = True
            return
        (docid, param) = self.encryption
        if literal_name(param.get('Filter')) != 'Standard':
            raise PDFEncryptionError('Unknown filter: param=%r' % param)
        V = int_value(param.get('V', 0))
        if not (V == 1 or V == 2):
            raise PDFEncryptionError('Unknown algorithm: param=%r' % param)
        length = int_value(param.get('Length', 40)) # Key length (bits)
        O = str_value(param['O'])
        R = int_value(param['R']) # Revision
        if 5 <= R:
            raise PDFEncryptionError('Unknown revision: %r' % R)
        U = str_value(param['U'])
        P = int_value(param['P'])
        self.is_printable = bool(P & 4)
        self.is_modifiable = bool(P & 8)
        self.is_extractable = bool(P & 16)
        # Algorithm 3.2
        password = (password+self.PASSWORD_PADDING)[:32] # 1
        hash = md5.md5(password) # 2
        hash.update(O) # 3
        hash.update(struct.pack('<l', P)) # 4
        hash.update(docid[0]) # 5
        if 4 <= R:
            # 6
            raise PDFNotImplementedError('Revision 4 encryption is currently unsupported')
        if 3 <= R:
            # 8
            for _ in xrange(50):
                hash = md5.md5(hash.digest()[:length/8])
        key = hash.digest()[:length/8]
        if R == 2:
            # Algorithm 3.4
            u1 = Arcfour(key).process(self.PASSWORD_PADDING)
        elif R == 3:
            # Algorithm 3.5
            hash = md5.md5(self.PASSWORD_PADDING) # 2
            hash.update(docid[0]) # 3
            x = Arcfour(key).process(hash.digest()[:16]) # 4
            for i in xrange(1,19+1):
                k = ''.join( chr(ord(c) ^ i) for c in key )
                x = Arcfour(k).process(x)
            u1 = x+x # 32bytes total
        if R == 2:
            is_authenticated = (u1 == U)
        else:
            is_authenticated = (u1[:16] == U[:16])
        if not is_authenticated:
            raise PDFPasswordIncorrect
        self.decrypt_key = key
        self.decipher = self.decrypt_rc4  # XXX may be AES
        return

    def decrypt_rc4(self, objid, genno, data):
        key = self.decrypt_key + struct.pack('<L',objid)[:3]+struct.pack('<L',genno)[:2]
        hash = md5.md5(key)
        key = hash.digest()[:min(len(key),16)]
        return Arcfour(key).process(data)

    KEYWORD_OBJ = KWD('obj')
    def getobj(self, objid):
        if not self.xrefs:
            raise PDFException('PDFDocument is not initialized')
        if 2 <= self.debug:
            print >>sys.stderr, 'getobj: objid=%r' % (objid)
        if objid in self._cached_objs:
            genno = 0
            obj = self._cached_objs[objid]
        else:
            for xref in self.xrefs:
                try:
                    (strmid, index) = xref.get_pos(objid)
                    break
                except KeyError:
                    pass
            else:
                if STRICT:
                    raise PDFSyntaxError('Cannot locate objid=%r' % objid)
                # return null for a nonexistent reference.
                return None
            if strmid:
                stream = stream_value(self.getobj(strmid))
                if stream.get('Type') is not LITERAL_OBJSTM:
                    if STRICT:
                        raise PDFSyntaxError('Not a stream object: %r' % stream)
                try:
                    n = stream['N']
                except KeyError:
                    if STRICT:
                        raise PDFSyntaxError('N is not defined: %r' % stream)
                    n = 0
                if strmid in self._parsed_objs:
                    objs = self._parsed_objs[strmid]
                else:
                    parser = PDFStreamParser(stream.get_data())
                    parser.set_document(self)
                    objs = []
                    try:
                        while 1:
                            (_,obj) = parser.nextobject()
                            objs.append(obj)
                    except PSEOF:
                        pass
                    if self.caching:
                        self._parsed_objs[strmid] = objs
                genno = 0
                i = n*2+index
                try:
                    obj = objs[i]
                except IndexError:
                    raise PDFSyntaxError('Invalid object number: objid=%r' % (objid))
                if isinstance(obj, PDFStream):
                    obj.set_objid(objid, 0)
            else:
                self._parser.seek(index)
                (_,objid1) = self._parser.nexttoken() # objid
                (_,genno) = self._parser.nexttoken() # genno
                (_,kwd) = self._parser.nexttoken()
                # #### hack around malformed pdf files
                #assert objid1 == objid, (objid, objid1)
                if objid1 != objid:
                    x = []
                    while kwd is not self.KEYWORD_OBJ:
                        (_,kwd) = self._parser.nexttoken()
                        x.append(kwd)
                    if x:
                        objid1 = x[-2]
                        genno = x[-1]
                # #### end hack around malformed pdf files
                if kwd is not self.KEYWORD_OBJ:
                    raise PDFSyntaxError('Invalid object spec: offset=%r' % index)
                try:
                    (_,obj) = self._parser.nextobject()
                    if isinstance(obj, PDFStream):
                        obj.set_objid(objid, genno)
                except PSEOF:
                    return None
            if 2 <= self.debug:
                print >>sys.stderr, 'register: objid=%r: %r' % (objid, obj)
            if self.caching:
                self._cached_objs[objid] = obj
        if self.decipher:
            obj = decipher_all(self.decipher, objid, genno, obj)
        return obj

    INHERITABLE_ATTRS = set(['Resources', 'MediaBox', 'CropBox', 'Rotate'])
    def get_pages(self):
        if not self.xrefs:
            raise PDFException('PDFDocument is not initialized')
        def search(obj, parent):
            if isinstance(obj, int):
                objid = obj
                tree = dict_value(self.getobj(objid)).copy()
            else:
                objid = obj.objid
                tree = dict_value(obj).copy()
            for (k,v) in parent.iteritems():
                if k in self.INHERITABLE_ATTRS and k not in tree:
                    tree[k] = v
            if tree.get('Type') is LITERAL_PAGES and 'Kids' in tree:
                if 1 <= self.debug:
                    print >>sys.stderr, 'Pages: Kids=%r' % tree['Kids']
                for c in list_value(tree['Kids']):
                    for x in search(c, tree):
                        yield x
            elif tree.get('Type') is LITERAL_PAGE:
                if 1 <= self.debug:
                    print >>sys.stderr, 'Page: %r' % tree
                yield (objid, tree)
        if 'Pages' not in self.catalog: return
        for (pageid,tree) in search(self.catalog['Pages'], self.catalog):
            yield PDFPage(self, pageid, tree)
        return

    def get_outlines(self):
        if 'Outlines' not in self.catalog:
            raise PDFNoOutlines
        def search(entry, level):
            entry = dict_value(entry)
            if 'Title' in entry:
                if 'A' in entry or 'Dest' in entry:
                    title = decode_text(str_value(entry['Title']))
                    dest = entry.get('Dest')
                    action = entry.get('A')
                    se = entry.get('SE')
                    yield (level, title, dest, action, se)
            if 'First' in entry and 'Last' in entry:
                for x in search(entry['First'], level+1):
                    yield x
            if 'Next' in entry:
                for x in search(entry['Next'], level):
                    yield x
            return
        return search(self.catalog['Outlines'], 0)

    def lookup_name(self, cat, key):
        try:
            names = dict_value(self.catalog['Names'])
        except (PDFTypeError, KeyError):
            raise KeyError((cat,key))
        # may raise KeyError
        d0 = dict_value(names[cat])
        def lookup(d):
            if 'Limits' in d:
                (k1,k2) = list_value(d['Limits'])
                if key < k1 or k2 < key: return None
                if 'Names' in d:
                    objs = list_value(d['Names'])
                    names = dict(choplist(2, objs))
                    return names[key]
            if 'Kids' in d:
                for c in list_value(d['Kids']):
                    v = lookup(dict_value(c))
                    if v: return v
            raise KeyError((cat,key))
        return lookup(d0)

    def get_dest(self, name):
        try:
            # PDF-1.2 or later
            obj = self.lookup_name('Dests', name)
        except KeyError:
            # PDF-1.1 or prior
            if 'Dests' not in self.catalog:
                raise PDFDestinationNotFound(name)
            d0 = dict_value(self.catalog['Dests'])
            if name not in d0:
                raise PDFDestinationNotFound(name)
            obj = d0[name]
        return obj


##  PDFParser
##
class PDFParser(PSStackParser):

    """
    PDFParser fetch PDF objects from a file stream.
    It can handle indirect references by referring to
    a PDF document set by set_document method.
    It also reads XRefs at the end of every PDF file.

    Typical usage:
      parser = PDFParser(fp)
      parser.read_xref()
      parser.set_document(doc)
      parser.seek(offset)
      parser.nextobject()
    
    """

    def __init__(self, fp):
        PSStackParser.__init__(self, fp)
        self.doc = None
        self.fallback = False
        return

    def set_document(self, doc):
        """Associates the parser with a PDFDocument object."""
        self.doc = doc
        return

    KEYWORD_R = KWD('R')
    KEYWORD_NULL = KWD('null')
    KEYWORD_ENDOBJ = KWD('endobj')
    KEYWORD_STREAM = KWD('stream')
    KEYWORD_XREF = KWD('xref')
    KEYWORD_STARTXREF = KWD('startxref')
    def do_keyword(self, pos, token):
        """Handles PDF-related keywords."""
        
        if token in (self.KEYWORD_XREF, self.KEYWORD_STARTXREF):
            self.add_results(*self.pop(1))
        
        elif token is self.KEYWORD_ENDOBJ:
            self.add_results(*self.pop(4))

        elif token is self.KEYWORD_NULL:
            # null object
            self.push((pos, None))

        elif token is self.KEYWORD_R:
            # reference to indirect object
            try:
                ((_,objid), (_,genno)) = self.pop(2)
                (objid, genno) = (int(objid), int(genno))
                obj = PDFObjRef(self.doc, objid, genno)
                self.push((pos, obj))
            except PSSyntaxError:
                pass

        elif token is self.KEYWORD_STREAM:
            # stream object
            ((_,dic),) = self.pop(1)
            dic = dict_value(dic)
            objlen = 0
            if not self.fallback:
                try:
                    objlen = int_value(dic['Length'])
                except KeyError:
                    if STRICT:
                        raise PDFSyntaxError('/Length is undefined: %r' % dic)
            self.seek(pos)
            try:
                (_, line) = self.nextline()  # 'stream'
            except PSEOF:
                if STRICT:
                    raise PDFSyntaxError('Unexpected EOF')
                return
            pos += len(line)
            self.fp.seek(pos)
            data = self.fp.read(objlen)
            self.seek(pos+objlen)
            while 1:
                try:
                    (linepos, line) = self.nextline()
                except PSEOF:
                    if STRICT:
                        raise PDFSyntaxError('Unexpected EOF')
                    break
                if 'endstream' in line:
                    i = line.index('endstream')
                    objlen += i
                    data += line[:i]
                    break
                objlen += len(line)
                data += line
            self.seek(pos+objlen)
            # XXX limit objlen not to exceed object boundary
            if 2 <= self.debug:
                print >>sys.stderr, 'Stream: pos=%d, objlen=%d, dic=%r, data=%r...' % \
                      (pos, objlen, dic, data[:10])
            obj = PDFStream(dic, data, self.doc.decipher)
            self.push((pos, obj))

        else:
            # others
            self.push((pos, token))
        
        return

    def find_xref(self):
        """Internal function used to locate the first XRef."""
        # search the last xref table by scanning the file backwards.
        prev = None
        for line in self.revreadlines():
            line = line.strip()
            if 2 <= self.debug:
                print >>sys.stderr, 'find_xref: %r' % line
            if line == 'startxref': break
            if line:
                prev = line
        else:
            raise PDFNoValidXRef('Unexpected EOF')
        if 1 <= self.debug:
            print >>sys.stderr, 'xref found: pos=%r' % prev
        return long(prev)

    # read xref table
    def read_xref_from(self, start, xrefs):
        """Reads XRefs from the given location."""
        self.seek(start)
        self.reset()
        try:
            (pos, token) = self.nexttoken()
        except PSEOF:
            raise PDFNoValidXRef('Unexpected EOF')
        if 2 <= self.debug:
            print >>sys.stderr, 'read_xref_from: start=%d, token=%r' % (start, token)
        if isinstance(token, int):
            # XRefStream: PDF-1.5
            self.seek(pos)
            self.reset()
            xref = PDFXRefStream()
            xref.load(self, debug=self.debug)
        else:
            if token is self.KEYWORD_XREF:
                self.nextline()
            xref = PDFXRef()
            xref.load(self, debug=self.debug)
        xrefs.append(xref)
        trailer = xref.get_trailer()
        if 1 <= self.debug:
            print >>sys.stderr, 'trailer: %r' % trailer
        if 'XRefStm' in trailer:
            pos = int_value(trailer['XRefStm'])
            self.read_xref_from(pos, xrefs)
        if 'Prev' in trailer:
            # find previous xref
            pos = int_value(trailer['Prev'])
            self.read_xref_from(pos, xrefs)
        return

    # read xref tables and trailers
    def read_xref(self):
        """Reads all the XRefs in the PDF file and returns them."""
        xrefs = []
        try:
            pos = self.find_xref()
            self.read_xref_from(pos, xrefs)
        except PDFNoValidXRef:
            # fallback
            if 1 <= self.debug:
                print >>sys.stderr, 'no xref, fallback'
            self.fallback = True
            xref = PDFXRef()
            xref.load_fallback(self)
            xrefs.append(xref)
        return xrefs


##  PDFStreamParser
##
class PDFStreamParser(PDFParser):

    """
    PDFStreamParser is used to parse PDF content streams
    that is contained in each page and has instructions
    for rendering the page. A reference to a PDF document is
    needed because a PDF content stream can also have
    indirect references to other objects in the same document.
    """

    def __init__(self, data):
        PDFParser.__init__(self, StringIO(data))
        return

    def flush(self):
        self.add_results(*self.popall())
        return

    def do_keyword(self, pos, token):
        if token is self.KEYWORD_R:
            # reference to indirect object
            try:
                ((_,objid), (_,genno)) = self.pop(2)
                (objid, genno) = (int(objid), int(genno))
                obj = PDFObjRef(self.doc, objid, genno)
                self.push((pos, obj))
            except PSSyntaxError:
                pass
            return
        # others
        self.push((pos, token))
        return
