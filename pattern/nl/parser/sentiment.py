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
    kwargs.setdefault("negation", True)
    # Following is a neat trick that catches more adjectives.
    # Combined with negation: A 0.78 P 0.76  R 0.83 F1 0.79.
    #from pattern.nl.inflect import predicative
    #s = [w.strip("*#[]():;,.!?-\t\n\r\x0b\x0c") for w in s.lower().split()]
    #for i, w in enumerate(s):
    #    if w not in lexicon and predicative(w) in lexicon:
    #        s[i] = predicative(w)
    return _sentiment(s, **kwargs)
    
def polarity(s, **kwargs):
    return sentiment(s, **kwargs)[0]

def subjectivity(s, **kwargs):
    return sentiment(s, **kwargs)[1]
    
def positive(s, threshold=0.1, **kwargs):
    return polarity(s, **kwargs) >= threshold
    

# Evaluation.

#from pattern.db import Datasheet
#from pattern.metrics import test
#from random import shuffle
#from time import time
#
#def shuffled(list):
#    shuffle(list); return list
#
#reviews = {}
#for row in Datasheet.load("reviews.txt")[14000:]:
#    # (id, book_title, score, review_title, review)
#    score, title, review = int(row[2]), row[3], row[4]
#    reviews.setdefault(score, []).append(title+" "+review)
## Divide evenly between positive (4,5) and negative (1,2).
#m = min(len(a) for a in reviews.values())
#
#F = []
#for i in range(10):
#    t = time()
#    subset = []
#    for score, r in reviews.items():
#        subset.extend((score, review) for review in shuffled(r)[:m] if score != 3)
#    documents = [(review, score > 3) for score, review in subset]
#    F.append([f for f in test(lambda document: positive(document), documents)]) # A P R F1
#    print i, time()-t
#    
#F = [float(sum(row[i] for row in F)) / len(F) for i in range(len(F[0]))]
#print ["%.3f" % v for v in F]