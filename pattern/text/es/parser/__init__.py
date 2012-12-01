#### PATTERN | ES | RULE-BASED SHALLOW PARSER ######################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

import re
import os

try: 
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

# The tokenizer, chunker and relation finder are inherited from pattern.en.parser.
# The tagger is trained on the Spanish portion of Wikicorpus v.1.0 (FDL license),
# using 1.5M words from the tagged sections 10000-15000.
# Reference:
# Samuel Reese, Gemma Boleda, Montse Cuadros, Lluís Padró, German Rigau. 
# Wikicorpus: A Word-Sense Disambiguated Multilingual Wikipedia Corpus. 
# In Proceedings of 7th Language Resources and Evaluation Conference (LREC'10), 
# La Valleta, Malta. May, 2010. 
# http://www.lsi.upc.edu/~nlp/wikicorpus/

# Accuracy is around 92%, but Pattern scores may vary due to Parole => Penn Treebank mapping etc.
import sys; sys.path.insert(0, os.path.join(MODULE, "..", ".."))
from en.parser import Lexicon
from en.parser import PUNCTUATION, tokenize as _en_tokenize, parse as _en_parse, TaggedString
from en.parser import commandline

#### TOKENIZER #####################################################################################

ABBREVIATIONS = [
    "a.C.", "a.m.", "apdo.", "aprox.", "Av.", "Avda.", "c.c.", "D.", "Da.", "d.C.", "d.j.C.",
    "dna.", "Dr.", "Dra.", "esq.", "etc.", "Gob.", "h.", "m.n.", "no.", u"núm.", u"pág.",
    "P.D.", "P.S.", "p.ej.", "p.m.", "Profa.", "q.e.p.d.", "S.A.", "S.L.", "Sr.", "Sra.",
    "Srta.", "s.s.s.", "tel.", "Ud.", "Vd.", "Uds.", "Vds.", "v.", "vol.", "W.C."
]

def tokenize(s, punctuation=PUNCTUATION, abbreviations=ABBREVIATIONS, replace={}):
    return _en_tokenize(s, punctuation, abbreviations, replace)
    
_tokenize = tokenize

#### LEMMATIZER ####################################################################################
# Word lemmas using singularization and verb conjugation from the inflect module.

try: 
    from ..inflect import singularize, conjugate, predicative
except:
    try:
        sys.path.append(os.path.join(MODULE, ".."))
        from inflect import singularize, conjugate, predicative
    except:
        try: 
            from pattern.es.inflect import singularize, conjugate, predicative 
        except:
            singularize = lambda w: w
            conjugate   = lambda w, t: w
            predicative = lambda w: w

def lemma(word, pos="NN"):
    if pos == "NNS":
        return singularize(word)
    if pos.startswith(("VB","MD")):
        return conjugate(word, "infinitive") or word
    if pos.startswith(("JJ",)):
        return predicative(word)
    if pos.startswith(("DT",)):
        return singularize(word, pos="DT")
    return word

def find_lemmata(tagged):
    for token in tagged:
        token.append(lemma(token[0].lower(), pos=len(token) > 1 and token[1] or None))
    return tagged

#### PARSER ########################################################################################

# pattern.en.find_tags() has an optional "lexicon" parameter.
# We'll pass the Spanish lexicon to it instead of the default English lexicon:
lexicon = LEXICON = Lexicon()
lexicon.path = os.path.join(MODULE, "brill-lexicon.txt")
lexicon.lexical_rules.path = os.path.join(MODULE, "brill-lexical.txt")
lexicon.contextual_rules.path = os.path.join(MODULE, "brill-contextual.txt")
lexicon.named_entities.tag = "NP"

# Parole tagset:
# http://www.lsi.upc.edu/~nlp/SVMTool/parole.html
# http://nlp.lsi.upc.edu/freeling/doc/tagsets/tagset-es.html
PENN = PENNTREEBANK = TREEBANK = "penntreebank"
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

def parole2penntreebank(tag):
    """ Converts a Parole tag to Penn Treebank II tag.
        For example: importantísimo AQ => importantísimo/JJ
    """
    return parole.get(tag, tag)

def parse(s, tokenize=True, tags=True, chunks=True, relations=False, lemmata=False, encoding="utf-8", **kwargs):
    """ Takes a string (sentences) and returns a tagged Unicode string. 
        Sentences in the output are separated by newlines.
    """
    if tokenize:
        s = _tokenize(s)
    if isinstance(s, (list, tuple)):
        s = [isinstance(s, basestring) and s.split(" ") or s for s in s]
    if isinstance(s, basestring):
        s = [s.split(" ") for s in s.split("\n")]
    # Reuse the English parser:
    kwargs.update({
        "lemmata": False,
          "light": False,
        "lexicon": LEXICON,
       "language": "es",
        "default": "NC",
            "map": kwargs.get("tagset", "") != PAROLE and parole2penntreebank or None,
    })
    s = _en_parse(s, False, tags, chunks, relations, **kwargs)
    # Use pattern.es.inflect for lemmatization:
    if lemmata:
        p = [find_lemmata(sentence) for sentence in s.split()]
        p = "\n".join([" ".join(["/".join(token) for token in sentence]) for sentence in p])
        s = TaggedString(p, tags=s.tags+["lemma"], language="es")
    return s

def tag(s, tokenize=True, encoding="utf-8"):
    """ Returns a list of (token, tag)-tuples from the given string.
    """
    tags = []
    for sentence in parse(s, tokenize, True, False, False, False, encoding).split():
        for token in sentence:
            tags.append((token[0], token[1]))
    return tags

#### COMMAND LINE ##################################################################################
# From the folder that contains the "pattern" folder:
# python -m pattern.es.parser xml -s "A quien se hace de miel las moscas le comen." -OTCLI

if __name__ == "__main__":
    commandline(parse)