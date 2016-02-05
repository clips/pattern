#### PATTERN | IT ##################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2013 University of Antwerp, Belgium
# Copyright (c) 2013 St. Lucas University College of Art & Design, Antwerp.
# Author: Tom De Smedt <tom@organisms.be>, Fabio Marfia <marfia@elet.polimi.it>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# Italian linguistical tools using fast regular expressions.

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
    penntreebank2universal as _penntreebank2universal,
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
    Sentiment as _Sentiment,
    NOUN, VERB, ADJECTIVE, ADVERB,
    MOOD, IRONY
)
# Import spelling base class.
from pattern.text import (
    Spelling
)
# Import verb tenses.
from pattern.text import (
    INFINITIVE, PRESENT, PAST, FUTURE, CONDITIONAL,
    FIRST, SECOND, THIRD,
    SINGULAR, PLURAL, SG, PL,
    INDICATIVE, IMPERATIVE, SUBJUNCTIVE,
    IMPERFECTIVE, PERFECTIVE, PROGRESSIVE,
    IMPERFECT, PRETERITE,
    PARTICIPLE, GERUND
)
# Import inflection functions.
from pattern.text.it.inflect import (
    article, referenced, DEFINITE, INDEFINITE,
    pluralize, singularize, NOUN, VERB, ADJECTIVE,
    verbs, conjugate, lemma, lexeme, tenses,
    predicative, attributive,
    gender, MASCULINE, MALE, FEMININE, FEMALE, NEUTER, NEUTRAL, PLURAL, M, F, N, PL
)
# Import all submodules.
from pattern.text.it import inflect

sys.path.pop(0)

#--- PARSER ----------------------------------------------------------------------------------------

_subordinating_conjunctions = set((
    "che"   , u"perché", "sebbene", 
    "come"  , u"poiché", "senza", 
    "se"    , u"perciò", "salvo", 
    "mentre", u"finché", "dopo",
    "quando", u"benché"
))

def penntreebank2universal(token, tag):
    """ Converts a Penn Treebank II tag to a universal tag.
        For example: che/IN => che/CONJ
    """
    if tag == "IN" and token.lower() in _subordinating_conjunctions:
        return CONJ
    return _penntreebank2universal(token, tag)

ABBREVIATIONS = [
    "a.C.", "all.", "apr.", "art.", "artt.", "b.c.", "c.a.", "cfr.", "c.d.", 
    "c.m.", "C.V.", "d.C.", "Dott.", "ecc.", "egr.", "e.v.", "fam.", "giu.", 
    "Ing.", "L.", "n.", "op.", "orch.", "p.es.", "Prof.", "prof.", "ql.co.", 
    "secc.", "sig.", "s.l.m.", "s.r.l.", "Spett.", "S.P.Q.C.", "v.c."
]

replacements = (
    "a", "co", "all", "anch", "nient", "cinquant", 
    "b", "de", "dev", "bell", "quell", "diciott",
    "c", "gl", "don", "cent", "quest", "occupo",
    "d", "po", "dov", "dall", "trent", "sessant",
    "l", "un", "nel", "dell", "tropp",
    "m",              "king",
    "n",              "nell",
    "r",              "sant",
    "s",              "sott",
                      "sull",
                      "tant",
                      "tutt",
                      "vent")

replacements += tuple(k.capitalize() for k in replacements)
replacements  = dict((k+"'", k+"' ") for k in replacements)

def find_lemmata(tokens):
    """ Annotates the tokens with lemmata for plural nouns and conjugated verbs,
        where each token is a [word, part-of-speech] list.
    """
    for token in tokens:
        word, pos, lemma = token[0], token[1], token[0]
        if pos.startswith(("DT",)):
            lemma = singularize(word, pos="DT")
        if pos.startswith("JJ"):
            lemma = predicative(word)  
        if pos == "NNS":
            lemma = singularize(word)
        if pos.startswith(("VB", "MD")):
            lemma = conjugate(word, INFINITIVE) or word
        token.append(lemma.lower())
    return tokens

class Parser(_Parser):
    
    def find_tokens(self, tokens, **kwargs):
        kwargs.setdefault("abbreviations", ABBREVIATIONS)
        kwargs.setdefault("replace", replacements)
        #return _Parser.find_tokens(self, tokens, **kwargs)
        
        s = _Parser.find_tokens(self, tokens, **kwargs)
        s = [s.replace(" &contraction ;", u"'").replace("XXX -", "-") for s in s]
        return s

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

parser = Parser(
     lexicon = os.path.join(MODULE, "it-lexicon.txt"),
   frequency = os.path.join(MODULE, "it-frequency.txt"),
  morphology = os.path.join(MODULE, "it-morphology.txt"),
     context = os.path.join(MODULE, "it-context.txt"),
     default = ("NN", "NNP", "CD"),
    language = "it"
)

lexicon = parser.lexicon # Expose lexicon.

sentiment = Sentiment(
        path = os.path.join(MODULE, "it-sentiment.xml"), 
      synset = None,
   negations = ("mai", "no", "non"),
   modifiers = ("RB",),
   modifier  = lambda w: w.endswith(("mente")),
   tokenizer = parser.find_tokens,
    language = "it"
)

spelling = Spelling(
        path = os.path.join(MODULE, "it-spelling.txt")
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

def keywords(s, top=10, **kwargs):
    """ Returns a sorted list of keywords in the given string.
    """
    return parser.find_keywords(s, **dict({
        "frequency": parser.frequency,
              "top": top,
              "pos": ("NN",),
           "ignore": ("rt",)}, **kwargs))

def suggest(w):
    """ Returns a list of (word, confidence)-tuples of spelling corrections.
    """
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

split = tree # Backwards compatibility.

#---------------------------------------------------------------------------------------------------
# python -m pattern.it xml -s "Il gatto nero faceva le fusa." -OTCL

if __name__ == "__main__":
    commandline(parse)