#### PATTERN | NL | SENTIMENT ########################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

######################################################################################################

import os

try: 
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

# The lexicon is inherited from pattern.en.parser.sentiment.Lexicon.
import sys; sys.path.insert(0, os.path.join(MODULE, "..", ".."))
from en.parser.sentiment import Lexicon as _Lexicon, sentiment as _sentiment
from en.parser.sentiment import NOUN, VERB, ADJECTIVE, ADVERB

#### SUBJECTIVITY LEXICON ############################################################################

class Lexicon(_Lexicon):
    
    def __init__(self, path=os.path.join(MODULE, "sentiment.xml"), **kwargs):
        # Use Dutch XML corpus.
        # Use synset id's from Cornetto instead of WordNet. 
        kwargs.setdefault("synsets", "cornetto_synset_id")
        _Lexicon.__init__(self, path, **kwargs)
    
    def synset(self, id, pos=None):
        if not self._parsed:
            self._parse()
        return self._synsets.get(id, None)

lexicon = _lexicon = Lexicon(path=os.path.join(MODULE, "sentiment.xml"))

#### SENTIMENT #######################################################################################

def sentiment(s, **kwargs):
    kwargs.setdefault("lexicon", _lexicon)
    return _sentiment(s, **kwargs)
    
def polarity(s, **kwargs):
    return sentiment(s, **kwargs)[0]

def subjectivity(s, **kwargs):
    return sentiment(s, **kwargs)[1]
    
def positive(s, threshold=0.1, **kwargs):
    return polarity(s, **kwargs) >= threshold
