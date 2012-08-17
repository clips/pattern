#### PATTERN | EN ##################################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# English linguistical tools using fast regular expressions.

from inflect import \
    article, referenced, DEFINITE, INDEFINITE, \
    pluralize, singularize, NOUN, VERB, ADJECTIVE, \
    conjugate, lemma, lexeme, tenses, VERBS, \
    grade, comparative, superlative, COMPARATIVE, SUPERLATIVE, \
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

from inflect.quantify import \
    number, numerals, quantify, reflect
    
from inflect.spelling import \
    suggest as spelling

from parser           import tokenize, parse, tag
from parser.tree      import Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table
from parser.tree      import SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR
from parser.modality  import mood, INDICATIVE, IMPERATIVE, CONDITIONAL, SUBJUNCTIVE
from parser.modality  import modality, EPISTEMIC
from parser.modality  import negated
from parser.sentiment import sentiment, polarity, subjectivity, positive
from parser.sentiment import NOUN, VERB, ADJECTIVE, ADVERB

import wordnet
import wordlist

def parsetree(s, *args, **kwargs):
    """ Returns a parsed Text from the given string.
    """
    return Text(parse(s, *args, **kwargs))

def split(s, token=[WORD, POS, CHUNK, PNP]):
    """ Returns a parsed Text from the given parsed string.
    """
    return Text(s, token)

def pprint(string, token=[WORD, POS, CHUNK, PNP], column=4):
    """ Pretty-prints the output of parse() as a table with outlined columns.
        Alternatively, you can supply a Text or Sentence object.
    """
    if isinstance(string, basestring):
        print "\n\n".join([table(sentence, fill=column) for sentence in Text(string, token)])
    if isinstance(string, Text):
        print "\n\n".join([table(sentence, fill=column) for sentence in string])
    if isinstance(string, Sentence):
        print table(string, fill=column)
        
def ngrams(string, n=3):
    """ Returns a list of n-grams (tuples of n successive words) from the given string.
        Alternatively, you can supply a Text or Sentence object.
        n-grams will not run over sentence markers (i.e., .!?).
    """
    def strip_period(s, punctuation=(".:;,!?()[]'\"")):
        return [w for w in s if (isinstance(w, Word) and w.string or w) not in punctuation]
    if n <= 0:
        return []
    if isinstance(string, basestring):
        s = [strip_period(s.split(" ")) for s in tokenize(string)]
    if isinstance(string, Sentence):
        s = [strip_period(string)]
    if isinstance(string, Text):
        s = [strip_period(s) for s in string]
    g = []
    for s in s:
        #s = [None] + s + [None]
        g.extend([tuple(s[i:i+n]) for i in range(len(s)-n+1)])
    return g
