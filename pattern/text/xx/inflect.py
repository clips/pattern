#### PATTERN | XX | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c)
# Author:
# License:
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Template for pattern.xx.inflect with functions for word inflection in language XXXXX.
# inflection is the modification of a word to express different grammatical categories,
# such as tense, mood, voice, aspect, person, number, gender and case.
# Conjugation is the inflection of verbs.
# To construct a lemmatizer for pattern.xx.parser.find_lemmata(),
# we need functions for noun singularization, verb infinitives, predicate adjectives, etc.

import os
import sys
import re

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""
    
sys.path.insert(0, os.path.join(MODULE, "..", "..", "..", ".."))

# Import Verbs base class and verb tenses.
from pattern.text import Verbs as _Verbs
from pattern.text import (
    INFINITIVE, PRESENT, PAST, FUTURE,
    FIRST, SECOND, THIRD,
    SINGULAR, PLURAL, SG, PL,
    PROGRESSIVE,
    PARTICIPLE
)

sys.path.pop(0)

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"

VOWELS = "aeiouy"
re_vowel = re.compile(r"a|e|i|o|u|y", re.I)
is_vowel = lambda ch: ch in VOWELS

#### ARTICLE #######################################################################################

# Inflection gender.
MASCULINE, FEMININE, NEUTER, PLURAL = \
    MALE, FEMALE, NEUTRAL, PLURAL = \
        M, F, N, PL = "m", "f", "n", "p"

def definite_article(word):
    """ Returns the definite article for a given word.
    """
    return "the"

def indefinite_article(word):
    """ Returns the indefinite article for a given word.
    """
    return "a"

DEFINITE, INDEFINITE = \
    "definite", "indefinite"

def article(word, function=INDEFINITE):
    """ Returns the indefinite or definite article for the given word.
    """
    return function == DEFINITE \
       and definite_article(word) \
        or indefinite_article(word)

_article = article

def referenced(word, article=INDEFINITE):
    """ Returns a string with the article + the word.
    """
    return "%s %s" % (_article(word, article), word)

#### PLURALIZE ######################################################################################

def pluralize(word, pos=NOUN, custom={}):
    """ Returns the plural of a given word.
    """
    return word + "s"

#### SINGULARIZE ###################################################################################

def singularize(word, pos=NOUN, custom={}):
    """ Returns the singular of a given word.
    """
    return word.rstrip("s")

#### VERB CONJUGATION ##############################################################################
# The verb table was trained on CELEX and contains the top 2000 most frequent verbs.

class Verbs(_Verbs):
    
    def __init__(self):
        _Verbs.__init__(self, os.path.join(MODULE, "xx-verbs.txt"),
            language = "xx",
              # The order of tenses in the given file; see pattern.text.__init__.py => Verbs.
              format = [0, 1, 2, 3, 7, 8, 17, 18, 19, 23, 25, 24, 16, 9, 10, 11, 15, 33, 26, 27, 28, 32],
             default = {}  
            )
    
    def find_lemma(self, verb):
        """ Returns the base form of the given inflected verb, using a rule-based approach.
        """
        return verb

    def find_lexeme(self, verb):
        """ For a regular verb (base form), returns the forms using a rule-based approach.
        """
        return []

verbs = Verbs()

conjugate, lemma, lexeme, tenses = \
    verbs.conjugate, verbs.lemma, verbs.lexeme, verbs.tenses

#### ATTRIBUTIVE & PREDICATIVE #####################################################################

def attributive(adjective):
    """ For a predicative adjective, returns the attributive form.
    """
    return adjective

def predicative(adjective):
    """ Returns the predicative adjective.
    """
    return adjective