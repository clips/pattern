#### PATTERN | FR | SENTIMENT ######################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
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

#### SUBJECTIVITY LEXICON ##########################################################################

class Lexicon(_Lexicon):
    
    def __init__(self, path=os.path.join(MODULE, "sentiment.xml"), **kwargs):
        # Use French XML corpus.
        _Lexicon.__init__(self, path, **kwargs)
    
    @property
    def negation(self):
        return ("ne", "ni", "non", "pas", "rien", "sans", "aucun", "jamais")
    
    def synset(self, id, pos=None):
        return None

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

#print sentiment("bon")           # (+0.7, 0.7)
#print sentiment("pas bon")       # (-0.7, 0.7)
#print sentiment(u"très bon")     # (+1.0, 1.0)
#print sentiment(u"pas très bon") # (-1.0, 1.0)