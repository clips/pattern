#### PATTERN | TEXT ################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# English, German and Dutch linguistical tools using fast regular expressions.

from en import Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table
from en import SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR
from en import \
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

def _multilingual(function, *args, **kwargs):
    """ Returns the value from the function with the given name in the given language module.
        By default, language="en".
    """
    language = kwargs.pop("language", "en")
    for module in ("en", "de", "nl"):
        if module == language:
            module = __import__(module)
            return getattr(module, function)(*args, **kwargs)

def ngrams(*args, **kwargs):
    return _multilingual("ngrams", *args, **kwargs)

def tokenize(*args, **kwargs):
    return _multilingual("tokenize", *args, **kwargs)

def parse(*args, **kwargs):
    return _multilingual("parse", *args, **kwargs)
        
def parsetree(*args, **kwargs):
    return _multilingual("parsetree", *args, **kwargs)

def split(*args, **kwargs):
    return _multilingual("split", *args, **kwargs)
    
def tag(*args, **kwargs):
    return _multilingual("tag", *args, **kwargs)
    
def sentiment(*args, **kwargs):
    return _multilingual("sentiment", *args, **kwargs)

def singularize(*args, **kwargs):
    return _multilingual("singularize", *args, **kwargs)
    
def pluralize(*args, **kwargs):
    return _multilingual("pluralize", *args, **kwargs)

def conjugate(*args, **kwargs):
    return _multilingual("conjugate", *args, **kwargs)
