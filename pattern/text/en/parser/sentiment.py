#### PATTERN | EN | SENTIMENT ######################################################################
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

### LIST FUNCTIONS #################################################################################

def column(list, i):
    return [row[i] for row in list]

def avg(list):
    return sum(list) / float(len(list) or 1)

### STRING FUNCTIONS ###############################################################################

def encode_emoticons(string):
    """ Returns the string with emoticons encoded as entities, e.g., :-) => &happy;
    """
    string = " " + string + " "
    for (smileys, entity) in (
      ((":)", ":-)"), "&happy;"),
      ((":(", ":-("), "&sad;")):
        for smiley in smileys:
            string = string.replace(" %s " % smiley, " %s " % entity)
    return string[1:-1]

#### SUBJECTIVITY LEXICON ##########################################################################

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
        
    @property
    def negation(self):
        return ("no", "not", "never")
    
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
    # dict.copy() is not implemented.
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

    def iterkeys(self):
        if not self._parsed:
            self._parse()
        return self._words.iterkeys()
        
    def itervalues(self):
        if not self._parsed:
            self._parse()
        return self._words.itervalues()
        
    def iteritems(self):
        if not self._parsed:
            self._parse()
        return self._words.iteritems()

lexicon = _lexicon = Lexicon()

#### SENTIMENT #####################################################################################

class Assessment:
    
    def __init__(self, words=[], p=0.0, s=0.0, i=1.0, n=+1):
        """ A chunk of words annotated with (polarity, subjectivity, intensity, negation)-scores.
        """
        self.chunk = words
        self.p = p # polarity
        self.s = s # subjectivity
        self.i = i # intensity
        self.n = n # negation
    
    @property
    def polarity(self):
        return self.p
    @property
    def subjectivity(self):
        return self.s
    @property
    def intensity(self):
        return self.i
    @property
    def negation(self):
        return self.n
    
    def __repr__(self):
        return "Assessment(chunk=%s, p=%s, s=%s, i=%s, n=%s)" % (
            repr(self.chunk), self.p, self.s, self.i, self.n)

class Score(tuple):
    
    def __new__(self, assessments=[]):
        """ Average (polarity, subjectivity) for all assessments.
        """
        self.assessments = a = [(" ".join(a.chunk), a.p*a.n, a.s) for a in assessments] # (chunk, polarity, subjectivity)
        return tuple.__new__(self, [
            max(-1.0, min(+1.0, sum(column(a,1)) / (len(a) or 1.0))), 
            max(-1.0, min(+1.0, sum(column(a,2)) / (len(a) or 1.0)))])

def sentiment(s, **kwargs):
    """ Returns a (polarity, subjectivity)-tuple for the given sentence, 
        with polarity between -1.0 and 1.0 and subjectivity between 0.0 and 1.0.
        The sentence can be a string, Synset, Text, Sentence, Chunk or Word.
    """
    lexicon, negation, pos = (
        kwargs.get("lexicon", _lexicon), 
        kwargs.get("negation", False),
        kwargs.get("pos", None))
        
    a = [] # Assesments as chunks of words (negation + modifier + adjective).

    def _score(words, language="en", negation=False):
        negated  = None  # Preceding negation (e.g., "not beautiful").
        modifier = None  # Preceding adverb/adjective.
        for i, (w, pos) in enumerate(words):
            # Only assess known words, preferably by correct part-of-speech.
            # Including unknown words (e.g. polarity=0 and subjectivity=0) lowers the average.
            if w in lexicon and pos in lexicon[w]:
                if modifier is not None and ( \
                  (language == "en" and "RB" in lexicon[modifier[0]] and "JJ" in lexicon[w]) or \
                  (language == "fr" and "RB" in lexicon[modifier[0]] and "JJ" in lexicon[w]) or \
                  (language == "nl" and "JJ" in lexicon[modifier[0]] and "JJ" in lexicon[w])):
                    # Known word preceded by a modifier.
                    # For English, adverb + adjective uses the intensity score.
                    # For Dutch, adjective + adjective uses the intensity score.
                    # For example: "echt" + "teleurgesteld" = 1.6 * -0.4, not 0.2 + -0.4
                    # ("hopeloos voorspelbaar", "ontzettend spannend", "verschrikkelijk goed", ...)
                    (p, s, i), i0 = lexicon[w][pos], a[-1].i
                    a[-1].chunk.append(w)
                    a[-1].p = min(p * i0, 1.0)
                    a[-1].s = min(s * i0, 1.0)
                    a[-1].i = min(i * i0, 1.0)
                else:
                    # Known word not preceded by a modifier.
                    a.append(Assessment([w], *lexicon[w][pos]))
                if negated is not None:
                    # Known word (or modifier + word) preceded by a negation:
                    # "not really good" (reduced intensity for "really").
                    a[-1].chunk.insert(0, negated)
                    #a[-1].i = a[-1]!= 0 and (1.0 / a[-1].i) or 0
                    a[-1].n = -1
                modifier = (w, pos) # Word may be a modifier, check next word.
                negated = None
            else:
                if negation and w in lexicon.negation:
                    negated = w
                else:
                    negated = None
                if negated is not None and modifier is not None and (
                  (language == "en" and pos == "RB" or modifier[0].endswith("ly")) or \
                  (language == "fr" and pos == "RB" or modifier[0].endswith("ment")) or \
                  (language == "nl")):
                    # Unknown word is a negation preceded by a modifier:
                    # "really not good" (full intensity for "really").
                    a[-1].chunk.append(negated)
                    a[-1].n = -1
                    negated = None
                else:
                    # Unknown word, ignore.
                    modifier = None
                if w == "!" and len(a) > 0:
                    # Exclamation marks as intensifiers can be beneficial.
                    for w in a[-3:]: w.p = min(w.p * 1.25, 1.0)
                if w in ("&happy;", "&happy"):
                    # Emoticon :-)
                    a.append(Assessment([w], +1.0))
                if w in ("&sad;", "&sad"):
                    # Emoticon :-(
                    a.append(Assessment([w], -1.0))
    
    # From pattern.en.wordnet.Synset: 
    # sentiment(synsets("horrible", "JJ")[0]) => (-0.6, 1.0)
    if hasattr(s, "gloss") and lexicon.language == "en":
        a.append(Assessment([""], *(lexicon.synset(s.id, pos=s.pos) or (0,0))))
    # From WordNet id (EN): 
    # sentiment("a-00193480") => horrible => (-0.6, 1.0)
    elif isinstance(s, basestring) and s.startswith(("n-","v-","a-","r-")) and s[2:].isdigit():
        a.append(Assessment([s], *(lexicon.synset(s, pos=None) or (0,0))))
    # From Cornetto id (NL):
    # sentiment("c_267") => verschrikkelijk => (-0.9, 1.0)
    elif isinstance(s, basestring) and s.startswith(("n_","d_","c_")) and s.lstrip("acdnrv-_").isdigit():
        a.append(Assessment([s], *(lexicon.synset(s, pos=None) or (0,0))))
    # From plain string: 
    # sentiment("a horrible movie") => (-0.6, 1.0)
    elif isinstance(s, basestring):
        s = s.lower()
        s = s.replace("!", " !")
        s = encode_emoticons(s)
        _score([(w.strip("*#[]():;,.?-\t\n\r\x0b\x0c"), pos) for w in s.split()], lexicon.language, negation)
    # From pattern.en.Text, using word lemmata and parts-of-speech when available.
    elif hasattr(s, "sentences"):
        _score([(w.lemma or w.string.lower(), w.pos[:2]) for w in chain(*(s.words for s in s))], lexicon.language, negation)
    # From pattern.en.Sentence or pattern.en.Chunk.
    elif hasattr(s, "words"):
        _score([(w.lemma or w.string.lower(), w.pos[:2]) for w in s.words], lexicon.language, negation)
    # From pattern.en.Word.
    elif hasattr(s, "lemma"):
        _score([(s.lemma or s.string.lower(), s.pos[:2])], lexicon.language, negation)
    # From a flat list of words:
    elif isinstance(s, list):
        _score([(w, None) for w in s], lexicon.language, negation)
        
    # Return average (polarity, subjectivity).
    return Score(a)

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

#### SENTIWORDNET ##################################################################################
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
                    # Several WordNet 3.0 entries may point to the same WordNet 2.1 entry.
                    k = "%s-%s" % (s[0], str(k[0]).zfill(8)) # "a-00193480"
                    if not k in self._synsets or s[4].split(" ")[0].endswith("#1"):
                        self._synsets[k] = v
                for w in (w for w in s[4].split(" ") if w.endswith("#1")):
                    self._words[w[:-2].replace("_", " ")] = v
