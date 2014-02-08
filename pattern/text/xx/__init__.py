#### PATTERN | XX ##################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) year, institute, country
# Author: Name (e-mail)
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Template for pattern.xx, bundling natural language processing tools for language XXXXX.
# The module bundles a shallow parser (part-of-speech tagger, chunker, lemmatizer)
# with functions for word inflection (singularization, pluralization, conjugation)
# and sentiment analysis.

# Base classes for the parser, verb table and sentiment lexicon are inherited from pattern.text.
# The parser can be subclassed with a custom tokenizer (finds sentence boundaries)
# and lemmatizer (uses word inflection to find the base form of words).
# The part-of-speech tagger requires a lexicon of tagged known words and rules for unknown words.

# Tools for word inflection should be bundled in pattern.text.xx.inflect.

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
# Import parse tree base classes.
from pattern.text.tree import (
    Tree, Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table,
    SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR
)
# Import sentiment analysis base classes.
from pattern.text import (
    Sentiment,
    NOUN, VERB, ADJECTIVE, ADVERB,
    MOOD, IRONY
)
# Import spelling base class.
from pattern.text import (
    Spelling
)
# Import verb tenses.
from pattern.text import (
    INFINITIVE, PRESENT, PAST, FUTURE,
    FIRST, SECOND, THIRD,
    SINGULAR, PLURAL, SG, PL,
    PROGRESSIVE,
    PARTICIPLE
)
# Import inflection functions.
from pattern.text.xx.inflect import (
    article, referenced, DEFINITE, INDEFINITE,
    pluralize, singularize, NOUN, VERB, ADJECTIVE,
    verbs, conjugate, lemma, lexeme, tenses,
    predicative, attributive
)
# Import all submodules.
from pattern.text.xx import inflect

sys.path.pop(0)

#--- PARSER ----------------------------------------------------------------------------------------

# Pattern uses the Penn Treebank II tagset (http://www.clips.ua.ac.be/pages/penn-treebank-tagset).
# The lexicon for pattern.xx may be using a different tagset (e.g., PAROLE, WOTAN).
# The following functions are meant to map the tags to Penn Treebank II, see Parser.find_chunks().

TAGSET = {"??": "NN"} # pattern.xx tagset => Penn Treebank II.

def tagset2penntreebank(tag):
    return TAGSET.get(tag, tag)

# Different languages have different contractions (e.g., English "I've" or French "j'ai")
# and abbreviations. The following functions define contractions and abbreviations
# for pattern.xx, see also Parser.find_tokens().

REPLACEMENTS  = {"'s": " 's", "'ve": " 've"}
ABBREVIATIONS = set(("e.g.", "etc.", "i.e."))

# A lemmatizer can be constructed if we have a pattern.xx.inflect,
# with functions for noun singularization and verb conjugation (i.e., infinitives).

def find_lemmata(tokens):
    """ Annotates the tokens with lemmata for plural nouns and conjugated verbs,
        where each token is a [word, part-of-speech] list.
    """
    for token in tokens:
        word, pos, lemma = token[0], token[1], token[0]
        if pos.startswith("JJ"):
            lemma = predicative(word)  
        if pos == "NNS":
            lemma = singularize(word)
        if pos.startswith(("VB", "MD")):
            lemma = conjugate(word, INFINITIVE) or word
        token.append(lemma.lower())
    return tokens

# Subclass the base parser with the language-specific functionality:

class Parser(_Parser):
    
    def find_tokens(self, tokens, **kwargs):
        kwargs.setdefault("abbreviations", ABBREVIATIONS)
        kwargs.setdefault("replace", REPLACEMENTS)
        return _Parser.find_tokens(self, tokens, **kwargs)
        
    def find_tags(self, tokens, **kwargs):
        kwargs.setdefault("map", tagset2penntreebank)
        return _Parser.find_tags(self, tokens, **kwargs)
        
    def find_chunks(self, tokens, **kwargs):
        return _Parser.find_chunks(self, tokens, **kwargs)

    def find_lemmata(self, tokens, **kwargs):
        return find_lemmata(tokens)

# The parser's part-of-speech tagger requires a lexicon of tagged known words,
# and rules for unknown words. See pattern.text.Morphology and pattern.text.Context
# for further details. A tutorial on how to acquire data for the lexicon is here:
# http://www.clips.ua.ac.be/pages/using-wiktionary-to-build-an-italian-part-of-speech-tagger

# Create the parser with default tags for unknown words:
# (noun, proper noun, numeric).

parser = Parser(
     lexicon = os.path.join(MODULE, "xx-lexicon.txt"), 
  morphology = os.path.join(MODULE, "xx-morphology.txt"), 
     context = os.path.join(MODULE, "xx-context.txt"),
    entities = os.path.join(MODULE, "xx-entities.txt"),
     default = ("NN", "NNP", "CD"),
    language = "xx"
)

lexicon = parser.lexicon # Expose lexicon.

# Create the sentiment lexicon,
# see pattern/text/xx/xx-sentiment.xml for further details.
# We also need to define the tag for modifiers,
# words that modify the score of the following word 
# (e.g., *very* good, *not good, ...)

sentiment = Sentiment(
        path = os.path.join(MODULE, "xx-sentiment.xml"), 
      synset = None,
   negations = ("no", "not", "never"),
   modifiers = ("RB",),
   modifier  = lambda w: w.endswith("ly"), # brilliantly, hardly, partially, ...
    language = "xx"
)

# Nothing should be changed below.

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

def tree(s, token=[WORD, POS, CHUNK, PNP, REL, LEMMA]):
    """ Returns a parsed Text from the given parsed string.
    """
    return Text(s, token)
    
def tag(s, tokenize=True, encoding="utf-8", **kwargs):
    """ Returns a list of (token, tag)-tuples from the given string.
    """
    tags = []
    for sentence in parse(s, tokenize, True, False, False, False, encoding, **kwargs).split():
        for token in sentence:
            tags.append((token[0], token[1]))
    return tags
  
def polarity(s, **kwargs):
    """ Returns the sentence polarity (positive/negative) between -1.0 and 1.0.
    """
    return sentiment(s, **kwargs)[0]

def subjectivity(s, **kwargs):
    """ Returns the sentence subjectivity (objective/subjective) between 0.0 and 1.0.
    """
    return sentiment(s, **kwargs)[1]
    
def positive(s, threshold=0.1, **kwargs):
    """ Returns True if the given sentence has a positive sentiment.
    """
    return polarity(s, **kwargs) >= threshold

split = tree # Backwards compatibility.

#---------------------------------------------------------------------------------------------------
# python -m pattern.xx xml -s "..." -OTCL

if __name__ == "__main__":
    commandline(parse)