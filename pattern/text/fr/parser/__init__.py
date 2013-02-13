#### PATTERN | FR | RULE-BASED SHALLOW PARSER ######################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2013 University of Antwerp, Belgium
# Authors: Tom De Smedt <tom@organisms.be>, Rémi de Zoeten (CloseAlert.nl)
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
# The tagger is based on Lefff (Lexique des Formes Fléchies du Français).
# Reference:
# Benoît Sagot, Lionel Clément, Érice Villemonte de la Clergerie, Pierre Boullier.
# The Lefff 2 syntactic lexicon for French: architecture, acquisition.
# http://alpage.inria.fr/~sagot/lefff-en.html

# For words in Lefff that can have different part-of-speech tags,
# we used Lexique to find the most frequent POS-tag:
# http://www.lexique.org/

import sys; sys.path.insert(0, os.path.join(MODULE, "..", ".."))
from en.parser import Lexicon
from en.parser import PUNCTUATION, tokenize as _en_tokenize, parse as _en_parse, TaggedString
from en.parser import commandline

#### TOKENIZER #####################################################################################

# While contractions in English are optional, they are required in French:
replacements = {
       "l'": "l' ",  # le/la
       "c'": "c' ",  # ce
       "d'": "d' ",  # de
       "j'": "j' ",  # je
       "m'": "m' ",  # me
       "n'": "n' ",  # ne
      "qu'": "qu' ", # que
       "s'": "s' ",  # se
       "t'": "t' ",  # te
   "jusqu'": "jusqu' ",
  "lorsqu'": "lorsqu' ",
  "puisqu'": "puisqu' ",

}
replacements.update(((k.upper(), v.upper()) for k, v in replacements.items()))

ABBREVIATIONS = [
    u"av.", u"boul.", u"C.-B.", u"c.-à-d.", u"ex.", u"éd.", u"fig.", u"I.-P.-E.", u"J.-C.", 
    u"Ltee.", u"Ltée.", u"M.", u"Me.","Mlle.", u"Mlles.", u"MM.", u"N.-B.", u"N.-É.", u"p.", 
    u"S.B.E.", u"Ste.", u"T.-N.", u"t.a.b."
]

def tokenize(s, punctuation=PUNCTUATION, abbreviations=ABBREVIATIONS, replace=replacements):
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
    if pos.startswith(("DT","PR","WP")):
        return singularize(word, pos=pos)
    return word

def find_lemmata(tagged):
    for token in tagged:
        token.append(lemma(token[0].lower(), pos=len(token) > 1 and token[1] or None))
    return tagged

#### PARSER ########################################################################################

# pattern.en.find_tags() has an optional "lexicon" parameter.
# We'll pass the French lexicon to it instead of the default English lexicon:
lexicon = LEXICON = Lexicon()
lexicon.path = os.path.join(MODULE, "brill-lexicon.txt")
lexicon.lexical_rules.path = os.path.join(MODULE, "brill-lexical.txt")
lexicon.contextual_rules.path = os.path.join(MODULE, "brill-contextual.txt")
lexicon.named_entities.tag = "NNP"

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
       "language": "fr",
        "default": "NN",
            "map": None,
    })
    s = _en_parse(s, False, tags, chunks, relations, **kwargs)
    # Use pattern.fr.inflect for lemmatization:
    if lemmata:
        p = [find_lemmata(sentence) for sentence in s.split()]
        s = TaggedString(p, tags=s.tags+["lemma"], language="fr")
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
# python -m pattern.fr.parser xml -s "C'est l'exception qui confirme la règle." -OTCLI

if __name__ == "__main__":
    commandline(parse)