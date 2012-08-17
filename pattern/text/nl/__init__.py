#### PATTERN | NL ##################################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Dutch linguistical tools using fast regular expressions.

from parser           import tokenize, parse, tag
from parser.sentiment import sentiment, polarity, subjectivity, positive
from parser.sentiment import NOUN, VERB, ADJECTIVE, ADVERB

from inflect import \
    pluralize, singularize, NOUN, VERB, ADJECTIVE, \
    conjugate, lemma, lexeme, tenses, VERBS, \
    predicative, attributive, \
    INFINITIVE, \
    PRESENT_1ST_PERSON_SINGULAR, \
    PRESENT_2ND_PERSON_SINGULAR, \
    PRESENT_3RD_PERSON_SINGULAR, \
    PRESENT_PLURAL, \
    PRESENT_PARTICIPLE, \
    PAST, \
    PAST_1ST_PERSON_SINGULAR, \
    PAST_2ND_PERSON_SINGULAR, \
    PAST_3RD_PERSON_SINGULAR, \
    PAST_PLURAL, \
    PAST_PARTICIPLE

# Language-independent functionality is inherited from pattern.en:
# Submodules pattern.nl.inflect and pattern.nl.parser import from pattern.en.
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from en import split, pprint, ngrams
from en import Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table
from en import SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR

def parsetree(s, *args, **kwargs):
    return Text(parse(s, *args, **kwargs))