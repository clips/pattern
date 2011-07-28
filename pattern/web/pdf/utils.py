#!/usr/bin/env python2
"""
Miscellaneous Routines.
"""
import struct
from sys import maxint as INF


##  Matrix operations
##
MATRIX_IDENTITY = (1, 0, 0, 1, 0, 0)

def mult_matrix((a1,b1,c1,d1,e1,f1), (a0,b0,c0,d0,e0,f0)):
    """Returns the multiplication of two matrices."""
    return (a0*a1+c0*b1,    b0*a1+d0*b1,
            a0*c1+c0*d1,    b0*c1+d0*d1,
            a0*e1+c0*f1+e0, b0*e1+d0*f1+f0)

def translate_matrix((a,b,c,d,e,f), (x,y)):
    """Translates a matrix by (x,y)."""
    return (a,b,c,d,x*a+y*c+e,x*b+y*d+f)

def apply_matrix_pt((a,b,c,d,e,f), (x,y)):
    """Applies a matrix to a point."""
    return (a*x+c*y+e, b*x+d*y+f)

def apply_matrix_norm((a,b,c,d,e,f), (p,q)):
    """Equivalent to apply_matrix_pt(M, (p,q)) - apply_matrix_pt(M, (0,0))"""
    return (a*p+c*q, b*p+d*q)


##  Utility functions
##

# uniq
def uniq(objs):
    """Eliminates duplicated elements."""
    done = set()
    for obj in objs:
        if obj in done: continue
        done.add(obj)
        yield obj
    return

# csort
def csort(objs, key=lambda x:x):
    """Order-preserving sorting function."""
    idxs = dict( (obj,i) for (i,obj) in enumerate(objs) )
    return sorted(objs, key=lambda obj: (key(obj), idxs[obj]))

# fsplit
def fsplit(pred, objs):
    """Split a list into two classes according to the predicate."""
    t = []
    f = []
    for obj in objs:
        if pred(obj):
            t.append(obj)
        else:
            f.append(obj)
    return (t,f)

# drange
def drange(v0, v1, d):
    """Returns a discrete range."""
    assert v0 < v1
    return xrange(int(v0)/d, int(v1+d-1)/d)

# get_bound
def get_bound(pts):
    """Compute a minimal rectangle that covers all the points."""
    (x0, y0, x1, y1) = (INF, INF, -INF, -INF)
    for (x,y) in pts:
        x0 = min(x0, x)
        y0 = min(y0, y)
        x1 = max(x1, x)
        y1 = max(y1, y)
    return (x0,y0,x1,y1)

# pick
def pick(seq, func, maxobj=None):
    """Picks the object obj where func(obj) has the highest value."""
    maxscore = None
    for obj in seq:
        score = func(obj)
        if maxscore is None or maxscore < score:
            (maxscore,maxobj) = (score,obj)
    return maxobj

# choplist
def choplist(n, seq):
    """Groups every n elements of the list."""
    r = []
    for x in seq:
        r.append(x)
        if len(r) == n:
            yield tuple(r)
            r = []
    return

# nunpack
def nunpack(s, default=0):
    """Unpacks 1 to 4 byte integers (big endian)."""
    l = len(s)
    if not l:
        return default
    elif l == 1:
        return ord(s)
    elif l == 2:
        return struct.unpack('>H', s)[0]
    elif l == 3:
        return struct.unpack('>L', '\x00'+s)[0]
    elif l == 4:
        return struct.unpack('>L', s)[0]
    else:
        raise TypeError('invalid length: %d' % l)

# decode_text
PDFDocEncoding = ''.join( unichr(x) for x in (
  0x0000, 0x0001, 0x0002, 0x0003, 0x0004, 0x0005, 0x0006, 0x0007,
  0x0008, 0x0009, 0x000a, 0x000b, 0x000c, 0x000d, 0x000e, 0x000f,
  0x0010, 0x0011, 0x0012, 0x0013, 0x0014, 0x0015, 0x0017, 0x0017,
  0x02d8, 0x02c7, 0x02c6, 0x02d9, 0x02dd, 0x02db, 0x02da, 0x02dc,
  0x0020, 0x0021, 0x0022, 0x0023, 0x0024, 0x0025, 0x0026, 0x0027,
  0x0028, 0x0029, 0x002a, 0x002b, 0x002c, 0x002d, 0x002e, 0x002f,
  0x0030, 0x0031, 0x0032, 0x0033, 0x0034, 0x0035, 0x0036, 0x0037,
  0x0038, 0x0039, 0x003a, 0x003b, 0x003c, 0x003d, 0x003e, 0x003f,
  0x0040, 0x0041, 0x0042, 0x0043, 0x0044, 0x0045, 0x0046, 0x0047,
  0x0048, 0x0049, 0x004a, 0x004b, 0x004c, 0x004d, 0x004e, 0x004f,
  0x0050, 0x0051, 0x0052, 0x0053, 0x0054, 0x0055, 0x0056, 0x0057,
  0x0058, 0x0059, 0x005a, 0x005b, 0x005c, 0x005d, 0x005e, 0x005f,
  0x0060, 0x0061, 0x0062, 0x0063, 0x0064, 0x0065, 0x0066, 0x0067,
  0x0068, 0x0069, 0x006a, 0x006b, 0x006c, 0x006d, 0x006e, 0x006f,
  0x0070, 0x0071, 0x0072, 0x0073, 0x0074, 0x0075, 0x0076, 0x0077,
  0x0078, 0x0079, 0x007a, 0x007b, 0x007c, 0x007d, 0x007e, 0x0000,
  0x2022, 0x2020, 0x2021, 0x2026, 0x2014, 0x2013, 0x0192, 0x2044,
  0x2039, 0x203a, 0x2212, 0x2030, 0x201e, 0x201c, 0x201d, 0x2018,
  0x2019, 0x201a, 0x2122, 0xfb01, 0xfb02, 0x0141, 0x0152, 0x0160,
  0x0178, 0x017d, 0x0131, 0x0142, 0x0153, 0x0161, 0x017e, 0x0000,
  0x20ac, 0x00a1, 0x00a2, 0x00a3, 0x00a4, 0x00a5, 0x00a6, 0x00a7,
  0x00a8, 0x00a9, 0x00aa, 0x00ab, 0x00ac, 0x0000, 0x00ae, 0x00af,
  0x00b0, 0x00b1, 0x00b2, 0x00b3, 0x00b4, 0x00b5, 0x00b6, 0x00b7,
  0x00b8, 0x00b9, 0x00ba, 0x00bb, 0x00bc, 0x00bd, 0x00be, 0x00bf,
  0x00c0, 0x00c1, 0x00c2, 0x00c3, 0x00c4, 0x00c5, 0x00c6, 0x00c7,
  0x00c8, 0x00c9, 0x00ca, 0x00cb, 0x00cc, 0x00cd, 0x00ce, 0x00cf,
  0x00d0, 0x00d1, 0x00d2, 0x00d3, 0x00d4, 0x00d5, 0x00d6, 0x00d7,
  0x00d8, 0x00d9, 0x00da, 0x00db, 0x00dc, 0x00dd, 0x00de, 0x00df,
  0x00e0, 0x00e1, 0x00e2, 0x00e3, 0x00e4, 0x00e5, 0x00e6, 0x00e7,
  0x00e8, 0x00e9, 0x00ea, 0x00eb, 0x00ec, 0x00ed, 0x00ee, 0x00ef,
  0x00f0, 0x00f1, 0x00f2, 0x00f3, 0x00f4, 0x00f5, 0x00f6, 0x00f7,
  0x00f8, 0x00f9, 0x00fa, 0x00fb, 0x00fc, 0x00fd, 0x00fe, 0x00ff,
))
def decode_text(s):
    """Decodes a PDFDocEncoding string to Unicode."""
    if s.startswith('\xfe\xff'):
        return unicode(s[2:], 'utf-16be', 'ignore')
    else:
        return ''.join( PDFDocEncoding[ord(c)] for c in s )

# enc
def enc(x, codec='ascii'):
    """Encodes a string for SGML/XML/HTML"""
    x = x.replace('&','&amp;').replace('>','&gt;').replace('<','&lt;').replace('"','&quot;')
    return x.encode(codec, 'xmlcharrefreplace')

def bbox2str((x0,y0,x1,y1)):
    return '%.3f,%.3f,%.3f,%.3f' % (x0, y0, x1, y1)

def matrix2str((a,b,c,d,e,f)):
    return '[%.2f,%.2f,%.2f,%.2f, (%.2f,%.2f)]' % (a,b,c,d,e,f)


##  ObjIdRange
##
class ObjIdRange(object):

    "A utility class to represent a range of object IDs."
    
    def __init__(self, start, nobjs):
        self.start = start
        self.nobjs = nobjs
        return

    def __repr__(self):
        return '<ObjIdRange: %d-%d>' % (self.get_start_id(), self.get_end_id())

    def get_start_id(self):
        return self.start

    def get_end_id(self):
        return self.start + self.nobjs - 1

    def get_nobjs(self):
        return self.nobjs


##  Plane
##
##  A set-like data structure for objects placed on a plane.
##  Can efficiently find objects in a certain rectangular area.
##  It maintains two parallel lists of objects, each of
##  which is sorted by its x or y coordinate.
##
class Plane(object):

    def __init__(self, objs=None, gridsize=50):
        self._objs = []
        self._grid = {}
        self.gridsize = gridsize
        if objs is not None:
            for obj in objs:
                self.add(obj)
        return

    def __repr__(self):
        return ('<Plane objs=%r>' % list(self))

    def __iter__(self):
        return iter(self._objs)

    def __len__(self):
        return len(self._objs)

    def __contains__(self, obj):
        return obj in self._objs

    def _getrange(self, (x0,y0,x1,y1)):
        for y in drange(y0, y1, self.gridsize):
            for x in drange(x0, x1, self.gridsize):
                yield (x,y)
        return
    
    # add(obj): place an object.
    def add(self, obj):
        for k in self._getrange((obj.x0, obj.y0, obj.x1, obj.y1)):
            if k not in self._grid:
                r = []
                self._grid[k] = r
            else:
                r = self._grid[k]
            r.append(obj)
        self._objs.append(obj)
        return

    # remove(obj): displace an object.
    def remove(self, obj):
        for k in self._getrange((obj.x0, obj.y0, obj.x1, obj.y1)):
            try:
                self._grid[k].remove(obj)
            except (KeyError, ValueError):
                pass
        self._objs.remove(obj)
        return

    # find(): finds objects that are in a certain area.
    def find(self, (x0,y0,x1,y1)):
        done = set()
        for k in self._getrange((x0,y0,x1,y1)):
            if k not in self._grid: continue
            for obj in self._grid[k]:
                if obj in done: continue
                done.add(obj)
                if (obj.x1 <= x0 or x1 <= obj.x0 or
                    obj.y1 <= y0 or y1 <= obj.y0): continue
                yield obj
        return


# create_bmp
def create_bmp(data, bits, width, height):
    info = struct.pack('<IiiHHIIIIII', 40, width, height, 1, bits, 0, len(data), 0, 0, 0, 0)
    assert len(info) == 40, len(info)
    header = struct.pack('<ccIHHI', 'B', 'M', 14+40+len(data), 0, 0, 14+40)
    assert len(header) == 14, len(header)
    # XXX re-rasterize every line
    return header+info+data
