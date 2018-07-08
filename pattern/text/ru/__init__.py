#### PATTERN | RU ##################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# English linguistical tools using fast regular expressions.

from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

import os
import sys

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

sys.path.insert(0, os.path.join(MODULE, "..", "..", "..", ".."))

# Import parser base classes.
from pattern.text import (
    Lexicon, Model, Morphology, Context, Parser as _Parser, ngrams, pprint, commandline,
    PUNCTUATION
)
# Import parser universal tagset.
from pattern.text import (
    penntreebank2universal,
    PTB, PENN, UNIVERSAL,
    NOUN, VERB, ADJ, ADV, PRON, DET, PREP, ADP, NUM, CONJ, INTJ, PRT, PUNC, X
)
# Import parse tree base classes.
from pattern.text.tree import (
    Tree, Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table,
    SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR
)

# Import spelling base class.
from pattern.text import (
    Spelling
)

sys.path.pop(0)

#--- Russian PARSER --------------------------------------------------------------------------------


class Parser(_Parser):

    def find_tags(self, tokens, **kwargs):
        if kwargs.get("tagset") in (PENN, None):
            kwargs.setdefault("map", lambda token, tag: (token, tag))
        if kwargs.get("tagset") == UNIVERSAL:
            kwargs.setdefault("map", lambda token, tag: penntreebank2universal(token, tag))
        return _Parser.find_tags(self, tokens, **kwargs)

parser = Parser(
    lexicon=os.path.join(MODULE, "ru-lexicon.txt"),  # A dict of known words => most frequent tag.
    frequency=os.path.join(MODULE, "ru-frequency.txt"),  # A dict of word frequency.
    model=os.path.join(MODULE, "ru-model.slp"),  # A SLP classifier trained on WSJ (01-07).
    #morphology=os.path.join(MODULE, "en-morphology.txt"),  # A set of suffix rules
    #context=os.path.join(MODULE, "en-context.txt"),  # A set of contextual rules.
    #entities=os.path.join(MODULE, "en-entities.txt"),  # A dict of named entities: John = NNP-PERS.
    #default=("NN", "NNP", "CD"),
    language="ru"
)


spelling = Spelling(
    path=os.path.join(MODULE, "ru-spelling.txt"),
    alphabet='CYRILLIC'
)


def tokenize(s, *args, **kwargs):
    """ Returns a list of sentences, where punctuation marks have been split from words.
    """
    return parser.find_tokens(s, *args, **kwargs)


def parse(s, *args, **kwargs):
    """ Returns a tagged Unicode string.
    """
    return parser.parse(s, *args, **kwargs)


def parsetree(s, *args, **kwargs):
    """ Returns a parsed Text from the given string.
    """
    return Text(parse(s, *args, **kwargs))


def suggest(w):
    """ Returns a list of (word, confidence)-tuples of spelling corrections.
    """
    return spelling.suggest(w)