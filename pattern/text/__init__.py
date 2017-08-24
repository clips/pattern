#### PATTERN | TEXT | PARSER #######################################################################
# -*- coding: utf-8 -*-
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
import sys
import re
import string
import types
import codecs

from io import open

from codecs import BOM_UTF8
BOM_UTF8 = BOM_UTF8.decode('utf-8')

from xml.etree import cElementTree
from itertools import chain
from math import log

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

from pattern.text.tree import Tree, Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table
from pattern.text.tree import SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR

DEFAULT = "default"

from pattern.helpers import encode_string, decode_string

decode_utf8 = decode_string
encode_utf8 = encode_string

PUNCTUATION = ".,;:!?()[]{}`'\"@#$^&*+-|=~_"


def ngrams(string, n=3, punctuation=PUNCTUATION, continuous=False):
    """ Returns a list of n-grams (tuples of n successive words) from the given string.
        Alternatively, you can supply a Text or Sentence object.
        With continuous=False, n-grams will not run over sentence markers (i.e., .!?).
        Punctuation marks are stripped from words.
    """
    def strip_punctuation(s, punctuation=set(punctuation)):
        return [w for w in s if (isinstance(w, Word) and w.string or w) not in punctuation]
    if n <= 0:
        return []
    if isinstance(string, list):
        s = [strip_punctuation(string)]
    if isinstance(string, str):
        s = [strip_punctuation(s.split(" ")) for s in tokenize(string)]
    if isinstance(string, Sentence):
        s = [strip_punctuation(string)]
    if isinstance(string, Text):
        s = [strip_punctuation(s) for s in string]
    if continuous:
        s = [sum(s, [])]
    g = []
    for s in s:
        #s = [None] + s + [None]
        g.extend([tuple(s[i:i + n]) for i in range(len(s) - n + 1)])
    return g

FLOODING = re.compile(r"((.)\2{2,})", re.I) # ooo, xxx, !!!, ...


def deflood(s, n=3):
    """ Returns the string with no more than n repeated characters, e.g.,
        deflood("NIIIICE!!", n=1) => "Nice!"
        deflood("nice.....", n=3) => "nice..."
    """
    if n == 0:
        return s[0:0]
    return re.sub(r"((.)\2{%s,})" % (n - 1), lambda m: m.group(1)[0] * n, s)


def decamel(s, separator="_"):
    """ Returns the string with CamelCase converted to underscores, e.g.,
        decamel("TomDeSmedt", "-") => "tom-de-smedt"
        decamel("getHTTPResponse2) => "get_http_response2"
    """
    s = re.sub(r"([a-z0-9])([A-Z])", "\\1%s\\2" % separator, s)
    s = re.sub(r"([A-Z])([A-Z][a-z])", "\\1%s\\2" % separator, s)
    s = s.lower()
    return s


def pprint(string, token=[WORD, POS, CHUNK, PNP], column=4):
    """ Pretty-prints the output of Parser.parse() as a table with outlined columns.
        Alternatively, you can supply a tree.Text or tree.Sentence object.
    """
    if isinstance(string, str):
        print("\n\n".join([table(sentence, fill=column) for sentence in Text(string, token)]))
    if isinstance(string, Text):
        print("\n\n".join([table(sentence, fill=column) for sentence in string]))
    if isinstance(string, Sentence):
        print(table(string, fill=column))

#--- LAZY DICTIONARY -------------------------------------------------------------------------------
# A lazy dictionary is empty until one of its methods is called.
# This way many instances (e.g., lexicons) can be created without using memory until used.


class lazydict(dict):

    def load(self):
        # Must be overridden in a subclass.
        # Must load data with dict.__setitem__(self, k, v) instead of lazydict[k] = v.
        pass

    def _lazy(self, method, *args):
        """ If the dictionary is empty, calls lazydict.load().
            Replaces lazydict.method() with dict.method() and calls it.
        """
        if dict.__len__(self) == 0:
            self.load()
            setattr(self, method, types.MethodType(getattr(dict, method), self))
        return getattr(dict, method)(self, *args)

    def __repr__(self):
        return self._lazy("__repr__")

    def __len__(self):
        return self._lazy("__len__")

    def __iter__(self):
        return self._lazy("__iter__")

    def __contains__(self, *args):
        return self._lazy("__contains__", *args)

    def __getitem__(self, *args):
        return self._lazy("__getitem__", *args)

    def __setitem__(self, *args):
        return self._lazy("__setitem__", *args)

    def __delitem__(self, *args):
        return self._lazy("__delitem__", *args)

    def setdefault(self, *args):
        return self._lazy("setdefault", *args)

    def get(self, *args, **kwargs):
        return self._lazy("get", *args)

    def items(self):
        return self._lazy("items")

    def keys(self):
        return self._lazy("keys")

    def values(self):
        return self._lazy("values")

    def update(self, *args):
        return self._lazy("update", *args)

    def pop(self, *args):
        return self._lazy("pop", *args)

    def popitem(self, *args):
        return self._lazy("popitem", *args)

#--- LAZY LIST -------------------------------------------------------------------------------------


class lazylist(list):

    def load(self):
        # Must be overridden in a subclass.
        # Must load data with list.append(self, v) instead of lazylist.append(v).
        pass

    def _lazy(self, method, *args):
        """ If the list is empty, calls lazylist.load().
            Replaces lazylist.method() with list.method() and calls it.
        """
        if list.__len__(self) == 0:
            self.load()
            setattr(self, method, types.MethodType(getattr(list, method), self))
        return getattr(list, method)(self, *args)

    def __repr__(self):
        return self._lazy("__repr__")

    def __len__(self):
        return self._lazy("__len__")

    def __iter__(self):
        return self._lazy("__iter__")

    def __contains__(self, *args):
        return self._lazy("__contains__", *args)

    def __getitem__(self, *args):
        return self._lazy("__getitem__", *args)

    def __setitem__(self, *args):
        return self._lazy("__setitem__", *args)

    def __delitem__(self, *args):
        return self._lazy("__delitem__", *args)

    def insert(self, *args):
        return self._lazy("insert", *args)

    def append(self, *args):
        return self._lazy("append", *args)

    def extend(self, *args):
        return self._lazy("extend", *args)

    def remove(self, *args):
        return self._lazy("remove", *args)

    def pop(self, *args):
        return self._lazy("pop", *args)

    def index(self, *args):
        return self._lazy("index", *args)

    def count(self, *args):
        return self._lazy("count", *args)

#--- LAZY SET --------------------------------------------------------------------------------------


class lazyset(set):

    def load(self):
        # Must be overridden in a subclass.
        # Must load data with list.append(self, v) instead of lazylist.append(v).
        pass

    def _lazy(self, method, *args):
        """ If the list is empty, calls lazylist.load().
            Replaces lazylist.method() with list.method() and calls it.
        """
        print("!")
        if set.__len__(self) == 0:
            self.load()
            setattr(self, method, types.MethodType(getattr(set, method), self))
        return getattr(set, method)(self, *args)

    def __repr__(self):
        return self._lazy("__repr__")

    def __len__(self):
        return self._lazy("__len__")

    def __iter__(self):
        return self._lazy("__iter__")

    def __contains__(self, *args):
        return self._lazy("__contains__", *args)

    def __sub__(self, *args):
        return self._lazy("__sub__", *args)

    def __and__(self, *args):
        return self._lazy("__and__", *args)

    def __or__(self, *args):
        return self._lazy("__or__", *args)

    def __xor__(self, *args):
        return self._lazy("__xor__", *args)

    def __isub__(self, *args):
        return self._lazy("__isub__", *args)

    def __iand__(self, *args):
        return self._lazy("__iand__", *args)

    def __ior__(self, *args):
        return self._lazy("__ior__", *args)

    def __ixor__(self, *args):
        return self._lazy("__ixor__", *args)

    def __gt__(self, *args):
        return self._lazy("__gt__", *args)

    def __lt__(self, *args):
        return self._lazy("__lt__", *args)

    def __gte__(self, *args):
        return self._lazy("__gte__", *args)

    def __lte__(self, *args):
        return self._lazy("__lte__", *args)

    def add(self, *args):
        return self._lazy("add", *args)

    def pop(self, *args):
        return self._lazy("pop", *args)

    def remove(self, *args):
        return self._lazy("remove", *args)

    def discard(self, *args):
        return self._lazy("discard", *args)

    def isdisjoint(self, *args):
        return self._lazy("isdisjoint", *args)

    def issubset(self, *args):
        return self._lazy("issubset", *args)

    def issuperset(self, *args):
        return self._lazy("issuperset", *args)

    def union(self, *args):
        return self._lazy("union", *args)

    def intersection(self, *args):
        return self._lazy("intersection", *args)

    def difference(self, *args):
        return self._lazy("difference", *args)

#### PARSER ########################################################################################
# Pattern's text parsers are based on Brill's algorithm, or optionally on a trained language model.
# Brill's algorithm automatically acquires a lexicon of known words (aka tag dictionary),
# and a set of rules for tagging unknown words from a training corpus.
# Morphological rules are used to tag unknown words based on word suffixes (e.g., -ly = adverb).
# Contextual rules are used to tag unknown words based on a word's role in the sentence.
# Named entity rules are used to annotate proper nouns (NNP's: Google = NNP-ORG).
# When available, the parser will use a faster and more accurate language model (SLP, SVM, NB, ...).

#--- LEXICON ---------------------------------------------------------------------------------------


def _read(path, encoding="utf-8", comment=";;;"):
    """ Returns an iterator over the lines in the file at the given path,
        strippping comments and decoding each line to Unicode.
    """
    if path:
        if isinstance(path, str) and os.path.exists(path):
            # From file path.
            f = open(path, "r", encoding="utf-8")
        elif isinstance(path, str):
            # From string.
            f = path.splitlines()
        else:
            # From file or buffer.
            f = path
        for i, line in enumerate(f):
            line = line.strip(BOM_UTF8) if i == 0 and isinstance(line, str) else line
            line = line.strip()
            line = decode_utf8(line, encoding)
            if not line or (comment and line.startswith(comment)):
                continue
            yield line
    raise StopIteration


class Lexicon(lazydict):

    def __init__(self, path=""):
        """ A dictionary of known words and their part-of-speech tags.
        """
        self._path = path

    @property
    def path(self):
        return self._path

    def load(self):
        # Arnold NNP x
        dict.update(self, (x.split(" ")[:2] for x in _read(self._path)))

#--- FREQUENCY -------------------------------------------------------------------------------------


class Frequency(lazydict):

    def __init__(self, path=""):
        """ A dictionary of words and their relative document frequency.
        """
        self._path = path

    @property
    def path(self):
        return self._path

    def load(self):
        # and 0.4805
        for x in _read(self.path):
            x = x.split()
            dict.__setitem__(self, x[0], float(x[1]))

#--- LANGUAGE MODEL --------------------------------------------------------------------------------
# A language model determines the statistically most probable tag for an unknown word.
# A pattern.vector Classifier such as SLP can be used to produce a language model,
# by generalizing patterns from a treebank (i.e., a corpus of hand-tagged texts).
# For example:
# "generalizing/VBG from/IN patterns/NNS" and
# "dancing/VBG with/IN squirrels/NNS"
# both have a pattern -ing/VBG + [?] + NNS => IN.
# Unknown words preceded by -ing and followed by a plural noun will be tagged IN (preposition),
# unless (put simply) a majority of other patterns learned by the classifier disagrees.


class Model(object):

    def __init__(self, path="", classifier=None, known=set(), unknown=set()):
        """ A language model using a classifier (e.g., SLP, SVM) trained on morphology and context.
        """
        try:
            from pattern.vector import Classifier
            from pattern.vector import Perceptron
        except ImportError:
            sys.path.insert(0, os.path.join(MODULE, ".."))
            from vector import Classifier
            from vector import Perceptron
        self._path = path
        # Use a property instead of a subclass, so users can choose their own classifier.
        self._classifier = Classifier.load(path) if path else classifier or Perceptron()
        # Parser.lexicon entries can be ambiguous (e.g., about/IN  is RB 25% of the time).
        # Parser.lexicon entries also in Model.unknown are overruled by the model.
        # Parser.lexicon entries also in Model.known are not learned by the model
        # (only their suffix and context is learned, see Model._v() below).
        self.unknown = unknown | self._classifier._data.get("model_unknown", set())
        self.known = known

    @property
    def path(self):
        return self._path

    @classmethod
    def load(self, path="", lexicon={}):
        return Model(path, lexicon)

    def save(self, path, final=True):
        self._classifier._data["model_unknown"] = self.unknown
        self._classifier.save(path, final) # final = unlink training data (smaller file).

    def train(self, token, tag, previous=None, next=None):
        """ Trains the model to predict the given tag for the given token,
            in context of the given previous and next (token, tag)-tuples.
        """
        self._classifier.train(self._v(token, previous, next), type=tag)

    def classify(self, token, previous=None, next=None, **kwargs):
        """ Returns the predicted tag for the given token,
            in context of the given previous and next (token, tag)-tuples.
        """
        return self._classifier.classify(self._v(token, previous, next), **kwargs)

    def apply(self, token, previous=(None, None), next=(None, None)):
        """ Returns a (token, tag)-tuple for the given token,
            in context of the given previous and next (token, tag)-tuples.
        """
        return [token[0], self._classifier.classify(self._v(token[0], previous, next))]

    def _v(self, token, previous=None, next=None):
        """ Returns a training vector for the given token and its context.
        """
        def f(v, *s):
            v[" ".join(s)] = 1
        p, n = previous, next
        p = ("", "") if not p else (p[0] or "", p[1] or "")
        n = ("", "") if not n else (n[0] or "", n[1] or "")
        v = {}
        f(v, "b", "b")         # Bias.
        f(v, "h", token[:1])   # Capitalization.
        f(v, "w", token[-6:] if token not in self.known or token in self.unknown else "")
        f(v, "x", token[-3:])  # Word suffix.
        f(v, "-x", p[0][-3:])   # Word suffix left.
        f(v, "+x", n[0][-3:])   # Word suffix right.
        f(v, "-t", p[1])        # Tag left.
        f(v, "-+", p[1] + n[1]) # Tag left + right.
        f(v, "+t", n[1])        # Tag right.
        return v

    def _get_description(self):
        return self._classifier.description

    def _set_description(self, s):
        self._classifier.description = s

    description = property(_get_description, _set_description)

#--- MORPHOLOGICAL RULES ---------------------------------------------------------------------------
# Brill's algorithm generates lexical (i.e., morphological) rules in the following format:
# NN s fhassuf 1 NNS x => unknown words ending in -s and tagged NN change to NNS.
#     ly hassuf 2 RB x => unknown words ending in -ly change to RB.


class Morphology(lazylist):

    def __init__(self, path="", known={}):
        """ A list of rules based on word morphology (prefix, suffix).
        """
        self.known = known
        self._path = path
        self._cmd = set((
                "word", # Word is x.
                "char", # Word contains x.
             "haspref", # Word starts with x.
              "hassuf", # Word end with x.
             "addpref", # x + word is in lexicon.
              "addsuf", # Word + x is in lexicon.
          "deletepref", # Word without x at the start is in lexicon.
           "deletesuf", # Word without x at the end is in lexicon.
            "goodleft", # Word preceded by word x.
           "goodright", # Word followed by word x.
        ))
        self._cmd.update([("f" + x) for x in self._cmd])

    @property
    def path(self):
        return self._path

    def load(self):
        # ["NN", "s", "fhassuf", "1", "NNS", "x"]
        list.extend(self, (x.split() for x in _read(self._path)))

    def apply(self, token, previous=(None, None), next=(None, None)):
        """ Applies lexical rules to the given token, which is a [word, tag] list.
        """
        w = token[0]
        for r in self:
            if r[1] in self._cmd: # Rule = ly hassuf 2 RB x
                f, x, pos, cmd = bool(0), r[0], r[-2], r[1].lower()
            if r[2] in self._cmd: # Rule = NN s fhassuf 1 NNS x
                f, x, pos, cmd = bool(1), r[1], r[-2], r[2].lower().lstrip("f")
            if f and token[1] != r[0]:
                continue
            if (cmd == "word"       and x == w) \
            or (cmd == "char"       and x in w) \
            or (cmd == "haspref"    and w.startswith(x)) \
            or (cmd == "hassuf"     and w.endswith(x)) \
            or (cmd == "addpref"    and x + w in self.known) \
            or (cmd == "addsuf"     and w + x in self.known) \
            or (cmd == "deletepref" and w.startswith(x) and w[len(x):] in self.known) \
            or (cmd == "deletesuf"  and w.endswith(x) and w[:-len(x)] in self.known) \
            or (cmd == "goodleft"   and x == next[0]) \
            or (cmd == "goodright"  and x == previous[0]):
                token[1] = pos
        return token

    def insert(self, i, tag, affix, cmd="hassuf", tagged=None):
        """ Inserts a new rule that assigns the given tag to words with the given affix,
            e.g., Morphology.append("RB", "-ly").
        """
        if affix.startswith("-") and affix.endswith("-"):
            affix, cmd = affix[+1:-1], "char"
        if affix.startswith("-"):
            affix, cmd = affix[+1:-0], "hassuf"
        if affix.endswith("-"):
            affix, cmd = affix[+0:-1], "haspref"
        if tagged:
            r = [tagged, affix, "f" + cmd.lstrip("f"), tag, "x"]
        else:
            r = [affix, cmd.lstrip("f"), tag, "x"]
        lazylist.insert(self, i, r)

    def append(self, *args, **kwargs):
        self.insert(len(self) - 1, *args, **kwargs)

    def extend(self, rules=[]):
        for r in rules:
            self.append(*r)

#--- CONTEXT RULES ---------------------------------------------------------------------------------
# Brill's algorithm generates contextual rules in the following format:
# VBD VB PREVTAG TO => unknown word tagged VBD changes to VB if preceded by a word tagged TO.


class Context(lazylist):

    def __init__(self, path=""):
        """ A list of rules based on context (preceding and following words).
        """
        self._path = path
        self._cmd = set((
               "prevtag", # Preceding word is tagged x.
               "nexttag", # Following word is tagged x.
              "prev2tag", # Word 2 before is tagged x.
              "next2tag", # Word 2 after is tagged x.
           "prev1or2tag", # One of 2 preceding words is tagged x.
           "next1or2tag", # One of 2 following words is tagged x.
        "prev1or2or3tag", # One of 3 preceding words is tagged x.
        "next1or2or3tag", # One of 3 following words is tagged x.
           "surroundtag", # Preceding word is tagged x and following word is tagged y.
                 "curwd", # Current word is x.
                "prevwd", # Preceding word is x.
                "nextwd", # Following word is x.
            "prev1or2wd", # One of 2 preceding words is x.
            "next1or2wd", # One of 2 following words is x.
         "next1or2or3wd", # One of 3 preceding words is x.
         "prev1or2or3wd", # One of 3 following words is x.
             "prevwdtag", # Preceding word is x and tagged y.
             "nextwdtag", # Following word is x and tagged y.
             "wdprevtag", # Current word is y and preceding word is tagged x.
             "wdnexttag", # Current word is x and following word is tagged y.
             "wdand2aft", # Current word is x and word 2 after is y.
          "wdand2tagbfr", # Current word is y and word 2 before is tagged x.
          "wdand2tagaft", # Current word is x and word 2 after is tagged y.
               "lbigram", # Current word is y and word before is x.
               "rbigram", # Current word is x and word after is y.
            "prevbigram", # Preceding word is tagged x and word before is tagged y.
            "nextbigram", # Following word is tagged x and word after is tagged y.
        ))

    @property
    def path(self):
        return self._path

    def load(self):
        # ["VBD", "VB", "PREVTAG", "TO"]
        list.extend(self, (x.split() for x in _read(self._path)))

    def apply(self, tokens):
        """ Applies contextual rules to the given list of tokens,
            where each token is a [word, tag] list.
        """
        o = [("STAART", "STAART")] * 3 # Empty delimiters for look ahead/back.
        t = o + tokens + o
        for i, token in enumerate(t):
            for r in self:
                if token[1] == "STAART":
                    continue
                if token[1] != r[0] and r[0] != "*":
                    continue
                cmd, x, y = r[2], r[3], r[4] if len(r) > 4 else ""
                cmd = cmd.lower()
                if (cmd == "prevtag"        and x ==  t[i - 1][1]) \
                or (cmd == "nexttag"        and x ==  t[i + 1][1]) \
                or (cmd == "prev2tag"       and x ==  t[i - 2][1]) \
                or (cmd == "next2tag"       and x ==  t[i + 2][1]) \
                or (cmd == "prev1or2tag"    and x in (t[i - 1][1], t[i - 2][1])) \
                or (cmd == "next1or2tag"    and x in (t[i + 1][1], t[i + 2][1])) \
                or (cmd == "prev1or2or3tag" and x in (t[i - 1][1], t[i - 2][1], t[i - 3][1])) \
                or (cmd == "next1or2or3tag" and x in (t[i + 1][1], t[i + 2][1], t[i + 3][1])) \
                or (cmd == "surroundtag"    and x ==  t[i - 1][1] and y == t[i + 1][1]) \
                or (cmd == "curwd"          and x ==  t[i + 0][0]) \
                or (cmd == "prevwd"         and x ==  t[i - 1][0]) \
                or (cmd == "nextwd"         and x ==  t[i + 1][0]) \
                or (cmd == "prev1or2wd"     and x in (t[i - 1][0], t[i - 2][0])) \
                or (cmd == "next1or2wd"     and x in (t[i + 1][0], t[i + 2][0])) \
                or (cmd == "prevwdtag"      and x ==  t[i - 1][0] and y == t[i - 1][1]) \
                or (cmd == "nextwdtag"      and x ==  t[i + 1][0] and y == t[i + 1][1]) \
                or (cmd == "wdprevtag"      and x ==  t[i - 1][1] and y == t[i + 0][0]) \
                or (cmd == "wdnexttag"      and x ==  t[i + 0][0] and y == t[i + 1][1]) \
                or (cmd == "wdand2aft"      and x ==  t[i + 0][0] and y == t[i + 2][0]) \
                or (cmd == "wdand2tagbfr"   and x ==  t[i - 2][1] and y == t[i + 0][0]) \
                or (cmd == "wdand2tagaft"   and x ==  t[i + 0][0] and y == t[i + 2][1]) \
                or (cmd == "lbigram"        and x ==  t[i - 1][0] and y == t[i + 0][0]) \
                or (cmd == "rbigram"        and x ==  t[i + 0][0] and y == t[i + 1][0]) \
                or (cmd == "prevbigram"     and x ==  t[i - 2][1] and y == t[i - 1][1]) \
                or (cmd == "nextbigram"     and x ==  t[i + 1][1] and y == t[i + 2][1]):
                    t[i] = [t[i][0], r[1]]
        return t[len(o):-len(o)]

    def insert(self, i, tag1, tag2, cmd="prevtag", x=None, y=None):
        """ Inserts a new rule that updates words with tag1 to tag2,
            given constraints x and y, e.g., Context.append("TO < NN", "VB")
        """
        if " < " in tag1 and not x and not y:
            tag1, x = tag1.split(" < ")
            cmd = "prevtag"
        if " > " in tag1 and not x and not y:
            x, tag1 = tag1.split(" > ")
            cmd = "nexttag"
        lazylist.insert(self, i, [tag1, tag2, cmd, x or "", y or ""])

    def append(self, *args, **kwargs):
        self.insert(len(self) - 1, *args, **kwargs)

    def extend(self, rules=[]):
        for r in rules:
            self.append(*r)

#--- NAMED ENTITY RECOGNIZER -----------------------------------------------------------------------

RE_ENTITY1 = re.compile(r"^http://")                            # http://www.domain.com/path
RE_ENTITY2 = re.compile(r"^www\..*?\.(com|org|net|edu|de|uk)$") # www.domain.com
RE_ENTITY3 = re.compile(r"^[\w\-\.\+]+@(\w[\w\-]+\.)+[\w\-]+$") # name@domain.com


class Entities(lazydict):

    def __init__(self, path="", tag="NNP"):
        """ A dictionary of named entities and their labels.
            For domain names and e-mail adresses, regular expressions are used.
        """
        self.tag = tag
        self._path = path
        self._cmd = ((
            "pers", # Persons: George/NNP-PERS
             "loc", # Locations: Washington/NNP-LOC
             "org", # Organizations: Google/NNP-ORG
        ))

    @property
    def path(self):
        return self._path

    def load(self):
        # ["Alexander", "the", "Great", "PERS"]
        # {"alexander": [["alexander", "the", "great", "pers"], ...]}
        for x in _read(self.path):
            x = [x.lower() for x in x.split()]
            dict.setdefault(self, x[0], []).append(x)

    def apply(self, tokens):
        """ Applies the named entity recognizer to the given list of tokens,
            where each token is a [word, tag] list.
        """
        # Note: we could also scan for patterns, e.g.,
        # "my|his|her name is|was *" => NNP-PERS.
        i = 0
        while i < len(tokens):
            w = tokens[i][0].lower()
            if RE_ENTITY1.match(w) \
            or RE_ENTITY2.match(w) \
            or RE_ENTITY3.match(w):
                tokens[i][1] = self.tag
            if w in self:
                for e in self[w]:
                    # Look ahead to see if successive words match the named entity.
                    e, tag = (e[:-1], "-" + e[-1].upper()) if e[-1] in self._cmd else (e, "")
                    b = True
                    for j, e in enumerate(e):
                        if i + j >= len(tokens) or tokens[i + j][0].lower() != e:
                            b = False
                            break
                    if b:
                        for token in tokens[i:i + j + 1]:
                            token[1] = token[1] if token[1].startswith(self.tag) else self.tag
                            token[1] += tag
                        i += j
                        break
            i += 1
        return tokens

    def append(self, entity, name="pers"):
        """ Appends a named entity to the lexicon,
            e.g., Entities.append("Hooloovoo", "PERS")
        """
        e = list(map(lambda s: s.lower(), entity.split(" ") + [name]))
        self.setdefault(e[0], []).append(e)

    def extend(self, entities):
        for entity, name in entities:
            self.append(entity, name)

#### PARSER ########################################################################################

#--- PARSER ----------------------------------------------------------------------------------------
# A shallow parser can be used to retrieve syntactic-semantic information from text
# in an efficient way (usually at the expense of deeper configurational syntactic information).
# The shallow parser in Pattern is meant to handle the following tasks:
# 1)  Tokenization: split punctuation marks from words and find sentence periods.
# 2)       Tagging: find the part-of-speech tag of each word (noun, verb, ...) in a sentence.
# 3)      Chunking: find words that belong together in a phrase.
# 4) Role labeling: find the subject and object of the sentence.
# 5) Lemmatization: find the base form of each word ("was" => "is").

#    WORD     TAG     CHUNK      PNP        ROLE        LEMMA
#------------------------------------------------------------------
#     The      DT      B-NP        O        NP-SBJ-1      the
#   black      JJ      I-NP        O        NP-SBJ-1      black
#     cat      NN      I-NP        O        NP-SBJ-1      cat
#     sat      VB      B-VP        O        VP-1          sit
#      on      IN      B-PP      B-PNP      PP-LOC        on
#     the      DT      B-NP      I-PNP      NP-OBJ-1      the
#     mat      NN      I-NP      I-PNP      NP-OBJ-1      mat
#       .      .        O          O          O           .

# The example demonstrates what information can be retrieved:
#
# - the period is split from "mat." = the end of the sentence,
# - the words are annotated: NN (noun), VB (verb), JJ (adjective), DT (determiner), ...
# - the phrases are annotated: NP (noun phrase), VP (verb phrase), PNP (preposition), ...
# - the phrases are labeled: SBJ (subject), OBJ (object), LOC (location), ...
# - the phrase start is marked: B (begin), I (inside), O (outside),
# - the past tense "sat" is lemmatized => "sit".

# By default, the English parser uses the Penn Treebank II tagset:
# http://www.clips.ua.ac.be/pages/penn-treebank-tagset
PTB = PENN = "penn"


class Parser(object):

    def __init__(self, lexicon={}, frequency={}, model=None, morphology=None, context=None, entities=None, default=("NN", "NNP", "CD"), language=None):
        """ A simple shallow parser using a Brill-based part-of-speech tagger.
            The given lexicon is a dictionary of known words and their part-of-speech tag.
            The given default tags are used for unknown words.
            Unknown words that start with a capital letter are tagged NNP (except for German).
            Unknown words that contain only digits and punctuation are tagged CD.
            Optionally, morphological and contextual rules (or a language model) can be used 
            to improve the tags of unknown words.
            The given language can be used to discern between
            Germanic and Romance languages for phrase chunking.
        """
        self.lexicon = lexicon or {}
        self.frequency = frequency or {}
        self.model = model
        self.morphology = morphology
        self.context = context
        self.entities = entities
        self.default = default
        self.language = language
        # Load data.
        f = lambda s: isinstance(s, str) or hasattr(s, "read")
        if f(lexicon):
            # Known words.
            self.lexicon = Lexicon(path=lexicon)
        if f(frequency):
            # Word frequency.
            self.frequency = Frequency(path=frequency)
        if f(morphology):
            # Unknown word rules based on word suffix.
            self.morphology = Morphology(path=morphology, known=self.lexicon)
        if f(context):
            # Unknown word rules based on word context.
            self.context = Context(path=context)
        if f(entities):
            # Named entities.
            self.entities = Entities(path=entities, tag=default[1])
        if f(model):
            # Word part-of-speech classifier.
            try:
                self.model = Model(path=model)
            except ImportError: # pattern.vector
                pass

    def find_keywords(self, string, **kwargs):
        """ Returns a sorted list of keywords in the given string.
        """
        return find_keywords(string,
                     parser = self,
                        top = kwargs.pop("top", 10),
                  frequency = kwargs.pop("frequency", {}), **kwargs
        )

    def find_tokens(self, string, **kwargs):
        """ Returns a list of sentences from the given string.
            Punctuation marks are separated from each word by a space.
        """
        # "The cat purs." => ["The cat purs ."]
        return find_tokens(string,
                punctuation = kwargs.get("punctuation", PUNCTUATION),
              abbreviations = kwargs.get("abbreviations", ABBREVIATIONS),
                    replace = kwargs.get("replace", replacements),
                  linebreak = r"\n{2,}")

    def find_tags(self, tokens, **kwargs):
        """ Annotates the given list of tokens with part-of-speech tags.
            Returns a list of tokens, where each token is now a [word, tag]-list.
        """
        # ["The", "cat", "purs"] => [["The", "DT"], ["cat", "NN"], ["purs", "VB"]]
        return find_tags(tokens,
                    lexicon = kwargs.get("lexicon", self.lexicon or {}),
                      model = kwargs.get("model", self.model),
                 morphology = kwargs.get("morphology", self.morphology),
                    context = kwargs.get("context", self.context),
                   entities = kwargs.get("entities", self.entities),
                   language = kwargs.get("language", self.language),
                    default = kwargs.get("default", self.default),
                        map = kwargs.get("map", None))

    def find_chunks(self, tokens, **kwargs):
        """ Annotates the given list of tokens with chunk tags.
            Several tags can be added, for example chunk + preposition tags.
        """
        # [["The", "DT"], ["cat", "NN"], ["purs", "VB"]] =>
        # [["The", "DT", "B-NP"], ["cat", "NN", "I-NP"], ["purs", "VB", "B-VP"]]
        return find_prepositions(
               find_chunks(tokens,
                   language = kwargs.get("language", self.language)))

    def find_prepositions(self, tokens, **kwargs):
        """ Annotates the given list of tokens with prepositional noun phrase tags.
        """
        return find_prepositions(tokens) # See also Parser.find_chunks().

    def find_labels(self, tokens, **kwargs):
        """ Annotates the given list of tokens with verb/predicate tags.
        """
        return find_relations(tokens)

    def find_lemmata(self, tokens, **kwargs):
        """ Annotates the given list of tokens with word lemmata.
        """
        return [token + [token[0].lower()] for token in tokens]

    def parse(self, s, tokenize=True, tags=True, chunks=True, relations=False, lemmata=False, encoding="utf-8", **kwargs):
        """ Takes a string (sentences) and returns a tagged Unicode string (TaggedString).
            Sentences in the output are separated by newlines.
            With tokenize=True, punctuation is split from words and sentences are separated by \n.
            With tags=True, part-of-speech tags are parsed (NN, VB, IN, ...).
            With chunks=True, phrase chunk tags are parsed (NP, VP, PP, PNP, ...).
            With relations=True, semantic role labels are parsed (SBJ, OBJ).
            With lemmata=True, word lemmata are parsed.
            Optional parameters are passed to
            the tokenizer, tagger, chunker, labeler and lemmatizer.
        """
        # Tokenizer.
        if tokenize is True:
            s = self.find_tokens(s, **kwargs)
        if isinstance(s, (list, tuple)):
            s = [isinstance(s, str) and s.split(" ") or s for s in s]
        if isinstance(s, str):
            s = [s.split(" ") for s in s.split("\n")]
        # Unicode.
        for i in range(len(s)):
            for j in range(len(s[i])):
                if isinstance(s[i][j], str):
                    s[i][j] = decode_string(s[i][j], encoding)
            # Tagger (required by chunker, labeler & lemmatizer).
            if tags or chunks or relations or lemmata:
                s[i] = self.find_tags(s[i], **kwargs)
            else:
                s[i] = [[w] for w in s[i]]
            # Chunker.
            if chunks or relations:
                s[i] = self.find_chunks(s[i], **kwargs)
            # Labeler.
            if relations:
                s[i] = self.find_labels(s[i], **kwargs)
            # Lemmatizer.
            if lemmata:
                s[i] = self.find_lemmata(s[i], **kwargs)
        # Slash-formatted tagged string.
        # With collapse=False (or split=True), returns raw list
        # (this output is not usable by tree.Text).
        if not kwargs.get("collapse", True) \
            or kwargs.get("split", False):
            return s
        # Construct TaggedString.format.
        # (this output is usable by tree.Text).
        format = ["word"]
        if tags:
            format.append("part-of-speech")
        if chunks:
            format.extend(("chunk", "preposition"))
        if relations:
            format.append("relation")
        if lemmata:
            format.append("lemma")
        # Collapse raw list.
        # Sentences are separated by newlines, tokens by spaces, tags by slashes.
        # Slashes in words are encoded with &slash;
        for i in range(len(s)):
            for j in range(len(s[i])):
                s[i][j][0] = s[i][j][0].replace("/", "&slash;")
                s[i][j] = "/".join(s[i][j])
            s[i] = " ".join(s[i])
        s = "\n".join(s)
        s = TaggedString(s, format, language=kwargs.get("language", self.language))
        return s

#--- TAGGED STRING ---------------------------------------------------------------------------------
# Pattern.parse() returns a TaggedString: a Unicode string with "tags" and "language" attributes.
# The pattern.text.tree.Text class uses this attribute to determine the token format and
# transform the tagged string to a parse tree of nested Sentence, Chunk and Word objects.

TOKENS = "tokens"


class TaggedString(str):

    def __new__(self, string, tags=["word"], language=None):
        """ Unicode string with tags and language attributes.
            For example: TaggedString("cat/NN/NP", tags=["word", "pos", "chunk"]).
        """
        # From a TaggedString:
        if isinstance(string, str) and hasattr(string, "tags"):
            tags, language = string.tags, string.language
        # From a TaggedString.split(TOKENS) list:
        if isinstance(string, list):
            string = [[[x.replace("/", "&slash;") for x in token] for token in s] for s in string]
            string = "\n".join(" ".join("/".join(token) for token in s) for s in string)
        s = str.__new__(self, string)
        s.tags = list(tags)
        s.language = language
        return s

    def split(self, sep=TOKENS):
        """ Returns a list of sentences, where each sentence is a list of tokens,
            where each token is a list of word + tags.
        """
        if sep != TOKENS:
            return str.split(self, sep)
        if len(self) == 0:
            return []
        return [[[x.replace("&slash;", "/") for x in token.split("/")]
            for token in sentence.split(" ")]
                for sentence in str.split(self, "\n")]

#--- UNIVERSAL TAGSET ------------------------------------------------------------------------------
# The default part-of-speech tagset used in Pattern is Penn Treebank II.
# However, not all languages are well-suited to Penn Treebank (which was developed for English).
# As more languages are implemented, this is becoming more problematic.
#
# A universal tagset is proposed by Slav Petrov (2012):
# http://www.petrovi.de/data/lrec.pdf
#
# Subclasses of Parser should start implementing
# Parser.parse(tagset=UNIVERSAL) with a simplified tagset.
# The names of the constants correspond to Petrov's naming scheme, while
# the value of the constants correspond to Penn Treebank.

UNIVERSAL = "universal"

NOUN, VERB, ADJ, ADV, PRON, DET, PREP, ADP, NUM, CONJ, INTJ, PRT, PUNC, X = \
    "NN", "VB", "JJ", "RB", "PR", "DT", "PP", "PP", "NO", "CJ", "UH", "PT", ".", "X"


def penntreebank2universal(token, tag):
    """ Returns a (token, tag)-tuple with a simplified universal part-of-speech tag.
    """
    if tag.startswith(("NNP-", "NNPS-")):
        return (token, "%s-%s" % (NOUN, tag.split("-")[-1]))
    if tag in ("NN", "NNS", "NNP", "NNPS", "NP"):
        return (token, NOUN)
    if tag in ("MD", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ"):
        return (token, VERB)
    if tag in ("JJ", "JJR", "JJS"):
        return (token, ADJ)
    if tag in ("RB", "RBR", "RBS", "WRB"):
        return (token, ADV)
    if tag in ("PR", "PRP", "PRP$", "WP", "WP$"):
        return (token, PRON)
    if tag in ("DT", "PDT", "WDT", "EX"):
        return (token, DET)
    if tag in ("IN", "PP"):
        return (token, PREP)
    if tag in ("CD", "NO"):
        return (token, NUM)
    if tag in ("CC", "CJ"):
        return (token, CONJ)
    if tag in ("UH",):
        return (token, INTJ)
    if tag in ("POS", "PT", "RP", "TO"):
        return (token, PRT)
    if tag in ("SYM", "LS", ".", "!", "?", ",", ":", "(", ")", "\"", "#", "$"):
        return (token, PUNC)
    return (token, X)

#--- TOKENIZER -------------------------------------------------------------------------------------

TOKEN = re.compile(r"(\S+)\s")

# Common accent letters.
DIACRITICS = \
diacritics = "àáâãäåąāæçćčςďèéêëēěęģìíîïīłįķļľņñňńйðòóôõöøþřšťùúûüůųýÿўžż"

# Common punctuation marks.
PUNCTUATION = \
punctuation = ".,;:!?()[]{}`''\"@#$^&*+-|=~_"

# Common abbreviations.
ABBREVIATIONS = \
abbreviations = set((
    "a.", "adj.", "adv.", "al.", "a.m.", "art.", "c.", "capt.", "cert.", "cf.", "col.", "Col.",
    "comp.", "conf.", "def.", "Dep.", "Dept.", "Dr.", "dr.", "ed.", "e.g.", "esp.", "etc.", "ex.",
    "f.", "fig.", "gen.", "id.", "i.e.", "int.", "l.", "m.", "Med.", "Mil.", "Mr.", "n.", "n.q.",
    "orig.", "pl.", "pred.", "pres.", "p.m.", "ref.", "v.", "vs.", "w/"
))

RE_ABBR1 = re.compile(r"^[A-Za-z]\.$")     # single letter, "T. De Smedt"
RE_ABBR2 = re.compile(r"^([A-Za-z]\.)+$")  # alternating letters, "U.S."
RE_ABBR3 = re.compile(r"^[A-Z][%s]+.$" % ( # capital followed by consonants, "Mr."
        "|".join("bcdfghjklmnpqrstvwxz")))

# Common contractions.
replacements = {
     "'d": " 'd",
     "'m": " 'm",
     "'s": " 's",
    "'ll": " 'll",
    "'re": " 're",
    "'ve": " 've",
    "n't": " n't"
}

# Common emoticons.
EMOTICONS = \
emoticons = { # (facial expression, sentiment)-keys
    ("love" , +1.00): set(("<3", "♥", "❤")),
    ("grin" , +1.00): set((">:D", ":-D", ":D", "=-D", "=D", "X-D", "x-D", "XD", "xD", "8-D")),
    ("taunt", +0.75): set((">:P", ":-P", ":P", ":-p", ":p", ":-b", ":b", ":c)", ":o)", ":^)")),
    ("smile", +0.50): set((">:)", ":-)", ":)", "=)", "=]", ":]", ":}", ":>", ":3", "8)", "8-)")),
    ("wink" , +0.25): set((">;]", ";-)", ";)", ";-]", ";]", ";D", ";^)", "*-)", "*)")),
    ("blank", +0.00): set((":-|", ":|")),
    ("gasp" , -0.05): set((">:o", ":-O", ":O", ":o", ":-o", "o_O", "o.O", "°O°", "°o°")),
    ("worry", -0.25): set((">:/", ":-/", ":/", ":\\", ">:\\", ":-.", ":-s", ":s", ":S", ":-S", ">.>")),
    ("frown", -0.75): set((">:[", ":-(", ":(", "=(", ":-[", ":[", ":{", ":-<", ":c", ":-c", "=/")),
    ("cry"  , -1.00): set((":'(", ":'''(", ";'("))
}

RE_EMOTICONS = [r" ?".join(map(re.escape, e)) for v in EMOTICONS.values() for e in v]
RE_EMOTICONS = re.compile(r"(%s)($|\s)" % "|".join(RE_EMOTICONS))

# Common emoji.
EMOJI = \
emoji = { # (facial expression, sentiment)-keys
    ("love" , +1.00): set(("❤️", "💜", "💚", "💙", "💛", "💕")),
    ("grin" , +1.00): set(("😀", "😄", "😃", "😆", "😅", "😂", "😁", "😻", "😍", "😈", "👌")),
    ("taunt", +0.75): set(("😛", "😝", "😜", "😋", "😇")),
    ("smile", +0.50): set(("😊", "😌", "😏", "😎", "☺", "👍")),
    ("wink" , +0.25): set(("😉")),
    ("blank", +0.00): set(("😐", "😶")),
    ("gasp" , -0.05): set(("😳", "😮", "😯", "😧", "😦", "🙀")),
    ("worry", -0.25): set(("😕", "😬")),
    ("frown", -0.75): set(("😟", "😒", "😔", "😞", "😠", "😩", "😫", "😡", "👿")),
    ("cry"  , -1.00): set(("😢", "😥", "😓", "😪", "😭", "😿")),
}

RE_EMOJI = [e for v in EMOJI.values() for e in v]
RE_EMOJI = re.compile(r"(\s?)(%s)(\s?)" % "|".join(RE_EMOJI))

# Mention marker: "@tomdesmedt".
RE_MENTION = re.compile(r"\@([0-9a-zA-z_]+)(\s|\,|\:|\.|\!|\?|$)")

# Sarcasm marker: "(!)".
RE_SARCASM = re.compile(r"\( ?\! ?\)")

# Paragraph line breaks
# (\n\n marks end of sentence).
EOS = "END-OF-SENTENCE"


def find_tokens(string, punctuation=PUNCTUATION, abbreviations=ABBREVIATIONS, replace=replacements, linebreak=r"\n{2,}"):
    """ Returns a list of sentences. Each sentence is a space-separated string of tokens (words).
        Handles common cases of abbreviations (e.g., etc., ...).
        Punctuation marks are split from other words. Periods (or ?!) mark the end of a sentence.
        Headings without an ending period are inferred by line breaks.
    """
    # Handle punctuation.
    punctuation = tuple(punctuation)
    # Handle replacements (contractions).
    for a, b in replace.items():
        string = re.sub(a, b, string)
    # Handle Unicode quotes.
    if isinstance(string, str):
        string = string.replace("“", " “ ")
        string = string.replace("”", " ” ")
        string = string.replace("‘", " ‘ ")
        string = string.replace("’", " ’ ")
    # Collapse whitespace.
    string = re.sub("\r\n", "\n", string)
    string = re.sub(linebreak, " %s " % EOS, string)
    string = re.sub(r"\s+", " ", string)
    tokens = []
    # Handle punctuation marks.
    for t in TOKEN.findall(string + " "):
        if len(t) > 0:
            tail = []
            if not RE_MENTION.match(t):
                while t.startswith(punctuation) and \
                  t not in replace:
                    # Split leading punctuation.
                    if t.startswith(punctuation):
                        tokens.append(t[0]); t = t[1:]
            if not False:
                while t.endswith(punctuation) and \
                  t not in replace:
                    # Split trailing punctuation.
                    if t.endswith(punctuation) and not t.endswith("."):
                        tail.append(t[-1]); t = t[:-1]
                    # Split ellipsis (...) before splitting period.
                    if t.endswith("..."):
                        tail.append("..."); t = t[:-3].rstrip(".")
                    # Split period (if not an abbreviation).
                    if t.endswith("."):
                        if t in abbreviations or \
                          RE_ABBR1.match(t) is not None or \
                          RE_ABBR2.match(t) is not None or \
                          RE_ABBR3.match(t) is not None:
                            break
                        else:
                            tail.append(t[-1]); t = t[:-1]
            if t != "":
                tokens.append(t)
            tokens.extend(reversed(tail))
    # Handle citations (periods + quotes).
    if isinstance(string, str):
        quotes = ("'", "\"", "”", "’")
    else:
        quotes = ("'", "\"")
    # Handle sentence breaks (periods, quotes, parenthesis).
    sentences, i, j = [[]], 0, 0
    while j < len(tokens):
        if tokens[j] in ("...", ".", "!", "?", EOS):
            while j < len(tokens) \
              and (tokens[j] in ("...", ".", "!", "?", EOS) or tokens[j] in quotes):
                if tokens[j] in quotes and sentences[-1].count(tokens[j]) % 2 == 0:
                    break # Balanced quotes.
                j += 1
            sentences[-1].extend(t for t in tokens[i:j] if t != EOS)
            sentences.append([])
            i = j
        j += 1
    # Handle emoticons.
    sentences[-1].extend(tokens[i:j])
    sentences = (" ".join(s) for s in sentences if len(s) > 0)
    sentences = (RE_SARCASM.sub("(!)", s) for s in sentences)
    sentences = [RE_EMOTICONS.sub(
        lambda m: m.group(1).replace(" ", "") + m.group(2), s) for s in sentences]
    sentences = [RE_EMOJI.sub(
        lambda m: (m.group(1) or " ") + m.group(2) + (m.group(3) or " "), s) for s in sentences]
    sentences = [s.replace("  ", " ").strip() for s in sentences]
    return sentences

#--- PART-OF-SPEECH TAGGER -------------------------------------------------------------------------

# Unknown words are recognized as numbers if they contain only digits and -,.:/%$
CD = re.compile(r"^[0-9\-\,\.\:\/\%\$]+$")


def _suffix_rules(token, tag="NN"):
    """ Default morphological tagging rules for English, based on word suffixes.
    """
    if isinstance(token, (list, tuple)):
        token, tag = token
    if token.endswith("ing"):
        tag = "VBG"
    if token.endswith("ly"):
        tag = "RB"
    if token.endswith("s") and not token.endswith(("is", "ous", "ss")):
        tag = "NNS"
    if token.endswith(("able", "al", "ful", "ible", "ient", "ish", "ive", "less", "tic", "ous")) or "-" in token:
        tag = "JJ"
    if token.endswith("ed"):
        tag = "VBN"
    if token.endswith(("ate", "ify", "ise", "ize")):
        tag = "VBP"
    return [token, tag]


def find_tags(tokens, lexicon={}, model=None, morphology=None, context=None, entities=None, default=("NN", "NNP", "CD"), language="en", map=None, **kwargs):
    """ Returns a list of [token, tag]-items for the given list of tokens:
        ["The", "cat", "purs"] => [["The", "DT"], ["cat", "NN"], ["purs", "VB"]]
        Words are tagged using the given lexicon of (word, tag)-items.
        Unknown words are tagged NN by default.
        Unknown words that start with a capital letter are tagged NNP (unless language="de").
        Unknown words that consist only of digits and punctuation marks are tagged CD.
        Unknown words are then improved with morphological rules.
        All words are improved with contextual rules.
        If a model is given, uses model for unknown words instead of morphology and context.
        If map is a function, it is applied to each (token, tag) after applying all rules.
    """
    tagged = []
    # Tag known words.
    for i, token in enumerate(tokens):
        tagged.append([token, lexicon.get(token, i == 0 and lexicon.get(token.lower()) or None)])
    # Tag unknown words.
    for i, (token, tag) in enumerate(tagged):
        prev, next = (None, None), (None, None)
        if i > 0:
            prev = tagged[i - 1]
        if i < len(tagged) - 1:
            next = tagged[i + 1]
        if tag is None or token in (model is not None and model.unknown or ()):
            # Use language model (i.e., SLP).
            if model is not None:
                tagged[i] = model.apply([token, None], prev, next)
            # Use NNP for capitalized words (except in German).
            elif token.istitle() and language != "de":
                tagged[i] = [token, default[1]]
            # Use CD for digits and numbers.
            elif CD.match(token) is not None:
                tagged[i] = [token, default[2]]
            # Use suffix rules (e.g., -ly = RB).
            elif morphology is not None:
                tagged[i] = morphology.apply([token, default[0]], prev, next)
            # Use suffix rules (English default).
            elif language == "en":
                tagged[i] = _suffix_rules([token, default[0]])
            # Use most frequent tag (NN).
            else:
                tagged[i] = [token, default[0]]
    # Tag words by context.
    if context is not None and model is None:
        tagged = context.apply(tagged)
    # Tag named entities.
    if entities is not None:
        tagged = entities.apply(tagged)
    # Map tags with a custom function.
    if map is not None:
        tagged = [list(map(token, tag)) or [token, default[0]] for token, tag in tagged]
    return tagged

#--- PHRASE CHUNKER --------------------------------------------------------------------------------

SEPARATOR = "/"

NN = r"NN|NNS|NNP|NNPS|NNPS?\-[A-Z]{3,4}|PR|PRP|PRP\$"
VB = r"VB|VBD|VBG|VBN|VBP|VBZ"
JJ = r"JJ|JJR|JJS"
RB = r"(?<!W)RB|RBR|RBS"
CC = r"CC|CJ"

# Chunking rules.
# CHUNKS[0] = Germanic: RB + JJ precedes NN ("the round table").
# CHUNKS[1] = Romance : RB + JJ precedes or follows NN ("la table ronde", "une jolie fille").
CHUNKS = [[
    # Germanic languages: da, de, en, is, nl, no, sv (also applies to cs, pl, ru, ...)
    (  "NP", r"((NN)/)* ((DT|CD|CC)/)* ((RB|JJ)/)* (((JJ)/(CC|,)/)*(JJ)/)* ((NN)/)+"),
    (  "VP", r"(((MD|TO|RB)/)* ((VB)/)+ ((RP)/)*)+"),
    (  "VP", r"((MD)/)"),
    (  "PP", r"((IN|PP)/)+"),
    ("ADJP", r"((RB|JJ)/)* ((JJ)/,/)* ((JJ)/(CC)/)* ((JJ)/)+"),
    ("ADVP", r"((RB)/)+"),
], [
    # Romance languages: ca, es, fr, it, pt, ro
    (  "NP", r"((NN)/)* ((DT|CD|CC)/)* ((RB|JJ|,)/)* (((JJ)/(CC|,)/)*(JJ)/)* ((NN)/)+ ((RB|JJ)/)*"),
    (  "VP", r"(((MD|TO|RB)/)* ((VB)/)+ ((RP)/)* ((RB)/)*)+"),
    (  "VP", r"((MD)/)"),
    (  "PP", r"((IN|PP)/)+"),
    ("ADJP", r"((RB|JJ)/)* ((JJ)/,/)* ((JJ)/(CC)/)* ((JJ)/)+"),
    ("ADVP", r"((RB)/)+"),
]]

for i in (0, 1):
    for j, (tag, s) in enumerate(CHUNKS[i]):
        s = s.replace("NN", NN)
        s = s.replace("VB", VB)
        s = s.replace("JJ", JJ)
        s = s.replace("RB", RB)
        s = s.replace(" ", "")
        s = re.compile(s)
        CHUNKS[i][j] = (tag, s)

# Handle ADJP before VP,
# so that RB prefers next ADJP over previous VP.
CHUNKS[0].insert(1, CHUNKS[0].pop(3))
CHUNKS[1].insert(1, CHUNKS[1].pop(3))


def find_chunks(tagged, language="en"):
    """ The input is a list of [token, tag]-items.
        The output is a list of [token, tag, chunk]-items:
        The/DT nice/JJ fish/NN is/VBZ dead/JJ ./. =>
        The/DT/B-NP nice/JJ/I-NP fish/NN/I-NP is/VBZ/B-VP dead/JJ/B-ADJP ././O
    """
    chunked = [x for x in tagged]
    tags = "".join("%s%s" % (tag, SEPARATOR) for token, tag in tagged)
    # Use Germanic or Romance chunking rules according to given language.
    for tag, rule in CHUNKS[int(language in ("ca", "es", "fr", "it", "pt", "ro"))]:
        for m in rule.finditer(tags):
            # Find the start of chunks inside the tags-string.
            # Number of preceding separators = number of preceding tokens.
            i = m.start()
            j = tags[:i].count(SEPARATOR)
            n = m.group(0).count(SEPARATOR)
            for k in range(j, j + n):
                if len(chunked[k]) == 3:
                    continue
                if len(chunked[k]) < 3:
                    # A conjunction or comma cannot be start of a chunk.
                    if k == j and chunked[k][1] in ("CC", "CJ", ","):
                        j += 1
                    # Mark first token in chunk with B-.
                    elif k == j:
                        chunked[k].append("B-" + tag)
                    # Mark other tokens in chunk with I-.
                    else:
                        chunked[k].append("I-" + tag)
    # Mark chinks (tokens outside of a chunk) with O-.
    for chink in filter(lambda x: len(x) < 3, chunked):
        chink.append("O")
    # Post-processing corrections.
    for i, (word, tag, chunk) in enumerate(chunked):
        if tag.startswith("RB") and chunk == "B-NP":
            # "Perhaps you" => ADVP + NP
            # "Really nice work" => NP
            # "Really, nice work" => ADVP + O + NP
            if i < len(chunked) - 1 and not chunked[i + 1][1].startswith("JJ"):
                chunked[i + 0][2] = "B-ADVP"
                chunked[i + 1][2] = "B-NP"
            if i < len(chunked) - 1 and chunked[i + 1][1] in ("CC", "CJ", ","):
                chunked[i + 1][2] = "O"
            if i < len(chunked) - 2 and chunked[i + 1][2] == "O":
                chunked[i + 2][2] = "B-NP"
    return chunked


def find_prepositions(chunked):
    """ The input is a list of [token, tag, chunk]-items.
        The output is a list of [token, tag, chunk, preposition]-items.
        PP-chunks followed by NP-chunks make up a PNP-chunk.
    """
    # Tokens that are not part of a preposition just get the O-tag.
    for ch in chunked:
        ch.append("O")
    for i, chunk in enumerate(chunked):
        if chunk[2].endswith("PP") and chunk[-1] == "O":
            # Find PP followed by other PP, NP with nouns and pronouns, VP with a gerund.
            if i < len(chunked) - 1 and \
             (chunked[i + 1][2].endswith(("NP", "PP")) or \
              chunked[i + 1][1] in ("VBG", "VBN")):
                chunk[-1] = "B-PNP"
                pp = True
                for ch in chunked[i + 1:]:
                    if not (ch[2].endswith(("NP", "PP")) or ch[1] in ("VBG", "VBN")):
                        break
                    if ch[2].endswith("PP") and pp:
                        ch[-1] = "I-PNP"
                    if not ch[2].endswith("PP"):
                        ch[-1] = "I-PNP"
                        pp = False
    return chunked

#--- SEMANTIC ROLE LABELER -------------------------------------------------------------------------
# Naive approach.

BE = dict.fromkeys(("be", "am", "are", "is", "being", "was", "were", "been"), True)
GO = dict.fromkeys(("go", "goes", "going", "went"), True)


def find_relations(chunked):
    """ The input is a list of [token, tag, chunk]-items.
        The output is a list of [token, tag, chunk, relation]-items.
        A noun phrase preceding a verb phrase is perceived as sentence subject.
        A noun phrase following a verb phrase is perceived as sentence object.
    """
    tag = lambda token: token[2].split("-")[-1] # B-NP => NP
    # Group successive tokens with the same chunk-tag.
    chunks = []
    for token in chunked:
        if len(chunks) == 0 \
        or token[2].startswith("B-") \
        or tag(token) != tag(chunks[-1][-1]):
            chunks.append([])
        chunks[-1].append(token + ["O"])
    # If a VP is preceded by a NP, the NP is tagged as NP-SBJ-(id).
    # If a VP is followed by a NP, the NP is tagged as NP-OBJ-(id).
    # Chunks that are not part of a relation get an O-tag.
    id = 0
    for i, chunk in enumerate(chunks):
        if tag(chunk[-1]) == "VP" and i > 0 and tag(chunks[i - 1][-1]) == "NP":
            if chunk[-1][-1] == "O":
                id += 1
            for token in chunk:
                token[-1] = "VP-" + str(id)
            for token in chunks[i - 1]:
                token[-1] += "*NP-SBJ-" + str(id)
                token[-1] = token[-1].lstrip("O-*")
        if tag(chunk[-1]) == "VP" and i < len(chunks) - 1 and tag(chunks[i + 1][-1]) == "NP":
            if chunk[-1][-1] == "O":
                id += 1
            for token in chunk:
                token[-1] = "VP-" + str(id)
            for token in chunks[i + 1]:
                token[-1] = "*NP-OBJ-" + str(id)
                token[-1] = token[-1].lstrip("O-*")
    # This is more a proof-of-concept than useful in practice:
    # PP-LOC = be + in|at + the|my
    # PP-DIR = go + to|towards + the|my
    for i, chunk in enumerate(chunks):
        if 0 < i < len(chunks) - 1 and len(chunk) == 1 and chunk[-1][-1] == "O":
            t0, t1, t2 = chunks[i - 1][-1], chunks[i][0], chunks[i + 1][0] # previous / current / next
            if tag(t1) == "PP" and t2[1] in ("DT", "PR", "PRP$"):
                if t0[0] in BE and t1[0] in ("in", "at"):
                    t1[-1] = "PP-LOC"
                if t0[0] in GO and t1[0] in ("to", "towards"):
                    t1[-1] = "PP-DIR"
    related = []
    [related.extend(chunk) for chunk in chunks]
    return related

#--- KEYWORDS EXTRACTION ---------------------------------------------------------------------------


def find_keywords(string, parser, top=10, frequency={}, ignore=("rt",), pos=("NN",), **kwargs):
    """ Returns a sorted list of keywords in the given string.
        The given parser (e.g., pattern.en.parser) is used to identify noun phrases.
        The given frequency dictionary can be a reference corpus,
        with relative document frequency (df, 0.0-1.0) for each lemma, 
        e.g., {"the": 0.8, "cat": 0.1, ...}
    """
    lemmata = kwargs.pop("lemmata", kwargs.pop("stem", True))
    t = []
    p = None
    n = 0
    # Remove hashtags.
    s = string.replace("#", ". ")
    # Parse + chunk string.
    for sentence in parser.parse(s, chunks=True, lemmata=lemmata).split():
        for w in sentence: # [token, tag, chunk, preposition, lemma]
            if w[2].startswith(("B", "O")):
                t.append([])
                p = None
            if w[1].startswith(("NNP", "DT")) and p and \
               p[1].startswith("NNP") and \
               p[0][0] != "@" and \
               w[0][0] != "A":
                p[+0] += " " + w[+0] # Merge NNP's: "Ms Kitty".
                p[-1] += " " + w[-1]
            else:
                t[-1].append(w)
            p = t[-1][-1] # word before
            n = n + 1     # word count
    # Parse context: {word: chunks}.
    ctx = {}
    for i, chunk in enumerate(t):
        ch = " ".join(w[0] for w in chunk)
        ch = ch.lower()
        for w in chunk:
            ctx.setdefault(w[0], set()).add(ch)
    # Parse keywords.
    m = {}
    for i, chunk in enumerate(t):
        # Head of "cat hair" => "hair".
        # Head of "poils de chat" => "poils".
        head = chunk[-int(parser.language not in ("ca", "es", "pt", "fr", "it", "pt", "ro"))]
        for w in chunk:
            # Lemmatize known words.
            k = lemmata and w[-1] in parser.lexicon and w[-1] or w[0]
            k = re.sub(r"\"\(\)", "", k)
            k = k.strip(":.?!")
            k = k.lower()
            if not w[1].startswith(pos):
                continue
            if len(k) == 1:
                continue
            if k.startswith(("http", "www.")):
                continue
            if k in ignore or lemmata and w[0] in ignore:
                continue
            if k not in m:
                m[k] = [0, 0, 0, 0, 0, 0]
            # Scoring:
            # 0) words that appear more frequently.
            # 1) words that appear in more contexts (semantic centrality).
            # 2) words that appear at the start (25%) of the text.
            # 3) words that are nouns.
            # 4) words that are not in a prepositional phrase.
            # 5) words that are the head of a chunk.
            noun = w[1].startswith("NN")
            m[k][0] += 1 / float(n)
            m[k][1] |= 1 if len(ctx[w[0]]) > 1 else 0
            m[k][2] |= 1 if i / float(len(t)) <= 0.25 else 0
            m[k][3] |= 1 if noun else 0
            m[k][4] |= 1 if noun and w[3].startswith("O") else 0
            m[k][5] |= 1 if noun and w == head else 0
    # Rate tf-idf.
    if frequency:
        for k in m:
            if not k.isalpha(): # @username, odd!ti's
                df = 1.0
            else:
                df = 1.0 / max(frequency.get(w[0].lower(), frequency.get(k, 0)), 0.0001)
                df = log(df)
            m[k][0] *= df
            #print k, m[k]
    # Sort candidates alphabetically by total score.
    # The harmonic mean will emphasize tf-idf score.
    hmean = lambda a: len(a) / sum(1.0 / (x or 0.0001) for x in a)
    m = [(hmean(m[k]), k) for k in m]
    m = sorted(m, key=lambda x: x[1])
    m = sorted(m, key=lambda x: x[0], reverse=True)
    m = [k for score, k in m]
    m = m[:top]
    return m

#### COMMAND LINE ##################################################################################
# The commandline() function enables command line support for a Parser.
# The following code can be added to pattern.en, for example:
#
# from pattern.text import Parser, commandline
# parse = Parser(lexicon=LEXICON).parse
# if __name__ == "main":
#     commandline(parse)
#
# The parser is then accessible from the command line:
# python -m pattern.en.parser xml -s "Hello, my name is Dr. Sbaitso. Nice to meet you." -OTCLI


def commandline(parse=Parser().parse):
    import optparse
    import codecs
    p = optparse.OptionParser()
    p.add_option("-f", "--file",      dest="file",      action="store",      help="text file to parse",   metavar="FILE")
    p.add_option("-s", "--string",    dest="string",    action="store",      help="text string to parse", metavar="STRING")
    p.add_option("-O", "--tokenize",  dest="tokenize",  action="store_true", help="tokenize the input")
    p.add_option("-T", "--tags",      dest="tags",      action="store_true", help="parse part-of-speech tags")
    p.add_option("-C", "--chunks",    dest="chunks",    action="store_true", help="parse chunk tags")
    p.add_option("-R", "--relations", dest="relations", action="store_true", help="find verb/predicate relations")
    p.add_option("-L", "--lemmata",   dest="lemmata",   action="store_true", help="find word lemmata")
    p.add_option("-e", "--encoding",  dest="encoding",  action="store_true", help="character encoding", default="utf-8")
    p.add_option("-v", "--version",   dest="version",   action="store_true", help="version info")
    o, arguments = p.parse_args()
    # Version info.
    if o.version:
        sys.path.insert(0, os.path.join(MODULE, "..", ".."))
        from pattern import __version__
        print(__version__)
        sys.path.pop(0)
    # Either a text file (-f) or a text string (-s) must be supplied.
    s = o.file and codecs.open(o.file, "r", o.encoding).read() or o.string
    # The given text can be parsed in two modes:
    # - implicit: parse everything (tokenize, tag/chunk, find relations, lemmatize).
    # - explicit: define what to parse manually.
    if s:
        explicit = False
        for option in [o.tokenize, o.tags, o.chunks, o.relations, o.lemmata]:
            if option is not None:
                explicit = True
                break
        if not explicit:
            a = {"encoding": o.encoding}
        else:
            a = {"tokenize": o.tokenize  or False,
                     "tags": o.tags      or False,
                   "chunks": o.chunks    or False,
                "relations": o.relations or False,
                  "lemmata": o.lemmata   or False,
                 "encoding": o.encoding}
        s = parse(s, **a)
        # The output can be either slash-formatted string or XML.
        if "xml" in arguments:
            s = Tree(s, s.tags).xml
        print(s)

#### VERBS #########################################################################################

#--- VERB TENSES -----------------------------------------------------------------------------------
# Conjugation is the inflection of verbs by tense, person, number, mood and aspect.

# VERB TENSE:
INFINITIVE, PRESENT, PAST, FUTURE = \
    INF, PRES, PST, FUT = \
        "infinitive", "present", "past", "future"

# VERB PERSON:
# 1st person = I or we (plural).
# 2nd person = you.
# 3rd person = he, she, it or they (plural).
FIRST, SECOND, THIRD = \
    1, 2, 3

# VERB NUMBER:
# singular number = I, you, he, she, it.
#   plural number = we, you, they.
SINGULAR, PLURAL = \
    SG, PL = \
        "singular", "plural"

# VERB MOOD:
#  indicative mood = a fact: "the cat meowed".
#  imperative mood = a command: "meow!".
# conditional mood = a hypothesis: "a cat *will* meow *if* it is hungry".
# subjunctive mood = a wish, possibility or necessity: "I *wish* the cat *would* stop meowing".
INDICATIVE, IMPERATIVE, CONDITIONAL, SUBJUNCTIVE = \
    IND, IMP, COND, SJV = \
        "indicative", "imperative", "conditional", "subjunctive"

# VERB ASPECT:
# imperfective aspect = a habitual or ongoing action: "it was midnight; the cat meowed".
#   perfective aspect = a momentary or completed action: "I flung my pillow at the cat".
#  progressive aspect = a incomplete action in progress: "the cat was meowing".
# Note: the progressive aspect is a subtype of the imperfective aspect.
IMPERFECTIVE, PERFECTIVE, PROGRESSIVE = \
    IPFV, PFV, PROG = \
        "imperfective", "perfective", "progressive"

# Imperfect = past tense + imperfective aspect.
# Preterite = past tense + perfective aspect.
IMPERFECT = "imperfect"
PRETERITE = "preterite"

# Participle = present tense  + progressive aspect.
PARTICIPLE, GERUND = "participle", "gerund"

# Continuous aspect ≈ progressive aspect.
CONTINUOUS = CONT = "continuous"

_ = None # prettify the table =>

# Unique index per tense (= tense + person + number + mood + aspect + negated? + aliases).
# The index is used to describe the format of the verb lexicon file.
# The aliases can be passed to Verbs.conjugate() and Tenses.__contains__().
TENSES = {
   None: (None, _,  _,    _,    _, False, (None   ,)), #       ENGLISH   SPANISH   GERMAN    DUTCH     FRENCH
     0 : ( INF, _,  _,    _,    _, False, ("inf"  ,)), #       to be     ser       sein      zijn      être
     1 : (PRES, 1, SG,  IND, IPFV, False, ("1sg"  ,)), #     I am        soy       bin       ben       suis
     2 : (PRES, 2, SG,  IND, IPFV, False, ("2sg"  ,)), #   you are       eres      bist      bent      es
     3 : (PRES, 3, SG,  IND, IPFV, False, ("3sg"  ,)), # (s)he is        es        ist       is        est
     4 : (PRES, 1, PL,  IND, IPFV, False, ("1pl"  ,)), #    we are       somos     sind      zijn      sommes
     5 : (PRES, 2, PL,  IND, IPFV, False, ("2pl"  ,)), #   you are       sois      seid      zijn      êtes
     6 : (PRES, 3, PL,  IND, IPFV, False, ("3pl"  ,)), #  they are       son       sind      zijn      sont
     7 : (PRES, _, PL,  IND, IPFV, False, ( "pl"  ,)), #       are
     8 : (PRES, _,  _,  IND, PROG, False, ("part" ,)), #       being     siendo              zijnd     étant
     9 : (PRES, 1, SG,  IND, IPFV, True,  ("1sg-" ,)), #     I am not
    10 : (PRES, 2, SG,  IND, IPFV, True,  ("2sg-" ,)), #   you aren't
    11 : (PRES, 3, SG,  IND, IPFV, True,  ("3sg-" ,)), # (s)he isn't
    12 : (PRES, 1, PL,  IND, IPFV, True,  ("1pl-" ,)), #    we aren't
    13 : (PRES, 2, PL,  IND, IPFV, True,  ("2pl-" ,)), #   you aren't
    14 : (PRES, 3, PL,  IND, IPFV, True,  ("3pl-" ,)), #  they aren't
    15 : (PRES, _, PL,  IND, IPFV, True,  ( "pl-" ,)), #       aren't
    16 : (PRES, _,  _,  IND, IPFV, True,  (   "-" ,)), #       isn't
    17 : ( PST, 1, SG,  IND, IPFV, False, ("1sgp" ,)), #     I was       era       war       was       étais
    18 : ( PST, 2, SG,  IND, IPFV, False, ("2sgp" ,)), #   you were      eras      warst     was       étais
    19 : ( PST, 3, SG,  IND, IPFV, False, ("3sgp" ,)), # (s)he was       era       war       was       était
    20 : ( PST, 1, PL,  IND, IPFV, False, ("1ppl" ,)), #    we were      éramos    waren     waren     étions
    21 : ( PST, 2, PL,  IND, IPFV, False, ("2ppl" ,)), #   you were      erais     wart      waren     étiez
    22 : ( PST, 3, PL,  IND, IPFV, False, ("3ppl" ,)), #  they were      eran      waren     waren     étaient
    23 : ( PST, _, PL,  IND, IPFV, False, ( "ppl" ,)), #       were
    24 : ( PST, _,  _,  IND, PROG, False, ("ppart",)), #       been      sido      gewesen   geweest   été
    25 : ( PST, _,  _,  IND, IPFV, False, (   "p" ,)), #       was
    26 : ( PST, 1, SG,  IND, IPFV, True,  ("1sgp-",)), #     I wasn't
    27 : ( PST, 2, SG,  IND, IPFV, True,  ("2sgp-",)), #   you weren't
    28 : ( PST, 3, SG,  IND, IPFV, True,  ("3sgp-",)), # (s)he wasn't
    29 : ( PST, 1, PL,  IND, IPFV, True,  ("1ppl-",)), #    we weren't
    30 : ( PST, 2, PL,  IND, IPFV, True,  ("2ppl-",)), #   you weren't
    31 : ( PST, 3, PL,  IND, IPFV, True,  ("3ppl-",)), #  they weren't
    32 : ( PST, _, PL,  IND, IPFV, True,  ( "ppl-",)), #       weren't
    33 : ( PST, _,  _,  IND, IPFV, True,  ( "p-"  ,)), #       wasn't
    34 : ( PST, 1, SG,  IND,  PFV, False, ("1sg+" ,)), #     I           fui                           fus
    35 : ( PST, 2, SG,  IND,  PFV, False, ("2sg+" ,)), #   you           fuiste                        fus
    36 : ( PST, 3, SG,  IND,  PFV, False, ("3sg+" ,)), # (s)he           fue                           fut
    37 : ( PST, 1, PL,  IND,  PFV, False, ("1pl+" ,)), #    we           fuimos                        fûmes
    38 : ( PST, 2, PL,  IND,  PFV, False, ("2pl+" ,)), #   you           fuisteis                      fûtes
    39 : ( PST, 3, PL,  IND,  PFV, False, ("3pl+" ,)), #  they           fueron                        furent
    40 : ( FUT, 1, SG,  IND, IPFV, False, ("1sgf" ,)), #     I           seré                          serai
    41 : ( FUT, 2, SG,  IND, IPFV, False, ("2sgf" ,)), #   you           serás                         seras
    42 : ( FUT, 3, SG,  IND, IPFV, False, ("3sgf" ,)), # (s)he           será                          sera
    43 : ( FUT, 1, PL,  IND, IPFV, False, ("1plf" ,)), #    we           seremos                       serons
    44 : ( FUT, 2, PL,  IND, IPFV, False, ("2plf" ,)), #   you           seréis                        serez
    45 : ( FUT, 3, PL,  IND, IPFV, False, ("3plf" ,)), #  they           serán                         seron
    46 : (PRES, 1, SG, COND, IPFV, False, ("1sg->",)), #     I           sería                         serais
    47 : (PRES, 2, SG, COND, IPFV, False, ("2sg->",)), #   you           serías                        serais
    48 : (PRES, 3, SG, COND, IPFV, False, ("3sg->",)), # (s)he           sería                         serait
    49 : (PRES, 1, PL, COND, IPFV, False, ("1pl->",)), #    we           seríamos                      serions
    50 : (PRES, 2, PL, COND, IPFV, False, ("2pl->",)), #   you           seríais                       seriez
    51 : (PRES, 3, PL, COND, IPFV, False, ("3pl->",)), #  they           serían                        seraient
    52 : (PRES, 2, SG,  IMP, IPFV, False, ("2sg!" ,)), #   you           sé        sei                 sois
    521: (PRES, 3, SG,  IMP, IPFV, False, ("3sg!" ,)), # (s)he
    53 : (PRES, 1, PL,  IMP, IPFV, False, ("1pl!" ,)), #    we                     seien               soyons
    54 : (PRES, 2, PL,  IMP, IPFV, False, ("2pl!" ,)), #   you           sed       seid                soyez
    541: (PRES, 3, PL,  IMP, IPFV, False, ("3pl!" ,)), #   you
    55 : (PRES, 1, SG,  SJV, IPFV, False, ("1sg?" ,)), #     I           sea       sei                 sois
    56 : (PRES, 2, SG,  SJV, IPFV, False, ("2sg?" ,)), #   you           seas      seist               sois
    57 : (PRES, 3, SG,  SJV, IPFV, False, ("3sg?" ,)), # (s)he           sea       sei                 soit
    58 : (PRES, 1, PL,  SJV, IPFV, False, ("1pl?" ,)), #    we           seamos    seien               soyons
    59 : (PRES, 2, PL,  SJV, IPFV, False, ("2pl?" ,)), #   you           seáis     seiet               soyez
    60 : (PRES, 3, PL,  SJV, IPFV, False, ("3pl?" ,)), #  they           sean      seien               soient
    61 : (PRES, 1, SG,  SJV,  PFV, False, ("1sg?+",)), #     I
    62 : (PRES, 2, SG,  SJV,  PFV, False, ("2sg?+",)), #   you
    63 : (PRES, 3, SG,  SJV,  PFV, False, ("3sg?+",)), # (s)he
    64 : (PRES, 1, PL,  SJV,  PFV, False, ("1pl?+",)), #    we
    65 : (PRES, 2, PL,  SJV,  PFV, False, ("2pl?+",)), #   you
    66 : (PRES, 3, PL,  SJV,  PFV, False, ("3pl?+",)), #  they
    67 : ( PST, 1, SG,  SJV, IPFV, False, ("1sgp?",)), #     I           fuera     wäre                fusse
    68 : ( PST, 2, SG,  SJV, IPFV, False, ("2sgp?",)), #   you           fueras    wärest              fusses
    69 : ( PST, 3, SG,  SJV, IPFV, False, ("3sgp?",)), # (s)he           fuera     wäre                fût
    70 : ( PST, 1, PL,  SJV, IPFV, False, ("1ppl?",)), #    we           fuéramos  wären               fussions
    71 : ( PST, 2, PL,  SJV, IPFV, False, ("2ppl?",)), #   you           fuerais   wäret               fussiez
    72 : ( PST, 3, PL,  SJV, IPFV, False, ("3ppl?",)), #  they           fueran    wären               fussent
}

# Map tenses and aliases to unique index.
# Aliases include:
# - a short number: "s", "sg", "singular" => SINGULAR,
# - a short string: "1sg" => 1st person singular present,
# - a unique index:  1    => 1st person singular present,
# -  Penn treebank: "VBP" => 1st person singular present.
TENSES_ID = {}
TENSES_ID[INFINITIVE] = 0
for i, (tense, person, number, mood, aspect, negated, aliases) in TENSES.items():
    for a in aliases + (i,):
        TENSES_ID[i] = \
        TENSES_ID[a] = \
        TENSES_ID[(tense, person, number, mood, aspect, negated)] = i
    if number == SG:
        for sg in ("s", "sg", "singular"):
            TENSES_ID[(tense, person, sg, mood, aspect, negated)] = i
    if number == PL:
        for pl in ("p", "pl", "plural"):
            TENSES_ID[(tense, person, pl, mood, aspect, negated)] = i

# Map Penn Treebank tags to unique index.
for tag, tense in (
  ("VB", 0),    # infinitive
  ("VBP", 1),   # present 1 singular
  ("VBZ", 3),   # present 3 singular
  ("VBG", 8),   # present participle
  ("VBN", 24),  # past participle
  ("VBD", 25)): # past
    TENSES_ID[tag.lower()] = tense

# tense(tense=INFINITIVE)
# tense(tense=(PRESENT, 3, SINGULAR))
# tense(tense=PRESENT, person=3, number=SINGULAR, mood=INDICATIVE, aspect=IMPERFECTIVE, negated=False)


def tense_id(*args, **kwargs):
    """ Returns the tense id for a given (tense, person, number, mood, aspect, negated).
        Aliases and compound forms (e.g., IMPERFECT) are disambiguated.
    """
    # Unpack tense given as a tuple, e.g., tense((PRESENT, 1, SG)):
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        if args[0] not in ((PRESENT, PARTICIPLE), (PAST, PARTICIPLE)):
            args = args[0]
    # No parameters defaults to tense=INFINITIVE, tense=PRESENT otherwise.
    if len(args) == 0 and len(kwargs) == 0:
        t = INFINITIVE
    else:
        t = PRESENT
    # Set default values.
    tense   = kwargs.get("tense"  , args[0] if len(args) > 0 else t)
    person  = kwargs.get("person" , args[1] if len(args) > 1 else 3) or None
    number  = kwargs.get("number" , args[2] if len(args) > 2 else SINGULAR)
    mood    = kwargs.get("mood"   , args[3] if len(args) > 3 else INDICATIVE)
    aspect  = kwargs.get("aspect" , args[4] if len(args) > 4 else IMPERFECTIVE)
    negated = kwargs.get("negated", args[5] if len(args) > 5 else False)
    # Disambiguate wrong order of parameters.
    if mood in (PERFECTIVE, IMPERFECTIVE):
        mood, aspect = INDICATIVE, mood
    # Disambiguate INFINITIVE.
    # Disambiguate PARTICIPLE, IMPERFECT, PRETERITE.
    # These are often considered to be tenses but are in fact tense + aspect.
    if tense == INFINITIVE:
        person = number = mood = aspect = None
        negated = False
    if tense in ((PRESENT, PARTICIPLE), PRESENT + PARTICIPLE, PARTICIPLE, GERUND):
        tense, aspect = PRESENT, PROGRESSIVE
    if tense in ((PAST, PARTICIPLE), PAST + PARTICIPLE):
        tense, aspect = PAST, PROGRESSIVE
    if tense == IMPERFECT:
        tense, aspect = PAST, IMPERFECTIVE
    if tense == PRETERITE:
        tense, aspect = PAST, PERFECTIVE
    if aspect in (CONTINUOUS, PARTICIPLE, GERUND):
        aspect = PROGRESSIVE
    if aspect == PROGRESSIVE:
        person = number = None
    # Disambiguate CONDITIONAL.
    # In Spanish, the conditional is regarded as an indicative tense.
    if tense == CONDITIONAL and mood == INDICATIVE:
        tense, mood = PRESENT, CONDITIONAL
    # Disambiguate aliases: "pl" =>
    # (PRESENT, None, PLURAL, INDICATIVE, IMPERFECTIVE, False).
    return TENSES_ID.get(tense.lower(),
           TENSES_ID.get((tense, person, number, mood, aspect, negated)))

tense = tense_id

#--- VERB CONJUGATIONS -----------------------------------------------------------------------------
# Verb conjugations based on a table of known verbs and rules for unknown verbs.
# Verb conjugations are useful to find the verb infinitive in the parser's lemmatizer.
# For unknown verbs, Verbs.find_lemma() and Verbs.find_lexeme() are called.
# These must be implemented in a subclass with rules for unknown verbs.


class Verbs(lazydict):

    def __init__(self, path="", format=[], default={}, language=None):
        """ A dictionary of verb infinitives, each linked to a list of conjugated forms.
            Each line in the file at the given path is one verb, with the tenses separated by a comma.
            The format defines the order of tenses (see TENSES).
            The default dictionary defines default tenses for omitted tenses.
        """
        self._path = path
        self._language = language
        self._format = dict((TENSES_ID[id], i) for i, id in enumerate(format))
        self._default = default
        self._inverse = {}

    def load(self):
        # have,,,has,,having,,,,,had,had,haven't,,,hasn't,,,,,,,hadn't,hadn't
        id = self._format[TENSES_ID[INFINITIVE]]
        for v in _read(self._path):
            v = v.split(",")
            dict.__setitem__(self, v[id], v)
            for x in (x for x in v if x):
                self._inverse[x] = v[id]

    @property
    def path(self):
        return self._path

    @property
    def language(self):
        return self._language

    @property
    def infinitives(self):
        """ Yields a dictionary of (infinitive, [inflections])-items.
        """
        if dict.__len__(self) == 0:
            self.load()
        return self

    @property
    def inflections(self):
        """ Yields a dictionary of (inflected, infinitive)-items.
        """
        if dict.__len__(self) == 0:
            self.load()
        return self._inverse

    @property
    def TENSES(self):
        """ Yields a list of tenses for this language, excluding negations.
            Each tense is a (tense, person, number, mood, aspect)-tuple.
        """
        a = set(TENSES[id] for id in self._format)
        a = a.union(set(TENSES[id] for id in self._default.keys()))
        a = a.union(set(TENSES[id] for id in self._default.values()))
        a = sorted(x[:-2] for x in a if x[-2] is False) # Exclude negation.
        return a

    def lemma(self, verb, parse=True):
        """ Returns the infinitive form of the given verb, or None.
        """
        if dict.__len__(self) == 0:
            self.load()
        if verb.lower() in self._inverse:
            return self._inverse[verb.lower()]
        if verb in self._inverse:
            return self._inverse[verb]
        if parse is True: # rule-based
            return self.find_lemma(verb)

    def lexeme(self, verb, parse=True):
        """ Returns a list of all possible inflections of the given verb.
        """
        a = []
        b = self.lemma(verb, parse=parse)
        if b in self:
            a = [x for x in self[b] if x != ""]
        elif parse is True: # rule-based
            a = self.find_lexeme(b)
        u = []
        [u.append(x) for x in a if x not in u]
        return u

    def conjugate(self, verb, *args, **kwargs):
        """ Inflects the verb and returns the given tense (or None).
            For example: be
            - Verbs.conjugate("is", INFINITVE) => be
            - Verbs.conjugate("be", PRESENT, 1, SINGULAR) => I am
            - Verbs.conjugate("be", PRESENT, 1, PLURAL) => we are
            - Verbs.conjugate("be", PAST, 3, SINGULAR) => he was
            - Verbs.conjugate("be", PAST, aspect=PROGRESSIVE) => been
            - Verbs.conjugate("be", PAST, person=1, negated=True) => I wasn't
        """
        id = tense_id(*args, **kwargs)
        # Get the tense index from the format description (or a default).
        i1 = self._format.get(id)
        i2 = self._format.get(self._default.get(id))
        i3 = self._format.get(self._default.get(self._default.get(id)))
        b = self.lemma(verb, parse=kwargs.get("parse", True))
        v = []
        # Get the verb lexeme and return the requested index.
        if b in self:
            v = self[b]
            for i in (i1, i2, i3):
                if i is not None and 0 <= i < len(v) and v[i]:
                    return v[i]
        if kwargs.get("parse", True) is True: # rule-based
            v = self.find_lexeme(b)
            for i in (i1, i2, i3):
                if i is not None and 0 <= i < len(v) and v[i]:
                    return v[i]

    def tenses(self, verb, parse=True):
        """ Returns a list of possible tenses for the given inflected verb.
        """
        verb = verb.lower()
        a = set()
        b = self.lemma(verb, parse=parse)
        v = []
        if b in self:
            v = self[b]
        elif parse is True: # rule-based
            v = self.find_lexeme(b)
        # For each tense in the verb lexeme that matches the given tense,
        # 1) retrieve the tense tuple,
        # 2) retrieve the tense tuples for which that tense is a default.
        for i, tense in enumerate(v):
            if tense == verb:
                for id, index in self._format.items():
                    if i == index:
                        a.add(id)
                for id1, id2 in self._default.items():
                    if id2 in a:
                        a.add(id1)
                for id1, id2 in self._default.items():
                    if id2 in a:
                        a.add(id1)

        a = list(TENSES[id][:-2] for id in a)

        # In Python 2, None is always smaller than anything else while in Python 3, comparison with incompatible types yield TypeError.
        # This is why we need to use a custom key function.
        a = Tenses(sorted(a, key = lambda x: 0 if x[1] is None else x[1]))

        return a

    def find_lemma(self, verb):
        # Must be overridden in a subclass.
        # Must return the infinitive for the given conjugated (unknown) verb.
        return verb

    def find_lexeme(self, verb):
        # Must be overridden in a subclass.
        # Must return the list of conjugations for the given (unknown) verb.
        return []


class Tenses(list):

    def __contains__(self, tense):
        # t in tenses(verb) also works when t is an alias (e.g. "1sg").
        return list.__contains__(self, TENSES[tense_id(tense)][:-2])

### SENTIMENT POLARITY LEXICON #####################################################################
# A sentiment lexicon can be used to discern objective facts from subjective opinions in text.
# Each word in the lexicon has scores for:
# 1)     polarity: negative vs. positive    (-1.0 => +1.0)
# 2) subjectivity: objective vs. subjective (+0.0 => +1.0)
# 3)    intensity: modifies next word?      (x0.5 => x2.0)

# For English, adverbs are used as modifiers (e.g., "very good").
# For Dutch, adverbial adjectives are used as modifiers
# ("hopeloos voorspelbaar", "ontzettend spannend", "verschrikkelijk goed").
# Negation words (e.g., "not") reverse the polarity of the following word.

# Sentiment()(txt) returns an averaged (polarity, subjectivity)-tuple.
# Sentiment().assessments(txt) returns a list of (chunk, polarity, subjectivity, label)-tuples.

# Semantic labels are useful for fine-grained analysis, e.g.,
# negative words + positive emoticons could indicate cynicism.

# Semantic labels:
MOOD = "mood"  # emoticons, emojis
IRONY = "irony" # sarcasm mark (!)

NOUN, VERB, ADJECTIVE, ADVERB = \
    "NN", "VB", "JJ", "RB"

RE_SYNSET = re.compile(r"^[acdnrv][-_][0-9]+$")


def avg(list):
    return sum(list) / float(len(list) or 1)


class Score(tuple):

    def __new__(self, polarity, subjectivity, assessments=[]):
        """ A (polarity, subjectivity)-tuple with an assessments property.
        """
        return tuple.__new__(self, [polarity, subjectivity])

    def __init__(self, polarity, subjectivity, assessments=[]):
        self.assessments = assessments


class Sentiment(lazydict):

    def __init__(self, path="", language=None, synset=None, confidence=None, **kwargs):
        """ A dictionary of words (adjectives) and polarity scores (positive/negative).
            The value for each word is a dictionary of part-of-speech tags.
            The value for each word POS-tag is a tuple with values for
            polarity (-1.0-1.0), subjectivity (0.0-1.0) and intensity (0.5-2.0).
        """
        self._path       = path   # XML file path.
        self._language   = None   # XML language attribute ("en", "fr", ...)
        self._confidence = None   # XML confidence attribute threshold (>=).
        self._synset     = synset # XML synset attribute ("wordnet_id", "cornetto_id", ...)
        self._synsets    = {}     # {"a-01123879": (1.0, 1.0, 1.0)}
        self.labeler     = {}     # {"dammit": "profanity"}
        self.tokenizer   = kwargs.get("tokenizer", find_tokens)
        self.negations   = kwargs.get("negations", ("no", "not", "n't", "never"))
        self.modifiers   = kwargs.get("modifiers", ("RB",))
        self.modifier    = kwargs.get("modifier", lambda w: w.endswith("ly"))
        self.ngrams      = kwargs.get("ngrams", 3)

    @property
    def path(self):
        return self._path

    @property
    def language(self):
        return self._language

    @property
    def confidence(self):
        return self._confidence

    def load(self, path=None):
        """ Loads the XML-file (with sentiment annotations) from the given path.
            By default, Sentiment.path is lazily loaded.
        """
        # <word form="great" wordnet_id="a-01123879" pos="JJ" polarity="1.0" subjectivity="1.0" intensity="1.0" />
        # <word form="damnmit" polarity="-0.75" subjectivity="1.0" label="profanity" />
        if not path:
            path = self._path
        if not os.path.exists(path):
            return
        words, synsets, labels = {}, {}, {}
        xml = cElementTree.parse(path)
        xml = xml.getroot()
        for w in xml.findall("word"):
            if self._confidence is None \
            or self._confidence <= float(w.attrib.get("confidence", 0.0)):
                w, pos, p, s, i, label, synset = (
                    w.attrib.get("form"),
                    w.attrib.get("pos"),
                    w.attrib.get("polarity", 0.0),
                    w.attrib.get("subjectivity", 0.0),
                    w.attrib.get("intensity", 1.0),
                    w.attrib.get("label"),
                    w.attrib.get(self._synset) # wordnet_id, cornetto_id, ...
                )
                psi = (float(p), float(s), float(i))
                if w:
                    words.setdefault(w, {}).setdefault(pos, []).append(psi)
                if w and label:
                    labels[w] = label
                if synset:
                    synsets.setdefault(synset, []).append(psi)
        self._language = xml.attrib.get("language", self._language)
        # Average scores of all word senses per part-of-speech tag.
        for w in words:
            words[w] = dict((pos, list(map(avg, zip(*psi)))) for pos, psi in words[w].items())
        # Average scores of all part-of-speech tags.
        for w, pos in words.items():
            words[w][None] = list(map(avg, zip(*pos.values())))
        # Average scores of all synonyms per synset.
        for id, psi in synsets.items():
            synsets[id] = list(map(avg, zip(*psi)))
        dict.update(self, words)
        dict.update(self.labeler, labels)
        dict.update(self._synsets, synsets)

    def synset(self, id, pos=ADJECTIVE):
        """ Returns a (polarity, subjectivity)-tuple for the given synset id.
            For example, the adjective "horrible" has id 193480 in WordNet:
            Sentiment.synset(193480, pos="JJ") => (-0.6, 1.0, 1.0).
        """
        id = str(id).zfill(8)
        if not id.startswith(("n-", "v-", "a-", "r-")):
            if pos == NOUN:
                id = "n-" + id
            if pos == VERB:
                id = "v-" + id
            if pos == ADJECTIVE:
                id = "a-" + id
            if pos == ADVERB:
                id = "r-" + id
        if dict.__len__(self) == 0:
            self.load()
        try:
            return tuple(self._synsets[id])[:2]
        except KeyError: # Some WordNet id's are not zero padded.
            return tuple(self._synsets.get(re.sub(r"-0+", "-", id), (0.0, 0.0))[:2])

    def __call__(self, s, negation=True, ngrams=DEFAULT, **kwargs):
        """ Returns a (polarity, subjectivity)-tuple for the given sentence,
            with polarity between -1.0 and 1.0 and subjectivity between 0.0 and 1.0.
            The sentence can be a string, Synset, Text, Sentence, Chunk, Word, Document, Vector.
            An optional weight parameter can be given,
            as a function that takes a list of words and returns a weight.
        """
        def avg(assessments, weighted=lambda w: 1):
            s, n = 0, 0
            for words, score in assessments:
                w = weighted(words)
                s += w * score
                n += w
            return s / float(n or 1)
        ngrams = ngrams if ngrams != DEFAULT else self.ngrams
        # A pattern.en.wordnet.Synset.
        # Sentiment(synsets("horrible", "JJ")[0]) => (-0.6, 1.0)
        if hasattr(s, "gloss"):
            a = [(s.synonyms[0],) + self.synset(s.id, pos=s.pos) + (None,)]
        # A synset id.
        # Sentiment("a-00193480") => horrible => (-0.6, 1.0)   (English WordNet)
        # Sentiment("c_267") => verschrikkelijk => (-0.9, 1.0) (Dutch Cornetto)
        elif isinstance(s, str) and RE_SYNSET.match(s):
            a = [(s.synonyms[0],) + self.synset(s.id, pos=s.pos) + (None,)]
        # A string of words.
        # Sentiment("a horrible movie") => (-0.6, 1.0)
        elif isinstance(s, str):
            a = self.assessments(((w.lower(), None) for w in " ".join(self.tokenizer(s)).split()), negation, ngrams)
        # A pattern.en.Text.
        elif hasattr(s, "sentences"):
            a = self.assessments(((w.lemma or w.string.lower(), w.pos[:2]) for w in chain(*s)), negation, ngrams)
        # A pattern.en.Sentence or pattern.en.Chunk.
        elif hasattr(s, "lemmata"):
            a = self.assessments(((w.lemma or w.string.lower(), w.pos[:2]) for w in s.words), negation, ngrams)
        # A pattern.en.Word.
        elif hasattr(s, "lemma"):
            a = self.assessments(((s.lemma or s.string.lower(), s.pos[:2]),), negation, ngrams)
        # A pattern.vector.Document.
        # Average score = weighted average using feature weights.
        # Bag-of words is unordered: inject None between each two words
        # to stop assessments() from scanning for preceding negation & modifiers.
        elif hasattr(s, "terms"):
            a = self.assessments(chain(*(((w, None), (None, None)) for w in s)), negation, ngrams)
            kwargs.setdefault("weight", lambda w: s.terms[w[0]])
        # A dict of (word, weight)-items.
        elif isinstance(s, dict):
            a = self.assessments(chain(*(((w, None), (None, None)) for w in s)), negation, ngrams)
            kwargs.setdefault("weight", lambda w: s[w[0]])
        # A list of words.
        elif isinstance(s, list):
            a = self.assessments(((w, None) for w in s), negation, ngrams)
        else:
            a = []
        weight = kwargs.get("weight", lambda w: 1)
        # Each "w" in "a" is a (words, polarity, subjectivity, label)-tuple.
        return Score(polarity = avg(map(lambda w: (w[0], w[1]), a), weight),
                 subjectivity = avg(map(lambda w: (w[0], w[2]), a), weight),
                  assessments = a)

    def assessments(self, words=[], negation=True, ngrams=DEFAULT):
        """ Returns a list of (chunk, polarity, subjectivity, label)-tuples for the given list of words:
            where chunk is a list of successive words: a known word optionally
            preceded by a modifier ("very good") or a negation ("not good").
        """
        ngrams = ngrams if ngrams != DEFAULT else self.ngrams
        words = list(words)
        index = 0
        a = []
        m = None # Preceding modifier (i.e., adverb or adjective).
        n = None # Preceding negation (e.g., "not beautiful").
        while index < len(words):
            w, pos = words[index]
            # Only assess known words, preferably by part-of-speech tag.
            # Including unknown words (polarity 0.0 and subjectivity 0.0) lowers the average.
            if w is None:
                index += 1
                continue
            for i in reversed(range(1, max(1, ngrams))):
                # Known idioms ("hit the spot").
                if index < len(words) - i:
                    idiom = words[index:index + i + 1]
                    idiom = " ".join(w_pos[0] or "END-OF-NGRAM" for w_pos in idiom)
                    if idiom in self:
                        w, pos = idiom, None
                        index += i
                        break
            if w in self and pos in self[w]:
                p, s, i = self[w][pos]
                # Known word not preceded by a modifier ("good").
                if m is None:
                    a.append(dict(w=[w], p=p, s=s, i=i, n=1, x=self.labeler.get(w)))
                # Known word preceded by a modifier ("really good").
                if m is not None:
                    a[-1]["w"].append(w)
                    a[-1]["p"] = max(-1.0, min(p * a[-1]["i"], +1.0))
                    a[-1]["s"] = max(-1.0, min(s * a[-1]["i"], +1.0))
                    a[-1]["i"] = i
                    a[-1]["x"] = self.labeler.get(w)
                # Known word preceded by a negation ("not really good").
                if n is not None:
                    a[-1]["w"].insert(0, n)
                    a[-1]["i"] = 1.0 / (a[-1]["i"] or 1)
                    a[-1]["n"] = -1
                # Known word may be a negation.
                # Known word may be modifying the next word (i.e., it is a known adverb).
                m = None
                n = None
                if pos and pos in self.modifiers or any(map(self[w].__contains__, self.modifiers)):
                    m = (w, pos)
                if negation and w in self.negations:
                    n = w
            else:
                # Unknown word may be a negation ("not good").
                if negation and w in self.negations:
                    n = w
                # Unknown word. Retain negation across small words ("not a good").
                elif n and len(w.strip("'")) > 1:
                    n = None
                # Unknown word may be a negation preceded by a modifier ("really not good").
                if n is not None and m is not None and (pos in self.modifiers or self.modifier(m[0])):
                    a[-1]["w"].append(n)
                    a[-1]["n"] = -1
                    n = None
                # Unknown word. Retain modifier across small words ("really is a good").
                elif m and len(w) > 2:
                    m = None
                # Exclamation marks boost previous word.
                if w == "!" and len(a) > 0:
                    a[-1]["w"].append("!")
                    a[-1]["p"] = max(-1.0, min(a[-1]["p"] * 1.25, +1.0))
                # Exclamation marks in parentheses indicate sarcasm.
                if w == "(!)":
                    a.append(dict(w=[w], p=0.0, s=1.0, i=1.0, n=1, x=IRONY))
                # EMOTICONS: {("grin", +1.0): set((":-D", ":D"))}
                if w.isalpha() is False and len(w) <= 5 and w not in PUNCTUATION: # speedup
                    for E in (EMOTICONS, EMOJI):
                        for (type, p), e in E.items():
                            if w in map(lambda e: e.lower(), e):
                                a.append(dict(w=[w], p=p, s=1.0, i=1.0, n=1, x=MOOD))
                                break
            index += 1
        for i in range(len(a)):
            w = a[i]["w"]
            p = a[i]["p"]
            s = a[i]["s"]
            n = a[i]["n"]
            x = a[i]["x"]
            # "not good" = slightly bad, "not bad" = slightly good.
            a[i] = (w, p * -0.5 if n < 0 else p, s, x)
        return a

    def annotate(self, word, pos=None, polarity=0.0, subjectivity=0.0, intensity=1.0, label=None):
        """ Annotates the given word with polarity, subjectivity and intensity scores,
            and optionally a semantic label (e.g., MOOD for emoticons, IRONY for "(!)").
        """
        w = self.setdefault(word, {})
        w[pos] = w[None] = (polarity, subjectivity, intensity)
        if label:
            self.labeler[word] = label

    def save(self, path):
        """ Saves the lexicon as an XML-file.
        """
        # WordNet id's, word sense descriptions and confidence scores
        # from a bundled XML (e.g., en/lexicon-en.xml) are not saved.
        a = []
        a.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
        a.append("<sentiment>")
        for w in sorted(self):
            for pos, (p, s, i) in self[w].items():
                pos = pos or ""
                if pos or len(self[w]) == 1:
                    a.append("\t<word %s %s %s %s %s %s />" % (
                              "form=\"%s\""   % w,
                               "pos=\"%s\""   % pos,
                          "polarity=\"%.2f\"" % p,
                      "subjectivity=\"%.2f\"" % s,
                         "intensity=\"%.2f\"" % i,
                             "label=\"%s\""   % self.labeler.get(w, "")
                    ))
        a.append("</sentiment>")
        f = open(path, "w", encoding="utf-8")
        f.write(BOM_UTF8 + encode_utf8("\n".join(a)))
        f.close()

#### SPELLING CORRECTION ###########################################################################
# Based on: Peter Norvig, "How to Write a Spelling Corrector", http://norvig.com/spell-correct.html


class Spelling(lazydict):

    ALPHA = "abcdefghijklmnopqrstuvwxyz"

    def __init__(self, path=""):
        self._path = path

    def load(self):
        for x in _read(self._path):
            x = x.split()
            dict.__setitem__(self, x[0], int(x[1]))

    @property
    def path(self):
        return self._path

    @property
    def language(self):
        return self._language

    @classmethod
    def train(self, s, path="spelling.txt"):
        """ Counts the words in the given string and saves the probabilities at the given path.
            This can be used to generate a new model for the Spelling() constructor.
        """
        model = {}
        for w in re.findall("[a-z]+", s.lower()):
            model[w] = w in model and model[w] + 1 or 1
        model = ("%s %s" % (k, v) for k, v in sorted(model.items()))
        model = "\n".join(model)
        f = open(path, "w", encoding="utf-8")
        f.write(model)
        f.close()

    def _edit1(self, w):
        """ Returns a set of words with edit distance 1 from the given word.
        """
        # Of all spelling errors, 80% is covered by edit distance 1.
        # Edit distance 1 = one character deleted, swapped, replaced or inserted.
        split = [(w[:i], w[i:]) for i in range(len(w) + 1)]
        delete, transpose, replace, insert = (
            [a + b[1:] for a, b in split if b],
            [a + b[1] + b[0] + b[2:] for a, b in split if len(b) > 1],
            [a + c + b[1:] for a, b in split for c in Spelling.ALPHA if b],
            [a + c + b[0:] for a, b in split for c in Spelling.ALPHA]
        )
        return set(delete + transpose + replace + insert)

    def _edit2(self, w):
        """ Returns a set of words with edit distance 2 from the given word
        """
        # Of all spelling errors, 99% is covered by edit distance 2.
        # Only keep candidates that are actually known words (20% speedup).
        return set(e2 for e1 in self._edit1(w) for e2 in self._edit1(e1) if e2 in self)

    def _known(self, words=[]):
        """ Returns the given list of words filtered by known words.
        """
        return set(w for w in words if w in self)

    def suggest(self, w):
        """ Return a list of (word, confidence) spelling corrections for the given word,
            based on the probability of known words with edit distance 1-2 from the given word.
        """
        if len(self) == 0:
            self.load()
        if len(w) == 1:
            return [(w, 1.0)] # I
        if w in PUNCTUATION:
            return [(w, 1.0)] # .?!
        if w.replace(".", "").isdigit():
            return [(w, 1.0)] # 1.5
        candidates = self._known([w]) \
                  or self._known(self._edit1(w)) \
                  or self._known(self._edit2(w)) \
                  or [w]
        candidates = [(self.get(c, 0.0), c) for c in candidates]
        s = float(sum(p for p, w in candidates) or 1)
        candidates = sorted(((p / s, w) for p, w in candidates), reverse=True)
        candidates = [(w.istitle() and x.title() or x, p) for p, x in candidates] # case-sensitive
        return candidates

#### MULTILINGUAL ##################################################################################
# The default functions in each language submodule, with an optional language parameter:
# from pattern.text import parse
# print(parse("The cat sat on the mat.", language="en"))
# print(parse("De kat zat op de mat.", language="nl"))

LANGUAGES = ["en", "es", "de", "fr", "it", "nl"]

_modules = {}


def _module(language):
    """ Returns the given language module (e.g., "en" => pattern.en).
    """

    if sys.version > '3':
        return _modules.setdefault(language, __import__(language, globals(), {}, [], 1))
    else:
        return _modules.setdefault(language, __import__(language, globals(), {}, [], -1))


def _multilingual(function, *args, **kwargs):
    """ Returns the value from the function with the given name in the given language module.
        By default, language="en".
    """
    return getattr(_module(kwargs.pop("language", "en")), function)(*args, **kwargs)


def language(s):
    """ Returns a (language, confidence)-tuple for the given string.
    """
    s = decode_utf8(s)
    s = set(w.strip(PUNCTUATION) for w in s.replace("'", "' ").split())
    n = float(len(s) or 1)
    p = {}
    for xx in LANGUAGES:
        lexicon = _module(xx).__dict__["lexicon"]
        p[xx] = sum(1 for w in s if w in lexicon) / n
    return max(p.items(), key=lambda kv: (kv[1], int(kv[0] == "en")))

lang = language


def tokenize(*args, **kwargs):
    return _multilingual("tokenize", *args, **kwargs)


def parse(*args, **kwargs):
    return _multilingual("parse", *args, **kwargs)


def parsetree(*args, **kwargs):
    return _multilingual("parsetree", *args, **kwargs)


def split(*args, **kwargs):
    return _multilingual("split", *args, **kwargs)


def tag(*args, **kwargs):
    return _multilingual("tag", *args, **kwargs)


def keywords(*args, **kwargs):
    return _multilingual("keywords", *args, **kwargs)


def suggest(*args, **kwargs):
    return _multilingual("suggest", *args, **kwargs)


def sentiment(*args, **kwargs):
    return _multilingual("sentiment", *args, **kwargs)


def singularize(*args, **kwargs):
    return _multilingual("singularize", *args, **kwargs)


def pluralize(*args, **kwargs):
    return _multilingual("pluralize", *args, **kwargs)


def conjugate(*args, **kwargs):
    return _multilingual("conjugate", *args, **kwargs)


def predicative(*args, **kwargs):
    return _multilingual("predicative", *args, **kwargs)


def suggest(*args, **kwargs):
    return _multilingual("suggest", *args, **kwargs)
