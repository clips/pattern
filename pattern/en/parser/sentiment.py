#### PATTERN | EN | SENTIMENT ########################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

from glob      import glob
from xml.dom   import minidom
from itertools import chain

import os
try: 
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

### LIST FUNCTIONS ###################################################################################

def column(list, i):
    return [row[i] for row in list]

def avg(list):
    return sum(list) / (len(list) or 1)

#### SUBJECTIVITY LEXICON ############################################################################

NOUN, VERB, ADJECTIVE, ADVERB = \
    "NN", "VB", "JJ", "RB"

class Lexicon:
    
    def __init__(self, path=os.path.join(MODULE, "sentiment.xml"), **kwargs):
        """ A lexicon with sentiment scores for words (adjectives).
            A dictionary of words, where each word is a dictionary of part-of-speech tags.
            Each POS-tag is a tuple with polarity (-1.0-1.0), subjectivity (0.0-1.0), intensity (0.5-2.0).
        """
        self.path = path
        self._language = None
        self._words = {}
        self._synsets = {}
        self._parsed = False
        self._kwargs = kwargs
    
    @property
    def language(self):
        if not self._parsed:
            self._parse()
        return self._language
    
    def _parse_xml(self, reliability=None):
        """ Returns a (language, words)-tuple, where each word is a list of
            (form, WordNet3 id, part-of-speech, (polarity, subjectivity, intensity))-tuples.
        """
        # <word form="great" wordnet_id="a-01123879" pos="JJ" polarity="1.0" subjectivity="1.0" intensity="1.0" />
        xml = minidom.parse(self.path)
        xml = xml.documentElement
        language = xml.getAttribute("language") or None
        words = []
        for w in xml.getElementsByTagName("word"):
            if reliability is None \
            or reliability <= (float(w.getAttribute("reliability") or 0.0)):
                words.append((w.getAttribute("form"), # Can also be "cornetto_id":
                              w.getAttribute(self._kwargs.get("synsets", "wordnet_id")),
                              w.getAttribute("pos") or None,
                       (float(w.getAttribute("polarity") or 0.0),
                        float(w.getAttribute("subjectivity") or 0.0),
                        float(w.getAttribute("intensity") or 1.0))))
        return (language, words)
        
    def _parse(self, reliability=None):
        """ Parses the source XML and averages the scores per word
            (word senses are grouped per part-of-speech tag).
        """
        language, words = self._parse_xml(reliability)
        self._words.clear()
        self._language = language
        self._parsed = True        
        for w, id, pos, psi in words:
            # Group word scores by part-of-speech tag.
            self._words.setdefault(w, {}).setdefault(pos, []).append(psi)
            self._synsets.setdefault(id, []).append(psi)
        for id, psi in self._synsets.items():
            # Average score of all synonyms in the synset.
            self._synsets[id] = (avg(column(psi,0)), avg(column(psi,1)), avg(column(psi,2)))
        for w, v in self._words.items():
            # Average score of all senses per part-of-speech tag.
            for pos, psi in v.items():
                v[pos] = (avg(column(psi,0)), avg(column(psi,1)), avg(column(psi,2)))
        for w, v in self._words.items():
            # Create a "None" part-of-speech tag for plain string.
            # None-POS has average score of all part-of-speech tags.
            psi = v.values()
            v[None] = (avg(column(psi,0)), avg(column(psi,1)), avg(column(psi,2)))

    def load(self, path=None):
        # Backwards compatibility with pattern.en.wordnet.Sentiment.
        if path is not None:
            self._path = path
        self._parse()

    def synset(self, id, pos=ADJECTIVE):
        """ Returns the scores for the given WordNet ID, 
            for example: Lexicon.synset(193480, pos="JJ") => "horrible" => (-0.6, 1.0, 1.0).
        """
        if not self._parsed:
            self._parse()
        id = {NOUN:"n-", VERB:"v-", ADJECTIVE:"a-", ADVERB:"r-", None:""}[pos] + str(id).zfill(8)
        return self._synsets.get(id, None)

    # Implement dict methods to first call Lexicon._parse().
    # dict.copy() and iteritems|keys|values() is not implemented.
    def __setitem__(self, k, v):
        if not self._parsed:
            self._parse()
        self._words[k] = v
        
    def __getitem__(self, k):
        if not self._parsed:
            self._parse()
        self.__getitem__ = self._words.__getitem__   # 5% speedup
        return self._words[k]
        
    def __iter__(self):
        if not self._parsed:
            self._parse()
        return iter(self._words)
        
    def __len__(self):
        if not self._parsed:
            self._parse()
        return len(self._words)
        
    def __contains__(self, k):
        if not self._parsed:
            self._parse()
        self.__contains__ = self._words.__contains__ # 20% speedup
        return k in self._words
        
    def keys(self):
        if not self._parsed:
            self._parse()
        return self._words.keys()
        
    def values(self):
        if not self._parsed:
            self._parse()
        return self._words.values()
        
    def items(self):
        if not self._parsed:
            self._parse()
        return self._words.items()
        
    def has_key(self, k):
        if not self._parsed:
            self._parse()
        return k in self._words
        
    def get(self, k, default=None):
        if not self._parsed:
            self._parse()
        return self._words.get(k, default)
        
    def pop(self, k, default=None):
        if not self._parsed:
            self._parse()
        return self._words.pop(k, default)
        
    def setdefault(self, k, v=None):
        if not self._parsed:
            self._parse()
        return self._words.setdefault(k, v)
        
    def update(self, *args):
        if not self._parsed:
            self._parse()
        self._words.update(*args)

lexicon = _lexicon = Lexicon()

#### SENTIMENT #######################################################################################

def sentiment(s, **kwargs):
    """ Returns a (polarity, subjectivity)-tuple for the given sentence, 
        with polarity between -1.0 and 1.0 and subjectivity between 0.0 and 1.0.
        The sentence can be a string, Synset, Text, Sentence, Chunk or Word.
    """
    lexicon, pos = (
        kwargs.get("lexicon", _lexicon), 
        kwargs.get("pos", None))
    v = []
    
    def _score(words, language="en"):
        prev = None
        for w, pos in words:
            # Only process known words, preferably by correct part-of-speech.
            # Including unknown words (e.g. polarity=0 and subjectivity=0) lowers the average.
            if w in lexicon and pos in lexicon[w]:
                if prev is not None and \
                  (language == "en" and "RB" in lexicon[prev[0]] and "JJ" in lexicon[w]) or \
                  (language == "nl" and "JJ" in lexicon[prev[0]] and "JJ" in lexicon[w]):
                    # For English, adverb + adjective uses the intensity score.
                    # For Dutch, adjective + adjective uses the intensity score.
                    # For example: "echt" + "teleurgesteld" = 1.6 * -0.4, not 0.2 + -0.4
                    # ("hopeloos voorspelbaar", "ontzettend spannend", "verschrikkelijk goed", ...)
                    i = lexicon[prev[0]][prev[1]][2]
                    v[-1] = lexicon[w][pos]
                    v[-1] = tuple(v*i for v in v[-1])
                else:
                    v.append(lexicon[w][pos])
                prev = (w, pos)
            else:
                prev = None

    # From pattern.en.wordnet.Synset: 
    # sentiment(synsets("horrible", "JJ")[0]) => (-0.6, 1.0)
    if hasattr(s, "gloss") and lexicon.language == "en":
        v.append(lexicon.synset(s.id, pos=s.pos) or (0,0))
    # From WordNet id (EN): 
    # sentiment("a-00193480") => horrible => (-0.6, 1.0)
    elif isinstance(s, basestring) and s.startswith(("n-","v-","a-","r-")) and s[2:].isdigit():
        v.append(lexicon.synset(s, pos=None) or (0,0))
    # From Cornetto id (NL):
    # sentiment("c_267") => verschrikkelijk => (-0.9, 1.0)
    elif isinstance(s, basestring) and s.startswith(("n_","d_","c_")) and s.lstrip("acdnrv-_").isdigit():
        v.append(lexicon.synset(s, pos=None) or (0,0))
    # From plain string: 
    # sentiment("a horrible movie") => (-0.6, 1.0)
    elif isinstance(s, basestring):
        _score([(w.strip("*#[]():;,.!?-\t\n\r\x0b\x0c"), pos) for w in s.lower().split()])
    # From pattern.en.Text, using word lemmata and parts-of-speech when available.
    elif hasattr(s, "sentences"):
        _score([(w.lemma or w.string, w.pos) for w in chain(*(s.words for s in s))], lexicon.language)
    # From pattern.en.Sentence or pattern.en.Chunk.
    elif hasattr(s, "words"):
        _score([(w.lemma or w.string, w.pos) for w in s.words], lexicon.language)
    # From pattern.en.Word.
    elif hasattr(s, "lemma"):
        _score([(s.lemma or s.string, s.pos)], lexicon.language)
    # Return average (polarity, subjectivity).
    n = len(v) or 1
    return (sum(column(v,0))/n, sum(column(v,1))/n)
    
def polarity(s, **kwargs):
    """ Returns the sentence polarity (positive/negative sentiment) between -1.0 and 1.0.
    """
    return sentiment(s, **kwargs)[0]

def subjectivity(s, **kwargs):
    """ Returns the sentence subjectivity (objective/subjective) between 0.0 and 1.0.
    """
    return sentiment(s, **kwargs)[1]
    
def positive(s, threshold=0.1, **kwargs):
    """ Returns True if the given sentence is likely to carry a positive sentiment.
    """
    return polarity(s, **kwargs) >= threshold

#import sys; sys.path.append("../..")
#from en.parser import parse
#from en.wordnet import Synset, synsets
#from en.parser.tree import Text, Sentence
#print sentiment("a-00193480")
#print sentiment(synsets("horrible", pos="JJ")[0])
#print sentiment("horrible")
#print sentiment("A really bad, horrible book.")
#print sentiment(Text(parse("A bad book. Really horrible.")))

#### SENTIWORDNET ####################################################################################
# http://nmis.isti.cnr.it/sebastiani/Publications/LREC06.pdf
# http://nmis.isti.cnr.it/sebastiani/Publications/LREC10.pdf

class SentiWordNet(Lexicon):
    
    def __init__(self, **kwargs):
        """ A lexicon with sentiment scores from SentiWordNet (http://sentiwordnet.isti.cnr.it).
            A dictionary of words, where each word is linked to a (polarity, subjectivity)-tuple.
        """
        # Note: words are stored without diacritics, use wordnet.normalize(word) for lookup.
        kwargs.setdefault("path", "SentiWordNet*.txt")
        Lexicon.__init__(self, **kwargs)
        # Each WordNet3 id in SentiWordNet will be passed through map().
        # For example, this can be used to map the id's to WordNet2 id's.
        self._map = kwargs.get("map", lambda id, pos: (id, pos))
    
    def _parse_path(self):
        """ For backwards compatibility, look for SentiWordNet*.txt in:
            pattern/en/parser/, patter/en/wordnet/, or the given path.
        """
        try: f = (
            glob(os.path.join(self.path)) + \
            glob(os.path.join(MODULE, self.path)) + \
            glob(os.path.join(MODULE, "..", "wordnet", self.path)))[0]
        except IndexError:
            raise ImportError, "can't find SentiWordnet data file"
        return f
    
    def _parse(self):
        self._words.clear()
        self._parsed = True
        for s in open(self._parse_path()).readlines():
            if not s.startswith(("#", "\t")):
                s = s.split("\t") # pos (a/n/v/r), offset, positive, negative, senses, gloss
                k = self._map(s[1], pos=s[0])
                v = (
                    float(s[2]) - float(s[3]), 
                    float(s[2]) + float(s[3]))
                if k is not None:
                    # Apply the score to the first synonym in the synset.
                    self._synsets["%s-%s" % (s[0], str(k[0]).zfill(8))] = v # "a-00193480"
                for w in (w for w in s[4].split(" ") if w.endswith("#1")):
                    self._words[w[:-2].replace("_", " ")] = v
