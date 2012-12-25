#### PATTERN | NL | SENTIMENT ######################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

import os

try: 
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

# The lexicon is inherited from pattern.en.parser.sentiment.Lexicon.
import sys; sys.path.insert(0, os.path.join(MODULE, "..", ".."))
from en.parser.sentiment import Lexicon as _Lexicon, sentiment as _sentiment
from en.parser.sentiment import NOUN, VERB, ADJECTIVE, ADVERB

from nl.inflect import attributive

#### SUBJECTIVITY LEXICON ##########################################################################

class Lexicon(_Lexicon):
    
    def __init__(self, path=os.path.join(MODULE, "sentiment.xml"), **kwargs):
        # Use Dutch XML corpus.
        # Use synset id's from Cornetto instead of WordNet. 
        kwargs.setdefault("synsets", "cornetto_synset_id")
        _Lexicon.__init__(self, path, **kwargs)

    @property
    def negation(self):
        return ("geen", "niet", "nooit")

    def _parse(self):
        _Lexicon._parse(self)
        # Map "verschrikkelijk" to adverbial "verschrikkelijke".
        # Combined with negation, this increases accuracy to 79%.
        # A 0.75, P 0.72, R 0.82, F1 0.77 becomes:
        # A 0.79, P 0.77, R 0.83, F1 0.80.
        # Accuracy also increases by using exclamation marks as intensifier:
        # A 0.80, P 0.77, R 0.84, F1 0.81.
        for w, pos in self.items():
            if "JJ" in pos:
                a = attributive(w)
                if a not in self: 
                    self[a] = { "JJ": pos["JJ"], None: pos["JJ"] }
    
    def synset(self, id, pos=None):
        if not self._parsed:
            self._parse()
        return self._synsets.get(id, None)

lexicon = _lexicon = Lexicon(path=os.path.join(MODULE, "sentiment.xml"))

#### SENTIMENT #####################################################################################

def sentiment(s, **kwargs):
    kwargs.setdefault("lexicon", _lexicon)
    kwargs.setdefault("negation", True)
    return _sentiment(s, **kwargs)
    
def polarity(s, **kwargs):
    return sentiment(s, **kwargs)[0]

def subjectivity(s, **kwargs):
    return sentiment(s, **kwargs)[1]
    
def positive(s, threshold=0.1, **kwargs):
    return polarity(s, **kwargs) >= threshold

#print sentiment("goed")               # (+0.6, 0.9)
#print sentiment("niet goed")          # (-0.6, 0.9)
#print sentiment("volkomen goed")      # (+1.0, 1.0)
#print sentiment("volkomen niet goed") # (-1.0, 1.0)
#print sentiment("niet volkomen goed") # (-0.3, 0.5)