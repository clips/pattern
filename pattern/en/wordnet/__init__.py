#### PATTERN | WORDNET ###############################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

######################################################################################################
# WordNet is a lexical database for the English language. 
# It groups English words into sets of synonyms called synsets, provides short, general definitions, 
# and records the various semantic relations between these synonym sets.

CORPUS = "" # Path to WordNet /dict folder.
import os; os.environ["WNHOME"] = os.path.join(os.path.dirname(__file__), CORPUS)
import glob

from pywordnet import wordnet as wn
from pywordnet import wntools
# The bundled version of pywordnet contains custom fixes:
# - line 674: added HYPONYM and HYPERNYM to the pointer table.
# - line 915: implements "x in Dictionary" instead of Dictionary.has_key(x)

try: 
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

#--- SENSES ------------------------------------------------------------------------------------------

NOUNS, VERBS, ADJECTIVES, ADVERBS = wn.N, wn.V, wn.ADJ, wn.ADV

NOUN = NN = "NN"
VERB = VB = "VB"
ADJECTIVE = ADJ = JJ = "JJ"
ADVERB = ADV = RB = "RB"

ignore_accents = [
    ("á|ä|â|å|à", "a"), 
    ("é|ë|ê|è", "e"), 
    ("í|ï|î|ì", "i"), 
    ("ó|ö|ô|ø|ò", "o"), 
    ("ú|ü|û|ù", "u"), 
    ("ÿ|ý", "y"), 
    ("š", "s"), 
    ("ç", "ç"), 
    ("ñ", "n")
]

def normalize(word):
    # Normalizes the word for synsets() or Sentiwordnet[].
    # WordNet does not take unicode.
    if not isinstance(word, basestring):
        word = str(word)
    if not isinstance(word, str):
        try: word = word.encode("utf-8")
        except:
            pass
    # Normalize common accented letters.
    for a, b in ignore_accents: 
        for a in a.split("|"): 
            word = word.replace(a, b)
    return word

def synsets(word, pos=NOUN):
    """ Returns a list of Synset objects, one for each word sense.
        Each word can be understood in different "senses", each of which is a set of synonyms (=Synset).
    """
    word = normalize(word)
    if pos == NOUN:
        w = wn.N[word]
    elif pos == VERB:
        w = wn.V[word]
    elif pos == ADJECTIVE:
        w = wn.ADJ[word]
    elif pos == ADVERB:
        w = wn.ADV[word]
    try:
        return [Synset(s.synset) for i, s in enumerate(w)]
    except:
        return []

#--- SYNSET ------------------------------------------------------------------------------------------

class Synset:
    
    def __init__(self, synset=None, pos=NOUN):
        """ A set of synonyms that share a common meaning.
        """
        if isinstance(synset, basestring):
            synset = synsets(synset)[0]
        if isinstance(synset, int):
            synset = wn.getSynset({NN:"n",VB:"v",JJ:"adj",RB:"adv"}[pos], synset)
        self._synset = synset

    @property
    def id(self):
        return self._synset.offset

    def __len__(self):
        return len(self._synset.getSenses())
    def __getitem__(self, i):
        return self._synset.getSenses()[i].form
    def __iter__(self):
        for s in self._synset.getSenses():
            yield s.form
            
    def __eq__(self, synset):
        return isinstance(synset, Synset) and self.id == synset.id
    def __ne__(self, synset):
        return not self.__eq__(synset)
        
    def __repr__(self):
        return "Synset(%s)" % repr(self[0])

    @property
    def pos(self):
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
    def senses(self):
        """ A list of word forms (i.e. synonyms), for example:
            synsets("TV")[0].senses => ["television", "telecasting", "TV", "video"]
        """
        return [s.form for s in self._synset.getSenses()]
        
    @property
    def gloss(self):
        """ A description string, for example:
            synsets("glass")[0].gloss => "a brittle transparent solid with irregular atomic structure".
        """
        return str(self._synset.gloss)
        
    @property
    def lexname(self):
        return self._synset.lexname and str(self._synset.lexname) or None

    def antonym(self):
        """ The semantically opposite synset, for example:
            synsets("death")[0].antonym => Synset("birth").
        """
        p = self._synset.getPointers(wn.ANTONYM)
        return len(p) > 0 and Synset(p[0].getTarget()) or None        

    def meronyms(self):
        """ A list of synsets that are semantic members/parts of this synset, for example:
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
        """ A list of synsets of which this synset is a member/part, for example:
            synsets("tree")[0].holonyms() => Synset("forest").
        """
        p = self._synset.getPointers(wn.MEMBER_MERONYM)
        p+= self._synset.getPointers(wn.PART_MERONYM)
        return [Synset(p.getTarget()) for p in p]

    def hyponyms(self, recursive=False, depth=None):
        """ A list of semantically more specific synsets, for example:
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
        """ The synset that is the semantic parent, for example:
            synsets("train")[0].hypernym => Synset("public transport").
        """
        p = self._synset.getPointers(wn.HYPERNYM)
        return len(p) > 0 and Synset(p[0].getTarget()) or None
        
    @property
    def ic(self):
        return information_content(self)
        
    def similarity(self, synset):
        """ Returns the semantic similarity of the given synsets.
            Lower numbers indicate higher similarity, for example:
            synsets("river")[0].similarity(synsets("lake")[0]) => 3.77
            synsets("river")[0].similarity(synsets("lion")[0]) => 786.05
        """
        # Lin semantic distance measure.
        lin = 2.0 * lcs(self, synset).ic / ((self.ic + synset.ic) or 1e-10)
        return lin
        
    def similar(self):
        """ For an adjective or verb, a list of similar synsets, for example:
            synsets("almigthy",JJ)[0].similar() => Synset("powerful").
        """
        p = [Synset(p.getTarget()) for p in self._synset.getPointers(wn.SIMILAR)]
        p+= [Synset(p.getTarget().synset) for p in self._synset.getPointers(wn.ALSO_SEE)]
        return p
        
    @property
    def weight(self):
        return sentiment.weight(self)

def similarity(synset1, synset2):
    return synset1.similarity(synset2)

def ancestor(synset1, synset2):
    """ Returns the common ancestor of both synsets.
        For example synsets("cat")[0].ancestor(synsets("dog")[0]) => Synset("carnivore")
    """
    # Note: a synset can have more than one hypernym, so we should check those as well.
    h1, h2 = synset1.hypernyms(recursive=True), synset2.hypernyms(recursive=True)
    for s in h1:
        if s in h2:
            return s
            
least_common_subsumer = lcs = ancestor

#--- LEMMA -------------------------------------------------------------------------------------------
# Guesses word lemma based on a few lookup files bundled with WordNet.

LEMMATA = {}
def lemma(word):
    if not LEMMATA:
        for exc in glob.glob(os.path.join(CORPUS, "dict", "*.exc")):
            for rule in open(exc).readlines():
                rule = rule.split(" ")
                LEMMATA[rule[0]] = rule[1].strip()
    return LEMMATA.get(word, word)  

#--- INFORMATION CONTENT -----------------------------------------------------------------------------

IC = {}
IC_CORPUS = os.path.join(os.path.dirname(__file__), "IC-Brown-Resnik.txt")
IC_MAX = 0
def information_content(synset):
    """ Returns the IC value for the given Synset, based on the Brown corpus.
    """
    # Information Content is used to calculate semantic similarity in Synset.similarity().
    # IC values for each synset are derived from the word's occurence in a given corpus (e.g. Brown). 
    # The idea is that less frequent words convey more information.
    # Semantic similarity depends on the amount of information two concepts (synsets) have in common,
    # given by the Most Speciﬁc Common Abstraction (MSCA), i.e. the shared ancestor in the taxonomy.
    # http://www.d.umn.edu/~tpederse/Pubs/AAAI04PedersenT.pdf
    # http://afflatus.ucd.ie/papers/ecai2004b.pdf
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
    return IC.get(synset.pos, {}).get(synset.id, 0.0)

#--- SENTIWORDNET ------------------------------------------------------------------------------------
# http://nmis.isti.cnr.it/sebastiani/Publications/LREC06.pdf

_map32_pos1 = {NN:"n", VB:"v", JJ:"a", RB:"r"}
_map32_pos2 = {"n":NN, "v":VB, "a":JJ, "r":RB}
_map32_cache = None
def map32(id, pos=NOUN):
    """ Returns an (id, pos)-tuple with the WordNet2 synset id for the given WordNet3 synset id.
        There is an error margin of 2%, returns None if no id was found.
    """
    global _map32_cache
    if not _map32_cache:
        _map32_cache = open(os.path.join(MODULE, "dict", "index.32")).readlines()
        _map32_cache = dict(x.strip().split(" ") for x in _map32_cache)
    k = pos in _map32_pos2 and pos or _map32_pos1.get(pos, "x")
    k+= str(id).lstrip("0")
    k = _map32_cache.get(k, None)
    if k is not None:
        return int(k[1:]), _map32_pos2[k[0]]
    return None

class Sentiwordnet(dict):
    
    def __init__(self):
        """ SentiWordNet is a lexical resource for opinion mining. 
            SentiWordNet assigns to each synset of WordNet three sentiment scores: 
            positivity, negativity, objectivity.
            It can be acquired from: http://sentiwordnet.isti.cnr.it/ (research license).
        """
        self._index = {} # Synset.id => (positive, negative)
    
    def __getitem__(self, word):
        return dict.get(self, normalize(word), (0.0, 0.0, 1.0))
    
    def weight(self, synset):
        """ Returns a (positive, negative, objective)-tuple of values between 0.0-1.0.
        """
        return self._index.get((synset.id, synset.pos), (0.0, 0.0, 1.0))

    def load(self, path=os.path.join(MODULE, "SentiWordNet*.txt")):
        """ Loads SentiWordNet-data from the given file.
        """
        # Sentiwordnet.weight() takes a Synset.
        # Sentiwordnet[word] takes a plain string and yields values for the 1st sense.
        e = 0
        pp = []
        W = {"n":wn.N,"v":wn.V,"a":wn.ADJ,"r":wn.ADV}
        for s in open(glob.glob(path)[0]).readlines():
            if not s.startswith(("#", "\t")):
                s = s.split("\t") # pos (a/n/v/r), offset, positive, negative, senses, gloss
                if s[2] != "0" or s[3] != "0":
                    w1 = float(s[2]) # positive
                    w2 = float(s[3]) # negative   
                    k = map32(s[1], pos=s[0]) # wn2 id.
                    v = (w1, w2, 1-(w1+w2))
                    if k is not None:
                        self._index[k] = v
                    for w in (w for w in s[4].split(" ") if w.endswith("#1")):
                        self[w[:-2].replace("_", " ")] = v

sentiment = Sentiwordnet()
