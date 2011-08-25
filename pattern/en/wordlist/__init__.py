#### PATTERN | VECTOR | WORDLIST #####################################################################
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

def wordlist(name): 
    return open(os.path.join(MODULE, name+".txt")).read().split(", ")

ACADEMIC  = wordlist("academic")  # English academic words.
BASIC     = wordlist("basic")     # English basic words (850) that express 90% of concepts.
PROFANITY = wordlist("profanity") # English swear words.
TIME      = wordlist("time")      # English time and date words.

# Note: if used for lookups, performance can be increased by using a dict:
# blacklist = dict.fromkeys(PROFANITY+TIME, True)
# for i in range(1000):
#    corpus.append(Document(src[i], exclude=blacklist))