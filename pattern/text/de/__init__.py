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
    INFINITIVE, \
    PRESENT_1ST_PERSON_SINGULAR, \
    PRESENT_2ND_PERSON_SINGULAR, \
    PRESENT_3RD_PERSON_SINGULAR, \
    PRESENT_1ST_PERSON_PLURAL, \
    PRESENT_2ND_PERSON_PLURAL, \
    PRESENT_3RD_PERSON_PLURAL, \
    PRESENT_PARTICIPLE, \
    PAST_1ST_PERSON_SINGULAR, \
    PAST_2ND_PERSON_SINGULAR, \
    PAST_3RD_PERSON_SINGULAR, \
    PAST_1ST_PERSON_PLURAL, \
    PAST_2ND_PERSON_PLURAL, \
    PAST_3RD_PERSON_PLURAL, \
    PAST_PARTICIPLE, \
    IMPERATIVE_2ND_PERSON_SINGULAR, \
    IMPERATIVE_1ST_PERSON_PLURAL, \
    IMPERATIVE_2ND_PERSON_PLURAL, \
    IMPERATIVE_3RD_PERSON_PLURAL, \
    PRESENT_SUBJUNCTIVE_1ST_PERSON_SINGULAR, \
    PRESENT_SUBJUNCTIVE_2ND_PERSON_SINGULAR, \
    PRESENT_SUBJUNCTIVE_3RD_PERSON_SINGULAR, \
    PRESENT_SUBJUNCTIVE_1ST_PERSON_PLURAL, \
    PRESENT_SUBJUNCTIVE_2ND_PERSON_PLURAL, \
    PRESENT_SUBJUNCTIVE_3RD_PERSON_PLURAL, \
    PAST_SUBJUNCTIVE_1ST_PERSON_SINGULAR, \
    PAST_SUBJUNCTIVE_2ND_PERSON_SINGULAR, \
    PAST_SUBJUNCTIVE_3RD_PERSON_SINGULAR, \
    PAST_SUBJUNCTIVE_1ST_PERSON_PLURAL, \
    PAST_SUBJUNCTIVE_2ND_PERSON_PLURAL, \
    PAST_SUBJUNCTIVE_3RD_PERSON_PLURAL

# Language-independent functionality is inherited from pattern.en:
# Submodules pattern.de.inflect and pattern.de.parser import from pattern.en.
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from en import split, pprint, ngrams
from en import Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table
from en import SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR

def parsetree(s, *args, **kwargs):
    return Text(parse(s, *args, **kwargs))