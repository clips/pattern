#### PATTERN | ES | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# A set of rule-based tools for Spanish word inflection:
# - pluralization and singularization of nouns,
# - conjugation of verbs

import re
import os

try:
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"
VOWELS = ("a", "e", "i", "o", "u")
vowel = lambda ch: ch in VOWELS

def normalize(vowel):
    return {u"á":"a", u"é":"e", u"í":"i", u"ó":"o", u"ú":"u"}.get(vowel, vowel)

# Accuracy:
# 78% pluralize()
# 94% singularize()
# 81% _parse_lemma() (0.55 regular 87% + 0.45 irregular 74%)
# 87% _parse_lexeme() (0.55 regular 99% + 0.45 irregular 72%)
# 93% predicative()

#### ARTICLE #######################################################################################
# Spanish inflection of depends on gender and number.

# Inflection gender.
MASCULINE, FEMININE, NEUTER, PLURAL = MALE, FEMALE, NEUTRAL, PLURAL = \
    "m", "f", "n", "p"

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

DEFINITE   = "definite"
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
    return "%s %s" % (_article(word, article), word)

#### PLURALIZE #####################################################################################

plural_irregular = {
     u"mamá": u"mamás",
     u"papá": u"papás",
     u"sofá": u"sofás",     
   u"dominó": u"dominós",
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
      "dica", u"grafía", u"logía")):
        return w
    # Words ending in a vowel get -s: gato => gatos.
    if w.endswith(VOWELS) or w.endswith(u"é"):
        return w + "s"
    # Words ending in a stressed vowel get -s: hindú => hindúes.
    if w.endswith((u"á", u"é", u"í", u"ó", u"ú")):
        return w + "es"
    # Words ending in -és get -eses: holandés => holandeses.
    if w.endswith(u"és"):
        return w[:-2] + "eses"
    # Words ending in -s preceded by an unstressed vowel: gafas => gafas.
    if w.endswith(u"s") and len(w) > 3 and vowel(w[-2]):
        return w
    # Words ending in -z get -ces: luz => luces
    if w.endswith(u"z"):
        return w[:-1] + "ces"
    # Words that change vowel stress: graduación => graduaciones.
    for a, b in (
      (u"án", "anes"),
      (u"én", "enes"),
      (u"ín", "ines"),
      (u"ón", "ones"),
      (u"ún", "unes")):
        if w.endswith(a):
            return w[:-2] + b
    # Words ending in a consonant get -es.
    return w + "es"

#print pluralize(u"libro")  # libros
#print pluralize(u"señor")  # señores
#print pluralize(u"ley")    # leyes
#print pluralize(u"mes")    # meses
#print pluralize(u"luz")    # luces
#print pluralize(u"inglés") # ingleses
#print pluralize(u"rubí")   # rubíes
#print pluralize(u"papá")   # papás

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
      ("anes", u"án"),
      ("enes", u"én"),
      ("eses", u"és"),
      ("ines", u"ín"),
      ("ones", u"ón"),
      ("unes", u"ún")):
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

import sys; sys.path.insert(0, os.path.join(MODULE, "..", ".."))
from en.inflect import Verbs
from en.inflect import \
    INFINITIVE, PRESENT, PAST, FUTURE, CONDITIONAL, \
    FIRST, SECOND, THIRD, \
    SINGULAR, PLURAL, SG, PL, \
    INDICATIVE, IMPERATIVE, SUBJUNCTIVE, \
    IMPERFECTIVE, PERFECTIVE, PROGRESSIVE, \
    IMPERFECT, PRETERITE, \
    PARTICIPLE, GERUND

# Defines the tenses on each line in verbs.txt (see pattern.en.inflect.TENSES).
FORMAT = [
    0, 1, 2, 3, 4, 5, 6, 8,     # indicativo presente
    58, 59, 60, 61, 62, 63, 16, # indicativo pretérito
    9, 10, 11, 12, 13, 14,      # indicativo imperfecto
    52, 53, 54, 55, 56, 57,     # indicativo futuro
    70, 71, 72, 73, 74, 75,     # indicativo condicional
    19, 22,                     # imperativo afirmativo
    24, 25, 26, 27, 28, 29,     # subjuntivo presente
    30, 31, 32, 33, 34, 35      # subjuntivo imperfecto
]

DEFAULT = {}

# Load the pattern.en.Verbs class, with a Spanish lexicon instead.
# Lexicon was mined from the Web and contains 570 frequent verbs (290 regular -ar, -er, -ir):
# Spanish Verb Forms, Fred F. Jehle (2012).
# http://users.ipfw.edu/jehle/verblist.htm
_verbs = VERBS = Verbs(os.path.join(MODULE, "verbs.txt"), FORMAT, DEFAULT, language="es")

conjugate, lemma, lexeme, tenses = \
    _verbs.conjugate, _verbs.lemma, _verbs.lexeme, _verbs.tenses

verb_irregular_inflections = [
    (u"yéramos", "ir"),    (u"cisteis", "cer"),   (u"tuviera", "tener"), (u"ndieron", "nder"),
    (u"ndiendo", "nder"),  (u"tándose", "tarse"), (u"ndieran", "nder"),  (u"ndieras", "nder"),
    (u"izaréis", "izar"),  (u"disteis", "der"),   (u"irtiera", "ertir"), (u"pusiera", "poner"),
    (u"endiste", "ender"), (u"laremos", "lar"),   (u"ndíamos", "nder"),  (u"icaréis", "icar"),
    (u"dábamos", "dar"),   (u"intiera", "entir"), (u"iquemos", "icar"),  (u"jéramos", "cir"),
    (u"dierais", "der"),   (u"endiera", "ender"), (u"iéndose", "erse"),  (u"jisteis", "cir"),
    (u"cierais", "cer"),   (u"ecíamos", "ecer"),  (u"áramos", "ar"),     (u"ríamos", "r"),
    (u"éramos", "r"),      (u"iríais", "ir"),     (u"temos", "tar"),     (u"steis", "r"),
    (u"ciera", "cer"),     (u"erais", "r"),       (u"timos", "tir"),     (u"uemos", "ar"),
    (u"tiera", "tir"),     (u"bimos", "bir"),     (u"ciéis", "ciar"),    (u"gimos", "gir"),
    (u"jiste", "cir"),     (u"mimos", "mir"),     (u"guéis", "gar"),     (u"stéis", "star"),
    (u"jimos", "cir"),     (u"inéis", "inar"),    (u"jemos", "jar"),     (u"tenga", "tener"),
    (u"quéis", "car"),     (u"bíais", "bir"),     (u"jeron", "cir"),     (u"uíais", "uir"),
    (u"ntéis", "ntar"),    (u"jeras", "cir"),     (u"jeran", "cir"),     (u"ducía", "ducir"),
    (u"yendo", "ir"),      (u"eemos", "ear"),     (u"ierta", "ertir"),   (u"ierte", "ertir"),
    (u"nemos", "nar"),     (u"ngáis", "ner"),     (u"liera", "ler"),     (u"endió", "ender"),
    (u"uyáis", "uir"),     (u"memos", "mar"),     (u"ciste", "cer"),     (u"ujera", "ucir"),
    (u"uimos", "uir"),     (u"ienda", "ender"),   (u"lléis", "llar"),    (u"iemos", "iar"),
    (u"iende", "ender"),   (u"rimos", "rir"),     (u"semos", "sar"),     (u"itéis", "itar"),
    (u"gíais", "gir"),     (u"ndáis", "nder"),    (u"tíais", "tir"),     (u"demos", "dar"),
    (u"lemos", "lar"),     (u"ponga", "poner"),   (u"yamos", "ir"),      (u"icéis", "izar"),
    (u"bais", "r"),        (u"rías", "r"),        (u"rían", "r"),        (u"iría", "ir"),
    (u"eran", "r"),        (u"eras", "r"),        (u"irán", "ir"),       (u"irás", "ir"),
    (u"ongo", "oner"),     (u"aiga", "aer"),      (u"ímos", "ir"),       (u"ibía", "ibir"),
    (u"diga", "decir"),    (u"edía", "edir"),     (u"orte", "ortar"),    (u"guió", "guir"),
    (u"iega", "egar"),     (u"oren", "orar"),     (u"ores", "orar"),     (u"léis", "lar"),
    (u"irme", "irmar"),    (u"siga", "seguir"),   (u"séis", "sar"),      (u"stré", "strar"),
    (u"cien", "ciar"),     (u"cies", "ciar"),     (u"dujo", "ducir"),    (u"eses", "esar"),
    (u"esen", "esar"),     (u"coja", "coger"),    (u"lice", "lizar"),    (u"tías", "tir"),
    (u"tían", "tir"),      (u"pare", "parar"),    (u"gres", "grar"),     (u"gren", "grar"),
    (u"tuvo", "tener"),    (u"uían", "uir"),      (u"uías", "uir"),      (u"quen", "car"),
    (u"ques", "car"),      (u"téis", "tar"),      (u"iero", "erir"),     (u"iere", "erir"),
    (u"uche", "uchar"),    (u"tuve", "tener"),    (u"inen", "inar"),     (u"pire", "pirar"),
    (u"reía", "reir"),     (u"uste", "ustar"),    (u"ibió", "ibir"),     (u"duce", "ducir"),
    (u"icen", "izar"),     (u"ices", "izar"),     (u"ines", "inar"),     (u"ires", "irar"),
    (u"iren", "irar"),     (u"duje", "ducir"),    (u"ille", "illar"),    (u"urre", "urrir"),
    (u"tido", "tir"),      (u"ndió", "nder"),     (u"uido", "uir"),      (u"uces", "ucir"),
    (u"ucen", "ucir"),     (u"iéis", "iar"),      (u"eció", "ecer"),     (u"jéis", "jar"),
    (u"erve", "ervar"),    (u"uyas", "uir"),      (u"uyan", "uir"),      (u"tía", "tir"),
    (u"uía", "uir"),       (u"aos", "arse"),      (u"gue", "gar"),       (u"qué", "car"),
    (u"que", "car"),       (u"rse", "rse"),       (u"ste", "r"),         (u"era", "r"),
    (u"tió", "tir"),       (u"ine", "inar"),      (u"ré", "r"),          (u"ya", "ir"),
    (u"ye", "ir"),         (u"tí", "tir"),        (u"cé", "zar"),        (u"ie", "iar"),
    (u"id", "ir"),         (u"ué", "ar"),
]

def _parse_lemma(verb):
    """ Returns the base form of the given inflected verb, using a rule-based approach.
    """
    # Spanish has 12,000+ verbs, ending in -ar (85%), -er (8%), -ir (7%).
    # Over 65% of -ar verbs (6500+) have a regular inflection.
    v = verb.lower()
    # Probably ends in -ir if preceding vowel in stem is -i.
    er_ir = lambda b: (len(b) > 2 and b[-2] == "i") and b+"ir" or b+"er"
    # Probably infinitive if ends in -ar, -er or -ir.
    if v.endswith(("ar", "er", "ir")):
        return v
    # Ruleset for irregular inflections adds 10% accuracy.
    for a, b in verb_irregular_inflections:
        if v.endswith(a):
            return v[:-len(a)] + b
    # reconozco => reconocer
    v = v.replace(u"zco", "ce")
    # reconozcamos => reconocer
    v = v.replace(u"zca", "ce")
    # reconozcáis => reconocer
    v = v.replace(u"zcá", "ce")
    # saldrár => saler
    if "ldr" in v: 
        return v[:v.index("ldr")+1] + "er"
    # compondrán => componer
    if "ndr" in v: 
        return v[:v.index("ndr")+1] + "er"
    # Many verbs end in -ar and have a regular inflection:
    for x in ((
      u"ando", u"ado", u"ad",                                # participle
      u"aré", u"arás", u"ará", u"aremos", u"aréis", u"arán", # future
      u"aría", u"arías", u"aríamos", u"aríais", u"arían",    # conditional
      u"aba", u"abas", u"ábamos", u"abais", u"aban",         # past imperfective
      u"é", u"aste", u"ó", u"asteis", u"aron",               # past perfective
      u"ara", u"aras", u"áramos", u"arais", u"aran")):       # past subjunctive
        if v.endswith(x):
            return v[:-len(x)] + "ar"
    # Many verbs end in -er and have a regular inflection:
    for x in ((
      u"iendo", u"ido", u"ed",                               # participle
      u"eré", u"erás", u"erá", u"eremos", u"eréis", u"erán", # future
      u"ería", u"erías", u"eríamos", u"eríais", u"erían",    # conditional
      u"ía", u"ías", u"íamos", u"íais", u"ían",              # past imperfective
      u"í", "iste", u"ió", "imos", "isteis", "ieron",        # past perfective
      u"era", u"eras", u"éramos", u"erais", u"eran")):       # past subjunctive
        if v.endswith(x):
            return er_ir(v[:-len(x)])
    # Many verbs end in -ir and have a regular inflection:
    for x in ((
      u"iré", u"irás", u"irá", u"iremos", u"iréis", u"irán", # future
      u"iría", u"irías", u"iríamos", u"iríais", u"irían")):  # past subjunctive
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
      ("amos", u"áis"), 
      ("emos", u"éis"), 
      ("imos", u"ís"))):
        for x in x:
            if v.endswith(x):
                return v[:-len(x)] + ("ar", "er", "ir")[i]
    return v

def _parse_lexeme(verb):
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
            b+u"o", b+u"as", b+u"a", b+u"amos", b+u"áis", b+u"an", b+u"ando",
            b+u"é", b+u"aste", b+u"ó", b+u"amos", b+u"asteis", b+u"aron", b+u"ado",
            b+u"aba", b+u"abas", b+u"aba", b+u"ábamos", b+u"abais", b+u"aban",
            v+u"é", v+u"ás", v+u"á", v+u"emos", v+u"éis", v+u"án",
            v+u"ía", v+u"ías", v+u"ía", v+u"íamos", v+u"íais", v+u"ían",
            b+u"a", v[:-1]+"d",
            b+u"e", b+u"es", b+u"e", b+u"emos", b+u"éis", b+u"en",
            v+u"a", v+u"as", v+u"a", b+u"áramos", v+u"ais", v+u"an"]
    else:
        # Regular inflection for verbs ending in -er and -ir.
        p1, p2 = v.endswith("er") and ("e", u"é") or ("i","e")
        return [v, 
            b+u"o", b+u"es", b+u"e", b+p1+u"mos", b+p2+u"is", b+u"en", b+u"iendo",
            b+u"í", b+u"iste", b+u"ió", b+u"imos", b+u"isteis", b+u"ieron", b+u"ido",
            b+u"ía", b+u"ías", b+u"ía", b+u"íamos", b+u"íais", b+u"ían",
            v+u"é", v+u"ás", v+u"á", v+u"emos", v+u"éis", v+u"án",
            v+u"ía", v+u"ías", v+u"ía", v+u"íamos", v+u"íais", v+u"ían",
            b+u"a", v[:-1]+"d",
            b+u"a", b+u"as", b+u"a", b+u"amos", b+u"áis", b+u"an",
            b+u"iera", b+u"ieras", b+u"iera", b+u"iéramos", b+u"ierais", b+u"ieran"]
    
_verbs.parse_lemma  = _parse_lemma
_verbs.parse_lexeme = _parse_lexeme

#### ATTRIBUTIVE & PREDICATIVE #####################################################################

MASCULINE, FEMININE, NEUTER, PLURAL = MALE, FEMALE, NEUTRAL, PLURAL = \
    "masculine", "feminine", "neuter", "plural"

def attributive(adjective, gender=MALE):
    w = adjective.lower()
    # normal => normales
    if PLURAL in gender and not vowel(w[-1:]):
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
        
#print attributive("intelligente", gender=PLURAL) # intelligentes
#print attributive("alto", gender=MALE+PLURAL)    # altos
#print attributive("alto", gender=FEMALE+PLURAL)  # altas
#print attributive("normal", gender=MALE)         # normal
#print attributive("normal", gender=FEMALE)       # normal
#print attributive("normal", gender=PLURAL)       # normales

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
        if len(w) >= 4 and not vowel(normalize(w[-3])) and not vowel(normalize(w[-4])):
            return w[:-1]
        return w[:-2]
    return w