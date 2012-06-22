#### PATTERN | EN | INFLECT ########################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# Based on: Peter Norvig, "How to Write a Spelling Corrector", http://norvig.com/spell-correct.html

import os
import re

try:
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""
    
#### SPELLING ######################################################################################

class Spelling(dict):
    
    ALPHA = "abcdefghijklmnopqrstuvwxyz"
    
    def __init__(self, model=os.path.join(MODULE, "spelling.txt")):
        self._model = model
        
    def load(self):
        # The data is lazily loaded when suggest() is called the first time.
        # The spelling.txt model is adopted from Norvig's big.txt (http://norvig.com/big.txt)
        # based on several public domain books from Project Gutenberg 
        # and lists of most frequent words from Wiktionary and the British National Corpus.
        data = (v.split() for v in open(self._model).readlines())
        data = ((k, int(v)) for k, v in data)
        dict.__init__(self, data)

    @classmethod
    def train(self, s, path="spelling.txt"):
        """ Counts the words in the given string and saves the probabilities at the given path.
            This can be used to generate a new model for the Spelling() constructor.
        """
        model = {}
        for w in re.findall("[a-z]+", s.lower()):
            model[w] = w in model and model[w] + 1 or 1
        model = ("%s %s" % (k, v) for k, v in model.items())
        model = "\n".join(model)
        f = open(path, "w")
        f.write(model)
        f.close()
        
    def _edit1(self, w):
        """ Returns a set of words with edit distance 1 from the given word.
        """
        # Of all spelling errors, about 80% will be edit distance 1.
        # Edit distance 1 means one character deleted, swapped, replaced or inserted.
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
        """ Return a list of (word, probability) spelling corrections for the given word,
            based on the probability of known words with edit distance 1-2 from the given word.
        """
        if len(self) == 0:
            self.load()
        candidates = self._known([w]) \
                  or self._known(self._edit1(w)) \
                  or self._known(self._edit2(w)) \
                  or [w]
        candidates = [(self.get(w, 0) + 1, w) for w in candidates]
        s = float(sum(p for p, w in candidates) or 1)
        #return max(candidates)[1]
        candidates = sorted(((p/s, w) for p, w in candidates), reverse=True)
        candidates = [(w, p) for p, w in candidates]
        return candidates

suggest = Spelling().suggest

#print suggest("cororect")
#print suggest("speling")
