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

import os
import sys
import glob

from math import log

try: 
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

# Path to WordNet /dict folder.
CORPUS = ""
os.environ["WNHOME"] = os.path.join(MODULE, CORPUS)
os.environ["WNSEARCHDIR"] = os.path.join(MODULE, CORPUS, "dict")

from pywordnet import wordnet as wn
from pywordnet import wntools

# The bundled version of PyWordNet has custom fixes.
# - line  365: check if lexnames exist.
# - line  765: check if lexnames exist + use os.path.join().
# - line  674: add HYPONYM and HYPERNYM to the pointer table.
# - line  916: implement "x in Dictionary" instead of Dictionary.has_key(x)
# - line  804: Dictionary.dataFile now stores a list of (file, size)-tuples.
# - line 1134: _dataFilePath() returns a list (i.e., data.noun can be split into data.noun1 + data.noun2).
# - line 1186: _lineAt() seeks in second datafile if offset > EOF first datafile.

VERSION = ""
s = open(os.path.join(MODULE, CORPUS, "dict", "index.noun")).read(2048)
if "WordNet 2.1" in s: VERSION = "2.1"
if "WordNet 3.0" in s: VERSION = "3.0"
del s

#---------------------------------------------------------------------------------------------------

DIACRITICS = {
    "a": ("á","ä","â","à","å"),
    "e": ("é","ë","ê","è"),
    "i": ("í","ï","î","ì"),
    "o": ("ó","ö","ô","ò","ō","ø"),
    "u": ("ú","ü","û","ù","ů"),
    "y": ("ý","ÿ","ý"),
    "s": ("š",),
    "c": ("ç","č"),
    "n": ("ñ",),
    "z": ("ž",)
}

def normalize(word):
    """ Normalizes the word for synsets() or Sentiwordnet[] by removing diacritics
        (PyWordNet does not take unicode).
    """
    if not isinstance(word, basestring):
        word = str(word)
    if not isinstance(word, str):
        try: word = word.encode("utf-8", "ignore")
        except:
            pass
    for k, v in DIACRITICS.items(): 
        for v in v: 
            word = word.replace(v, k)
    return word

### SYNSET #########################################################################################

NOUNS, VERBS, ADJECTIVES, ADVERBS = \
    wn.N, wn.V, wn.ADJ, wn.ADV

NOUN, VERB, ADJECTIVE, ADVERB = \
    NN, VB, JJ, RB = \
        "NN", "VB", "JJ", "RB"

def synsets(word, pos=NOUN):
    """ Returns a list of Synset objects, one for each word sense.
        Each word can be understood in different "senses", 
        each of which is part of a set of synonyms (= Synset).
    """
    word, pos = normalize(word), pos.lower()
    try:
        if pos.startswith(NOUN.lower()): # "NNS" or "nn" will also pass. 
            w = wn.N[word]
        elif pos.startswith(VERB.lower()):
            w = wn.V[word]
        elif pos.startswith(ADJECTIVE.lower()):
            w = wn.ADJ[word]
        elif pos.startswith(ADVERB.lower()):
            w = wn.ADV[word]
        else:
            raise TypeError("part of speech must be NOUN, VERB, ADJECTIVE or ADVERB, not %s" % repr(pos))
        return [Synset(s.synset) for i, s in enumerate(w)]
    except KeyError:
        return []
    return []

class Synset(object):
    
    def __init__(self, synset=None, pos=NOUN):
        """ A set of synonyms that share a common meaning.
        """
        if isinstance(synset, int):
            synset = wn.getSynset({NN: "n", VB: "v", JJ: "adj", RB: "adv"}[pos], synset)
        if isinstance(synset, basestring):
            synset = synsets(synset, pos)[0]._synset
        self._synset = synset

    def __iter__(self):
        for s in self._synset.getSenses(): yield unicode(s.form)
    def __len__(self):
        return len(self._synset.getSenses())
    def __getitem__(self, i):
        return unicode(self._synset.getSenses()[i].form)
    def __eq__(self, synset):
        return isinstance(synset, Synset) and self.id == synset.id
    def __ne__(self, synset):
        return not self.__eq__(synset)
    def __repr__(self):
        return "Synset(%s)" % repr(self[0])

    @property
    def id(self):
        return self._synset.offset

    @property
    def pos(self):
        """ Yields the part-of-speech tag (NOUN, VERB, ADJECTIVE or ADVERB).
        """
        pos = self._synset.pos
        if pos == "noun":
            return NOUN
        if pos == "verb":
            return VERB
        if pos == "adjective":
            return ADJECTIVE
        if pos == "adverb":
            return ADVERB
            
    part_of_speech = tag = pos

    @property
    def synonyms(self):
        """ Yields a list of word forms (i.e. synonyms), for example:
            synsets("TV")[0].synonyms => ["television", "telecasting", "TV", "video"]
        """
        return [unicode(s.form) for s in self._synset.getSenses()]
        
    senses = synonyms # Backwards compatibility; senses = list of Synsets for a word.
        
    @property
    def gloss(self):
        """ Yields a descriptive string, for example:
            synsets("glass")[0].gloss => "a brittle transparent solid with irregular atomic structure".
        """
        return unicode(self._synset.gloss)
        
    @property
    def lexname(self):
        """ Yields a category, e.g., noun.animal.
        """
        return self._synset.lexname and unicode(self._synset.lexname) or None

    @property
    def antonym(self):
        """ Yields the semantically opposite synset, for example:
            synsets("death")[0].antonym => Synset("birth").
        """
        p = self._synset.getPointers(wn.ANTONYM)
        return len(p) > 0 and Synset(p[0].getTarget()) or None        

    def meronyms(self):
        """ Yields a list of synsets that are semantic members/parts of this synset, for example:
            synsets("house")[0].meronyms() =>
            [Synset("library"), 
             Synset("loft"), 
             Synset("porch")
            ]
        """
        p = self._synset.getPointers(wn.MEMBER_HOLONYM)
        p+= self._synset.getPointers(wn.PART_HOLONYM)
        return [Synset(p.getTarget()) for p in p]

    def holonyms(self):
        """ Yields a list of synsets of which this synset is a member/part, for example:
            synsets("tree")[0].holonyms() => Synset("forest").
        """
        p = self._synset.getPointers(wn.MEMBER_MERONYM)
        p+= self._synset.getPointers(wn.PART_MERONYM)
        return [Synset(p.getTarget()) for p in p]

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
        p = [Synset(p.getTarget()) for p in self._synset.getPointers(wn.HYPONYM)]
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
        p = [Synset(p.getTarget()) for p in self._synset.getPointers(wn.HYPERNYM)]
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
        p = self._synset.getPointers(wn.HYPERNYM)
        return len(p) > 0 and Synset(p[0].getTarget()) or None

    def similar(self):
        """ Returns a list of similar synsets for adjectives and adverbs, for example:
            synsets("almigthy",JJ)[0].similar() => Synset("powerful").
        """
        # ALSO_SEE returns wn.Sense instead of wn.Synset in some cases:
        s = lambda x: isinstance(x, wn.Sense) and x.synset or x
        p = [Synset(s(p.getTarget())) for p in self._synset.getPointers(wn.SIMILAR)]
        p+= [Synset(s(p.getTarget())) for p in self._synset.getPointers(wn.ALSO_SEE)]
        return p
        
    def similarity(self, synset):
        """ Returns the semantic similarity of the given synsets (0.0-1.0).
            synsets("cat")[0].similarity(synsets("dog")[0]) => 0.86.
            synsets("cat")[0].similarity(synsets("box")[0]) => 0.17.
        """
        if self == synset:
            return 1.0
        try: # Lin semantic distance measure.
            lin = 2.0 * log(lcs(self, synset).ic) / (log(self.ic * synset.ic) or 1)
        except OverflowError:
            lin = 0.0
        except ValueError: # / log(0)
            lin = 0.0
        return abs(lin)
        
    @property
    def ic(self):
        return information_content(self)
        
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

IC = {} # Switch data file according to WordNet version:
IC_CORPUS = os.path.join(MODULE, "resnik-ic" + VERSION[0] + ".txt")
IC_MAX = 0

def information_content(synset):
    """ Returns the IC value for the given Synset (trained on the Brown corpus).
    """
    global IC_MAX
    if not IC:
        IC[NOUN] = {}
        IC[VERB] = {}
        for s in open(IC_CORPUS).readlines()[1:]: # Skip the header.
            s = s.split()
            id, w, pos = (
                int(s[0][:-1]), 
                float(s[1]), 
                s[0][-1] == "n" and NOUN or VERB)
            if len(s) == 3 and s[2] == "ROOT":
                IC[pos][0] = IC[pos].get(0,0) + w
            if w != 0:
                IC[pos][id] = w
            if w > IC_MAX:
                IC_MAX = w
    return IC.get(synset.pos, {}).get(synset.id, 0.0) / IC_MAX

### WORDNET3 TO WORDNET2 ###########################################################################
# Map WordNet3 synset id's to WordNet2 synset id's.

_map32_pos1  = {NN: "n", VB: "v", JJ: "a", RB: "r"}
_map32_pos2  = {"n": NN, "v": VB, "a": JJ, "r": RB}
_map32_cache = None

def map32(id, pos=NOUN):
    """ Returns an (id, pos)-tuple with the WordNet2 synset id for the given WordNet3 synset id.
        Returns None if no id was found.
    """
    global _map32_cache
    if not _map32_cache:
        _map32_cache = open(os.path.join(MODULE, "dict", "index.32")).readlines()
        _map32_cache = (x for x in _map32_cache if x[0] != ";") # comments
        _map32_cache = dict(x.strip().split(" ") for x in _map32_cache)
    k = pos in _map32_pos2 and pos or _map32_pos1.get(pos, "x")
    k+= str(id).lstrip("0")
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
    
    def __init__(self, path="SentiWordNet*.txt", language="en"):
        """ A sentiment lexicon with scores from SentiWordNet.
            The value for each word is a tuple with values for 
            polarity (-1.0-1.0), subjectivity (0.0-1.0) and intensity (0.5-2.0).
        """
        Sentiment.__init__(self, path=path, language=language)
    
    def load(self):
        # Backwards compatibility: look for SentiWordNet*.txt in:
        # given path, pattern/text/en/ or pattern/text/en/wordnet/
        try: f = (
            glob.glob(os.path.join(self.path)) + \
            glob.glob(os.path.join(MODULE, self.path)) + \
            glob.glob(os.path.join(MODULE, "..", self.path)))[0]
        except IndexError:
            raise ImportError("can't find SentiWordnet data file")
        # Map synset id: a-00193480" => (193480, JJ).
        # Map synset id's to WordNet2 if VERSION == 2:
        if int(float(VERSION)) == 3:
            m = lambda id, pos: (int(id.lstrip("0")), _map32_pos2[pos])
        if int(float(VERSION)) == 2:
            m = map32
        for s in open(f):
            if not s.startswith(("#", "\t")):
                pos, id, p, n, senses, gloss = s.split("\t")
                w = senses.split()
                k = m(id, pos)
                v = (float(p) - float(n), 
                     float(p) + float(n)
                     )
                # Apply the score to the first synonym in the synset.
                # Several WordNet3 entries may point to the same WordNet2 entry.
                if k is not None:
                    k = "%s-%s" % (pos, str(k[0]).zfill(8)) # "a-00193480"
                    if k not in self._synsets or w[0].endswith("#1"):
                        self._synsets[k] = v
                for w in w:
                    if w.endswith("#1"):
                        dict.__setitem__(self, w[:-2].replace("_", " "), v)

    # Words are stored without diacritics, 
    # use wordnet.normalize(word).
    def __getitem__(self, k):
        return Sentiment.__getitem__(self, normalize(k))
    def get(self, k, *args, **kwargs):
        return Sentiment.get(self, normalize(k), *args, **kwargs)
        
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
        return p < 0 and (0.0, -p, 1.0-s) or (p, 0.0, 1.0-s)

    def __contains__(self, w):
        return w in sentiwordnet

sentiment = sentiment()

#print sentiwordnet["industry"] # (0.0, 0.0)
#print sentiwordnet["horrible"] # (-0.625, 0.625)
#print sentiwordnet.synset(synsets("horrible", pos="JJ")[0].id, pos="JJ")
#print synsets("horrible", pos="JJ")[0].weight
