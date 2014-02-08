#### PATTERN | ES ##################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Spanish linguistical tools using fast regular expressions.

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
    penntreebank2universal,
    PTB, PENN, UNIVERSAL,
    NOUN, VERB, ADJ, ADV, PRON, DET, PREP, ADP, NUM, CONJ, INTJ, PRT, PUNC, X
)
# Import parse tree base classes.
from pattern.text.tree import (
    Tree, Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table,
    SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR
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
from pattern.text.es.inflect import (
    article, referenced, DEFINITE, INDEFINITE,
    MASCULINE, MALE, FEMININE, FEMALE, NEUTER, NEUTRAL, PLURAL, M, F, N, PL,
    pluralize, singularize, NOUN, VERB, ADJECTIVE,
    verbs, conjugate, lemma, lexeme, tenses,
    predicative, attributive
)
# Import all submodules.
from pattern.text.es import inflect

sys.path.pop(0)

#--- SPANISH PARSER --------------------------------------------------------------------------------
# The Spanish parser (accuracy 92%) is based on the Spanish portion Wikicorpus v.1.0 (FDL license),
# using 1.5M words from the tagged sections 10000-15000.
# Samuel Reese, Gemma Boleda, Montse Cuadros, Lluís Padró, German Rigau. 
# Wikicorpus: A Word-Sense Disambiguated Multilingual Wikipedia Corpus. 
# Proceedings of 7th Language Resources and Evaluation Conference (LREC'10), 
# La Valleta, Malta. May, 2010. 
# http://www.lsi.upc.edu/~nlp/wikicorpus/

# The lexicon uses the Parole tagset:
# http://www.lsi.upc.edu/~nlp/SVMTool/parole.html
# http://nlp.lsi.upc.edu/freeling/doc/tagsets/tagset-es.html
PAROLE = "parole"
parole = {
    "AO": "JJ",   # primera
    "AQ": "JJ",   # absurdo
    "CC": "CC",   # e
    "CS": "IN",   # porque
    "DA": "DT",   # el
    "DD": "DT",   # ese
    "DI": "DT",   # mucha
    "DP": "PRP$", # mi, nuestra
    "DT": "DT",   # cuántos
    "Fa": ".",    # !
    "Fc": ",",    # ,
    "Fd": ":",    # :
    "Fe": "\"",   # "
    "Fg": ".",    # -
    "Fh": ".",    # /
    "Fi": ".",    # ?
    "Fp": ".",    # .
    "Fr": ".",    # >>
    "Fs": ".",    # ...
   "Fpa": "(",    # (
   "Fpt": ")",    # )
    "Fx": ".",    # ;
    "Fz": ".",    # 
     "I": "UH",   # ehm
    "NC": "NN",   # islam
   "NCS": "NN",   # guitarra
   "NCP": "NNS",  # guitarras
    "NP": "NNP",  # Óscar
    "P0": "PRP",  # se
    "PD": "DT",   # ése
    "PI": "DT",   # uno
    "PP": "PRP",  # vos
    "PR": "WP$",  # qué
    "PT": "WP$",  # qué
    "PX": "PRP$", # mío
    "RG": "RB",   # tecnológicamente
    "RN": "RB",   # no
    "SP": "IN",   # por
   "VAG": "VBG",  # habiendo
   "VAI": "MD",   # había
   "VAN": "MD",   # haber
   "VAS": "MD",   # haya
   "VMG": "VBG",  # habiendo
   "VMI": "VB",   # habemos
   "VMM": "VB",   # compare
   "VMN": "VB",   # comparecer
   "VMP": "VBN",  # comparando
   "VMS": "VB",   # compararan
   "VSG": "VBG",  # comparando
   "VSI": "VB",   # será
   "VSN": "VB",   # ser
   "VSP": "VBN",  # sido
   "VSS": "VB",   # sea
     "W": "NN",   # septiembre
     "Z": "CD",   # 1,7
    "Zd": "CD",   # 1,7
    "Zm": "CD",   # £1,7
    "Zp": "CD",   # 1,7%
}

def parole2penntreebank(token, tag):
    """ Converts a Parole tag to a Penn Treebank II tag.
        For example: importantísimo/AQ => importantísimo/ADJ
    """
    return (token, parole.get(tag, tag))

def parole2universal(token, tag):
    """ Converts a Parole tag to a universal tag.
        For example: importantísimo/AQ => importantísimo/ADJ
    """
    if tag == "CS":
        return (token, CONJ)
    if tag == "DP":
        return (token, DET)
    if tag in ("P0", "PD", "PI", "PP", "PR", "PT", "PX"):
        return (token, PRON)
    return penntreebank2universal(*parole2penntreebank(token, tag))

ABBREVIATIONS = set((
    u"a.C.", u"a.m.", u"apdo.", u"aprox.", u"Av.", u"Avda.", u"c.c.", u"D.", u"Da.", u"d.C.", 
    u"d.j.C.", u"dna.", u"Dr.", u"Dra.", u"esq.", u"etc.", u"Gob.", u"h.", u"m.n.", u"no.", 
    u"núm.", u"pág.", u"P.D.", u"P.S.", u"p.ej.", u"p.m.", u"Profa.", u"q.e.p.d.", u"S.A.", 
    u"S.L.", u"Sr.", u"Sra.", u"Srta.", u"s.s.s.", u"tel.", u"Ud.", u"Vd.", u"Uds.", u"Vds.", 
    u"v.", u"vol.", u"W.C."
))

def find_lemmata(tokens):
    """ Annotates the tokens with lemmata for plural nouns and conjugated verbs,
        where each token is a [word, part-of-speech] list.
    """
    for token in tokens:
        word, pos, lemma = token[0], token[1], token[0]
        if pos.startswith(("DT",)):
            lemma = singularize(word, pos="DT")
        if pos.startswith(("JJ",)):
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
        kwargs.setdefault("replace", {})
        return _Parser.find_tokens(self, tokens, **kwargs)

    def find_lemmata(self, tokens, **kwargs):
        return find_lemmata(tokens)

    def find_tags(self, tokens, **kwargs):
        if kwargs.get("tagset") in (PENN, None):
            kwargs.setdefault("map", lambda token, tag: parole2penntreebank(token, tag))
        if kwargs.get("tagset") == UNIVERSAL:
            kwargs.setdefault("map", lambda token, tag: parole2universal(token, tag))
        if kwargs.get("tagset") is PAROLE:
            kwargs.setdefault("map", lambda token, tag: (token, tag))
        return _Parser.find_tags(self, tokens, **kwargs)

parser = Parser(
     lexicon = os.path.join(MODULE, "es-lexicon.txt"), 
  morphology = os.path.join(MODULE, "es-morphology.txt"), 
     context = os.path.join(MODULE, "es-context.txt"),
     default = ("NCS", "NP", "Z"),
    language = "es"
)

lexicon = parser.lexicon # Expose lexicon.

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

split = tree # Backwards compatibility.

#---------------------------------------------------------------------------------------------------
# python -m pattern.es xml -s "A quien se hace de miel las moscas le comen." -OTCL

if __name__ == "__main__":
    commandline(parse)