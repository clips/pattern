#### PATTERN | CACHE ###############################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

try:
    import hashlib; md5=hashlib.md5
except:
    import md5; md5=md5.new

#### UNICODE #######################################################################################
    
def decode_string(v, encoding="utf-8"):
    """ Returns the given value as a Unicode string (if possible).
    """
    if isinstance(encoding, basestring):
        encoding = ((encoding,),) + (("windows-1252",), ("utf-8", "ignore"))
    if isinstance(v, str):
        for e in encoding:
            try: return v.decode(*e)
            except:
                pass
        return v
    return unicode(v)

def encode_string(v, encoding="utf-8"):
    """ Returns the given value as a Python byte string (if possible).
    """
    if isinstance(encoding, basestring):
        encoding = ((encoding,),) + (("windows-1252",), ("utf-8", "ignore"))
    if isinstance(v, unicode):
        for e in encoding:
            try: return v.encode(*e)
            except:
                pass
        return v
    return str(v)

decode_utf8 = decode_string
encode_utf8 = encode_string

#### CACHE #########################################################################################
# Caching is implemented in URL.download(), which is used by all other downloaders.

import os
import glob
import tempfile
import codecs
import datetime

try: 
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

TMP = os.path.join(tempfile.gettempdir(), "pattern_web")

def date_now():
    return datetime.datetime.today()
def date_modified(path):
    return datetime.datetime.fromtimestamp(os.stat(path)[8])

class Cache(object):
    
    def __init__(self, path=os.path.join(MODULE, "tmp")):
        """ Cache with data stored as files with hashed filenames.
            Content retrieved from URLs and search engines are stored in cache for performance.
            The path where the cache is stored can be given. This way you can manage persistent
            sets of downloaded data. If path=TMP, cached items are stored in a temporary folder.
        """
        self.path = path
        
    def _get_path(self):
        return self._path
    def _set_path(self, path):
        if not os.path.isdir(path): 
            os.makedirs(path)
        self._path = path
    path = property(_get_path, _set_path)
    
    def _hash(self, k):
        k = encode_utf8(k) # MD5 works on Python byte strings.
        return os.path.join(self.path, md5(k).hexdigest())
    
    def __len__(self):
        return len(glob.glob(os.path.join(self.path, "*")))

    def __contains__(self, k):
        return os.path.exists(self._hash(k))
    
    def __getitem__(self, k):
        return self.get(k)

    def __setitem__(self, k, v):
        f = open(self._hash(k), "wb")
        f.write(codecs.BOM_UTF8)
        f.write(encode_utf8(v))
        f.close()

    def __delitem__(self, k):
        try: os.unlink(self._hash(k))
        except OSError:
            pass

    def get(self, k, unicode=True):
        """ Returns the data stored with the given id.
            With unicode=True, returns a Unicode string.
        """
        if k in self:
            f = open(self._hash(k), "rb"); v=f.read().lstrip(codecs.BOM_UTF8)
            f.close()
            if unicode is True:
                return decode_utf8(v)
            else:
                return v
        raise KeyError(k)

    def age(self, k):
        """ Returns the age of the cached item, in days.
        """
        p = self._hash(k)
        return os.path.exists(p) and (date_now() - date_modified(p)).days or 0
            
    def clear(self, age=None):
        """ Clears all items from the cache (whose age is the given amount of days or older).
        """
        n = date_now()
        for p in glob.glob(os.path.join(self.path, "*")):
            if age is None or (n - date_modified(p)).days >= age:
                os.unlink(p)
        
cache = Cache()