#### PATTERN | EN | ##################################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

######################################################################################################
# English linguistical tools using fast regular expressions.

from inflect import \
    article, referenced, DEFINITE, INDEFINITE, \
    pluralize, singularize, NOUN, VERB, ADJECTIVE, \
    conjugate, lemma, lexeme, tenses, \
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
    PAST_PARTICIPLE, \
    grade, comparative, superlative, COMPARATIVE, SUPERLATIVE

from inflect.quantify import \
    number, numerals, quantify, reflect

from parser          import parse, tag
from parser.tree     import Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table
from parser.tree     import SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR
from parser.modality import mood, INDICATIVE, IMPERATIVE, CONDITIONAL, SUBJUNCTIVE
from parser.modality import modality, EPISTEMIC

def split(s, token=[WORD, POS, CHUNK, PNP]):
    return Text(s, token)

def pprint(string, token=[WORD, POS, CHUNK, PNP], column=4):
    """ Pretty-prints the output of MBSP.parse() as a table with outlined columns.
        Alternatively, you can supply a Text or Sentence object.
    """
    if isinstance(string, basestring):
        print "\n\n".join([table(sentence, fill=column) for sentence in Text(string, token)])
    if isinstance(string, Text):
        print "\n\n".join([table(sentence, fill=column) for sentence in string])
    if isinstance(string, Sentence):
        print table(string, fill=column)