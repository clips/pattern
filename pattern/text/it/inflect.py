#### PATTERN | IT | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2013 University of Antwerp, Belgium
# Copyright (c) 2013 St. Lucas University College of Art & Design, Antwerp.
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# Regular expressions-based rules for Italian word inflection:
# - pluralization and singularization of nouns,
# - conjugation of verbs,
# - predicative adjectives.

# Accuracy:
# 92% for gender()
# 93% for pluralize()
# 84% for singularize()
# 82% for Verbs.find_lemma()
# 90% for Verbs.find_lexeme()
# 88% for predicative()

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

# Import Verbs base class and verb tenses.
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

VOWELS = "aeiouy"
re_vowel = re.compile(r"a|e|i|o|u|y", re.I)
is_vowel = lambda ch: ch in VOWELS

#### ARTICLE #######################################################################################

# Inflection gender.
MASCULINE, FEMININE, NEUTER, PLURAL = \
    MALE, FEMALE, NEUTRAL, PLURAL = \
        M, F, N, PL = "m", "f", "n", "p"

# Word starts with z or s + consonant?
zs = lambda w: w and (w[:1] == "z" or (w[:1] == "s" and not is_vowel(w[1:2])))


def definite_article(word, gender=MALE):
    """ Returns the definite article for a given word.
    """
    if PLURAL in gender and MALE in gender and (is_vowel(word[:1]) or zs(word)):
        return "gli"
    if PLURAL not in gender and word and is_vowel(word[:1]):
        return "l'"
    if PLURAL not in gender and MALE in gender and zs(word):
        return "lo"
    if MALE in gender:
        return PLURAL in gender and "i" or "il"
    if FEMALE in gender:
        return PLURAL in gender and "le" or "la"
    return "il"


def indefinite_article(word, gender=MALE):
    """ Returns the indefinite article for a given word.
    """
    if MALE in gender and zs(word):
        return PLURAL in gender and "degli" or "uno"
    if MALE in gender:
        return PLURAL in gender and "dei" or "un"
    if FEMALE in gender and is_vowel(word[:1]):
        return PLURAL in gender and "delle" or "un'"
    if FEMALE in gender:
        return PLURAL in gender and "delle" or "una"
    return "un"

DEFINITE, INDEFINITE = \
    "definite", "indefinite"


def article(word, function=INDEFINITE, gender=MALE):
    """ Returns the indefinite or definite article for the given word.
    """
    return function == DEFINITE \
       and definite_article(word, gender) \
        or indefinite_article(word, gender)

_article = article


def referenced(word, article=INDEFINITE, gender=MALE):
    """ Returns a string with the article + the word.
    """
    s = "%s&space;%s" % (_article(word, article, gender), word)
    s = s.replace("'&space;", "'")
    s = s.replace("&space;", " ")
    return s

#### GENDER #########################################################################################


def gender(word):
    """ Returns the gender for the given word, either:
        MALE, FEMALE, (MALE, FEMALE), (MALE, PLURAL) or (FEMALE, PLURAL).
    """
    w = word.lower()
    # Adjectives ending in -e: cruciale, difficile, ...
    if w.endswith(("ale", "ile", "ese", "nte")):
        return (MALE, FEMALE)
    # Most nouns ending in -a (-e) are feminine, -o (-i) masculine:
    if w.endswith(("ore", "ista", "mma")):
        return MALE
    if w.endswith(("a", "tà", "tù", "ione", "rice")):
        return FEMALE
    if w.endswith(("e", "oni")):
        return (FEMALE, PLURAL)
    if w.endswith("i"):
        return (MALE, PLURAL)
    if w.endswith("o"):
        return MALE
    return MALE

#### PLURALIZE ######################################################################################

plural_co_chi = set((
    "abbaco", "baco", "cuoco", "fungo", "rammarico", "strascio", "valico" # ...
))

plural_go_ghi = set((
    "albergo", "catalogo", "chirurgo", "dialogo", "manico", "monologo", "stomaco" # ...
))

plural_irregular = {
    "braccio": "braccia", # bracci (arms of a lamp or cross)
    "budello": "budelli", # budella (intestines)
    "camicia": "camicie",
        "bue": "buoi",
        "dio": "dei",
       "dito": "dita",
     "doccia": "docce",
     "inizio": "inizi",
     "labbro": "labbra", # labbri (borders)
       "mano": "mani",
    "negozio": "negozi",
       "osso": "ossa", # ossi (dog bones)
       "uomo": "uomini",
       "uovo": "uova"
}


def pluralize(word, pos=NOUN, custom={}):
    """ Returns the plural of a given word.
    """
    if word in custom:
        return custom[word]
    w = word.lower()
    if len(w) < 3:
        return w
    if w in plural_irregular:
        return plural_irregular[w]
    # provincia => province (but: socia => socie)
    if w.endswith(("cia", "gia")) and len(w) > 4 and not is_vowel(w[-4]):
        return w[:-2] + "e"
    # amica => amiche
    if w.endswith(("ca", "ga")):
        return w[:-2] + "he"
    # studentessa => studentesse
    if w.endswith("a"):
        return w[:-1] + "e"
    # studente => studenti
    if w.endswith("e"):
        return w[:-1] + "i"
    # viaggio => viaggi (but: leggìo => leggìi)
    if w.endswith("io"):
        return w[:-2] + "i"
    # abbaco => abbachi
    if w in plural_co_chi:
        return w[:-2] + "chi"
    # albergo => alberghi
    if w in plural_co_chi:
        return w[:-2] + "ghi"
    # amico => amici
    if w.endswith("o"):
        return w[:-1] + "i"
    return w

#### SINGULARIZE ###################################################################################

singular_majority_vote = [
    ("tenti", "tente"), ("anti", "ante"), ( "oni", "one" ), ( "nti", "nto" ),
    (  "ali", "ale"  ), ( "ici", "ico" ), ( "nze", "nza" ), ( "ori", "ore" ),
    (  "che", "ca"   ), ( "ati", "ato" ), ( "ari", "ario"), ( "tti", "tto" ),
    (  "eri", "ero"  ), ( "chi", "co"  ), ( "ani", "ano" ), ( "ure", "ura" ),
    (  "ità", "ità"  ), ( "ivi", "ivo" ), ( "ini", "ino" ), ( "iti", "ito" ),
    (  "emi", "ema"  ), ( "ili", "ile" ), ( "oli", "olo" ), ( "esi", "ese" ),
    (  "ate", "ata"  ), ( "ssi", "sso" ), ( "rie", "ria" ), ( "ine", "ina" ),
    (  "lli", "llo"  ), ( "ggi", "ggio"), ( "tri", "tro" ), ( "imi", "imo" )
]

singular_irregular = dict((v, k) for k, v in plural_irregular.items())


def singularize(word, pos=NOUN, custom={}):
    """ Returns the singular of a given word.
    """
    if word in custom:
        return custom[word]
    w = word.lower()
    # il gatti => il gatto
    if pos == "DT":
        if w in ("i", "gli"):
            return "il"
        if w == "el":
            return "la"
        return w
    if len(w) < 3:
        return w
    if w in singular_irregular:
        return singular_irregular[w]
    # Ruleset adds 16% accuracy.
    for a, b in singular_majority_vote:
        if w.endswith(a):
            return w[:-len(a)] + b
    # Probably an adjective ending in -e: cruciale, difficile, ...
    if w.endswith(("ali", "ari", "ili", "esi", "nti")):
        return w[:-1] + "e"
    # realisti => realista
    if w.endswith("isti"):
        return w[:-1] + "a"
    # amiche => amica
    if w.endswith(("che", "ghe")):
        return w[:-2] + "a"
    # alberghi => albergo
    if w.endswith(("chi", "ghi")):
        return w[:-2] + "o"
    # problemi => problema
    if w.endswith("emi"):
        return w[:-1] + "a"
    # case => case
    if w.endswith("e"):
        return w[:-1] + "a"
    # Ambigious: both -o and -a pluralize to -i.
    if w.endswith("i"):
        return w[:-1] + "o"
    return w

#### VERB CONJUGATION ##############################################################################
# The verb table was trained on Wiktionary and contains the top 1,250 frequent verbs.

verb_majority_vote = [
    ("iresti", "ire" ), ("ireste", "ire" ), ("iremmo", "ire" ), ("irebbe", "ire" ),
    ("iranno", "ire" ), ( "ssero", "re"  ), ( "ssimo", "re"  ), ( "ivate", "ire" ),
    ( "ivamo", "ire" ), ( "irete", "ire" ), ( "iremo", "ire" ), ( "irono", "ire" ),
    ( "scano", "re"  ), ( "hiamo", "are" ), ( "scono", "re"  ), ( "hiate", "are" ),
    (  "vano", "re"  ), (  "vate", "re"  ), (  "vamo", "re"  ), (  "simo", "e"   ),
    (  "rono", "re"  ), (  "isse", "ire" ), (  "isti", "ire" ), (  "tino", "tare"),
    (  "tato", "tare"), (  "irai", "ire" ), (  "tavo", "tare"), (  "tavi", "tare"),
    (  "tava", "tare"), (  "tate", "tare"), (  "iste", "ire" ), (  "irei", "ire" ),
    (  "immo", "ire" ), (  "rerò", "rare"), (  "rerà", "rare"), (  "iavo", "iare"),
    (  "iavi", "iare"), (  "iava", "iare"), (  "iato", "iare"), (  "iare", "iare"),
    (  "hino", "are" ), (   "ssi", "re"  ), (   "sse", "re"  ), (   "ndo", "re"  ),
    (   "irò", "ire" ), (   "tai", "tare"), (   "ite", "ire" ), (   "irà", "ire" ),
    (   "sco", "re"  ), (   "sca", "re"  ), (   "iai", "iare"), (    "ii", "ire" ),
    (    "hi", "are" )
]


class Verbs(_Verbs):

    def __init__(self):
        _Verbs.__init__(self, os.path.join(MODULE, "it-verbs.txt"),
            language = "it",
             default = {},
              format = [
                0, 1, 2, 3, 4, 5, 6, 8,     # indicativo presente
                34, 35, 36, 37, 38, 39, 24, # indicativo passato remoto
                17, 18, 19, 20, 21, 22,     # indicativo imperfetto
                40, 41, 42, 43, 44, 45,     # indicativo futuro semplice
                46, 47, 48, 49, 50, 51,     # condizionale presente
                    52, 521, 53, 54, 541,    # imperativo
                55, 56, 57, 58, 59, 60,     # congiuntivo presente
                67, 68, 69, 70, 71, 72      # congiontive imperfetto
            ])

    def find_lemma(self, verb):
        """ Returns the base form of the given inflected verb, using a rule-based approach.
        """
        v = verb.lower()
        # Probably infinitive if ends in -are, -ere, -ire or reflexive -rsi.
        if v.endswith(("are", "ere", "ire", "rsi")):
            return v
        # Ruleset adds 3% accuracy.
        for a, b in verb_majority_vote:
            if v.endswith(a):
                return v[:-len(a)] + b
        v = v.replace("cha", "ca")
        v = v.replace("che", "ce")
        v = v.replace("gha", "ga")
        v = v.replace("ghe", "ge")
        v = v.replace("ghi", "gi")
        v = v.replace("gge", "ggie")
        # Many verbs end in -ire and have a regular inflection:
        for x in ((
          "irò", "irai", "irà", "iremo", "irete", "iranno",           # future
          "irei", "iresti", "irebbe", "iremmo", "ireste", "irebbero", # conditional
          "ascano",                                                   # subjunctive I
          "issi", "isse", "issimo", "iste", "issero",                 # subjunctive II
          "ivo", "ivi", "iva", "ivamo", "ivate", "ivano",             # past imperfective
          "isti", "immo", "iste", "irono", "ito",                     # past perfective
          "isco", "isci", "isce", "ite", "iscono", "indo")):          # present
            if v.endswith(x):
                return v[:-len(x)] + "ire"
        # Many verbs end in -are and have a regular inflection:
        for x in ((
          "erò", "erai", "erà", "eremo", "erete", "eranno",           # future
          "erei", "eresti", "erebbe", "eremmo", "ereste", "erebbero", # conditional
          "iamo", "iate", "ino",                                      # subjunctive I
          "assi", "asse", "assimo", "aste", "assero",                 # subjunctive II
          "avo", "avi", "ava", "avamo", "avate", "avano",             # past imperfective
          "ai", "asti", "ò", "ammo", "aste", "arono", "ato",          # past perfective
          "iamo", "ate", "ano", "ando")):                             # present
            if v.endswith(x):
                return v[:-len(x)] + "are"
        # Many verbs end in -ere and have a regular inflection:
        for x in ((
          "essi", "esse", "essimo", "este", "essero",                 # subjunctive II
          "evo", "evi", "eva", "evamo", "evate", "evano",             # past imperfective
          "ei", "esti", "è", "emmo", "este", "erono", "eto",          # past perfective
          "ete", "ono", "endo")):                                     # present
            if v.endswith(x):
                return v[:-len(x)] + "ere"
        if v.endswith("à"):
            return v[:-1] + "e"
        if v.endswith("ì"):
            return v[:-1] + "ire"
        if v.endswith("e"):
            return v[:-1] + "ere"
        if v.endswith(("a", "i", "o")):
            return v[:-1] + "are"
        return v

    def find_lexeme(self, verb):
        """ For a regular verb (base form), returns the forms using a rule-based approach.
        """
        v = verb.lower()
        v = re.sub(r"rci$", "re", v)
        v = re.sub(r"rsi$", "re", v)
        v = re.sub(r"rre$", "re", v)
        b = v[:-3]
        if verb.endswith(("care", "gare")):
            b += "h"   # moltiplicare => tu moltiplichi
        if verb.endswith(("ciare", "giare")):
            b = b[:-1] # cominciare => tu cominci
        if v.endswith("are"):
            # -are = 1st conjugation
            a1, a2, a3, a4, a5, a6, a7 = "a", "a", "ò", "a", "i", "e", "a"
        elif v.endswith("ere"):
            # -ere = 2nd conjugation
            a1, a2, a3, a4, a5, a6, a7 = "e", "o", "è", "i", "a", "e", "e"
        elif v.endswith("ire"):
            # -ire = 3rd conjugation
            a1, a2, a3, a4, a5, a6, a7 = "i", "o", "i", "i", "a", "i", "e"
        else:
            # -orre, -urre = use 2nd conjugation
            a1, a2, a3, a4, a5, a6, a7 = "e", "o", "è", "i", "a", "e", "e"
        if verb.lower().endswith("ire"):
            # –ire verbs can add -isc between the root and declination.
            isc = "isc"
        else:
            isc = ""
        v = [verb.lower(),
            b + isc + "o", b + isc + "i", b + isc + a7, b + "iamo", b + a1 + "te", b + isc + a2 + "no", b + a1 + "ndo",
            b + a1 + "i", b + a1 + "sti", b + a3, b + a1 + "mmo", b + a1 + "ste", b + a1 + "rono", b + a1 + "to",
            b + a1 + "vo", b + a1 + "vi", b + a1 + "va", b + a1 + "vamo", b + a1 + "vate", b + a1 + "vano",
            b + a6 + "rò", b + a6 + "rai", b + a6 + "rà", b + a6 + "remo", b + a6 + "rete", b + a6 + "ranno",
            b + a6 + "rei", b + a6 + "resti", b + a6 + "rebbe", b + a6 + "remmo", b + a6 + "reste", b + a6 + "rebbero",
            b + isc + a4, b + isc + a5, b + "iamo", b + a1 + "te", b + isc + a5 + "no",
            b + isc + a5, b + isc + a5, b + isc + a5, b + "iamo", b + "iate", b + isc + a5 + "no",
            b + a1 + "ssi", b + a1 + "ssi", b + a1 + "sse", b + a1 + "ssimo", b + a1 + "ste", b + a1 + "ssero"
        ]
        for i, x in enumerate(v):
            x = x.replace("ii" , "i")
            x = x.replace("cha", "ca")
            x = x.replace("gha", "ga")
            x = x.replace("gga", "ggia")
            x = x.replace("cho", "co")
            x = x.replace("chò", "cò")
            v[i] = x
        return v

verbs = Verbs()

conjugate, lemma, lexeme, tenses = \
    verbs.conjugate, verbs.lemma, verbs.lexeme, verbs.tenses

#### ATTRIBUTIVE & PREDICATIVE #####################################################################

adjective_predicative = {
       "bei": "bello",
       "bel": "bello",
     "bell'": "bello",
     "begli": "bello",
      "buon": "buono",
     "buon'": "buona",
      "gran": "grande",
    "grand'": "grande",
    "grandi": "grande",
       "san": "santo",
     "sant'": "santa"
}


def attributive(adjective):
    """ For a predicative adjective, returns the attributive form.
    """
    # Must deal with feminine and plural.
    raise NotImplementedError


def predicative(adjective):
    """ Returns the predicative adjective.
    """
    w = adjective.lower()
    if w in adjective_predicative:
        return adjective_predicative[w]
    if w.endswith("ari"):
        return w + "o"
    if w.endswith(("ali", "ili", "esi", "nti", "ori")):
        return w[:-1] + "e"
    if w.endswith("isti"):
        return w[:-1] + "a"
    if w.endswith(("che", "ghe")):
        return w[:-2] + "a"
    if w.endswith(("chi", "ghi")):
        return w[:-2] + "o"
    if w.endswith("i"):
        return w[:-1] + "o"
    if w.endswith("e"):
        return w[:-1] + "a"
    return adjective
