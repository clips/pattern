#### PATTERN | WORDNET #############################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# WordNet is a lexical database for English.
# It disambiguates word senses, e.g., "tree" in the sense of a plant or in the sense of a graph.
# It groups similar word senses into sets of synonyms called synsets,
# with a short description and semantic relations to other synsets:
# -  synonym = a word that is similar in meaning,
# - hypernym = a word with a broader meaning,       (tree => plant)
# -  hyponym = a word with a more specific meaning, (tree => oak)
# -  holonym = a word that is the whole of parts,   (tree => forest)
# -  meronym = a word that is a part of the whole,  (tree => trunk)
# -  antonym = a word that is opposite in meaning.

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

import os
import sys
import glob

from io import open

from math import log

from pattern.text import lazydict

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

# Path to WordNet /dict folder.
#CORPUS = ""
#os.environ["WNHOME"] = os.path.join(MODULE, CORPUS)
#os.environ["WNSEARCHDIR"] = os.path.join(MODULE, CORPUS, "dict")

import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus import sentiwordnet as swn
from nltk.corpus import wordnet_ic as wn_ic
from nltk.corpus.reader.wordnet import Synset as WordNetSynset

# Make sure the necessary corpora are downloaded to the local drive
for token in ("wordnet", "wordnet_ic", "sentiwordnet"):
    try:
        nltk.data.find("corpora/" + token)
    except LookupError:
        try:
            nltk.download(token, quiet = True, raise_on_error = True)
        except ValueError:
            # Sometimes there are problems with the default index.xml URL. Then we will try this...
            from nltk.downloader import Downloader as NLTKDownloader
            d = NLTKDownloader("http://nltk.github.com/nltk_data/")
            d.download(token, quiet = True, raise_on_error = True)

# Use the Brown corpus for calculating information content (IC)
brown_ic = wn_ic.ic('ic-brown.dat')
IC_CORPUS, IC_MAX = brown_ic, {}
for key in IC_CORPUS:
    IC_MAX[key] = max(IC_CORPUS[key].values())

# This will hold the WordNet version
VERSION = wn.get_version() or "3.0"

#---------------------------------------------------------------------------------------------------

DIACRITICS = {
    "a": ("á", "ä", "â", "à", "å"),
    "e": ("é", "ë", "ê", "è"),
    "i": ("í", "ï", "î", "ì"),
    "o": ("ó", "ö", "ô", "ò", "ō", "ø"),
    "u": ("ú", "ü", "û", "ù", "ů"),
    "y": ("ý", "ÿ", "ý"),
    "s": ("š",),
    "c": ("ç", "č"),
    "n": ("ñ",),
    "z": ("ž",)
}


def normalize(word):
    """ Normalizes the word for synsets() or Sentiwordnet[] by removing diacritics
        (PyWordNet does not take unicode) and replacing spaces with underscores.
    """
    if not isinstance(word, str):
        word = str(word)
    if not isinstance(word, str):
        try:
            word = word.encode("utf-8", "ignore")
        except:
            pass
    for k, v in DIACRITICS.items():
        for v in v:
            word = word.replace(v, k)

    # Replace spaces with underscores
    word = word.replace(" ", "_")

    return word

### SYNSET #########################################################################################

NOUNS = lambda: wn.all_lemma_names(wn.NOUN)
VERBS = lambda: wn.all_lemma_names(wn.VERB)
ADJECTIVES = lambda: wn.all_lemma_names(wn.ADJ)
ADVERBS = lambda: wn.all_lemma_names(wn.ADV)

NOUN, VERB, ADJECTIVE, ADVERB = \
    NN, VB, JJ, RB = \
        "NN", "VB", "JJ", "RB"

_pattern2wordnet = {NN : wn.NOUN, VB : wn.VERB, JJ : wn.ADJ, RB: wn.ADV}
_wordnet2pattern = {v : k for k, v in _pattern2wordnet.items()}
_wordnet2pattern[wn.ADJ_SAT] = JJ


def synsets(word, pos=NOUN):
    """ Returns a list of Synset objects, one for each word sense.
        Each word can be understood in different "senses", 
        each of which is part of a set of synonyms (= Synset).
    """
    word, pos = normalize(word), pos.lower()
    try:
        if pos.startswith(NOUN.lower()): # "NNS" or "nn" will also pass.
            w = wn.synsets(word, pos = wn.NOUN)
        elif pos.startswith(VERB.lower()):
            w = wn.synsets(word, pos = wn.VERB)
        elif pos.startswith(ADJECTIVE.lower()):
            w = wn.synsets(word, pos = wn.ADJ)
        elif pos.startswith(ADVERB.lower()):
            w = wn.synsets(word, pos = wn.ADV)
        else:
            raise TypeError("part of speech must be NOUN, VERB, ADJECTIVE or ADVERB, not %s" % repr(pos))
        return [Synset(synset) for synset in w]
    except KeyError:
        return []
    return []


class _synset(lazydict):

    def __getitem__(self, k):
        for pos in ("n", "v", "a", "r"):
            try:
                synset = wn._synset_from_pos_and_offset(pos, k)
            except:
                pass
            if synset:
                return synset
        return None


class Synset(object):

    def __init__(self, synset):
        """ A set of synonyms that share a common meaning.
        """
        if isinstance(synset, WordNetSynset):
            self._wnsynset = synset
        elif isinstance(synset, Synset):
            self = self
        elif isinstance(synset, (tuple, int)):
            if isinstance(synset, int):
                synset = (synset, "NN")
            offset, pos = synset
            self._wnsynset = wn._synset_from_pos_and_offset(_pattern2wordnet[pos] if pos in _pattern2wordnet else pos, offset)
        else:
            raise NotImplementedError

        self._synset = _synset

    def __iter__(self):
        for s in self.synonyms:
            yield s

    def __len__(self):
        return len(self.synonyms)

    def __getitem__(self, i):
        return self.synonyms[i]

    def __eq__(self, synset):
        return isinstance(synset, Synset) and self.id == synset.id

    def __ne__(self, synset):
        return not self.__eq__(synset)
    __repr__ = lambda self: self._wnsynset.__repr__()

    @property
    def id(self):
        return self._wnsynset.offset()

    @property
    def pos(self):
        """ Yields the part-of-speech tag (NOUN, VERB, ADJECTIVE or ADVERB).
        """
        pos = self._wnsynset.pos()
        if pos == wn.NOUN:
            return NOUN
        if pos == wn.VERB:
            return VERB
        if pos == wn.ADJ or pos == wn.ADJ_SAT:
            return ADJECTIVE
        if pos == wn.ADV:
            return ADVERB

    part_of_speech = tag = pos

    @property
    def synonyms(self):
        """ Yields a list of word forms (i.e. synonyms), for example:
            synsets("TV")[0].synonyms => ["television", "telecasting", "TV", "video"]
        """
        return [s for s in self._wnsynset.lemma_names()]

    senses = synonyms # Backwards compatibility; senses = list of Synsets for a word.

    @property
    def gloss(self):
        """ Yields a descriptive string.
        """
        return self._wnsynset.definition()

    @property
    def lexname(self):
        """ Yields a category, e.g., noun.animal.
        """
        return self._wnsynset.lexname()

    @property
    def antonym(self):
        """ Yields the semantically opposite synset, for example:
            synsets("death")[0].antonym => Synset("birth").
        """
        p = [Synset(a.synset()) for l in self._wnsynset.lemmas() for a in l.antonyms()]
        return len(p) > 0 and p or None

    def meronyms(self):
        """ Yields a list of synsets that are semantic members/parts of this synset, for example:
            synsets("house")[0].meronyms() =>
            [Synset("library"),
             Synset("loft"),
             Synset("porch")
            ]
        """
        p = self._wnsynset.member_meronyms()
        p += self._wnsynset.part_meronyms()
        return [Synset(p) for p in p]

    def holonyms(self):
        """ Yields a list of synsets of which this synset is a member/part, for example:
            synsets("tree")[0].holonyms() => Synset("forest").
        """
        p = self._wnsynset.member_holonyms()
        p += self._wnsynset.part_holonyms()
        return [Synset(p) for p in p]

    def hyponyms(self, recursive=False, depth=None):
        """ Yields a list of semantically more specific synsets, for example:
            synsets("train")[0].hyponyms() =>
            [Synset("boat train"),
             Synset("car train"),
             Synset("freight train"),
             Synset("hospital train"),
             Synset("mail train"),
             Synset("passenger train"),
             Synset("streamliner"),
             Synset("subway train")
            ]
        """
        p = [Synset(p) for p in self._wnsynset.hyponyms()]
        if depth is None and recursive is False:
            return p
        if depth == 0:
            return []
        if depth is not None:
            depth -= 1
        if depth is None or depth > 0:
            [p.extend(s.hyponyms(True, depth)) for s in list(p)]
        return p

    def hypernyms(self, recursive=False, depth=None):
        """ Yields a list of semantically broader synsets.
        """
        p = [Synset(p) for p in self._wnsynset.hypernyms()]
        if depth is None and recursive is False:
            return p
        if depth == 0:
            return []
        if depth is not None:
            depth -= 1
        if depth is None or depth > 0:
            [p.extend(s.hypernyms(True, depth)) for s in list(p)]
        return p

    @property
    def hypernym(self):
        """ Yields the synset that is the semantic parent, for example:
            synsets("train")[0].hypernym => Synset("public transport").
        """
        p = self.hypernyms()
        return len(p) > 0 and p[0] or None

    def similar(self):
        """ Returns a list of similar synsets for adjectives and adverbs, for example:
            synsets("almigthy",JJ)[0].similar() => Synset("powerful").
        """
        # ALSO_SEE returns wn.Sense instead of wn.Synset in some cases:
        #s = lambda x: isinstance(x, wn.Sense) and x.synset or x
        p = [Synset(p) for p in self._wnsynset.similar_tos()]
        p += [Synset(p) for p in self._wnsynset.also_sees()]
        return p

    def similarity(self, synset):
        """ Returns the semantic similarity of the given synsets (0.0-1.0).
            synsets("cat")[0].similarity(synsets("dog")[0]) => 0.86.
            synsets("cat")[0].similarity(synsets("box")[0]) => 0.17.
        """

        return self._wnsynset.lin_similarity(synset._wnsynset, IC_CORPUS)

    @property
    def ic(self):
        offset, pos = self.id, self.pos
        if pos in _pattern2wordnet:
            pos = _pattern2wordnet[pos]
        if pos in IC_CORPUS and offset in IC_CORPUS[pos]:
            return IC_CORPUS[pos][offset] / IC_MAX[pos]
        return None

    @property
    def weight(self):
        return sentiwordnet is not None \
           and sentiwordnet.synset(self.id, self.pos)[:2] \
            or None


def similarity(synset1, synset2):
    """ Returns the semantic similarity of the given synsets.
    """
    return synset1.similarity(synset2)


def ancestor(synset1, synset2):
    """ Returns the common ancestor of both synsets.
        For example synsets("cat")[0].ancestor(synsets("dog")[0]) => Synset("carnivore")
    """
    h1, h2 = synset1.hypernyms(recursive=True), synset2.hypernyms(recursive=True)
    for s in h1:
        if s in h2:
            return s

least_common_subsumer = lcs = ancestor

### INFORMATION CONTENT ############################################################################
# Information Content (IC) is used to calculate semantic similarity in Synset.similarity().
# Information Content values for each synset are derived from word frequency in a given corpus.
# The idea is that less frequent words convey more information.
# Semantic similarity depends on the amount of information two concepts (synsets) have in common,
# given by the Most Speciﬁc Common Abstraction (MSCA), i.e. the shared ancestor in the taxonomy.
# http://www.d.umn.edu/~tpederse/Pubs/AAAI04PedersenT.pdf
# http://afflatus.ucd.ie/papers/ecai2004b.pdf

#IC = {} # Switch data file according to WordNet version:
#IC_CORPUS = os.path.join(MODULE, "resnik-ic" + VERSION[0] + ".txt")
#IC_MAX = 0

# def information_content(synset):
#     """ Returns the IC value for the given Synset (trained on the Brown corpus).
#     """
#     global IC_MAX
#     if not IC:
#         IC[NOUN] = {}
#         IC[VERB] = {}
#         for s in open(IC_CORPUS).readlines()[1:]: # Skip the header.
#             s = s.split()
#             id, w, pos = (
#                 int(s[0][:-1]),
#                 float(s[1]),
#                 s[0][-1] == "n" and NOUN or VERB)
#             if len(s) == 3 and s[2] == "ROOT":
#                 IC[pos][0] = IC[pos].get(0,0) + w
#             if w != 0:
#                 IC[pos][id] = w
#             if w > IC_MAX:
#                 IC_MAX = w
#     return IC.get(synset.pos, {}).get(synset.id, 0.0) / IC_MAX

### WORDNET3 TO WORDNET2 ###########################################################################
# Map WordNet3 synset id's to WordNet2 synset id's.

_map32_pos1 = {NN: "n", VB: "v", JJ: "a", RB: "r"}
_map32_pos2 = {"n": NN, "v": VB, "a": JJ, "s" : JJ, "r": RB}
_map32_cache = None


def map32(id, pos=NOUN):
    """ Returns an (id, pos)-tuple with the WordNet2 synset id for the given WordNet3 synset id.
        Returns None if no id was found.
    """
    global _map32_cache
    if not _map32_cache:
        _map32_cache = open(os.path.join(MODULE, "dict", "index.32"), encoding="latin-1").readlines()
        _map32_cache = (x for x in _map32_cache if x[0] != ";") # comments
        _map32_cache = dict(x.strip().split(" ") for x in _map32_cache)
    k = pos in _map32_pos2 and pos or _map32_pos1.get(pos, "x")
    k += str(id).lstrip("0")
    k = _map32_cache.get(k, None)
    if k is not None:
        return int(k[1:]), _map32_pos2[k[0]]
    return None

#### SENTIWORDNET ##################################################################################
# http://nmis.isti.cnr.it/sebastiani/Publications/LREC06.pdf
# http://nmis.isti.cnr.it/sebastiani/Publications/LREC10.pdf

sys.path.insert(0, os.path.join(MODULE, "..", ".."))

try:
    from pattern.text import Sentiment
except:
    class Sentiment(object):
        PLACEHOLDER = True

sys.path.pop(0)


class SentiWordNet(Sentiment):

    def __init__(self, path=None, language="en"):
        """ A sentiment lexicon with scores from SentiWordNet.
            The value for each word is a tuple with values for
            polarity (-1.0-1.0), subjectivity (0.0-1.0) and intensity (0.5-2.0).
        """
        Sentiment.__init__(self, path=path, language=language)

    def load(self):
        pass

    def synset(self, id, pos=ADJECTIVE):
        if pos in _pattern2wordnet:
            pos = _pattern2wordnet[pos]
        try:
            s = wn._synset_from_pos_and_offset(pos, id)
            lemma = s.lemma_names()[0]
            return self[lemma]
        except:
            pass

        return None

    # Words are stored without diacritics,
    # use wordnet.normalize(word).
    def __getitem__(self, k):
        synsets = list(swn.senti_synsets(k))
        if synsets:
            p, n = synsets[0].pos_score(), synsets[0].neg_score()
            v = (float(p) - float(n), float(p) + float(n))
            return v
        else:
            return None

    def assessments(self, words=[], negation=True):
        raise NotImplementedError

    def __call__(self, s, negation=True):
        raise NotImplementedError

if not hasattr(Sentiment, "PLACEHOLDER"):
    sentiwordnet = SentiWordNet()
else:
    sentiwordnet = None

# Backwards compatibility.
# Older code may be using pattern.en.wordnet.sentiment[w],
# which yields a (positive, negative, neutral)-tuple.


class sentiment(object):

    def load(self, **kwargs):
        sentiwordnet.load(**kwargs)

    def __getitem__(self, w):
        p, s = sentiwordnet.get(w, (0.0, 0.0))
        return p < 0 and (0.0, -p, 1.0 - s) or (p, 0.0, 1.0 - s)

    def __contains__(self, w):
        return w in sentiwordnet

sentiment = sentiment()

#print sentiwordnet["industry"] # (0.0, 0.0)
#print sentiwordnet["horrible"] # (-0.625, 0.625)
#print sentiwordnet.synset(synsets("horrible", pos="JJ")[0].id, pos="JJ")
#print synsets("horrible", pos="JJ")[0].weight
