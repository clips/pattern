#### PATTERN | DE | RULE-BASED SHALLOW PARSER ######################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 Gerold Schneider, Martin Volk and University of Antwerp, Belgium
# Authors: Gerold Schneider & Martin Volk (German language model), Tom De Smedt <tom@organisms.be>
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
# The tagger is based on Schneider & Volk's German language model:
# Schneider, G., Volk, M. (1998). Adding Manual Constraints and Lexical Look-up to a Brill-Tagger for German.
# In: Proceedings of the ESSLLI workshop on recent advances in corpus annotation. Saarbrucken, Germany.
# http://www.zora.uzh.ch/28579/
# Accuracy is reported around 96%, but Pattern scores may vary from Schneider & Volk's original
# due to STTS => Penn Treebank mapping etc.
import sys; sys.path.insert(0, os.path.join(MODULE, "..", ".."))
from en.parser import Lexicon
from en.parser import PUNCTUATION, tokenize as _en_tokenize, parse as _en_parse, TaggedString
from en.parser import commandline

#### TOKENIZER #####################################################################################

ABBREVIATIONS = [
    "Abs.", "Abt.", "Ass.", "Br.", "Ch.", "Chr.", "Cie.", "Co.", "Dept.", "Diff.", 
    "Dr.", "Eidg.", "Exp.", "Fam.", "Fr.", "Hrsg.", "Inc.", "Inv.", "Jh.", "Jt.", "Kt.", 
    "Mio.", "Mrd.", "Mt.", "Mte.", "Nr.", "Nrn.", "Ord.", "Ph.", "Phil.", "Pkt.", 
    "Prof.", "Pt.", " S.", "St.", "Stv.", "Tit.", "VII.", "al.", "begr.","bzw.", 
    "chem.", "dent.", "dipl.", "e.g.", "ehem.", "etc.", "excl.", "exkl.", "hum.", 
    "i.e.", "incl.", "ing.", "inkl.", "int.", "iur.", "lic.", "med.", "no.", "oec.", 
    "phil.", "phys.", "pp.", "psych.", "publ.", "rer.", "sc.", "soz.", "spez.", "stud.", 
    "theol.", "usw.", "vet.", "vgl.", "vol.", "wiss.",
    "d.h.", "h.c.", u"o.ä.", "u.a.", "z.B.", "z.T.", "z.Zt."
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
            from pattern.de.inflect import singularize, conjugate, predicative 
        except:
            singularize = lambda w: w
            conjugate   = lambda w, t: w
            predicative = lambda w: w

def lemma(word, pos="NN"):
    if pos == "NNS":
        return singularize(word)
    if pos.startswith(("VB","MD")):
        return conjugate(word, "infinitive") or word
    if pos.startswith(("DT", "JJ")):
        return predicative(word)
    return word

def find_lemmata(tagged):
    for token in tagged:
        token.append(lemma(token[0].lower(), pos=len(token) > 1 and token[1] or None))
    return tagged

#### PARSER ########################################################################################

# pattern.en.find_tags() has an optional "lexicon" parameter.
# We'll pass the German lexicon to it instead of the default English lexicon:
lexicon = LEXICON = Lexicon()
lexicon.path = os.path.join(MODULE, "brill-lexicon.txt")
lexicon.lexical_rules.path = os.path.join(MODULE, "brill-lexical.txt")
lexicon.contextual_rules.path = os.path.join(MODULE, "brill-contextual.txt")
lexicon.named_entities.tag = "NE"

# Stuttgart/Tubinger Tagset (STTS):
# https://files.ifi.uzh.ch/cl/tagger/UIS-STTS-Diffs.html
PENN = PENNTREEBANK = TREEBANK = "penntreebank"
STTS = "stts"
stts = {
     "ADJA": "JJ",   # das große Haus
     "ADJD": "JJ",   # er ist schnell
      "ADV": "RB",   # schon
     "APPR": "IN",   # in der Stadt
  "APPRART": "IN",   # im Haus
     "APPO": "IN",   # der Sache wegen
     "APZR": "IN",   # von jetzt an
      "ART": "DT",   # der, die, eine
   "ARTDEF": "DT",   # der, die
   "ARTIND": "DT",   # eine
     "CARD": "CD",   # zwei
  "CARDNUM": "CD",   # 3
     "KOUI": "IN",   # [um] zu leben
     "KOUS": "IN",   # weil, damit, ob
      "KON": "CC",   # und, oder, aber
    "KOKOM": "IN",   # als, wie
     "KONS": "IN",   # usw.
       "NN": "NN",   # Tisch, Herr
      "NNS": "NNS",  # Tischen, Herren
       "NE": "NNP",  # Hans, Hamburg
      "PDS": "DT",   # dieser, jener
     "PDAT": "DT",   # jener Mensch
      "PIS": "DT",   # keiner, viele, niemand
     "PIAT": "DT",   # kein Mensch
    "PIDAT": "DT",   # die beiden Brüder
     "PPER": "PRP",  # ich, er, ihm, mich, dir
     "PPOS": "PRP$", # meins, deiner
   "PPOSAT": "PRP$", # mein Buch, deine Mutter
    "PRELS": "WDT",  # der Hund, [der] bellt
   "PRELAT": "WDT",  # der Mann, [dessen] Hund bellt
      "PRF": "PRP",  # erinnere [dich]
      "PWS": "WP",   # wer
     "PWAT": "WP",   # wessen, welche
     "PWAV": "WRB",  # warum, wo, wann
      "PAV": "RB",   # dafur, dabei, deswegen, trotzdem
    "PTKZU": "TO",   # zu gehen, zu sein
   "PTKNEG": "RB",   # nicht
    "PTKVZ": "RP",   # pass [auf]!
   "PTKANT": "UH",   # ja, nein, danke, bitte
     "PTKA": "RB",   # am schönsten, zu schnell 
    "VVFIN": "VB",   # du [gehst], wir [kommen] an
    "VAFIN": "VB",   # du [bist], wir [werden]
    "VVINF": "VB",   # gehen, ankommen
    "VAINF": "VB",   # werden, sein
    "VVIZU": "VB",   # anzukommen
    "VVIMP": "VB",   # [komm]!
    "VAIMP": "VB",   # [sei] ruhig!
     "VVPP": "VBN",  # gegangen, angekommen
     "VAPP": "VBN",  # gewesen
    "VMFIN": "MD",   # dürfen
    "VMINF": "MD",   # wollen
     "VMPP": "MD",   # gekonnt
     "SGML": "SYM",  #
       "FM": "FW",   #
      "ITJ": "UH",   # ach, tja
       "XY": "NN",   #
       "XX": "NN",   #
    "LINUM": "LS",   # 1.
        "C": ",",    # ,
       "Co": ":",    # :
       "Ex": ".",    # ! 
       "Pc": ")",    # )
       "Po": "(",    # (
        "Q": ".",    # ?
      "QMc": "\"",   # "
      "QMo": "\"",   # "
        "S": ".",    # .
       "Se": ":",    # ;
}

def stts2penntreebank(tag):
    """ Converts an STTS tag to Penn Treebank II tag.
        For example: ohne APPR => ohne/IN
    """
    return stts.get(tag, tag)

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
       "language": "de",
        "default": "NN",
            "map": kwargs.get("tagset", "") != STTS and stts2penntreebank or None,
    })
    # The German lexicon uses "ss" instead of "ß".
    # Instead of simply replacing it, we keep a hash map of the normalized words.
    # After parsing we restore the "ß" so the output stays identical to the input.
    m = dict((token.replace(u"ß", "ss"), token) for sentence in s for token in sentence)
    s = [[token.replace(u"ß", "ss") for token in sentence] for sentence in s]
    s = _en_parse(s, False, tags, chunks, relations, **kwargs)
    p = [[[m[token[0]]] + token[1:] for token in sentence] for sentence in s.split()]
    p = "\n".join([" ".join(["/".join(token) for token in sentence]) for sentence in p])
    s = TaggedString(p, tags=s.tags, language="de")
    # Use pattern.de.inflect for lemmatization:
    if lemmata:
        p = [find_lemmata(sentence) for sentence in s.split()]
        p = "\n".join([" ".join(["/".join(token) for token in sentence]) for sentence in p])
        s = TaggedString(p, tags=s.tags+["lemma"], language="de")
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
# python -m pattern.de.parser xml -s "Ein Unglück kommt selten allein." -OTCLI

if __name__ == "__main__":
    commandline(parse)