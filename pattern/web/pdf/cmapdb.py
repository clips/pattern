#!/usr/bin/env python2

""" Adobe character mapping (CMap) support.

CMaps provide the mapping between character codes and Unicode
code-points to character ids (CIDs).

More information is available on the Adobe website:

  http://opensource.adobe.com/wiki/display/cmap/CMap+Resources

"""

import sys
import re
import os
import os.path
import gzip
import cPickle as pickle
import cmap
import struct
from psparser import PSStackParser
from psparser import PSException, PSSyntaxError, PSTypeError, PSEOF
from psparser import PSLiteral, PSKeyword
from psparser import literal_name, keyword_name
from encodingdb import name2unicode
from utils import choplist, nunpack


class CMapError(Exception): pass


##  CMap
##
class CMap(object):

    debug = 0

    def __init__(self, code2cid=None):
        self.code2cid = code2cid or {}
        return

    def is_vertical(self):
        return False

    def use_cmap(self, cmap):
        assert isinstance(cmap, CMap)
        def copy(dst, src):
            for (k,v) in src.iteritems():
                if isinstance(v, dict):
                    d = {}
                    dst[k] = d
                    copy(d, v)
                else:
                    dst[k] = v
        copy(self.code2cid, cmap.code2cid)
        return

    def decode(self, code):
        if self.debug:
            print >>sys.stderr, 'decode: %r, %r' % (self, code)
        d = self.code2cid
        for c in code:
            c = ord(c)
            if c in d:
                d = d[c]
                if isinstance(d, int):
                    yield d
                    d = self.code2cid
            else:
                d = self.code2cid
        return

    def dump(self, out=sys.stdout, code2cid=None, code=None):
        if code2cid is None:
            code2cid = self.code2cid
            code = ()
        for (k,v) in sorted(code2cid.iteritems()):
            c = code+(k,)
            if isinstance(v, int):
                out.write('code %r = cid %d\n' % (c,v))
            else:
                self.dump(out=out, code2cid=v, code=c)
        return
    

##  IdentityCMap
##
class IdentityCMap(object):

    def __init__(self, vertical):
        self.vertical = vertical
        return

    def is_vertical(self):
        return self.vertical

    def decode(self, code):
        n = len(code)/2
        if n:
            return struct.unpack('>%dH' % n, code)
        else:
            return ()
        
            

##  UnicodeMap
##
class UnicodeMap(object):

    debug = 0

    def __init__(self, cid2unichr=None):
        self.cid2unichr = cid2unichr or {}
        return

    def get_unichr(self, cid):
        if self.debug:
            print >>sys.stderr, 'get_unichr: %r, %r' % (self, cid)
        return self.cid2unichr[cid]

    def dump(self, out=sys.stdout):
        for (k,v) in sorted(self.cid2unichr.iteritems()):
            out.write('cid %d = unicode %r\n' % (k,v))
        return


##  FileCMap
##
class FileCMap(CMap):

    def __init__(self):
        CMap.__init__(self)
        self.attrs = {}
        return

    def __repr__(self):
        return '<CMap: %s>' % self.attrs.get('CMapName')

    def is_vertical(self):
        return self.attrs.get('WMode', 0) != 0

    def set_attr(self, k, v):
        self.attrs[k] = v
        return

    def add_code2cid(self, code, cid):
        assert isinstance(code, str) and isinstance(cid, int)
        d = self.code2cid
        for c in code[:-1]:
            c = ord(c)
            if c in d:
                d = d[c]
            else:
                t = {}
                d[c] = t
                d =t
        c = ord(code[-1])
        d[c] = cid
        return


##  FileUnicodeMap
##
class FileUnicodeMap(UnicodeMap):
    
    def __init__(self):
        UnicodeMap.__init__(self)
        self.attrs = {}
        return

    def __repr__(self):
        return '<UnicodeMap: %s>' % self.attrs.get('CMapName')

    def set_attr(self, k, v):
        self.attrs[k] = v
        return

    def add_cid2unichr(self, cid, code):
        assert isinstance(cid, int)
        if isinstance(code, PSLiteral):
            # Interpret as an Adobe glyph name.
            self.cid2unichr[cid] = name2unicode(code.name)
        elif isinstance(code, str):
            # Interpret as UTF-16BE.
            self.cid2unichr[cid] = unicode(code, 'UTF-16BE', 'ignore')
        elif isinstance(code, int):
            self.cid2unichr[cid] = unichr(code)
        else:
            raise TypeError(code)
        return


##  PyCMap
##
class PyCMap(CMap):

    def __init__(self, name, module):
        CMap.__init__(self, module.CODE2CID)
        self.name = name
        self._is_vertical = module.IS_VERTICAL
        return

    def __repr__(self):
        return '<PyCMap: %s>' % (self.name)

    def is_vertical(self):
        return self._is_vertical
    

##  PyUnicodeMap
##
class PyUnicodeMap(UnicodeMap):
    
    def __init__(self, name, module, vertical):
        if vertical:
            cid2unichr = module.CID2UNICHR_V
        else:
            cid2unichr = module.CID2UNICHR_H
        UnicodeMap.__init__(self, cid2unichr)
        self.name = name
        return

    def __repr__(self):
        return '<PyUnicodeMap: %s>' % (self.name)


##  CMapDB
##
class CMapDB(object):

    debug = 0
    _cmap_cache = {}
    _umap_cache = {}
    
    class CMapNotFound(CMapError): pass

    @classmethod
    def _load_data(klass, name):
        filename = '%s.pickle.gz' % name
        if klass.debug:
            print >>sys.stderr, 'loading:', name
        default_path = os.environ.get('CMAP_PATH', '/usr/share/pdfminer/')
        for directory in (os.path.dirname(cmap.__file__), default_path):
            path = os.path.join(directory, filename)
            if os.path.exists(path):
                gzfile = gzip.open(path)
                try:
                    return type(name, (), pickle.loads(gzfile.read()))
                finally:
                    gzfile.close()
        else:
            raise CMapDB.CMapNotFound(name)

    @classmethod
    def get_cmap(klass, name):
        if name == 'Identity-H':
            return IdentityCMap(False)
        elif name == 'Identity-V':
            return IdentityCMap(True)
        try:
            return klass._cmap_cache[name]
        except KeyError:
            pass
        data = klass._load_data(name)
        klass._cmap_cache[name] = cmap = PyCMap(name, data)
        return cmap

    @classmethod
    def get_unicode_map(klass, name, vertical=False):
        try:
            return klass._umap_cache[name][vertical]
        except KeyError:
            pass
        data = klass._load_data('to-unicode-%s' % name)
        klass._umap_cache[name] = umaps = [PyUnicodeMap(name, data, v) for v in (False, True)]
        return umaps[vertical]


##  CMapParser
##
class CMapParser(PSStackParser):

    def __init__(self, cmap, fp):
        PSStackParser.__init__(self, fp)
        self.cmap = cmap
        self._in_cmap = False
        return

    def run(self):
        try:
            self.nextobject()
        except PSEOF:
            pass
        return

    def do_keyword(self, pos, token):
        name = token.name
        if name == 'begincmap':
            self._in_cmap = True
            self.popall()
            return
        elif name == 'endcmap':
            self._in_cmap = False
            return
        if not self._in_cmap: return
        #
        if name == 'def':
            try:
                ((_,k),(_,v)) = self.pop(2)
                self.cmap.set_attr(literal_name(k), v)
            except PSSyntaxError:
                pass
            return

        if name == 'usecmap':
            try:
                ((_,cmapname),) = self.pop(1)
                self.cmap.use_cmap(CMapDB.get_cmap(literal_name(cmapname)))
            except PSSyntaxError:
                pass
            except CMapDB.CMapNotFound:
                pass
            return

        if name == 'begincodespacerange':
            self.popall()
            return
        if name == 'endcodespacerange':
            self.popall()
            return

        if name == 'begincidrange':
            self.popall()
            return
        if name == 'endcidrange':
            objs = [ obj for (_,obj) in self.popall() ]
            for (s,e,cid) in choplist(3, objs):
                if (not isinstance(s, str) or not isinstance(e, str) or
                    not isinstance(cid, int) or len(s) != len(e)): continue
                sprefix = s[:-4]
                eprefix = e[:-4]
                if sprefix != eprefix: continue
                svar = s[-4:]
                evar = e[-4:]
                s1 = nunpack(svar)
                e1 = nunpack(evar)
                vlen = len(svar)
                #assert s1 <= e1
                for i in xrange(e1-s1+1):
                    x = sprefix+struct.pack('>L',s1+i)[-vlen:]
                    self.cmap.add_code2cid(x, cid+i)
            return

        if name == 'begincidchar':
            self.popall()
            return
        if name == 'endcidchar':
            objs = [ obj for (_,obj) in self.popall() ]
            for (cid,code) in choplist(2, objs):
                if isinstance(code, str) and isinstance(cid, str):
                    self.cmap.add_code2cid(code, nunpack(cid))
            return

        if name == 'beginbfrange':
            self.popall()
            return
        if name == 'endbfrange':
            objs = [ obj for (_,obj) in self.popall() ]
            for (s,e,code) in choplist(3, objs):
                if (not isinstance(s, str) or not isinstance(e, str) or
                    len(s) != len(e)): continue
                s1 = nunpack(s)
                e1 = nunpack(e)
                #assert s1 <= e1
                if isinstance(code, list):
                    for i in xrange(e1-s1+1):
                        self.cmap.add_cid2unichr(s1+i, code[i])
                else:
                    var = code[-4:]
                    base = nunpack(var)
                    prefix = code[:-4]
                    vlen = len(var)
                    for i in xrange(e1-s1+1):
                        x = prefix+struct.pack('>L',base+i)[-vlen:]
                        self.cmap.add_cid2unichr(s1+i, x)
            return

        if name == 'beginbfchar':
            self.popall()
            return
        if name == 'endbfchar':
            objs = [ obj for (_,obj) in self.popall() ]
            for (cid,code) in choplist(2, objs):
                if isinstance(cid, str) and isinstance(code, str):
                    self.cmap.add_cid2unichr(nunpack(cid), code)
            return

        if name == 'beginnotdefrange':
            self.popall()
            return
        if name == 'endnotdefrange':
            self.popall()
            return

        self.push((pos, token))
        return

# test
def main(argv):
    args = argv[1:]
    for fname in args:
        fp = file(fname, 'rb')
        cmap = FileUnicodeMap()
        #cmap = FileCMap()
        CMapParser(cmap, fp).run()
        fp.close()
        cmap.dump()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
