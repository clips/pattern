#### PATTERN | CACHE ###############################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

from io import open

try:
    import hashlib
    md5 = hashlib.md5
except:
    import md5
    md5 = md5.new

from pattern.helpers import encode_string, decode_string

decode_utf8 = decode_string
encode_utf8 = encode_string

#### CACHE #########################################################################################
# Caching is implemented in URL.download(), which is used by all other downloaders.

import os
import glob
import tempfile
import datetime

from io import open

from codecs import BOM_UTF8
BOM_UTF8 = BOM_UTF8.decode('utf-8')

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
        f = open(self._hash(k), "w", encoding = "utf-8")
        f.write(BOM_UTF8)
        v = decode_utf8(v)
        f.write(v)
        f.close()

    def __delitem__(self, k):
        try:
            os.unlink(self._hash(k))
        except OSError:
            pass

    def get(self, k, unicode=True):
        """ Returns the data stored with the given id.
            With unicode=True, returns a Unicode string.
        """
        if k in self:
            f = open(self._hash(k), "rb")
            v = f.read().lstrip(BOM_UTF8.encode("utf-8"))
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
