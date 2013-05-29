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

import os
import sys
import re

try:
    MODULE = os.path.dirname(os.path.abspath(__file__))
except:
    MODULE = ""
    
sys.path.insert(0, os.path.join(MODULE, "..", "..", "..", ".."))

from pattern.text import Verbs as _Verbs
from pattern.text import (
    INFINITIVE, PRESENT, PAST, FUTURE, CONDITIONAL,
    FIRST, SECOND, THIRD,
    SINGULAR, PLURAL, SG, PL,
    INDICATIVE, IMPERATIVE, SUBJUNCTIVE,
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
        if w == "du" : return "de"
        if w == "ces": return "ce"
        if w == "les": return "le"
        if w == "des": return "un"
        if w == "mes": return "mon"
        if w == "ses": return "son"
        if w == "tes": return "ton"
        if w == "nos": return "notre"
        if w == "vos": return "votre"
        if w.endswith(("'", u"’")):
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
    (u"issaient", u"ir"),   (u"eassions", u"er"),   (u"dissions", u"dre"), (u"çassions", u"cer"),
    (u"eraient", u"er"),    (u"assions", u"er"),    (u"issions", u"ir"),   (u"iraient", u"ir"),
    (u"isaient", u"ire"),   (u"geaient", u"ger"),   (u"eassent", u"er"),   (u"geasses", u"ger"),
    (u"eassiez", u"er"),    (u"dissiez", u"dre"),   (u"dissent", u"dre"),  (u"endrons", u"endre"),
    (u"endriez", u"endre"), (u"endrais", u"endre"), (u"erions", u"er"),    (u"assent", u"er"),
    (u"assiez", u"er"),     (u"raient", u"re"),     (u"issent", u"ir"),    (u"issiez", u"ir"),
    (u"irions", u"ir"),     (u"issons", u"ir"),     (u"issant", u"ir"),    (u"issait", u"ir"),
    (u"issais", u"ir"),     (u"aient", u"er"),      (u"èrent", u"er"),     (u"erait", u"er"),
    (u"eront", u"er"),      (u"erons", u"er"),      (u"eriez", u"er"),     (u"erais", u"er"),
    (u"asses", u"er"),      (u"rions", u"re"),      (u"isses", u"ir"),     (u"irent", u"ir"),
    (u"irait", u"ir"),      (u"irons", u"ir"),      (u"iriez", u"ir"),     (u"irais", u"ir"),
    (u"iront", u"ir"),      (u"issez", u"ir"),      (u"ions", u"er"),      (u"erez", u"er"),
    (u"eras", u"er"),       (u"erai", u"er"),       (u"asse", u"er"),      (u"âtes", u"er"),
    (u"âmes", u"er"),       (u"isse", u"ir"),       (u"îtes", u"ir"),      (u"îmes", u"ir"),
    (u"irez", u"ir"),       (u"iras", u"ir"),       (u"irai", u"ir"),      (u"ront", u"re"),
    (u"iez", u"er"),        (u"ent", u"er"),        (u"ais", u"er"),       (u"ons", u"er"),
    (u"ait", u"er"),        (u"ant", u"er"),        (u"era", u"er"),       (u"ira", u"ir"),
    (u"es", u"er"),         (u"ez", u"er"),         (u"as", u"er"),        (u"ai", u"er"),
    (u"ât", u"er"),         (u"is", u"ir"),         (u"it", u"ir"),        (u"ît", u"ir"),
    (u"ïr", u"ïr"),         (u"e", u"er"),          (u"é", u"er"),         (u"a", u"er"), 
    (u"t", u"re"),          (u"s", u"re"),          (u"i", u"ir"),         (u"u", u"re"),
    (u"d", u"dre"),         (u"z", u"ir"),          (u"l", u"lore"),       (u"x", u"oir"),
    (u"h", u"hoir"),        (u"ï", u"ïr"),          (u"o", u"oudre"),      (u"c", u"cre"),
    (u"g", u"ger"),         (u"b", u"ber"),         (u"û", u"ir")
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
        if v.endswith("ir") and not v.endswith(("couvrir", "cueillir", u"découvrir", "offrir", "ouvrir", "souffrir")):
            # Regular inflection for verbs ending in -ir.
            # Some -ir verbs drop the last letter of the stem: dormir => je dors (not: je dormis).
            if v.endswith(("dormir", "mentir", "partir", "sentir", "servir", "sortir")):
                b0 = b[:-1]
            else:
                b0 = b + "i"
            return [v, 
                b0+u"s", b0+u"s", b0+u"t", b+u"issons", b+u"issez", b+u"issent", b+u"issant", b+u"i",
                b+u"is", b+u"is", b+u"it", b+u"îmes", b+u"îtes", b+u"irent",
                b+u"issais", b+u"issais", b+u"issait", b+u"issions", b+u"issiez", b+u"issaient",
                v+u"ai", v+u"as", v+u"a", v+u"ons", v+u"ez", v+u"ont",            
                v+u"ais", v+u"ais", v+u"ait", v+u"ions", v+u"iez", v+u"aient",
                b+u"is", b+u"issons", b+u"issez",
                b+u"isse", b+u"isses", b+u"isse", b+u"issions", b+u"issiez", b+u"issent",
                b+u"isse", b+u"isses", b+u"ît", b+u"issions", b+u"issiez", b+u"issent"
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
                b0+u"s", b0+u"s", b0+u"", b1+u"ons", b1+u"ez", b1+u"ent", b1+u"ant", b+u"u",
                b+u"is", b+u"is", b+u"it", b1+u"îmes", b1+u"îtes", b1+u"irent",
                b+u"ais", b+u"ais", b+u"ait", b1+u"ions", b1+u"iez", b1+u"aient",
                b+u"rai", b+u"ras", b+u"ra", b+u"rons", b+u"rez", b+u"ront",            
                b+u"ais", b+u"ais", b+u"ait", b1+u"ions", b1+u"iez", b1+u"aient",
                b0+u"s", b1+u"ons", b1+u"ez",
                b+u"e", b+u"es", b+u"e", b1+u"ions", b1+u"iez", b1+u"ent",
                b+u"isse", b+u"isses", b+u"ît", b1+u"issions", b1+u"issiez", b1+u"issent"
            ]
        else:
            # Regular inflection for verbs ending in -er.
            # If the stem ends in -g, use -ge before hard vowels -a and -o: manger => mangeons.
            # If the stem ends in -c, use -ç before hard vowels -a and -o: lancer => lançons.
            e = v.endswith("ger") and u"e" or ""
            c = v.endswith("cer") and b[:-1]+u"ç" or b
            return [v, 
                b+u"e", b+u"es", b+u"e", c+e+u"ons", b+u"ez", b+u"ent", c+e+u"ant", b+u"é",
                c+e+u"ai", c+e+u"as", c+e+u"a", c+e+u"âmes", c+e+u"âtes", b+u"èrent",
                c+e+u"ais", c+e+u"ais", c+e+u"ait", b+u"ions", b+u"iez", c+e+u"aient",
                v+u"ai", v+u"as", v+u"a", v+u"ons", v+u"ez", v+u"ont",            
                v+u"ais", v+u"ais", v+u"ait", v+u"ions", v+u"iez", v+u"aient",
                b+u"e", c+e+u"ons", b+u"ez",
                b+u"e", b+u"es", b+u"e", b+u"ions", b+u"iez", b+u"ent",
                c+e+u"asse", c+e+u"asses", c+e+u"ât", c+e+u"assions", c+e+u"assiez", c+e+u"assent"
            ]

verbs = Verbs()

conjugate, lemma, lexeme, tenses = \
    verbs.conjugate, verbs.lemma, verbs.lexeme, verbs.tenses

#### ATTRIBUTIVE & PREDICATIVE #####################################################################

def attributive(adjective):
    # Must deal with feminine and plural.
    raise NotImplementedError

def predicative(adjective): 
    """ Returns the predicative adjective (lowercase): belles => beau.
    """
    w = adjective.lower()
    if w.endswith(("ais", "ois")):
        return w
    if w.endswith((u"és", u"ée", u"ées")):
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
    if w.endswith((u"ène", u"ènes")):
        return w.rstrip("s")
    if w.endswith(("ns", "ne", "nes")):
        return w.rstrip("es")
    if w.endswith(("ite", "ites")):
        return w.rstrip("es")
    if w.endswith(("is", "ise", "ises")):
        return w.rstrip("es") + "s"
    if w.endswith(("rice", "rices")):
        return w.rstrip("rices") + "eur"
    if w.endswith(("iers", u"ière", u"ières")):
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