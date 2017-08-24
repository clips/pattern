#### PATTERN | ES | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# Regular expressions-based rules for Spanish word inflection:
# - pluralization and singularization of nouns,
# - conjugation of verbs,
# - predicative adjectives.

# Accuracy:
# 78% for pluralize()
# 94% for singularize()
# 81% for Verbs.find_lemma() (0.55 regular 87% + 0.45 irregular 74%)
# 87% for Verbs.find_lexeme() (0.55 regular 99% + 0.45 irregular 72%)
# 93% for predicative()

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


def normalize(vowel):
    return {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"}.get(vowel, vowel)

#### ARTICLE #######################################################################################
# Spanish inflection of depends on gender and number.

# Inflection gender.
MASCULINE, FEMININE, NEUTER, PLURAL = \
    MALE, FEMALE, NEUTRAL, PLURAL = \
        M, F, N, PL = "m", "f", "n", "p"


def definite_article(word, gender=MALE):
    """ Returns the definite article (el/la/los/las) for a given word.
    """
    if MASCULINE in gender:
        return PLURAL in gender and "los" or "el"
    return PLURAL in gender and "las" or "la"


def indefinite_article(word, gender=MALE):
    """ Returns the indefinite article (un/una/unos/unas) for a given word.
    """
    if MASCULINE in gender:
        return PLURAL in gender and "unos" or "un"
    return PLURAL in gender and "unas" or "una"

DEFINITE = "definite"
INDEFINITE = "indefinite"


def article(word, function=INDEFINITE, gender=MALE):
    """ Returns the indefinite (un) or definite (el) article for the given word.
    """
    return function == DEFINITE \
       and definite_article(word, gender) \
        or indefinite_article(word, gender)
_article = article


def referenced(word, article=INDEFINITE, gender=MALE):
    """ Returns a string with the article + the word.
    """
    return "%s %s" % (_article(word, article, gender), word)

#### PLURALIZE #####################################################################################

plural_irregular = {
     "mamá": "mamás",
     "papá": "papás",
     "sofá": "sofás",
   "dominó": "dominós",
}


def pluralize(word, pos=NOUN, custom={}):
    """ Returns the plural of a given word.
        For example: gato => gatos.
        The custom dictionary is for user-defined replacements.
    """
    if word in custom:
        return custom[word]
    w = word.lower()
    # Article: masculine el => los, feminine la => las.
    if w == "el":
        return "los"
    if w == "la":
        return "las"
    # Irregular inflections.
    if w in plural_irregular:
        return plural_irregular[w]
    # Words endings that are unlikely to inflect.
    if w.endswith((
      "idad",
      "esis", "isis", "osis",
      "dica", "grafía", "logía")):
        return w
    # Words ending in a vowel get -s: gato => gatos.
    if w.endswith(VOWELS) or w.endswith("é"):
        return w + "s"
    # Words ending in a stressed vowel get -s: hindú => hindúes.
    if w.endswith(("á", "é", "í", "ó", "ú")):
        return w + "es"
    # Words ending in -és get -eses: holandés => holandeses.
    if w.endswith("és"):
        return w[:-2] + "eses"
    # Words ending in -s preceded by an unstressed vowel: gafas => gafas.
    if w.endswith("s") and len(w) > 3 and is_vowel(w[-2]):
        return w
    # Words ending in -z get -ces: luz => luces
    if w.endswith("z"):
        return w[:-1] + "ces"
    # Words that change vowel stress: graduación => graduaciones.
    for a, b in (
      ("án", "anes"),
      ("én", "enes"),
      ("ín", "ines"),
      ("ón", "ones"),
      ("ún", "unes")):
        if w.endswith(a):
            return w[:-2] + b
    # Words ending in a consonant get -es.
    return w + "es"

#print(pluralize("libro"))  # libros
#print(pluralize("señor"))  # señores
#print(pluralize("ley"))    # leyes
#print(pluralize("mes"))    # meses
#print(pluralize("luz"))    # luces
#print(pluralize("inglés")) # ingleses
#print(pluralize("rubí"))   # rubíes
#print(pluralize("papá"))   # papás

#### SINGULARIZE ###################################################################################


def singularize(word, pos=NOUN, custom={}):
    if word in custom:
        return custom[word]
    w = word.lower()
    # los gatos => el gato
    if pos == "DT":
        if w in ("la", "las", "los"):
            return "el"
        if w in ("una", "unas", "unos"):
            return "un"
        return w
    # hombres => hombre
    if w.endswith("es") and w[:-2].endswith(("br", "i", "j", "t", "zn")):
        return w[:-1]
    # gestiones => gestión
    for a, b in (
      ("anes", "án"),
      ("enes", "én"),
      ("eses", "és"),
      ("ines", "ín"),
      ("ones", "ón"),
      ("unes", "ún")):
        if w.endswith(a):
            return w[:-4] + b
    # hipotesis => hipothesis
    if w.endswith(("esis", "isis", "osis")):
        return w
    # luces => luz
    if w.endswith("ces"):
        return w[:-3] + "z"
    # hospitales => hospital
    if w.endswith("es"):
        return w[:-2]
    # gatos => gato
    if w.endswith("s"):
        return w[:-1]
    return w

#### VERB CONJUGATION ##############################################################################

verb_irregular_inflections = [
    ( "yéramos", "ir"   ), ( "cisteis", "cer"   ), ( "tuviera", "tener"), ( "ndieron", "nder" ),
    ( "ndiendo", "nder" ), ( "tándose", "tarse" ), ( "ndieran", "nder" ), ( "ndieras", "nder" ),
    ( "izaréis", "izar" ), ( "disteis", "der"   ), ( "irtiera", "ertir"), ( "pusiera", "poner"),
    ( "endiste", "ender"), ( "laremos", "lar"   ), ( "ndíamos", "nder" ), ( "icaréis", "icar" ),
    ( "dábamos", "dar"  ), ( "intiera", "entir" ), ( "iquemos", "icar" ), ( "jéramos", "cir"  ),
    ( "dierais", "der"  ), ( "endiera", "ender" ), ( "iéndose", "erse" ), ( "jisteis", "cir"  ),
    ( "cierais", "cer"  ), ( "ecíamos", "ecer"  ), ( "áramos", "ar"    ), ( "ríamos", "r"     ),
    ( "éramos", "r"     ), ( "iríais", "ir"     ), (   "temos", "tar"  ), (   "steis", "r"    ),
    (   "ciera", "cer"  ), (   "erais", "r"     ), (   "timos", "tir"  ), (   "uemos", "ar"   ),
    (   "tiera", "tir"  ), (   "bimos", "bir"   ), (  "ciéis", "ciar"  ), (   "gimos", "gir"  ),
    (   "jiste", "cir"  ), (   "mimos", "mir"   ), (  "guéis", "gar"   ), (  "stéis", "star"  ),
    (   "jimos", "cir"  ), (  "inéis", "inar"   ), (   "jemos", "jar"  ), (   "tenga", "tener"),
    (  "quéis", "car"   ), (  "bíais", "bir"    ), (   "jeron", "cir"  ), (  "uíais", "uir"   ),
    (  "ntéis", "ntar"  ), (   "jeras", "cir"   ), (   "jeran", "cir"  ), (  "ducía", "ducir" ),
    (   "yendo", "ir"   ), (   "eemos", "ear"   ), (   "ierta", "ertir"), (   "ierte", "ertir"),
    (   "nemos", "nar"  ), (  "ngáis", "ner"    ), (   "liera", "ler"  ), (  "endió", "ender" ),
    (  "uyáis", "uir"   ), (   "memos", "mar"   ), (   "ciste", "cer"  ), (   "ujera", "ucir" ),
    (   "uimos", "uir"  ), (   "ienda", "ender" ), (  "lléis", "llar"  ), (   "iemos", "iar"  ),
    (   "iende", "ender"), (   "rimos", "rir"   ), (   "semos", "sar"  ), (  "itéis", "itar"  ),
    (  "gíais", "gir"   ), (  "ndáis", "nder"   ), (  "tíais", "tir"   ), (   "demos", "dar"  ),
    (   "lemos", "lar"  ), (   "ponga", "poner" ), (   "yamos", "ir"   ), (  "icéis", "izar"  ),
    (    "bais", "r"    ), (   "rías", "r"      ), (   "rían", "r"     ), (   "iría", "ir"    ),
    (    "eran", "r"    ), (    "eras", "r"     ), (   "irán", "ir"    ), (   "irás", "ir"    ),
    (    "ongo", "oner" ), (    "aiga", "aer"   ), (   "ímos", "ir"    ), (   "ibía", "ibir"  ),
    (    "diga", "decir"), (   "edía", "edir"   ), (    "orte", "ortar"), (   "guió", "guir"  ),
    (    "iega", "egar" ), (    "oren", "orar"  ), (    "ores", "orar" ), (   "léis", "lar"   ),
    (    "irme", "irmar"), (    "siga", "seguir"), (   "séis", "sar"   ), (   "stré", "strar" ),
    (    "cien", "ciar" ), (    "cies", "ciar"  ), (    "dujo", "ducir"), (    "eses", "esar" ),
    (    "esen", "esar" ), (    "coja", "coger" ), (    "lice", "lizar"), (   "tías", "tir"   ),
    (   "tían", "tir"   ), (    "pare", "parar" ), (    "gres", "grar" ), (    "gren", "grar" ),
    (    "tuvo", "tener"), (   "uían", "uir"    ), (   "uías", "uir"   ), (    "quen", "car"  ),
    (    "ques", "car"  ), (   "téis", "tar"    ), (    "iero", "erir" ), (    "iere", "erir" ),
    (    "uche", "uchar"), (    "tuve", "tener" ), (    "inen", "inar" ), (    "pire", "pirar"),
    (   "reía", "reir"  ), (    "uste", "ustar" ), (   "ibió", "ibir"  ), (    "duce", "ducir"),
    (    "icen", "izar" ), (    "ices", "izar"  ), (    "ines", "inar" ), (    "ires", "irar" ),
    (    "iren", "irar" ), (    "duje", "ducir" ), (    "ille", "illar"), (    "urre", "urrir"),
    (    "tido", "tir"  ), (   "ndió", "nder"   ), (    "uido", "uir"  ), (    "uces", "ucir" ),
    (    "ucen", "ucir" ), (   "iéis", "iar"    ), (   "eció", "ecer"  ), (   "jéis", "jar"   ),
    (    "erve", "ervar"), (    "uyas", "uir"   ), (    "uyan", "uir"  ), (    "tía", "tir"   ),
    (    "uía", "uir"   ), (     "aos", "arse"  ), (     "gue", "gar"  ), (    "qué", "car"   ),
    (     "que", "car"  ), (     "rse", "rse"   ), (     "ste", "r"    ), (     "era", "r"    ),
    (    "tió", "tir"   ), (     "ine", "inar"  ), (     "ré", "r"     ), (      "ya", "ir"   ),
    (      "ye", "ir"   ), (     "tí", "tir"    ), (     "cé", "zar"   ), (      "ie", "iar"  ),
    (      "id", "ir"   ), (     "ué", "ar"     ),
]


class Verbs(_Verbs):

    def __init__(self):
        _Verbs.__init__(self, os.path.join(MODULE, "es-verbs.txt"),
            language = "es",
             default = {},
              format = [
                0, 1, 2, 3, 4, 5, 6, 8,     # indicativo presente
                34, 35, 36, 37, 38, 39, 24, # indicativo pretérito
                17, 18, 19, 20, 21, 22,     # indicativo imperfecto
                40, 41, 42, 43, 44, 45,     # indicativo futuro
                46, 47, 48, 49, 50, 51,     # indicativo condicional
                52, 54,                     # imperativo afirmativo
                55, 56, 57, 58, 59, 60,     # subjuntivo presente
                67, 68, 69, 70, 71, 72      # subjuntivo imperfecto
            ])

    def find_lemma(self, verb):
        """ Returns the base form of the given inflected verb, using a rule-based approach.
        """
        # Spanish has 12,000+ verbs, ending in -ar (85%), -er (8%), -ir (7%).
        # Over 65% of -ar verbs (6500+) have a regular inflection.
        v = verb.lower()
        # Probably ends in -ir if preceding vowel in stem is -i.
        er_ir = lambda b: (len(b) > 2 and b[-2] == "i") and b + "ir" or b + "er"
        # Probably infinitive if ends in -ar, -er or -ir.
        if v.endswith(("ar", "er", "ir")):
            return v
        # Ruleset for irregular inflections adds 10% accuracy.
        for a, b in verb_irregular_inflections:
            if v.endswith(a):
                return v[:-len(a)] + b
        # reconozco => reconocer
        v = v.replace("zco", "ce")
        # reconozcamos => reconocer
        v = v.replace("zca", "ce")
        # reconozcáis => reconocer
        v = v.replace("zcá", "ce")
        # saldrár => saler
        if "ldr" in v:
            return v[:v.index("ldr") + 1] + "er"
        # compondrán => componer
        if "ndr" in v:
            return v[:v.index("ndr") + 1] + "er"
        # Many verbs end in -ar and have a regular inflection:
        for x in ((
          "ando", "ado", "ad",                                # participle
          "aré", "arás", "ará", "aremos", "aréis", "arán", # future
          "aría", "arías", "aríamos", "aríais", "arían",    # conditional
          "aba", "abas", "ábamos", "abais", "aban",         # past imperfective
          "é", "aste", "ó", "asteis", "aron",               # past perfective
          "ara", "aras", "áramos", "arais", "aran")):       # past subjunctive
            if v.endswith(x):
                return v[:-len(x)] + "ar"
        # Many verbs end in -er and have a regular inflection:
        for x in ((
          "iendo", "ido", "ed",                               # participle
          "eré", "erás", "erá", "eremos", "eréis", "erán", # future
          "ería", "erías", "eríamos", "eríais", "erían",    # conditional
          "ía", "ías", "íamos", "íais", "ían",              # past imperfective
          "í", "iste", "ió", "imos", "isteis", "ieron",        # past perfective
          "era", "eras", "éramos", "erais", "eran")):       # past subjunctive
            if v.endswith(x):
                return er_ir(v[:-len(x)])
        # Many verbs end in -ir and have a regular inflection:
        for x in ((
          "iré", "irás", "irá", "iremos", "iréis", "irán", # future
          "iría", "irías", "iríamos", "iríais", "irían")):  # past subjunctive
            if v.endswith(x):
                return v[:-len(x)] + "ir"
        # Present 1sg -o: yo hablo, como, vivo => hablar, comer, vivir.
        if v.endswith("o"):
            return v[:-1] + "ar"
        # Present 2sg, 3sg and 3pl: tú hablas.
        if v.endswith(("as", "a", "an")):
            return v.rstrip("sn")[:-1] + "ar"
        # Present 2sg, 3sg and 3pl: tú comes, tú vives.
        if v.endswith(("es", "e", "en")):
            return er_ir(v.rstrip("sn")[:-1])
        # Present 1pl and 2pl: nosotros hablamos.
        for i, x in enumerate((
          ("amos", "áis"),
          ("emos", "éis"),
          ("imos", "ís"))):
            for x in x:
                if v.endswith(x):
                    return v[:-len(x)] + ("ar", "er", "ir")[i]
        return v

    def find_lexeme(self, verb):
        """ For a regular verb (base form), returns the forms using a rule-based approach.
        """
        v = verb.lower()
        if v.endswith(("arse", "erse", "irse")):
            # Reflexive verbs: calmarse (calmar) => me calmo.
            b = v[:-4]
        else:
            b = v[:-2]
        if v.endswith("ar") or not v.endswith(("er", "ir")):
            # Regular inflection for verbs ending in -ar.
            return [v,
                b + "o", b + "as", b + "a", b + "amos", b + "áis", b + "an", b + "ando",
                b + "é", b + "aste", b + "ó", b + "amos", b + "asteis", b + "aron", b + "ado",
                b + "aba", b + "abas", b + "aba", b + "ábamos", b + "abais", b + "aban",
                v + "é", v + "ás", v + "á", v + "emos", v + "éis", v + "án",
                v + "ía", v + "ías", v + "ía", v + "íamos", v + "íais", v + "ían",
                b + "a", v[:-1] + "d",
                b + "e", b + "es", b + "e", b + "emos", b + "éis", b + "en",
                v + "a", v + "as", v + "a", b + "áramos", v + "ais", v + "an"]
        else:
            # Regular inflection for verbs ending in -er and -ir.
            p1, p2 = v.endswith("er") and ("e", "é") or ("i", "e")
            return [v,
                b + "o", b + "es", b + "e", b + p1 + "mos", b + p2 + "is", b + "en", b + "iendo",
                b + "í", b + "iste", b + "ió", b + "imos", b + "isteis", b + "ieron", b + "ido",
                b + "ía", b + "ías", b + "ía", b + "íamos", b + "íais", b + "ían",
                v + "é", v + "ás", v + "á", v + "emos", v + "éis", v + "án",
                v + "ía", v + "ías", v + "ía", v + "íamos", v + "íais", v + "ían",
                b + "a", v[:-1] + "d",
                b + "a", b + "as", b + "a", b + "amos", b + "áis", b + "an",
                b + "iera", b + "ieras", b + "iera", b + "iéramos", b + "ierais", b + "ieran"]

verbs = Verbs()

conjugate, lemma, lexeme, tenses = \
    verbs.conjugate, verbs.lemma, verbs.lexeme, verbs.tenses

#### ATTRIBUTIVE & PREDICATIVE #####################################################################


def attributive(adjective, gender=MALE):
    w = adjective.lower()
    # normal => normales
    if PLURAL in gender and not is_vowel(w[-1:]):
        return w + "es"
    # el chico inteligente => los chicos inteligentes
    if PLURAL in gender and w.endswith(("a", "e")):
        return w + "s"
    # el chico alto => los chicos altos
    if w.endswith("o"):
        if FEMININE in gender and PLURAL in gender:
            return w[:-1] + "as"
        if FEMININE in gender:
            return w[:-1] + "a"
        if PLURAL in gender:
            return w + "s"
    return w

#print(attributive("intelligente", gender=PLURAL)) # intelligentes
#print(attributive("alto", gender=MALE+PLURAL))    # altos
#print(attributive("alto", gender=FEMALE+PLURAL))  # altas
#print(attributive("normal", gender=MALE))         # normal
#print(attributive("normal", gender=FEMALE))       # normal
#print(attributive("normal", gender=PLURAL))       # normales


def predicative(adjective):
    """ Returns the predicative adjective (lowercase).
        In Spanish, the attributive form is always used for descriptive adjectives:
        "el chico alto" => masculine,
        "la chica alta" => feminine.
        The predicative is useful for lemmatization.
    """
    w = adjective.lower()
    # histéricos => histérico
    if w.endswith(("os", "as")):
        w = w[:-1]
    # histérico => histérico
    if w.endswith("o"):
        return w
    # histérica => histérico
    if w.endswith("a"):
        return w[:-1] + "o"
    # horribles => horrible, humorales => humoral
    if w.endswith("es"):
        if len(w) >= 4 and not is_vowel(normalize(w[-3])) and not is_vowel(normalize(w[-4])):
            return w[:-1]
        return w[:-2]
    return w
