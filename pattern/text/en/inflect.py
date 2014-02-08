#### PATTERN | EN | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# Regular expressions-based rules for English word inflection:
# - pluralization and singularization of nouns and adjectives,
# - conjugation of verbs,
# - comparative and superlative of adjectives.

# Accuracy (measured on CELEX English morphology word forms):
# 95% for pluralize()
# 96% for singularize()
# 95% for Verbs.find_lemma() (for regular verbs)
# 96% for Verbs.find_lexeme() (for regular verbs)

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
    PROGRESSIVE,
    PARTICIPLE
)

sys.path.pop(0)

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"

VOWELS = "aeiouy"
re_vowel = re.compile(r"a|e|i|o|u|y", re.I)
is_vowel = lambda ch: ch in VOWELS

#### ARTICLE #######################################################################################
# Based on the Ruby Linguistics module by Michael Granger:
# http://www.deveiate.org/projects/Linguistics/wiki/English

RE_ARTICLE = map(lambda x: (re.compile(x[0]), x[1]), (
    ("euler|hour(?!i)|heir|honest|hono", "an"),       # exceptions: an hour, an honor
    # Abbreviations:
    # strings of capitals starting with a vowel-sound consonant followed by another consonant,
    # which are not likely to be real words.
    (r"(?!FJO|[HLMNS]Y.|RY[EO]|SQU|(F[LR]?|[HL]|MN?|N|RH?|S[CHKLMNPTVW]?|X(YL)?)[AEIOU])[FHLMNRSX][A-Z]", "an"),
    (r"^[aefhilmnorsx][.-]"  , "an"),
    (r"^[a-z][.-]"           , "a" ),
    (r"^[^aeiouy]"           , "a" ), # consonants: a bear
    (r"^e[uw]"               , "a" ), # -eu like "you": a european
    (r"^onc?e"               , "a" ), #  -o like "wa" : a one-liner
    (r"uni([^nmd]|mo)"       , "a" ), #  -u like "you": a university
    (r"^u[bcfhjkqrst][aeiou]", "a" ), #  -u like "you": a uterus
    (r"^[aeiou]"             , "an"), # vowels: an owl
    (r"y(b[lor]|cl[ea]|fere|gg|p[ios]|rou|tt)", "an"), # y like "i": an yclept, a year
    (r""                     , "a" )  # guess "a"
))

def definite_article(word):
    return "the"

def indefinite_article(word):
    """ Returns the indefinite article for a given word.
        For example: indefinite_article("university") => "a" university.
    """
    word = word.split(" ")[0]
    for rule, article in RE_ARTICLE:
        if rule.search(word) is not None:
            return article

DEFINITE, INDEFINITE = \
    "definite", "indefinite"

def article(word, function=INDEFINITE):
    """ Returns the indefinite (a or an) or definite (the) article for the given word.
    """
    return function == DEFINITE and definite_article(word) or indefinite_article(word)

_article = article

def referenced(word, article=INDEFINITE):
    """ Returns a string with the article + the word.
    """
    return "%s %s" % (_article(word, article), word)

#print referenced("hour")        
#print referenced("FBI")
#print referenced("bear")
#print referenced("one-liner")
#print referenced("european")
#print referenced("university")
#print referenced("uterus")
#print referenced("owl")
#print referenced("yclept")
#print referenced("year")

#### PLURALIZE #####################################################################################
# Based on "An Algorithmic Approach to English Pluralization" by Damian Conway:
# http://www.csse.monash.edu.au/~damian/papers/HTML/Plurals.html

# Prepositions are used in forms like "mother-in-law" and "man at arms".
plural_prepositions = set((
    "about"  , "before" , "during", "of"   , "till" ,
    "above"  , "behind" , "except", "off"  , "to"   ,
    "across" , "below"  , "for"   , "on"   , "under",
    "after"  , "beneath", "from"  , "onto" , "until",
    "among"  , "beside" , "in"    , "out"  , "unto" ,
    "around" , "besides", "into"  , "over" , "upon" ,
    "at"     , "between", "near"  , "since", "with" ,
    "athwart", "betwixt", 
               "beyond", 
               "but", 
               "by"))

# Inflection rules that are either:
# - general,
# - apply to a certain category of words,
# - apply to a certain category of words only in classical mode,
# - apply only in classical mode.
# Each rule is a (suffix, inflection, category, classic)-tuple.
plural_rules = [
       # 0) Indefinite articles and demonstratives.
    ((   r"^a$|^an$", "some"       , None, False),
     (     r"^this$", "these"      , None, False),
     (     r"^that$", "those"      , None, False),
     (      r"^any$", "all"        , None, False)
    ), # 1) Possessive adjectives.
    ((       r"^my$", "our"        , None, False),
     (     r"^your$", "your"       , None, False),
     (      r"^thy$", "your"       , None, False),
     (r"^her$|^his$", "their"      , None, False),
     (      r"^its$", "their"      , None, False),
     (    r"^their$", "their"      , None, False)
    ), # 2) Possessive pronouns.
    ((     r"^mine$", "ours"       , None, False),
     (    r"^yours$", "yours"      , None, False),
     (    r"^thine$", "yours"      , None, False),
     (r"^her$|^his$", "theirs"     , None, False),
     (      r"^its$", "theirs"     , None, False),
     (    r"^their$", "theirs"     , None, False)
    ), # 3) Personal pronouns.
    ((        r"^I$", "we"         , None, False),
     (       r"^me$", "us"         , None, False),
     (   r"^myself$", "ourselves"  , None, False),
     (      r"^you$", "you"        , None, False),
     (r"^thou$|^thee$", "ye"       , None, False),
     ( r"^yourself$", "yourself"   , None, False),
     (  r"^thyself$", "yourself"   , None, False),     
     ( r"^she$|^he$", "they"       , None, False),
     (r"^it$|^they$", "they"       , None, False),
     (r"^her$|^him$", "them"       , None, False),
     (r"^it$|^them$", "them"       , None, False),
     (  r"^herself$", "themselves" , None, False),
     (  r"^himself$", "themselves" , None, False),
     (   r"^itself$", "themselves" , None, False),
     ( r"^themself$", "themselves" , None, False),
     (  r"^oneself$", "oneselves"  , None, False)
    ), # 4) Words that do not inflect.
    ((          r"$", ""  , "uninflected", False),
     (          r"$", ""  , "uncountable", False),
     (         r"s$", "s" , "s-singular" , False),
     (      r"fish$", "fish"       , None, False),
     (r"([- ])bass$", "\\1bass"    , None, False),
     (       r"ois$", "ois"        , None, False),
     (     r"sheep$", "sheep"      , None, False),
     (      r"deer$", "deer"       , None, False),
     (       r"pox$", "pox"        , None, False),
     (r"([A-Z].*)ese$", "\\1ese"   , None, False),
     (      r"itis$", "itis"       , None, False),
     (r"(fruct|gluc|galact|lact|ket|malt|rib|sacchar|cellul)ose$", "\\1ose", None, False)
    ), # 5) Irregular plural forms (e.g., mongoose, oxen).
    ((     r"atlas$", "atlantes"   , None, True ),
     (     r"atlas$", "atlases"    , None, False),
     (      r"beef$", "beeves"     , None, True ),
     (   r"brother$", "brethren"   , None, True ),
     (     r"child$", "children"   , None, False),
     (    r"corpus$", "corpora"    , None, True ),
     (    r"corpus$", "corpuses"   , None, False),
     (      r"^cow$", "kine"       , None, True ),
     ( r"ephemeris$", "ephemerides", None, False),
     (  r"ganglion$", "ganglia"    , None, True ),
     (     r"genie$", "genii"      , None, True ),
     (     r"genus$", "genera"     , None, False),
     (  r"graffito$", "graffiti"   , None, False),
     (      r"loaf$", "loaves"     , None, False),
     (     r"money$", "monies"     , None, True ),
     (  r"mongoose$", "mongooses"  , None, False),
     (    r"mythos$", "mythoi"     , None, False),
     (   r"octopus$", "octopodes"  , None, True ),
     (      r"opus$", "opera"      , None, True ),
     (      r"opus$", "opuses"     , None, False),
     (       r"^ox$", "oxen"       , None, False),
     (     r"penis$", "penes"      , None, True ),
     (     r"penis$", "penises"    , None, False),
     ( r"soliloquy$", "soliloquies", None, False),
     (    r"testis$", "testes"     , None, False),
     (    r"trilby$", "trilbys"    , None, False),
     (      r"turf$", "turves"     , None, True ),
     (     r"numen$", "numena"     , None, False),
     (   r"occiput$", "occipita"   , None, True )
    ), # 6) Irregular inflections for common suffixes (e.g., synopses, mice, men).
    ((       r"man$", "men"        , None, False),
     (    r"person$", "people"     , None, False),
     (r"([lm])ouse$", "\\1ice"     , None, False),
     (     r"tooth$", "teeth"      , None, False),
     (     r"goose$", "geese"      , None, False),
     (      r"foot$", "feet"       , None, False),
     (      r"zoon$", "zoa"        , None, False),
     ( r"([csx])is$", "\\1es"      , None, False)
    ), # 7) Fully assimilated classical inflections 
       #    (e.g., vertebrae, codices).
    ((        r"ex$", "ices" , "ex-ices" , False),
     (        r"ex$", "ices" , "ex-ices*", True ), # * = classical mode
     (        r"um$", "a"    ,    "um-a" , False),
     (        r"um$", "a"    ,    "um-a*", True ),
     (        r"on$", "a"    ,    "on-a" , False),
     (         r"a$", "ae"   ,    "a-ae" , False),
     (         r"a$", "ae"   ,    "a-ae*", True )
    ), # 8) Classical variants of modern inflections 
       #    (e.g., stigmata, soprani).
    ((      r"trix$", "trices"     , None, True),
     (       r"eau$", "eaux"       , None, True),
     (       r"ieu$", "ieu"        , None, True),
     ( r"([iay])nx$", "\\1nges"    , None, True),
     (        r"en$", "ina"  ,  "en-ina*", True),
     (         r"a$", "ata"  ,   "a-ata*", True),
     (        r"is$", "ides" , "is-ides*", True),
     (        r"us$", "i"    ,    "us-i*", True),
     (        r"us$", "us "  ,   "us-us*", True),
     (         r"o$", "i"    ,     "o-i*", True),
     (          r"$", "i"    ,      "-i*", True),
     (          r"$", "im"   ,     "-im*", True)
    ), # 9) -ch, -sh and -ss take -es in the plural 
       #    (e.g., churches, classes).
    ((   r"([cs])h$", "\\1hes"     , None, False),
     (        r"ss$", "sses"       , None, False),
     (         r"x$", "xes"        , None, False)
    ), # 10) -f or -fe sometimes take -ves in the plural 
       #     (e.g, lives, wolves).
    (( r"([aeo]l)f$", "\\1ves"     , None, False),
     ( r"([^d]ea)f$", "\\1ves"     , None, False),
     (       r"arf$", "arves"      , None, False),
     (r"([nlw]i)fe$", "\\1ves"     , None, False),
    ), # 11) -y takes -ys if preceded by a vowel, -ies otherwise 
       #     (e.g., storeys, Marys, stories).
    ((r"([aeiou])y$", "\\1ys"      , None, False),
     (r"([A-Z].*)y$", "\\1ys"      , None, False),
     (         r"y$", "ies"        , None, False)
    ), # 12) -o sometimes takes -os, -oes otherwise.
       #     -o is preceded by a vowel takes -os 
       #     (e.g., lassos, potatoes, bamboos).
    ((         r"o$", "os",        "o-os", False),
     (r"([aeiou])o$", "\\1os"      , None, False),
     (         r"o$", "oes"        , None, False)
    ), # 13) Miltary stuff 
       #     (e.g., Major Generals).
    ((         r"l$", "ls", "general-generals", False),
    ), # 14) Assume that the plural takes -s 
       #     (cats, programmes, ...).
    ((          r"$", "s"          , None, False),)
]

# For performance, compile the regular expressions once:
plural_rules = [[(re.compile(r[0]), r[1], r[2], r[3]) for r in grp] for grp in plural_rules]

# Suffix categories.
plural_categories = {
    "uninflected": [ 
        "bison"      , "debris"     , "headquarters" , "news"       , "swine"        ,
        "bream"      , "diabetes"   , "herpes"       , "pincers"    , "trout"        ,
        "breeches"   , "djinn"      , "high-jinks"   , "pliers"     , "tuna"         ,
        "britches"   , "eland"      , "homework"     , "proceedings", "whiting"      ,
        "carp"       , "elk"        , "innings"      , "rabies"     , "wildebeest"
        "chassis"    , "flounder"   , "jackanapes"   , "salmon"     ,
        "clippers"   , "gallows"    , "mackerel"     , "scissors"   , 
        "cod"        , "graffiti"   , "measles"      , "series"     , 
        "contretemps",                "mews"         , "shears"     , 
        "corps"      ,                "mumps"        , "species"
        ],
    "uncountable": [
        "advice"     , "fruit"      , "ketchup"      , "meat"       , "sand"         ,
        "bread"      , "furniture"  , "knowledge"    , "mustard"    , "software"     ,
        "butter"     , "garbage"    , "love"         , "news"       , "understanding",
        "cheese"     , "gravel"     , "luggage"      , "progress"   , "water"
        "electricity", "happiness"  , "mathematics"  , "research"   , 
        "equipment"  , "information", "mayonnaise"   , "rice"
        ],
    "s-singular": [
        "acropolis"  , "caddis"     , "dais"         , "glottis"    , "pathos"       ,
        "aegis"      , "cannabis"   , "digitalis"    , "ibis"       , "pelvis"       ,
        "alias"      , "canvas"     , "epidermis"    , "lens"       , "polis"        ,
        "asbestos"   , "chaos"      , "ethos"        , "mantis"     , "rhinoceros"   ,
        "bathos"     , "cosmos"     , "gas"          , "marquis"    , "sassafras"    ,
        "bias"       ,                "glottis"      , "metropolis" , "trellis"
        ],
    "ex-ices": [
        "codex"      , "murex"      , "silex"
        ],
    "ex-ices*": [
        "apex"       , "index"      , "pontifex"     , "vertex"     , 
        "cortex"     , "latex"      , "simplex"      , "vortex"
        ],
    "um-a": [
        "agendum"    , "candelabrum", "desideratum"  , "extremum"   , "stratum"      ,
        "bacterium"  , "datum"      , "erratum"      , "ovum"
        ],
    "um-a*": [
        "aquarium"   , "emporium"   , "maximum"      , "optimum"    , "stadium"      ,
        "compendium" , "enconium"   , "medium"       , "phylum"     , "trapezium"    ,
        "consortium" , "gymnasium"  , "memorandum"   , "quantum"    , "ultimatum"    ,
        "cranium"    , "honorarium" , "millenium"    , "rostrum"    , "vacuum"       ,
        "curriculum" , "interregnum", "minimum"      , "spectrum"   , "velum"        ,
        "dictum"     , "lustrum"    , "momentum"     , "speculum"
        ],
    "on-a": [
        "aphelion"   , "hyperbaton" , "perihelion"   ,
        "asyndeton"  , "noumenon"   , "phenomenon"   , 
        "criterion"  , "organon"    , "prolegomenon"
        ],
    "a-ae": [
        "alga"       , "alumna"     , "vertebra"
        ],
    "a-ae*": [
        "abscissa"   , "aurora"     , "hyperbola"    , "nebula"     , 
        "amoeba"     , "formula"    , "lacuna"       , "nova"       ,
        "antenna"    , "hydra"      , "medusa"       , "parabola"
        ],
    "en-ina*": [
        "foramen"    , "lumen"      , "stamen"
    ],
    "a-ata*": [
        "anathema"   , "dogma"      , "gumma"        , "miasma"     , "stigma"       ,
        "bema"       , "drama"      , "lemma"        , "schema"     , "stoma"        ,
        "carcinoma"  , "edema"      , "lymphoma"     , "oedema"     , "trauma"       ,
        "charisma"   , "enema"      , "magma"        , "sarcoma"    ,
        "diploma"    , "enigma"     , "melisma"      , "soma"       ,
        ],
    "is-ides*": [
        "clitoris"   , "iris"
        ],
    "us-i*": [
        "focus"      , "nimbus"     , "succubus"     ,
        "fungus"     , "nucleolus"  , "torus"        , 
        "genius"     , "radius"     , "umbilicus"    , 
        "incubus"    , "stylus"     , "uterus"
        ],
    "us-us*": [
        "apparatus"  , "hiatus"     , "plexus"       , "status"
        "cantus"     , "impetus"    , "prospectus"   ,
        "coitus"     , "nexus"      , "sinus"        , 
        ],
    "o-i*": [
        "alto"       , "canto"      , "crescendo"    , "soprano"    ,
        "basso"      , "contralto"  , "solo"         , "tempo"
        ],
    "-i*": [
        "afreet"     , "afrit"      , "efreet"
        ],
    "-im*": [
        "cherub"     , "goy"        , "seraph"
        ],
    "o-os": [
        "albino"     , "dynamo"     , "guano"        , "lumbago"    , "photo"        ,
        "archipelago", "embryo"     , "inferno"      , "magneto"    , "pro"          ,
        "armadillo"  , "fiasco"     , "jumbo"        , "manifesto"  , "quarto"       ,
        "commando"   , "generalissimo",                "medico"     , "rhino"        ,
        "ditto"      , "ghetto"     , "lingo"        , "octavo"     , "stylo"
        ],
    "general-generals": [
        "Adjutant"   , "Brigadier"  , "Lieutenant"   , "Major"      , "Quartermaster", 
        "adjutant"   , "brigadier"  , "lieutenant"   , "major"      , "quartermaster"
        ]
}

def pluralize(word, pos=NOUN, custom={}, classical=True):
    """ Returns the plural of a given word, e.g., child => children.
        Handles nouns and adjectives, using classical inflection by default
        (i.e., where "matrix" pluralizes to "matrices" and not "matrixes").
        The custom dictionary is for user-defined replacements.
    """
    if word in custom:
        return custom[word]
    # Recurse genitives.
    # Remove the apostrophe and any trailing -s, 
    # form the plural of the resultant noun, and then append an apostrophe (dog's => dogs').
    if word.endswith(("'", "'s")):
        w = word.rstrip("'s")
        w = pluralize(w, pos, custom, classical)
        if w.endswith("s"):
            return w + "'"
        else:
            return w + "'s"
    # Recurse compound words
    # (e.g., Postmasters General, mothers-in-law, Roman deities).    
    w = word.replace("-", " ").split(" ")
    if len(w) > 1:
        if w[1] == "general" or \
           w[1] == "General" and \
           w[0] not in plural_categories["general-generals"]:
            return word.replace(w[0], pluralize(w[0], pos, custom, classical))
        elif w[1] in plural_prepositions:
            return word.replace(w[0], pluralize(w[0], pos, custom, classical))
        else:
            return word.replace(w[-1], pluralize(w[-1], pos, custom, classical))
    # Only a very few number of adjectives inflect.
    n = range(len(plural_rules))
    if pos.startswith(ADJECTIVE):
        n = [0, 1]
    # Apply pluralization rules.
    for i in n:
        for suffix, inflection, category, classic in plural_rules[i]:
            # A general rule, or a classic rule in classical mode.
            if category is None:
                if not classic or (classic and classical):
                    if suffix.search(word) is not None:
                        return suffix.sub(inflection, word)
            # A rule pertaining to a specific category of words.
            if category is not None:
                if word in plural_categories[category] and (not classic or (classic and classical)):
                    if suffix.search(word) is not None:
                        return suffix.sub(inflection, word)
    return word

#print pluralize("part-of-speech")
#print pluralize("child")
#print pluralize("dog's")
#print pluralize("wolf")
#print pluralize("bear")
#print pluralize("kitchen knife")
#print pluralize("octopus", classical=True)
#print pluralize("matrix", classical=True)
#print pluralize("matrix", classical=False)
#print pluralize("my", pos=ADJECTIVE)

#### SINGULARIZE ###################################################################################
# Adapted from Bermi Ferrer's Inflector for Python:
# http://www.bermi.org/inflector/

# Copyright (c) 2006 Bermi Ferrer Martinez
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software to deal in this software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of this software, and to permit
# persons to whom this software is furnished to do so, subject to the following
# condition:
#
# THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THIS SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THIS SOFTWARE.

singular_rules = [
    (r'(?i)(.)ae$'            , '\\1a'    ),
    (r'(?i)(.)itis$'          , '\\1itis' ),
    (r'(?i)(.)eaux$'          , '\\1eau'  ),
    (r'(?i)(quiz)zes$'        , '\\1'     ),
    (r'(?i)(matr)ices$'       , '\\1ix'   ),
    (r'(?i)(ap|vert|ind)ices$', '\\1ex'   ),
    (r'(?i)^(ox)en'           , '\\1'     ),
    (r'(?i)(alias|status)es$' , '\\1'     ),
    (r'(?i)([octop|vir])i$'   ,  '\\1us'  ),
    (r'(?i)(cris|ax|test)es$' , '\\1is'   ),
    (r'(?i)(shoe)s$'          , '\\1'     ),
    (r'(?i)(o)es$'            , '\\1'     ),
    (r'(?i)(bus)es$'          , '\\1'     ),
    (r'(?i)([m|l])ice$'       , '\\1ouse' ),
    (r'(?i)(x|ch|ss|sh)es$'   , '\\1'     ),
    (r'(?i)(m)ovies$'         , '\\1ovie' ),
    (r'(?i)(.)ombies$'        , '\\1ombie'),
    (r'(?i)(s)eries$'         , '\\1eries'),
    (r'(?i)([^aeiouy]|qu)ies$', '\\1y'    ),
	# -f, -fe sometimes take -ves in the plural 
	# (e.g., lives, wolves).
    (r"([aeo]l)ves$"          , "\\1f"    ),
    (r"([^d]ea)ves$"          , "\\1f"    ),
    (r"arves$"                , "arf"     ),
    (r"erves$"                , "erve"    ),
    (r"([nlw]i)ves$"          , "\\1fe"   ),
    (r'(?i)([lr])ves$'        , '\\1f'    ),
    (r"([aeo])ves$"           , "\\1ve"   ),
    (r'(?i)(sive)s$'          , '\\1'     ),
    (r'(?i)(tive)s$'          , '\\1'     ),
    (r'(?i)(hive)s$'          , '\\1'     ),
    (r'(?i)([^f])ves$'        , '\\1fe'   ),
    # -ses suffixes.
    (r'(?i)(^analy)ses$'      , '\\1sis'  ),
    (r'(?i)((a)naly|(b)a|(d)iagno|(p)arenthe|(p)rogno|(s)ynop|(t)he)ses$', '\\1\\2sis'),
    (r'(?i)(.)opses$'         , '\\1opsis'),
    (r'(?i)(.)yses$'          , '\\1ysis' ),
    (r'(?i)(h|d|r|o|n|b|cl|p)oses$', '\\1ose'),
    (r'(?i)(fruct|gluc|galact|lact|ket|malt|rib|sacchar|cellul)ose$', '\\1ose'),
    (r'(?i)(.)oses$'          , '\\1osis' ),
    # -a
    (r'(?i)([ti])a$'          , '\\1um'   ),
    (r'(?i)(n)ews$'           , '\\1ews'  ),
    (r'(?i)s$'                , ''        ),
]

# For performance, compile the regular expressions only once:
singular_rules = [(re.compile(r[0]), r[1]) for r in singular_rules]

singular_uninflected = set((
    "bison"      , "debris"   , "headquarters", "pincers"    , "trout"     ,
    "bream"      , "diabetes" , "herpes"      , "pliers"     , "tuna"      ,
    "breeches"   , "djinn"    , "high-jinks"  , "proceedings", "whiting"   ,
    "britches"   , "eland"    , "homework"    , "rabies"     , "wildebeest"
    "carp"       , "elk"      , "innings"     , "salmon"     , 
    "chassis"    , "flounder" , "jackanapes"  , "scissors"   , 
    "christmas"  , "gallows"  , "mackerel"    , "series"     , 
    "clippers"   , "georgia"  , "measles"     , "shears"     , 
    "cod"        , "graffiti" , "mews"        , "species"    , 
    "contretemps",              "mumps"       , "swine"      , 
    "corps"      ,              "news"        , "swiss"      , 
))
singular_uncountable = set((
    "advice"     , "equipment", "happiness"   , "luggage"    , "news"      , "software"     ,
    "bread"      , "fruit"    , "information" , "mathematics", "progress"  , "understanding",
    "butter"     , "furniture", "ketchup"     , "mayonnaise" , "research"  , "water"
    "cheese"     , "garbage"  , "knowledge"   , "meat"       , "rice"      , 
    "electricity", "gravel"   , "love"        , "mustard"    , "sand"      , 
))
singular_ie = set((
    "alergie"    , "cutie"    , "hoagie"      , "newbie"     , "softie"    , "veggie"       , 
    "auntie"     , "doggie"   , "hottie"      , "nightie"    , "sortie"    , "weenie"       , 
    "beanie"     , "eyrie"    , "indie"       , "oldie"      , "stoolie"   , "yuppie"       , 
    "birdie"     , "freebie"  , "junkie"      , "^pie"       , "sweetie"   , "zombie"
    "bogie"      , "goonie"   , "laddie"      , "pixie"      , "techie"    , 
    "bombie"     , "groupie"  , "laramie"     , "quickie"    , "^tie"      , 
    "collie"     , "hankie"   , "lingerie"    , "reverie"    , "toughie"   , 
    "cookie"     , "hippie"   , "meanie"      , "rookie"     , "valkyrie"  , 
))
singular_irregular = {
       "atlantes": "atlas", 
        "atlases": "atlas", 
           "axes": "axe",
         "beeves": "beef", 
       "brethren": "brother", 
       "children": "child",
       "children": "child", 
        "corpora": "corpus", 
       "corpuses": "corpus", 
    "ephemerides": "ephemeris", 
           "feet": "foot",
        "ganglia": "ganglion", 
          "geese": "goose",
         "genera": "genus", 
          "genii": "genie", 
       "graffiti": "graffito", 
         "helves": "helve",
           "kine": "cow", 
         "leaves": "leaf",
         "loaves": "loaf", 
            "men": "man",
      "mongooses": "mongoose", 
         "monies": "money", 
          "moves": "move",
         "mythoi": "mythos", 
         "numena": "numen", 
       "occipita": "occiput", 
      "octopodes": "octopus", 
          "opera": "opus", 
         "opuses": "opus", 
            "our": "my",
           "oxen": "ox", 
          "penes": "penis", 
        "penises": "penis", 
         "people": "person",
          "sexes": "sex",
    "soliloquies": "soliloquy", 
          "teeth": "tooth",
         "testes": "testis", 
        "trilbys": "trilby", 
         "turves": "turf", 
            "zoa": "zoon",
}

def singularize(word, pos=NOUN, custom={}):
    """ Returns the singular of a given word.
    """
    if word in custom:
        return custom[word]
    # Recurse compound words (e.g. mothers-in-law). 
    if "-" in word:
        w = word.split("-")
        if len(w) > 1 and w[1] in plural_prepositions:
            return singularize(w[0], pos, custom)+"-"+"-".join(w[1:])
    # dogs' => dog's
    if word.endswith("'"):
        return singularize(word[:-1]) + "'s"
    w = word.lower()
    for x in singular_uninflected:
        if x.endswith(w):
            return word
    for x in singular_uncountable:
        if x.endswith(w):
            return word
    for x in singular_ie:
        if w.endswith(x+"s"):
            return w
    for x in singular_irregular:
        if w.endswith(x):
            return re.sub('(?i)'+x+'$', singular_irregular[x], word)
    for suffix, inflection in singular_rules:
        m = suffix.search(word)
        g = m and m.groups() or [] 
        if m:
            for k in range(len(g)):
                if g[k] is None:
                    inflection = inflection.replace('\\' + str(k + 1), '')
            return suffix.sub(inflection, word)
    return word

#### VERB CONJUGATION ##############################################################################

class Verbs(_Verbs):
    
    def __init__(self):
        _Verbs.__init__(self, os.path.join(MODULE, "en-verbs.txt"),
            language = "en",
              format = [0, 1, 2, 3, 7, 8, 17, 18, 19, 23, 25, 24, 16, 9, 10, 11, 15, 33, 26, 27, 28, 32],
             default = {
                 1: 0,   2: 0,   3: 0,   7: 0,  # present singular => infinitive ("I walk")
                 4: 7,   5: 7,   6: 7,          # present plural
                17: 25, 18: 25, 19: 25, 23: 25, # past singular
                20: 23, 21: 23, 22: 23,         # past plural
                 9: 16, 10: 16, 11: 16, 15: 16, # present singular negated
                12: 15, 13: 15, 14: 15,         # present plural negated
                26: 33, 27: 33, 28: 33,         # past singular negated
                29: 32, 30: 32, 31: 32, 32: 33  # past plural negated
            })
    
    def find_lemma(self, verb):
        """ Returns the base form of the given inflected verb, using a rule-based approach.
            This is problematic if a verb ending in -e is given in the past tense or gerund.
        """
        v = verb.lower()
        b = False
        if v in ("'m", "'re", "'s", "n't"):
            return "be"
        if v in ("'d", "'ll"):
            return "will"
        if v in  ("'ve"):
            return "have"
        if v.endswith("s"):
            if v.endswith("ies") and len(v) > 3 and v[-4] not in VOWELS:
                return v[:-3]+"y" # complies => comply
            if v.endswith(("sses", "shes", "ches", "xes")):
                return v[:-2]     # kisses => kiss
            return v[:-1]
        if v.endswith("ied") and re_vowel.search(v[:-3]) is not None:
            return v[:-3]+"y"     # envied => envy
        if v.endswith("ing") and re_vowel.search(v[:-3]) is not None:
            v = v[:-3]; b=True;   # chopping => chopp
        if v.endswith("ed") and re_vowel.search(v[:-2]) is not None:
            v = v[:-2]; b=True;   # danced => danc
        if b:
            # Doubled consonant after short vowel: chopp => chop.
            if len(v) > 3 and v[-1] == v[-2] and v[-3] in VOWELS and v[-4] not in VOWELS and not v.endswith("ss"):
                return v[:-1]
            if v.endswith(("ick", "ack")):
                return v[:-1]     # panick => panic
            # Guess common cases where the base form ends in -e:
            if v.endswith(("v", "z", "c", "i")):
                return v+"e"      # danc => dance
            if v.endswith("g") and v.endswith(("dg", "lg", "ng", "rg")):
                return v+"e"      # indulg => indulge
            if v.endswith(("b", "d", "g", "k", "l", "m", "r", "s", "t")) \
              and len(v) > 2 and v[-2] in VOWELS and not v[-3] in VOWELS \
              and not v.endswith("er"): 
                return v+"e"      # generat => generate
            if v.endswith("n") and v.endswith(("an", "in")) and not v.endswith(("ain", "oin", "oan")):
                return v+"e"      # imagin => imagine
            if v.endswith("l") and len(v) > 1 and v[-2] not in VOWELS:
                return v+"e"      # squabbl => squabble
            if v.endswith("f") and len(v) > 2 and v[-2] in VOWELS and v[-3] not in VOWELS:
                return v+"e"      # chaf => chafed
            if v.endswith("e"):
                return v+"e"      # decre => decree
            if v.endswith(("th", "ang", "un", "cr", "vr", "rs", "ps", "tr")):
                return v+"e"
        return v

    def find_lexeme(self, verb):
        """ For a regular verb (base form), returns the forms using a rule-based approach.
        """
        v = verb.lower()
        if len(v) > 1 and v.endswith("e") and v[-2] not in VOWELS:
            # Verbs ending in a consonant followed by "e": dance, save, devote, evolve.
            return [v, v, v, v+"s", v, v[:-1]+"ing"] + [v+"d"]*6
        if len(v) > 1 and v.endswith("y") and v[-2] not in VOWELS:
            # Verbs ending in a consonant followed by "y": comply, copy, magnify.
            return [v, v, v, v[:-1]+"ies", v, v+"ing"] + [v[:-1]+"ied"]*6
        if v.endswith(("ss", "sh", "ch", "x")):
            # Verbs ending in sibilants: kiss, bless, box, polish, preach.
            return [v, v, v, v+"es", v, v+"ing"] + [v+"ed"]*6
        if v.endswith("ic"):
            # Verbs ending in -ic: panic, mimic.
            return [v, v, v, v+"es", v, v+"king"] + [v+"ked"]*6
        if len(v) > 1 and v[-1] not in VOWELS and v[-2] not in VOWELS:
            # Verbs ending in a consonant cluster: delight, clamp.
            return [v, v, v, v+"s", v, v+"ing"] + [v+"ed"]*6
        if (len(v) > 1 and v.endswith(("y", "w")) and v[-2] in VOWELS) \
        or (len(v) > 2 and v[-1] not in VOWELS and v[-2] in VOWELS and v[-3] in VOWELS) \
        or (len(v) > 3 and v[-1] not in VOWELS and v[-3] in VOWELS and v[-4] in VOWELS):
            # Verbs ending in a long vowel or diphthong followed by a consonant: paint, devour, play.
            return [v, v, v, v+"s", v, v+"ing"] + [v+"ed"]*6
        if len(v) > 2 and v[-1] not in VOWELS and v[-2] in VOWELS and v[-3] not in VOWELS:
            # Verbs ending in a short vowel followed by a consonant: chat, chop, or compel.
            return [v, v, v, v+"s", v, v+v[-1]+"ing"] + [v+v[-1]+"ed"]*6
        return [v, v, v, v+"s", v, v+"ing"] + [v+"ed"]*6

verbs = Verbs()

conjugate, lemma, lexeme, tenses = \
    verbs.conjugate, verbs.lemma, verbs.lexeme, verbs.tenses

#print conjugate("imaginarify", "part", parse=True)
#print conjugate("imaginarify", "part", parse=False)

#### COMPARATIVE & SUPERLATIVE #####################################################################

VOWELS = "aeiouy"

grade_irregular = {
       "bad": (  "worse", "worst"),
       "far": ("further", "farthest"),
      "good": ( "better", "best"), 
      "hind": ( "hinder", "hindmost"),
       "ill": (  "worse", "worst"),
      "less": ( "lesser", "least"),
    "little": (   "less", "least"),
      "many": (   "more", "most"),
      "much": (   "more", "most"),
      "well": ( "better", "best")
}

grade_uninflected = ["giant", "glib", "hurt", "known", "madly"]

COMPARATIVE = "er"
SUPERLATIVE = "est"

def _count_syllables(word):
    """ Returns the estimated number of syllables in the word by counting vowel-groups.
    """
    n = 0
    p = False # True if the previous character was a vowel.
    for ch in word.endswith("e") and word[:-1] or word:
        v = ch in VOWELS
        n += int(v and not p)
        p = v
    return n

def grade(adjective, suffix=COMPARATIVE):
    """ Returns the comparative or superlative form of the given adjective.
    """
    n = _count_syllables(adjective)	
    if adjective in grade_irregular:
        # A number of adjectives inflect irregularly.
        return grade_irregular[adjective][suffix != COMPARATIVE]
    elif adjective in grade_uninflected:
        # A number of adjectives don't inflect at all.
        return "%s %s" % (suffix == COMPARATIVE and "more" or "most", adjective)
    elif n <= 2 and adjective.endswith("e"):
        # With one syllable and ending with an e: larger, wiser.
        suffix = suffix.lstrip("e")
    elif n == 1 and len(adjective) >= 3 \
     and adjective[-1] not in VOWELS and adjective[-2] in VOWELS and adjective[-3] not in VOWELS:
        # With one syllable ending with consonant-vowel-consonant: bigger, thinner.
        if not adjective.endswith(("w")): # Exceptions: lower, newer.
            suffix = adjective[-1] + suffix
    elif n == 1:
        # With one syllable ending with more consonants or vowels: briefer.
        pass
    elif n == 2 and adjective.endswith("y"):
        # With two syllables ending with a y: funnier, hairier.
        adjective = adjective[:-1] + "i"
    elif n == 2 and adjective[-2:] in ("er", "le", "ow"):
        # With two syllables and specific suffixes: gentler, narrower.
        pass
    else:
        # With three or more syllables: more generous, more important.
        return "%s %s" % (suffix==COMPARATIVE and "more" or "most", adjective)
    return adjective + suffix

def comparative(adjective):
    return grade(adjective, COMPARATIVE)

def superlative(adjective):
    return grade(adjective, SUPERLATIVE)

#### ATTRIBUTIVE & PREDICATIVE #####################################################################

def attributive(adjective):
    return adjective

def predicative(adjective):
    return adjective
