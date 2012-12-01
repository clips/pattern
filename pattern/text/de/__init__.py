#### PATTERN | DE ##################################################################################
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# German linguistical tools using fast regular expressions.

from parser import tokenize, parse, tag

from inflect import \
    article, referenced, DEFINITE, INDEFINITE, \
    gender, MASCULINE, MALE, FEMININE, FEMALE, NEUTER, NEUTRAL, PLURAL, \
    pluralize, singularize, NOUN, VERB, ADJECTIVE, \
    conjugate, lemma, lexeme, tenses, VERBS, \
    grade, comparative, superlative, COMPARATIVE, SUPERLATIVE, \
    predicative, attributive, \
    NOMINATIVE, ACCUSATIVE, DATIVE, GENITIVE, SUBJECT, OBJECT, INDIRECT, PROPERTY, \
    INFINITIVE, PRESENT, PAST, FUTURE, \
    FIRST, SECOND, THIRD, \
    SINGULAR, PLURAL, SG, PL, \
    INDICATIVE, IMPERATIVE, SUBJUNCTIVE, \
    PROGRESSIVE, \
    PARTICIPLE, GERUND

# Language-independent functionality is inherited from pattern.en:
# Submodules pattern.de.inflect and pattern.de.parser import from pattern.en.
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from en import split, pprint, ngrams
from en import Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table
from en import SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR

def parsetree(s, *args, **kwargs):
    return Text(parse(s, *args, **kwargs))