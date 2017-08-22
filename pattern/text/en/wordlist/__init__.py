#### PATTERN | VECTOR | WORDLIST ###################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

import os
from io import open

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""


class Wordlist(object):

    def __init__(self, name, data=[]):
        """ Lazy read-only list of words.
        """
        self._name = name
        self._data = data

    def _load(self):
        if not self._data:
            self._data = open(os.path.join(MODULE, self._name + ".txt")).read().split(", ")

    def __repr__(self):
        self._load()
        return repr(self._data)

    def __iter__(self):
        self._load()
        return iter(self._data)

    def __len__(self):
        self._load()
        return len(self._data)

    def __contains__(self, w):
        self._load()
        return w in self._data

    def __add__(self, iterable):
        self._load()
        return Wordlist(None, data=sorted(self._data + list(iterable)))

    def __getitem__(self, i):
        self._load()
        return self._data[i]

    def __setitem__(self, i, v):
        self._load()
        self._data[i] = v

    def insert(self, i, v):
        self._load()
        self._data.insert(i, v)

    def append(self, v):
        self._load()
        self._data.append(v)

    def extend(self, v):
        self._load()
        self._data.extend(v)

ACADEMIC  = Wordlist("academic")  # English academic words.
BASIC     = Wordlist("basic")     # English basic words (850) that express 90% of concepts.
PROFANITY = Wordlist("profanity") # English swear words.
TIME      = Wordlist("time")      # English time and date words.
STOPWORDS = Wordlist("stopwords") # English stop words ("a", "the", ...).

# Note: if used for lookups, performance can be increased by using a dict:
# blacklist = dict.fromkeys(PROFANITY+TIME, True)
# for i in range(1000):
#    corpus.append(Document(src[i], exclude=blacklist))
