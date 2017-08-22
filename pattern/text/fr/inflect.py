#### PATTERN | FR | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2013 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# Regular expressions-based rules for French word inflection:
# - pluralization and singularization of nouns,
# - conjugation of verbs,
# - predicative and attributive of adjectives.

# Accuracy:
# 92% for pluralize()
# 93% for singularize()
# 80% for Verbs.find_lemma() (mixed regular/irregular)
# 86% for Verbs.find_lexeme() (mixed regular/irregular)
# 95% predicative() (measured on Lexique French morphology word forms)

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

from pattern.text import Verbs as _Verbs
from pattern.text import (
    INFINITIVE, PRESENT, PAST, FUTURE,
    FIRST, SECOND, THIRD,
    SINGULAR, PLURAL, SG, PL,
    INDICATIVE, IMPERATIVE, SUBJUNCTIVE, CONDITIONAL,
    IMPERFECTIVE, PERFECTIVE, PROGRESSIVE,
    IMPERFECT, PRETERITE,
    PARTICIPLE, GERUND
)

sys.path.pop(0)

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"

VOWELS = ("a", "e", "i", "o", "u")
re_vowel = re.compile(r"a|e|i|o|u", re.I)
is_vowel = lambda ch: ch in VOWELS

#### PLURALIZE #####################################################################################

plural_irregular = {
       "bleu": "bleus",
       "pneu": "pneus",
    "travail": "travaux",
    "vitrail": "vitraux"
}


def pluralize(word, pos=NOUN, custom={}):
    """ Returns the plural of a given word.
        The custom dictionary is for user-defined replacements.
    """
    if word in custom:
        return custom[word]
    w = word.lower()
    if w in plural_irregular:
        return plural_irregular[w]
    if w.endswith(("ais", "ois")):
        return w + "es"
    if w.endswith(("s", "x")):
        return w
    if w.endswith("al"):
        return w[:-2] + "aux"
    if w.endswith(("au", "eu")):
        return w + "x"
    return w + "s"

#### SINGULARIZE ###################################################################################


def singularize(word, pos=NOUN, custom={}):
    if word in custom:
        return custom[word]
    w = word.lower()
    # Common articles, determiners, pronouns:
    if pos in ("DT", "PRP", "PRP$", "WP", "RB", "IN"):
        if w == "du":
            return "de"
        if w == "ces":
            return "ce"
        if w == "les":
            return "le"
        if w == "des":
            return "un"
        if w == "mes":
            return "mon"
        if w == "ses":
            return "son"
        if w == "tes":
            return "ton"
        if w == "nos":
            return "notre"
        if w == "vos":
            return "votre"
        if w.endswith(("'", "’")):
            return w[:-1] + "e"
    if w.endswith("nnes"):  # parisiennes => parisien
        return w[:-3]
    if w.endswith("ntes"):  # passantes => passant
        return w[:-2]
    if w.endswith("euses"): # danseuses => danseur
        return w[:-3] + "r"
    if w.endswith("s"):
        return w[:-1]
    if w.endswith(("aux", "eux", "oux")):
        return w[:-1]
    if w.endswith("ii"):
        return w[:-1] + "o"
    if w.endswith(("ia", "ma")):
        return w[:-1] + "um"
    if "-" in w:
        return singularize(w.split("-")[0]) + "-" + "-".join(w.split("-")[1:])
    return w

#### VERB CONJUGATION ##############################################################################

verb_inflections = [
    ("issaient", "ir"   ), ("eassions", "er"   ), ("dissions", "dre" ), ("çassions", "cer"  ),
    ( "eraient", "er"   ), ( "assions", "er"   ), ( "issions", "ir"  ), (  "iraient", "ir"   ),
    ( "isaient", "ire"  ), ( "geaient", "ger"  ), ( "eassent", "er"  ), (  "geasses", "ger"  ),
    ( "eassiez", "er"   ), ( "dissiez", "dre"  ), ( "dissent", "dre" ), (  "endrons", "endre"),
    ( "endriez", "endre"), ( "endrais", "endre"), (  "erions", "er"  ), (   "assent", "er"   ),
    (  "assiez", "er"   ), (  "raient", "re"   ), (  "issent", "ir"  ), (   "issiez", "ir"   ),
    (  "irions", "ir"   ), (  "issons", "ir"   ), (  "issant", "ir"  ), (   "issait", "ir"   ),
    (  "issais", "ir"   ), (   "aient", "er"   ), (  "èrent", "er"  ), (    "erait", "er"   ),
    (   "eront", "er"   ), (   "erons", "er"   ), (   "eriez", "er"  ), (    "erais", "er"   ),
    (   "asses", "er"   ), (   "rions", "re"   ), (   "isses", "ir"  ), (    "irent", "ir"   ),
    (   "irait", "ir"   ), (   "irons", "ir"   ), (   "iriez", "ir"  ), (    "irais", "ir"   ),
    (   "iront", "ir"   ), (   "issez", "ir"   ), (    "ions", "er"  ), (     "erez", "er"   ),
    (    "eras", "er"   ), (    "erai", "er"   ), (    "asse", "er"  ), (     "âtes", "er"   ),
    (    "âmes", "er"   ), (    "isse", "ir"   ), (    "îtes", "ir"  ), (     "îmes", "ir"   ),
    (    "irez", "ir"   ), (    "iras", "ir"   ), (    "irai", "ir"  ), (     "ront", "re"   ),
    (     "iez", "er"   ), (     "ent", "er"   ), (     "ais", "er"  ), (      "ons", "er"   ),
    (     "ait", "er"   ), (     "ant", "er"   ), (     "era", "er"  ), (      "ira", "ir"   ),
    (      "es", "er"   ), (      "ez", "er"   ), (      "as", "er"  ), (       "ai", "er"   ),
    (      "ât", "er"   ), (      "ds", "dre"  ), (      "is", "ir"  ), (       "it", "ir"   ),
    (      "ît", "ir"   ), (      "ïr", "ïr"   ), (      "nd", "ndre"), (       "nu", "nir"  ),
    (       "e", "er"   ), (       "é", "er"   ), (       "a", "er"  ), (        "t", "re"   ),
    (       "s", "re"   ), (       "i", "ir"   ), (       "û", "ir"  ), (        "u", "re"   ),
    (       "d", "dre"  )
]


class Verbs(_Verbs):

    def __init__(self):
        _Verbs.__init__(self, os.path.join(MODULE, "fr-verbs.txt"),
            language = "fr",
             default = {},
              format = [
                0, 1, 2, 3, 4, 5, 6, 8, 24, # indicatif présent
                34, 35, 36, 37, 38, 39,     # indicatif passé simple
                17, 18, 19, 20, 21, 22,     # indicatif imparfait
                40, 41, 42, 43, 44, 45,     # indicatif futur simple
                46, 47, 48, 49, 50, 51,     # conditionnel présent
                52, 53, 54,                 # impératif présent
                55, 56, 57, 58, 59, 60,     # subjonctif présent
                67, 68, 69, 70, 71, 72      # subjonctif imparfait
            ])

    def find_lemma(self, verb):
        """ Returns the base form of the given inflected verb, using a rule-based approach.
        """
        # French has 20,000+ verbs, ending in -er (majority), -ir, -re.
        v = verb.lower()
        if v.endswith(("er", "ir", "re")):
            return v
        for a, b in verb_inflections:
            if v.endswith(a):
                return v[:-len(a)] + b
        return v

    def find_lexeme(self, verb):
        """ For a regular verb (base form), returns the forms using a rule-based approach.
        """
        v = verb.lower()
        b = v[:-2]
        if v.endswith("ir") and not \
           v.endswith(("couvrir", "cueillir", "découvrir", "offrir", "ouvrir", "souffrir")):
            # Regular inflection for verbs ending in -ir.
            # Some -ir verbs drop the last letter of the stem: dormir => je dors (not: je dormis).
            if v.endswith(("dormir", "mentir", "partir", "sentir", "servir", "sortir")):
                b0 = b[:-1]
            else:
                b0 = b + "i"
            return [v,
                b0 + "s", b0 + "s", b0 + "t", b + "issons", b + "issez", b + "issent", b + "issant", b + "i",
                b + "is", b + "is", b + "it", b + "îmes", b + "îtes", b + "irent",
                b + "issais", b + "issais", b + "issait", b + "issions", b + "issiez", b + "issaient",
                v + "ai", v + "as", v + "a", v + "ons", v + "ez", v + "ont",
                v + "ais", v + "ais", v + "ait", v + "ions", v + "iez", v + "aient",
                b + "is", b + "issons", b + "issez",
                b + "isse", b + "isses", b + "isse", b + "issions", b + "issiez", b + "issent",
                b + "isse", b + "isses", b + "ît", b + "issions", b + "issiez", b + "issent"
            ]
        elif v.endswith("re"):
            # Regular inflection for verbs ending in -re.
            # Verbs ending in -attre and -ettre drop the -t in the singular form.
            if v.endswith(("ttre")):
                b0 = b1 = b[:-1]
            else:
                b0 = b1 = b
            # Verbs ending in -aindre, -eindre and -oindre drop the -d.
            if v.endswith("indre"):
                b0, b1 = b[:-1], b[:-2] + "gn"
            # Verbs ending in -prendre drop the -d in the plural form.
            if v.endswith("prendre"):
                b0, b1 = b, b[:-1]
            return [v,
                b0 + "s", b0 + "s", b0 + "", b1 + "ons", b1 + "ez", b1 + "ent", b1 + "ant", b + "u",
                b + "is", b + "is", b + "it", b1 + "îmes", b1 + "îtes", b1 + "irent",
                b + "ais", b + "ais", b + "ait", b1 + "ions", b1 + "iez", b1 + "aient",
                b + "rai", b + "ras", b + "ra", b + "rons", b + "rez", b + "ront",
                b + "ais", b + "ais", b + "ait", b1 + "ions", b1 + "iez", b1 + "aient",
                b0 + "s", b1 + "ons", b1 + "ez",
                b + "e", b + "es", b + "e", b1 + "ions", b1 + "iez", b1 + "ent",
                b + "isse", b + "isses", b + "ît", b1 + "issions", b1 + "issiez", b1 + "issent"
            ]
        else:
            # Regular inflection for verbs ending in -er.
            # If the stem ends in -g, use -ge before hard vowels -a and -o: manger => mangeons.
            # If the stem ends in -c, use -ç before hard vowels -a and -o: lancer => lançons.
            e = v.endswith("ger") and "e" or ""
            c = v.endswith("cer") and b[:-1] + "ç" or b
            return [v,
                b + "e", b + "es", b + "e", c + e + "ons", b + "ez", b + "ent", c + e + "ant", b + "é",
                c + e + "ai", c + e + "as", c + e + "a", c + e + "âmes", c + e + "âtes", b + "èrent",
                c + e + "ais", c + e + "ais", c + e + "ait", b + "ions", b + "iez", c + e + "aient",
                v + "ai", v + "as", v + "a", v + "ons", v + "ez", v + "ont",
                v + "ais", v + "ais", v + "ait", v + "ions", v + "iez", v + "aient",
                b + "e", c + e + "ons", b + "ez",
                b + "e", b + "es", b + "e", b + "ions", b + "iez", b + "ent",
                c + e + "asse", c + e + "asses", c + e + "ât", c + e + "assions", c + e + "assiez", c + e + "assent"
            ]

verbs = Verbs()

conjugate, lemma, lexeme, tenses = \
    verbs.conjugate, verbs.lemma, verbs.lexeme, verbs.tenses

#### ATTRIBUTIVE & PREDICATIVE #####################################################################


def attributive(adjective):
    """ For a predicative adjective, returns the attributive form.
    """
    # Must deal with feminine and plural.
    raise NotImplementedError


def predicative(adjective):
    """ Returns the predicative adjective (lowercase): belles => beau.
    """
    w = adjective.lower()
    if w.endswith(("ais", "ois")):
        return w
    if w.endswith(("és", "ée", "ées")):
        return w.rstrip("es")
    if w.endswith(("que", "ques")):
        return w.rstrip("s")
    if w.endswith(("nts", "nte", "ntes")):
        return w.rstrip("es")
    if w.endswith("eaux"):
        return w.rstrip("x")
    if w.endswith(("aux", "ale", "ales")):
        return w.rstrip("uxles") + "l"
    if w.endswith(("rteuse", "rteuses", "ailleuse")):
        return w.rstrip("es") + "r"
    if w.endswith(("euse", "euses")):
        return w.rstrip("es") + "x"
    if w.endswith(("els", "elle", "elles")):
        return w.rstrip("les") + "el"
    if w.endswith(("ifs", "ive", "ives")):
        return w.rstrip("es")[:-2] + "if"
    if w.endswith(("is", "ie", "ies")):
        return w.rstrip("es")
    if w.endswith(("enne", "ennes")):
        return w.rstrip("nes") + "en"
    if w.endswith(("onne", "onnes")):
        return w.rstrip("nes") + "n"
    if w.endswith(("igne", "ignes", "ingue", "ingues")):
        return w.rstrip("s")
    if w.endswith(("ène", "ènes")):
        return w.rstrip("s")
    if w.endswith(("ns", "ne", "nes")):
        return w.rstrip("es")
    if w.endswith(("ite", "ites")):
        return w.rstrip("es")
    if w.endswith(("is", "ise", "ises")):
        return w.rstrip("es") + "s"
    if w.endswith(("rice", "rices")):
        return w.rstrip("rices") + "eur"
    if w.endswith(("iers", "ière", "ières")):
        return w.rstrip("es")[:-3] + "ier"
    if w.endswith(("ette", "ettes")):
        return w.rstrip("tes") + "et"
    if w.endswith(("rds", "rde", "rdes")):
        return w.rstrip("es")
    if w.endswith(("nds", "nde", "ndes")):
        return w.rstrip("es")
    if w.endswith(("us", "ue", "ues")):
        return w.rstrip("es")
    return w.rstrip("s")
