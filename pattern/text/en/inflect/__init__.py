#### PATTERN | EN | INFLECT ########################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# A set of rule-based tools for English word inflection:
# - pluralization and singularization of nouns and adjectives,
# - conjugation of verbs,
# - comparatives and superlatives of adjectives.

import re
import os

try:
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"

# Accuracy (measured on CELEX English morphology word forms):
# 95% pluralize()
# 96% singularize()
# 95% _parse_lemma()
# 96% _parse_lexeme()

#### ARTICLE #######################################################################################
# Based on the Ruby Linguistics module by Michael Granger:
# http://www.deveiate.org/projects/Linguistics/wiki/English

article_rules = [        
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
]

# Compile the regular expressions.
for p in article_rules:
    p[0] = re.compile(p[0])

def definite_article(word):
    return "the"

def indefinite_article(word):
    """ Returns the indefinite article for a given word.
        For example: university => a university.
    """
    word = word.split(" ")[0]
    for rule, article in article_rules:
        if rule.search(word) is not None:
            return article

DEFINITE   = "definite"
INDEFINITE = "indefinite"

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

    if word in custom.keys():
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
# Each verb has morphs for infinitive, 3rd singular present, present participle, past and past participle.
# Verbs like "be" have other morphs as well (i.e. I am, you are, she is, they aren't).
# The following verbs can be negated: be, can, do, will, must, have, may, need, dare, ought.

INFINITIVE                  = "infinitive"
PRESENT_1ST_PERSON_SINGULAR = "present 1st person singular"
PRESENT_2ND_PERSON_SINGULAR = "present 2nd person singular"
PRESENT_3RD_PERSON_SINGULAR = "present 3rd person singular"
PRESENT_PLURAL              = "present plural"
PRESENT_PARTICIPLE          = "present participle"
PAST                        = "past"
PAST_1ST_PERSON_SINGULAR    = "past 1st person singular"
PAST_2ND_PERSON_SINGULAR    = "past 2nd person singular"
PAST_3RD_PERSON_SINGULAR    = "past 3rd person singular"
PAST_PLURAL                 = "past plural"
PAST_PARTICIPLE             = "past participle"

# Index of a tense in the source lexicon:
tenses_index = {
    INFINITIVE                  : 0,
    PRESENT_1ST_PERSON_SINGULAR : 1,
    PRESENT_2ND_PERSON_SINGULAR : 2,
    PRESENT_3RD_PERSON_SINGULAR : 3,
    PRESENT_PLURAL              : 4,
    PRESENT_PARTICIPLE          : 5,
    PAST_1ST_PERSON_SINGULAR    : 6,
    PAST_2ND_PERSON_SINGULAR    : 7,
    PAST_3RD_PERSON_SINGULAR    : 8,
    PAST_PLURAL                 : 9,
    PAST                        : 10,
    PAST_PARTICIPLE             : 11
}

# Shorthand tenses can be passed to conjugate() and Tenses.__contains__():
tenses_alias = (
    (INFINITIVE,                  ["inf", "VB"]),
    (PRESENT_1ST_PERSON_SINGULAR, ["1sg", "VBP"]),
    (PRESENT_2ND_PERSON_SINGULAR, ["2sg"]),
    (PRESENT_3RD_PERSON_SINGULAR, ["3sg", "VBZ"]),
    (PRESENT_PLURAL,              ["pl", "plural"]),
    (PRESENT_PARTICIPLE,          ["part", "prog", "progressive", "gerund", "VBG"]),
    (PAST,                        ["p", "VBD"]),
    (PAST_1ST_PERSON_SINGULAR,    ["1sgp"]),
    (PAST_2ND_PERSON_SINGULAR,    ["2sgp"]),
    (PAST_3RD_PERSON_SINGULAR,    ["3sgp"]),
    (PAST_PLURAL,                 ["ppl", "pplural"]),
    (PAST_PARTICIPLE,             ["ppart", "VBN"]),    
)
a = {}
for k, v in tenses_alias:
    for v in v: 
        a[v] = k
tenses_alias = a # alias => tense

class Verbs:
    
    def __init__(self, path=os.path.join(MODULE, "verbs.txt")):
        self.path    = path
        self._tenses = None # Dictionary of infinitive => list of tenses.
        self._lemmas = None # Dictionary of tense => infinitive. 
        self.parse_lemma  = lambda v: v
        self.parse_lexeme = lambda v: []

    @property
    def infinitives(self):
        if not self._tenses: self.load()
        return self._tenses
    @property
    def inflections(self):
        if not self._lemmas: self.load()
        return self._lemmas
    @property
    def TENSES(self):
        return tenses_index.keys()

    def __iter__(self):
        if not self._tenses: self.load(); return iter(self._tenses)
    def __len__(self):
        if not self._tenses: self.load(); return len(self._tenses)
    def __contains__(self, k):
        if not self._tenses: self.load(); return self._tenses.__contains__(k)
    def __setitem__(self, k, v):
        if not self._tenses: self.load(); self._tenses[k] = v
    def __getitem__(self, k):
        if not self._tenses: self.load(); return self._tenses[k]
    def get(self, k, default=None):
        if not self._tenses: self.load(); return self._tenses.get(k, default)
    
    def load(self):
        # The data is lazily loaded when lemma() is called the first time.
        # The verb.txt morphology is adopted from the XTAG morph_english.flat: 
        # http://www.cis.upenn.edu/~xtag/
        self._tenses = {}
        self._lemmas = {}
        for v in (v for v in reversed(open(self.path).readlines()) if not v.startswith(";;;")):
            v = v.strip().split(",")
            self._tenses[v[0]] = v
            for tense in (tense for tense in v if tense != ""): 
                self._lemmas[tense] = v[0]
                
    def __contains__(self, verb):
        if self._lemmas is None: 
            self.load()
        return verb in self._lemmas

    def lemma(self, verb, parse=True):
        """ Returns the infinitive form of the given verb (or None).
        """
        if self._tenses is None:
            self.load()
        if verb.lower() in self._lemmas:
            return self._lemmas[verb.lower()]
        if verb in self._lemmas:
            return self._lemmas[verb]
        if parse is True:
            # Rule-based approach.
            return self.parse_lemma(verb)

    def lexeme(self, verb, parse=True):
        """ Returns all possible inflections of the given verb.
        """
        b = self.lemma(verb)
        if b in self._tenses:
            a = [x for x in self._tenses.get(b, []) if x != ""]
            u = []; [u.append(x) for x in a if x not in u]
            return u
        if parse is True:
            # Rule-based approach.
            a = self.parse_lexeme(self.parse_lemma(verb))
            return [a[0], a[3], a[5], a[6]]
        return []

    def conjugate(self, verb, tense=INFINITIVE, negated=False, parse=True):
        """ Inflects the verb and returns the given tense (or None).
            For example: be
            - present 1sg/2sg/3sg/pl => I am, you are, she is, we are
            - present participle => being,
            - past => I was, you were, he was, we were
            - past participle => been,
            - negated present => I am not, you aren't, it isn't.
        """
        # Disambiguate aliases: "pl" => "present plural".
        # Get the associated tense index.
        t = tenses_alias.get(tense, tense) 
        i = tenses_index.get(t) + (negated and len(tenses_index) or 0)
        b = self.lemma(verb)
        if b in self._tenses:
            x = self._tenses[b][i]
            if x == "":
                # No tense for 1sg/2sg/3sg => return base form.
                if 0 < i <= 5: x = b
                # No tense for 1sgp/2sgp/3sgp => return past form.
                if 5 < i <= 9: x = self._tenses[b][10]
            return x
        if parse is True:
            # Rule-based approach.
            return self.parse_lexeme(self.parse_lemma(verb))[i]

    def tenses(self, verb, parse=True):
        """ Returns a list of tenses for the given verb inflection.
        """
        verb = verb.lower()
        b = self.lemma(verb)
        a = []
        if b in self._tenses:
            for tense, i in tenses_index.items():
                t = self._tenses[b]
                if t[i] == verb \
                or t[i+len(tenses_index)] == verb \
                or t[i] == "" and 0 < i <= 5 and verb == b \
                or t[i] == "" and 5 < i <= 9 and verb == t[10]:
                    a.append(tense)
        elif parse is True:
            # Rule-based approach.
            v = self.parse_lexeme(self.parse_lemma(verb))
            [a.append(tense) for tense, i in tenses_index.items() if i<len(v) and v[i] == verb]
        return Tenses(sorted(a))

class Tenses(list):
    def __contains__(self, tense):
        # t in tenses(verb) also works when t is an alias (e.g. "1sg").
        return list.__contains__(self, tenses_alias.get(tense, tense))

_verbs = VERBS = Verbs()
conjugate, lemma, lexeme, tenses = \
    _verbs.conjugate, _verbs.lemma, _verbs.lexeme, _verbs.tenses

#print conjugate("is", "ppart")
#print lemma("went")
#print lexeme("have")
#print tenses("have")

#--- RULE-BASED VERB CONJUGATION -------------------------------------------------------------------

VOWELS = "aeiouy"
re_vowel = re.compile(r"a|e|i|o|u|y", re.I)

def _parse_lemma(verb):
    """ Returns the base form of the given inflected verb, using a rule-based approach.
        This is problematic if a verb ending in -e is given in the past tense or gerund.
    """
    v = verb.lower()
    b = False
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

def _parse_lexeme(verb):
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

_verbs.parse_lemma  = _parse_lemma
_verbs.parse_lexeme = _parse_lexeme

#print conjugate("imaginarify", "part", parse=True)
#print conjugate("imaginarify", "part", parse=False)

# Accuracy of _parse_lemma():
#i = 0
#for v in VERBS.infinitives:
#    for tense in VERBS.TENSES:
#        if _parse_lemma(conjugate(v, tense)) == v: i+=1
#print float(i) / len(_verbs._tenses)*8

# Accuracy of _parse_lexeme():
#_verbs.load()
#i = 0
#n = 0
#for v, x1 in _verbs._tenses.iteritems():
#    x2 = _parse_lexeme(v)
#    for j in range(len(x2)):
#        if x1[j] and x1[j] == x2[j] or x1[j] == "" and x1[j>5 and 10 or 0] == x2[j]: i+=1
#        n += 1
#print float(i) / n

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
