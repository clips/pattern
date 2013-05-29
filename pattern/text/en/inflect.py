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
    MODULE = os.path.dirname(os.path.abspath(__file__))
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
    ["euler|hour(?!i)|heir|honest|hono", "an"],       # exceptions: an hour, an honor
    # Abbreviations:
    # strings of capitals starting with a vowel-sound consonant followed by another consonant,
    # which are not likely to be real words.
    ["(?!FJO|[HLMNS]Y.|RY[EO]|SQU|(F[LR]?|[HL]|MN?|N|RH?|S[CHKLMNPTVW]?|X(YL)?)[AEIOU])[FHLMNRSX][A-Z]", "an"],
    ["^[aefhilmnorsx][.-]", "an"],
    ["^[a-z][.-]", "a"],
    ["^[^aeiouy]", "a"],                              # consonants: a bear
    ["^e[uw]", "a"],                                  # eu like "you": a european
    ["^onc?e", "a"],                                  # o like "wa": a one-liner
    ["uni([^nmd]|mo)", "a"],                          # u like "you": a university
    ["^u[bcfhjkqrst][aeiou]", "a"],                   # u like "you": a uterus
    ["^[aeiou]", "an"],                               # vowels: an owl
    ["y(b[lor]|cl[ea]|fere|gg|p[ios]|rou|tt)", "an"], # y like "i": an yclept, a year
    ["", "a"]                                         # guess "a"
))

def definite_article(word):
    return "the"

def indefinite_article(word):
    """ Returns the indefinite article for a given word.
        For example: university => a university.
    """
    word = word.split(" ")[0]
    for rule, article in RE_ARTICLE:
        if rule.search(word) is not None:
            return article

DEFINITE, INDEFINITE = \
    "definite", "indefinite"

def article(word, function=INDEFINITE):
    """ Returns the indefinite (a/an) or definite (the) article for the given word.
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

# Prepositions are used to solve things like
# "mother-in-law" or "man at arms"
plural_prepositions = [
    "about", "above", "across", "after", "among", "around", "at", "athwart", "before", "behind", 
    "below", "beneath", "beside", "besides", "between", "betwixt", "beyond", "but", "by", "during", 
    "except", "for", "from", "in", "into", "near", "of", "off", "on", "onto", "out", "over", 
    "since", "till", "to", "under", "until", "unto", "upon", "with"
]

# Inflection rules that are either general,
# or apply to a certain category of words,
# or apply to a certain category of words only in classical mode,
# or apply only in classical mode.
# Each rule consists of:
# suffix, inflection, category and classic flag.
plural_rules = [
    # 0) Indefinite articles and demonstratives.
    [["^a$|^an$", "some", None, False],
     ["^this$", "these", None, False],
     ["^that$", "those", None, False],
     ["^any$", "all", None, False]
    ],
    # 1) Possessive adjectives.
    # Overlaps with 1/ for "his" and "its".
    # Overlaps with 2/ for "her".
    [["^my$", "our", None, False],
     ["^your$|^thy$", "your", None, False],
     ["^her$|^his$|^its$|^their$", "their", None, False]
    ],
    # 2) Possessive pronouns.
    [["^mine$", "ours", None, False],
     ["^yours$|^thine$", "yours", None, False],
     ["^hers$|^his$|^its$|^theirs$", "theirs", None, False]
    ],
    # 3) Personal pronouns.
    [["^I$", "we", None, False],
     ["^me$", "us", None, False],
     ["^myself$", "ourselves", None, False],
     ["^you$", "you", None, False],
     ["^thou$|^thee$", "ye", None, False],
     ["^yourself$|^thyself$", "yourself", None, False],
     ["^she$|^he$|^it$|^they$", "they", None, False],
     ["^her$|^him$|^it$|^them$", "them", None, False],
     ["^herself$|^himself$|^itself$|^themself$", "themselves", None, False],
     ["^oneself$", "oneselves", None, False]
    ],
    # 4) Words that do not inflect.
    [["$", "", "uninflected", False],
     ["$", "", "uncountable", False],
     ["s$", "s", "s-singular", False],
     ["fish$", "fish", None, False],
     ["([- ])bass$", "\\1bass", None, False],
     ["ois$", "ois", None, False],
     ["sheep$", "sheep", None, False],
     ["deer$", "deer", None, False],
     ["pox$", "pox", None, False],
     ["([A-Z].*)ese$", "\\1ese", None, False],
     ["itis$", "itis", None, False],
     ["(fruct|gluc|galact|lact|ket|malt|rib|sacchar|cellul)ose$", "\\1ose", None, False]
    ],
    # 5) Irregular plurals (mongoose, oxen).
    [["atlas$", "atlantes", None, True],
     ["atlas$", "atlases", None, False],
     ["beef$", "beeves", None, True],
     ["brother$", "brethren", None, True],
     ["child$", "children", None, False],
     ["corpus$", "corpora", None, True],
     ["corpus$", "corpuses", None, False],
     ["^cow$", "kine", None, True],
     ["ephemeris$", "ephemerides", None, False],
     ["ganglion$", "ganglia", None, True],
     ["genie$", "genii", None, True],
     ["genus$", "genera", None, False],
     ["graffito$", "graffiti", None, False],
     ["loaf$", "loaves", None, False],
     ["money$", "monies", None, True],
     ["mongoose$", "mongooses", None, False],
     ["mythos$", "mythoi", None, False],
     ["octopus$", "octopodes", None, True],
     ["opus$", "opera", None, True],
     ["opus$", "opuses", None, False],
     ["^ox$", "oxen", None, False],
     ["penis$", "penes", None, True],
     ["penis$", "penises", None, False],
     ["soliloquy$", "soliloquies", None, False],
     ["testis$", "testes", None, False],
     ["trilby$", "trilbys", None, False],
     ["turf$", "turves", None, True],
     ["numen$", "numena", None, False],
     ["occiput$", "occipita", None, True]
    ],
    # 6) Irregular inflections for common suffixes (synopses, mice, men).
    [["man$", "men", None, False],
     ["person$", "people", None, False],
     ["([lm])ouse$", "\\1ice", None, False],
     ["tooth$", "teeth", None, False],
     ["goose$", "geese", None, False],
     ["foot$", "feet", None, False],
     ["zoon$", "zoa", None, False],
     ["([csx])is$", "\\1es", None, False]
    ],
    # 7) Fully assimilated classical inflections (vertebrae, codices).
    [["ex$", "ices", "ex-ices", False],
     ["ex$", "ices", "ex-ices-classical", True],
     ["um$", "a", "um-a", False],
     ["um$", "a", "um-a-classical", True],
     ["on$", "a", "on-a", False],
     ["a$", "ae", "a-ae", False],
     ["a$", "ae", "a-ae-classical", True]
    ],
    # 8) Classical variants of modern inflections (stigmata, soprani).
    [["trix$", "trices", None, True],
     ["eau$", "eaux", None, True],
     ["ieu$", "ieu", None, True],
     ["([iay])nx$", "\\1nges", None, True],
     ["en$", "ina", "en-ina-classical", True],
     ["a$", "ata", "a-ata-classical", True],
     ["is$", "ides", "is-ides-classical", True],
     ["us$", "i", "us-i-classical", True],
     ["us$", "us", "us-us-classical", True],
     ["o$", "i", "o-i-classical", True],
     ["$", "i", "-i-classical", True],
     ["$", "im", "-im-classical", True]
    ],
    # 9) -ch, -sh and -ss take -es in the plural (churches, classes).
    [["([cs])h$", "\\1hes", None, False],
     ["ss$", "sses", None, False],
     ["x$", "xes", None, False]
    ],
    # 10) Certain words ending in -f or -fe take -ves in the plural (lives, wolves).
    [["([aeo]l)f$", "\\1ves", None, False],
     ["([^d]ea)f$", "\\1ves", None, False],
     ["arf$", "arves", None, False],
     ["([nlw]i)fe$", "\\1ves", None, False],
    ],
    # 11) -y takes -ys if preceded by a vowel or when a proper noun,
    # but -ies if preceded by a consonant (storeys, Marys, stories).
    [["([aeiou])y$", "\\1ys", None, False],
     ["([A-Z].*)y$", "\\1ys", None, False],
     ["y$", "ies", None, False]
    ],
    # 12) Some words ending in -o take -os, the rest take -oes.
    # Words in which the -o is preceded by a vowel always take -os (lassos, potatoes, bamboos).
    [["o$", "os", "o-os", False],
     ["([aeiou])o$", "\\1os", None, False],
     ["o$", "oes", None, False]
    ],
    # 13) Miltary stuff (Major Generals).
    [["l$", "ls", "general-generals", False]
    ],
    # 14) Otherwise, assume that the plural just adds -s (cats, programmes).
    [["$", "s", None, False]
    ],
]

# For performance, compile the regular expressions only once:
for ruleset in plural_rules:
    for rule in ruleset:
        rule[0] = re.compile(rule[0])

# Suffix categories.
plural_categories = {
    "uninflected": [
        "bison", "bream", "breeches", "britches", "carp", "chassis", "clippers", "cod", "contretemps",
        "corps", "debris", "diabetes", "djinn", "eland", "elk", "flounder", "gallows", "graffiti",
        "headquarters", "herpes", "high-jinks", "homework", "innings", "jackanapes", "mackerel",
        "measles", "mews", "mumps", "news", "pincers", "pliers", "proceedings", "rabies", "salmon",
        "scissors", "series", "shears", "species", "swine", "trout", "tuna", "whiting", "wildebeest"],
    "uncountable": [
        "advice", "bread", "butter", "cheese", "electricity", "equipment", "fruit", "furniture",
        "garbage", "gravel", "happiness", "information", "ketchup", "knowledge", "love", "luggage",
        "mathematics", "mayonnaise", "meat", "mustard", "news", "progress", "research", "rice",
        "sand", "software", "understanding", "water"],
    "s-singular": [
        "acropolis", "aegis", "alias", "asbestos", "bathos", "bias", "caddis", "cannabis", "canvas",
        "chaos", "cosmos", "dais", "digitalis", "epidermis", "ethos", "gas", "glottis", "glottis",
        "ibis", "lens", "mantis", "marquis", "metropolis", "pathos", "pelvis", "polis", "rhinoceros",
        "sassafras", "trellis"],
    "ex-ices": ["codex", "murex", "silex"],
    "ex-ices-classical": [
        "apex", "cortex", "index", "latex", "pontifex", "simplex", "vertex", "vortex"],
    "um-a": [
        "agendum", "bacterium", "candelabrum", "datum", "desideratum", "erratum", "extremum", 
        "ovum", "stratum"],
    "um-a-classical": [
        "aquarium", "compendium", "consortium", "cranium", "curriculum", "dictum", "emporium",
        "enconium", "gymnasium", "honorarium", "interregnum", "lustrum", "maximum", "medium",
        "memorandum", "millenium", "minimum", "momentum", "optimum", "phylum", "quantum", "rostrum",
        "spectrum", "speculum", "stadium", "trapezium", "ultimatum", "vacuum", "velum"],
    "on-a": [
        "aphelion", "asyndeton", "criterion", "hyperbaton", "noumenon", "organon", "perihelion",
        "phenomenon", "prolegomenon"],
    "a-ae": ["alga", "alumna", "vertebra"],
    "a-ae-classical": [
        "abscissa", "amoeba", "antenna", "aurora", "formula", "hydra", "hyperbola", "lacuna",
        "medusa", "nebula", "nova", "parabola"],
    "en-ina-classical": ["foramen", "lumen", "stamen"],
    "a-ata-classical": [
        "anathema", "bema", "carcinoma", "charisma", "diploma", "dogma", "drama", "edema", "enema",
        "enigma", "gumma", "lemma", "lymphoma", "magma", "melisma", "miasma", "oedema", "sarcoma",
        "schema", "soma", "stigma", "stoma", "trauma"],
    "is-ides-classical": ["clitoris", "iris"],
    "us-i-classical": [
        "focus", "fungus", "genius", "incubus", "nimbus", "nucleolus", "radius", "stylus", "succubus",
        "torus", "umbilicus", "uterus"],
    "us-us-classical": [
        "apparatus", "cantus", "coitus", "hiatus", "impetus", "nexus", "plexus", "prospectus",
        "sinus", "status"],
    "o-i-classical": ["alto", "basso", "canto", "contralto", "crescendo", "solo", "soprano", "tempo"],
    "-i-classical": ["afreet", "afrit", "efreet"],
    "-im-classical": ["cherub", "goy", "seraph"],
    "o-os": [
        "albino", "archipelago", "armadillo", "commando", "ditto", "dynamo", "embryo", "fiasco",
        "generalissimo", "ghetto", "guano", "inferno", "jumbo", "lingo", "lumbago", "magneto",
        "manifesto", "medico", "octavo", "photo", "pro", "quarto", "rhino", "stylo"],
    "general-generals": [
        "Adjutant", "Brigadier", "Lieutenant", "Major", "Quartermaster", 
        "adjutant", "brigadier", "lieutenant", "major", "quartermaster"],
}

def pluralize(word, pos=NOUN, custom={}, classical=True):
    """ Returns the plural of a given word.
        For example: child -> children.
        Handles nouns and adjectives, using classical inflection by default
        (e.g. where "matrix" pluralizes to "matrices" instead of "matrixes").
        The custom dictionary is for user-defined replacements.
    """

    if word in custom:
        return custom[word]

    # Recursion of genitives.
    # Remove the apostrophe and any trailing -s, 
    # form the plural of the resultant noun, and then append an apostrophe (dog's -> dogs').
    if word.endswith("'") or word.endswith("'s"):
        owner = word.rstrip("'s")
        owners = pluralize(owner, pos, custom, classical)
        if owners.endswith("s"):
            return owners + "'"
        else:
            return owners + "'s"
            
    # Recursion of compound words
    # (Postmasters General, mothers-in-law, Roman deities).    
    words = word.replace("-", " ").split(" ")
    if len(words) > 1:
        if words[1] == "general" or words[1] == "General" and \
            words[0] not in plural_categories["general-generals"]:
            return word.replace(words[0], pluralize(words[0], pos, custom, classical))
        elif words[1] in plural_prepositions:
            return word.replace(words[0], pluralize(words[0], pos, custom, classical))
        else:
            return word.replace(words[-1], pluralize(words[-1], pos, custom, classical))
    
    # Only a very few number of adjectives inflect.
    n = range(len(plural_rules))
    if pos.startswith(ADJECTIVE):
        n = [0, 1]

    # Apply pluralization rules.      
    for i in n:
        ruleset = plural_rules[i]	
        for rule in ruleset:
            suffix, inflection, category, classic = rule
            # A general rule, or a classic rule in classical mode.
            if category == None:
                if not classic or (classic and classical):
                    if suffix.search(word) is not None:
                        return suffix.sub(inflection, word)
            # A rule relating to a specific category of words.
            if category != None:
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
    ['(?i)(.)ae$', '\\1a'],
    ['(?i)(.)itis$', '\\1itis'],
    ['(?i)(.)eaux$', '\\1eau'],
    ['(?i)(quiz)zes$', '\\1'],
    ['(?i)(matr)ices$', '\\1ix'],
    ['(?i)(ap|vert|ind)ices$', '\\1ex'],
    ['(?i)^(ox)en', '\\1'],
    ['(?i)(alias|status)es$', '\\1'],
    ['(?i)([octop|vir])i$', '\\1us'],
    ['(?i)(cris|ax|test)es$', '\\1is'],
    ['(?i)(shoe)s$', '\\1'],
    ['(?i)(o)es$', '\\1'],
    ['(?i)(bus)es$', '\\1'],
    ['(?i)([m|l])ice$', '\\1ouse'],
    ['(?i)(x|ch|ss|sh)es$', '\\1'],
    ['(?i)(m)ovies$', '\\1ovie'],
    ['(?i)(.)ombies$', '\\1ombie'],
    ['(?i)(s)eries$', '\\1eries'],
    ['(?i)([^aeiouy]|qu)ies$', '\\1y'],
	# Certain words ending in -f or -fe take -ves in the plural (lives, wolves).
    ["([aeo]l)ves$", "\\1f"],
    ["([^d]ea)ves$", "\\1f"],
    ["arves$", "arf"],
    ["erves$", "erve"],
    ["([nlw]i)ves$", "\\1fe"],   
    ['(?i)([lr])ves$', '\\1f'],
    ["([aeo])ves$", "\\1ve"],
    ['(?i)(sive)s$', '\\1'],
    ['(?i)(tive)s$', '\\1'],
    ['(?i)(hive)s$', '\\1'],
    ['(?i)([^f])ves$', '\\1fe'],
    # -es suffix.
    ['(?i)(^analy)ses$', '\\1sis'],
    ['(?i)((a)naly|(b)a|(d)iagno|(p)arenthe|(p)rogno|(s)ynop|(t)he)ses$', '\\1\\2sis'],
    ['(?i)(.)opses$', '\\1opsis'],
    ['(?i)(.)yses$', '\\1ysis'],
    ['(?i)(h|d|r|o|n|b|cl|p)oses$', '\\1ose'],
    ['(?i)(fruct|gluc|galact|lact|ket|malt|rib|sacchar|cellul)ose$', '\\1ose'],
    ['(?i)(.)oses$', '\\1osis'],
    # -a
    ['(?i)([ti])a$', '\\1um'],
    ['(?i)(n)ews$', '\\1ews'],
    ['(?i)s$', ''],
]

# For performance, compile the regular expressions only once:
for rule in singular_rules:
    rule[0] = re.compile(rule[0])

singular_uninflected = [
    "bison", "bream", "breeches", "britches", "carp", "chassis", "christmas", "clippers", "cod", 
    "contretemps", "corps", "debris", "diabetes", "djinn", "eland", "elk", "flounder", "gallows", 
    "georgia", "graffiti", "headquarters", "herpes", "high-jinks", "homework", "innings", 
    "jackanapes", "mackerel", "measles", "mews", "mumps", "news", "pincers", "pliers", "proceedings", 
    "rabies", "salmon", "scissors", "series", "shears", "species", "swine", "swiss", "trout", "tuna", 
    "whiting", "wildebeest"
]
singular_uncountable = [
    "advice", "bread", "butter", "cheese", "electricity", "equipment", "fruit", "furniture", 
    "garbage", "gravel", "happiness", "information", "ketchup", "knowledge", "love", "luggage", 
    "mathematics", "mayonnaise", "meat", "mustard", "news", "progress", "research", "rice", "sand", 
    "software", "understanding", "water"
]
singular_ie = [
    "algerie", "auntie", "beanie", "birdie", "bogie", "bombie", "bookie", "collie", "cookie", "cutie", 
    "doggie", "eyrie", "freebie", "goonie", "groupie", "hankie", "hippie", "hoagie", "hottie", 
    "indie", "junkie", "laddie", "laramie", "lingerie", "meanie", "nightie", "oldie", "^pie", 
    "pixie", "quickie", "reverie", "rookie", "softie", "sortie", "stoolie", "sweetie", "techie", 
    "^tie", "toughie", "valkyrie", "veggie", "weenie", "yuppie", "zombie"
]
singular_irregular = {
            "men": "man",
         "people": "person",
       "children": "child",
          "sexes": "sex",
           "axes": "axe",
          "moves": "move",
          "teeth": "tooth",
          "geese": "goose",
           "feet": "foot",
            "zoa": "zoon",
       "atlantes": "atlas", 
        "atlases": "atlas", 
         "beeves": "beef", 
       "brethren": "brother", 
       "children": "child", 
        "corpora": "corpus", 
       "corpuses": "corpus", 
           "kine": "cow", 
    "ephemerides": "ephemeris", 
        "ganglia": "ganglion", 
          "genii": "genie", 
         "genera": "genus", 
       "graffiti": "graffito", 
         "helves": "helve",
         "leaves": "leaf",
         "loaves": "loaf", 
         "monies": "money", 
      "mongooses": "mongoose", 
         "mythoi": "mythos", 
      "octopodes": "octopus", 
          "opera": "opus", 
         "opuses": "opus", 
           "oxen": "ox", 
          "penes": "penis", 
        "penises": "penis", 
    "soliloquies": "soliloquy", 
         "testes": "testis", 
        "trilbys": "trilby", 
         "turves": "turf", 
         "numena": "numen", 
       "occipita": "occiput", 
            "our": "my",
}

def singularize(word, pos=NOUN, custom={}):

    if word in custom.keys():
        return custom[word]

    # Recursion of compound words (e.g. mothers-in-law). 
    if "-" in word:
        words = word.split("-")
        if len(words) > 1 and words[1] in plural_prepositions:
            return singularize(words[0], pos, custom)+"-"+"-".join(words[1:])
    # dogs' => dog's
    if word.endswith("'"):
        return singularize(word[:-1]) + "'s"

    lower = word.lower()
    for w in singular_uninflected:
        if w.endswith(lower):
            return word
    for w in singular_uncountable:
        if w.endswith(lower):
            return word
    for w in singular_ie:
        if lower.endswith(w+"s"):
            return w
    for w in singular_irregular.keys():
        if lower.endswith(w):
            return re.sub('(?i)'+w+'$', singular_irregular[w], word)

    for rule in singular_rules:
        suffix, inflection = rule
        match = suffix.search(word)
        if match:
            groups = match.groups()
            for k in range(0, len(groups)):
                if groups[k] == None:
                    inflection = inflection.replace('\\'+str(k+1), '')
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
       "bad": ("worse", "worst"),
       "far": ("further", "farthest"),
      "good": ("better", "best"), 
      "hind": ("hinder", "hindmost"),
       "ill": ("worse", "worst"),
      "less": ("lesser", "least"),
    "little": ("less", "least"),
      "many": ("more", "most"),
      "much": ("more", "most"),
      "well": ("better", "best")
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
