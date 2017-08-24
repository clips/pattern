#### PATTERN | NL ##################################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Dutch linguistical tools using fast regular expressions.

from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

import os
import sys
import re

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
    INFINITIVE, PRESENT, PAST, FUTURE,
    FIRST, SECOND, THIRD,
    SINGULAR, PLURAL, SG, PL,
    PROGRESSIVE,
    PARTICIPLE
)
# Import inflection functions.
from pattern.text.nl.inflect import (
    pluralize, singularize, NOUN, VERB, ADJECTIVE,
    verbs, conjugate, lemma, lexeme, tenses,
    predicative, attributive
)
# Import all submodules.
from pattern.text.nl import inflect

sys.path.pop(0)

#--- DUTCH PARSER ----------------------------------------------------------------------------------
# The Dutch parser (accuracy 92%) is based on Jeroen Geertzen's language model:
# Brill-NL, http://cosmion.net/jeroen/software/brill_pos/

# The lexicon uses the WOTAN tagset:
# http://lands.let.ru.nl/literature/hvh.1999.2.ps
WOTAN = "wotan"
wotan = {
    "Adj(": (("vergr", "JJR"), ("overtr", "JJS"), ("", "JJ")),
    "Adv(": (("deel", "RP"), ("", "RB")),
    "Art(": (("", "DT"),),
   "Conj(": (("", "CC"),),
     "Int": (("", "UH"),),
    "Misc": (("symb", "SYM"), ("vreemd", "FW")),
      "N(": (("eigen,ev", "NNP"), ("eigen,mv", "NNPS"), ("ev", "NN"), ("mv", "NNS")),
    "Num(": (("", "CD"),),
   "Prep(": (("inf", "TO"), ("", "IN")),
   "Pron(": (("bez", "PRP$"), ("", "PRP")),
   "Punc(": (("komma", ","), ("open", "("), ("sluit", ")"), ("schuin", "CC"), ("", ".")),
      "V(": (("hulp", "MD"), ("ott,3", "VBZ"), ("ott", "VBP"), ("ovt", "VBD"),
             ("verl", "VBN"), ("teg", "VBG"), ("", "VB"))
}


def wotan2penntreebank(token, tag):
    """ Converts a WOTAN tag to a Penn Treebank II tag.
        For example: bokkenrijders/N(soort,mv,neut) => bokkenrijders/NNS
    """
    for k, v in wotan.items():
        if tag.startswith(k):
            for a, b in v:
                if a in tag:
                    return (token, b)
    return (token, tag)


def wotan2universal(token, tag):
    """ Converts a WOTAN tag to a universal tag.
        For example: bokkenrijders/N(soort,mv,neut) => bokkenrijders/NOUN
    """
    if tag.startswith("Adv"):
        return (token, ADV)
    return penntreebank2universal(*wotan2penntreebank(token, tag))

ABBREVIATIONS = set((
    "a.d.h.v.", "afb.", "a.u.b.", "bv.", "b.v.", "bijv.", "blz.", "ca.", "cfr.", "dhr.", "dr.",
    "d.m.v.", "d.w.z.", "e.a.", "e.d.", "e.g.", "enz.", "etc.", "e.v.", "evt.", "fig.", "i.e.",
    "i.h.b.", "ir.", "i.p.v.", "i.s.m.", "m.a.w.", "max.", "m.b.t.", "m.b.v.", "mevr.", "min.",
    "n.a.v.", "nl.", "n.o.t.k.", "n.t.b.", "n.v.t.", "o.a.", "ong.", "pag.", "ref.", "t.a.v.",
    "tel.", "zgn."
))


def find_lemmata(tokens):
    """ Annotates the tokens with lemmata for plural nouns and conjugated verbs,
        where each token is a [word, part-of-speech] list.
    """
    for token in tokens:
        word, pos, lemma = token[0], token[1], token[0]
        if pos.startswith("JJ") and word.endswith("e"):
            lemma = predicative(word)
        if pos == "NNS":
            lemma = singularize(word)
        if pos.startswith(("VB", "MD")):
            lemma = conjugate(word, INFINITIVE) or word
        token.append(lemma.lower())
    return tokens


class Parser(_Parser):

    def find_tokens(self, tokens, **kwargs):
        # 's in Dutch preceded by a vowel indicates plural ("auto's"): don't replace.
        kwargs.setdefault("abbreviations", ABBREVIATIONS)
        kwargs.setdefault("replace", {"'n": " 'n"})
        s = _Parser.find_tokens(self, tokens, **kwargs)
        s = [re.sub(r"' s (ochtends|morgens|middags|avonds)", "'s \\1", s) for s in s]
        return s

    def find_lemmata(self, tokens, **kwargs):
        return find_lemmata(tokens)

    def find_tags(self, tokens, **kwargs):
        if kwargs.get("tagset") in (PENN, None):
            kwargs.setdefault("map", lambda token, tag: wotan2penntreebank(token, tag))
        if kwargs.get("tagset") == UNIVERSAL:
            kwargs.setdefault("map", lambda token, tag: wotan2universal(token, tag))
        if kwargs.get("tagset") is WOTAN:
            kwargs.setdefault("map", lambda token, tag: (token, tag))
        return _Parser.find_tags(self, tokens, **kwargs)


class Sentiment(_Sentiment):

    def load(self, path=None):
        _Sentiment.load(self, path)
        # Map "verschrikkelijk" to adverbial "verschrikkelijke" (+1%)
        if not path:
            for w, pos in list(dict.items(self)):
                if "JJ" in pos:
                    p, s, i = pos["JJ"]
                    self.annotate(attributive(w), "JJ", p, s, i)

parser = Parser(
     lexicon = os.path.join(MODULE, "nl-lexicon.txt"),
   frequency = os.path.join(MODULE, "nl-frequency.txt"),
  morphology = os.path.join(MODULE, "nl-morphology.txt"),
     context = os.path.join(MODULE, "nl-context.txt"),
     default = ("N(soort,ev,neut)", "N(eigen,ev)", "Num()"),
    language = "nl"
)

lexicon = parser.lexicon # Expose lexicon.

sentiment = Sentiment(
        path = os.path.join(MODULE, "nl-sentiment.xml"),
      synset = "cornetto_id",
   negations = ("geen", "gene", "ni", "niet", "nooit"),
   modifiers = ("JJ", "RB",),
   modifier = lambda w: w.endswith(("ig", "isch", "lijk")),
   tokenizer = parser.find_tokens,
    language = "nl"
)

spelling = Spelling(
        path = os.path.join(MODULE, "nl-spelling.txt")
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
           "ignore": ("rt", "mensen")}, **kwargs))


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
# python -m pattern.nl xml -s "De kat wil wel vis eten maar geen poot nat maken." -OTCL

if __name__ == "__main__":
    commandline(parse)
