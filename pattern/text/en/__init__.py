#### PATTERN | EN ##################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# English linguistical tools using fast regular expressions.

import os
import sys

try:
    MODULE = os.path.dirname(os.path.abspath(__file__))
except:
    MODULE = ""

sys.path.insert(0, os.path.join(MODULE, "..", "..", "..", ".."))

# Import parser base classes.
from pattern.text import (
    Lexicon, Spelling, Parser as _Parser, ngrams, pprint, commandline,
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
# Import sentiment analysis base classes.
from pattern.text import (
    Sentiment as _Sentiment, NOUN, VERB, ADJECTIVE, ADVERB
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
from pattern.text.en.inflect import (
    article, referenced, DEFINITE, INDEFINITE,
    pluralize, singularize, NOUN, VERB, ADJECTIVE,
    grade, comparative, superlative, COMPARATIVE, SUPERLATIVE,
    verbs, conjugate, lemma, lexeme, tenses,
    predicative, attributive
)
# Import quantification functions.
from pattern.text.en.inflect_quantify import (
    number, numerals, quantify, reflect
)
# Import mood & modality functions.
from pattern.text.en.modality import (
    mood, INDICATIVE, IMPERATIVE, CONDITIONAL, SUBJUNCTIVE,
    modality, uncertain, EPISTEMIC,
    negated
)
# Import all submodules.
from pattern.text.en import inflect
from pattern.text.en import wordnet
from pattern.text.en import wordlist

sys.path.pop(0)

#--- ENGLISH PARSER --------------------------------------------------------------------------------

def find_lemmata(tokens):
    """ Annotates the tokens with lemmata for plural nouns and conjugated verbs,
        where each token is a [word, part-of-speech] list.
    """
    for token in tokens:
        word, pos, lemma = token[0], token[1], token[0]
        # cats => cat
        if pos == "NNS":
            lemma = singularize(word)
        # sat => sit
        if pos.startswith(("VB", "MD")):
            lemma = conjugate(word, INFINITIVE) or word
        token.append(lemma.lower())
    return tokens

class Parser(_Parser):

    def find_lemmata(self, tokens, **kwargs):
        return find_lemmata(tokens)

    def find_tags(self, tokens, **kwargs):
        if kwargs.get("tagset") in (PENN, None):
            kwargs.setdefault("map", lambda token, tag: (token, tag))
        if kwargs.get("tagset") == UNIVERSAL:
            kwargs.setdefault("map", lambda token, tag: penntreebank2universal(token, tag))
        return _Parser.find_tags(self, tokens, **kwargs)

class Sentiment(_Sentiment):

    def load(self, path=None):
        _Sentiment.load(self, path)
        # Map "terrible" to adverb "terribly" (+1% accuracy)
        if not path:
            for w, pos in dict.items(self):
                if "JJ" in pos:
                    if w.endswith("y"):
                        w = w[:-1] + "i"
                    if w.endswith("le"):
                        w = w[:-2]
                    p, s, i = pos["JJ"]
                    self.annotate(w + "ly", "RB", p, s, i)

lexicon = Lexicon(
        path = os.path.join(MODULE, "en-lexicon.txt"),
  morphology = os.path.join(MODULE, "en-morphology.txt"),
     context = os.path.join(MODULE, "en-context.txt"),
    entities = os.path.join(MODULE, "en-entities.txt"),
    language = "en"
)

parser = Parser(
     lexicon = lexicon,
     default = ("NN", "NNP", "CD"),
    language = "en"
)

sentiment = Sentiment(
        path = os.path.join(MODULE, "en-sentiment.xml"),
      synset = "wordnet_id",
   negations = ("no", "not", "n't", "never"),
   modifiers = ("RB",),
   modifier  = lambda w: w.endswith("ly"),
   tokenizer = parser.find_tokens,
    language = "en"
)

spelling = Spelling(
        path = os.path.join(MODULE, "en-spelling.txt")
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

def split(s, token=[WORD, POS, CHUNK, PNP]):
    """ Returns a parsed Text from the given parsed string.
    """
    return Text(s, token)

def tag(s, tokenize=True, encoding="utf-8"):
    """ Returns a list of (token, tag)-tuples from the given string.
    """
    tags = []
    for sentence in parse(s, tokenize, True, False, False, False, encoding).split():
        for token in sentence:
            tags.append((token[0], token[1]))
    return tags

def suggest(w):
    """ Returns a list of (word, confidence)-tuples of spelling corrections.
    """
    # Don't correct one-letter, uppercased words
    if w in ['I', 'A']:
        return [(w, 1.0)]
    return spelling.suggest(w)

def polarity(s, **kwargs):
    """ Returns the sentence polarity (positive/negative) between -1.0 and 1.0.
    """
    return sentiment(s, **kwargs)[0]

def subjectivity(s, **kwargs):
    """ Returns the sentence subjectivity (objective/subjective) between 0.0 and 1.0.
    """
    return sentiment(s, **kwargs)[1]

def positive(s, threshold=0.1, **kwargs):
    """ Returns True if the given sentence has a positive sentiment (polarity >= threshold).
    """
    return polarity(s, **kwargs) >= threshold

#---------------------------------------------------------------------------------------------------
# python -m pattern.en xml -s "The cat sat on the mat." -OTCL

if __name__ == "__main__":
    commandline(parse)