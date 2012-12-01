#### PATTERN | DE | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# A set of rule-based tools for German word inflection:
# - pluralization and singularization of nouns,
# - conjugation of verbs
# - attributive and predicative of adjectives,
# - comparative and superlative of adjectives.

import re
import os

try:
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"
VOWELS = ("a", "e", "i", "o", "u")
vowel = lambda ch: ch in VOWELS

# Accuracy (measured on CELEX German morphology word forms):
# 75% gender()
# 72% pluralize()
# 84% singularize() (for nominative)
# 88% _parse_lemma()
# 87% _parse_lexeme()
# 98% predicative

#### ARTICLE #######################################################################################
# German inflection of depends on gender, role and number + the determiner (if any).

# Inflection gender.
# Masculine is the most common, so it is the default for all functions.
MASCULINE, FEMININE, NEUTER, PLURAL = MALE, FEMALE, NEUTRAL, PLURAL = \
    "masculine", "feminine", "neuter", "plural"

# Inflection role.
# - nom = subject, "Der Hund bellt" (the dog barks).
# - acc = object, "Das Mädchen küsst den Hund" (the girl kisses the dog).
# - dat = object (indirect), "Der Mann gibt einen Knochen zum Hund" (the man gives the dog a bone).
# - gen = property, "die Knochen des Hundes" (the dog's bone).
NOMINATIVE, ACCUSATIVE, DATIVE, GENITIVE = SUBJECT, OBJECT, INDIRECT, PROPERTY = \
    "nominative", "accusative", "dative", "genitive"

article_definite = {
    ("m", "nom"): "der", ("f", "nom"): "die", ("n", "nom"): "das", ("p", "nom"): "die",
    ("m", "acc"): "den", ("f", "acc"): "die", ("n", "acc"): "das", ("p", "acc"): "die",
    ("m", "dat"): "dem", ("f", "dat"): "der", ("n", "dat"): "dem", ("p", "dat"): "den",
    ("m", "gen"): "des", ("f", "gen"): "der", ("n", "gen"): "des", ("p", "gen"): "der",
}

article_indefinite = {
    ("m", "nom"): ""  , ("f", "nom"): "e" , ("n", "nom"): ""  , ("p", "nom"): "e",
    ("m", "acc"): "en", ("f", "acc"): "e" , ("n", "acc"): ""  , ("p", "acc"): "e",
    ("m", "dat"): "em", ("f", "dat"): "er", ("n", "dat"): "em", ("p", "dat"): "en",
    ("m", "gen"): "es", ("f", "gen"): "er", ("n", "gen"): "es", ("p", "gen"): "er",
}

def definite_article(word, gender=MALE, role=SUBJECT):
    """ Returns the definite article (der/die/das/die) for a given word.
    """
    return article_definite.get((gender[:1].lower(), role[:3].lower()))

def indefinite_article(word):
    """ Returns the indefinite article (ein) for a given word.
    """
    return article_indefinite.get((gender[:1].lower(), role[:1].lower()))

DEFINITE   = "definite"
INDEFINITE = "indefinite"

def article(word, function=INDEFINITE, gender=MALE, role=SUBJECT):
    """ Returns the indefinite (ein) or definite (der/die/das/die) article for the given word.
    """
    return function == DEFINITE \
       and definite_article(word, gender, role) \
        or indefinite_article(word, gender, role)
_article = article

def referenced(word, article=INDEFINITE, gender=MALE, role=SUBJECT):
    """ Returns a string with the article + the word.
    """
    return "%s %s" % (_article(word, article, gender, role), word)

#### GENDER #########################################################################################

gender_masculine = (
    "ant", "ast", "ich", "ig", "ismus", "ling", "or", "us"
)
gender_feminine = (
    "a", "anz", "ei", "enz", "heit", "ie", "ik", "in", "keit", "schaf", "sion", "sis", 
    u"tät", "tion", "ung", "ur"
)
gender_neuter = (
    "chen", "icht", "il", "it", "lein", "ma", "ment", "tel", "tum", "um","al", "an", "ar", 
    u"ät", "ent", "ett", "ier", "iv", "o", "on", "nis", "sal"
)
gender_majority_vote = {
    MASCULINE: (
        "ab", "af", "ag", "ak", "am", "an", "ar", "at", "au", "ch", "ck", "eb", "ef", "eg", 
        "el", "er", "es", "ex", "ff", "go", "hn", "hs", "ib", "if", "ig", "ir", "kt", "lf", 
        "li", "ll", "lm", "ls", "lt", "mi", "nd", "nk", "nn", "nt", "od", "of", "og", "or", 
        "pf", "ph", "pp", "ps", "rb", "rd", "rf", "rg", "ri", "rl", "rm", "rr", "rs", "rt", 
        "rz", "ss", "st", "tz", "ub", "uf", "ug", "uh", "un", "us", "ut", "xt", "zt"
    ), 
    FEMININE: (
        "be", "ce", "da", "de", "dt", "ee", "ei", "et", "eu", "fe", "ft", "ge", "he", "hr", 
        "ht", "ia", "ie", "ik", "in", "it", "iz", "ka", "ke", "la", "le", "me", "na", "ne", 
        "ng", "nz", "on", "pe", "ra", "re", "se", "ta", "te", "ue", "ur", "ve", "ze"
    ), 

    NEUTER: (
        "ad", "al", "as", "do", "ed", "eh", "em", "en", "hl", "id", "il", "im", "io", "is", 
        "iv", "ix", "ld", "lk", "lo", "lz", "ma", "md", "mm", "mt", "no", "ns", "ol", "om", 
        "op", "os", "ot", "pt", "rk", "rn", "ro", "to", "tt", "ul", "um", "uz"
    )
}

def gender(word, pos=NOUN):
    """ Returns the gender (MALE, FEMALE or NEUTRAL) for nouns (majority vote).
        Returns None for words that are not nouns.
    """
    w = word.lower()
    if pos == NOUN:
        # Default rules (baseline = 32%).
        if w.endswith(gender_masculine):
            return MASCULINE
        if w.endswith(gender_feminine):
            return FEMININE
        if w.endswith(gender_neuter):
            return NEUTER
        # Majority vote.
        for g in gender_majority_vote:
            if w.endswith(gender_majority_vote[g]):
                return g

#### PLURALIZE ######################################################################################

plural_inflections = [
    (u"aal", u"äle"),    (u"aat", u"aaten"), (u"abe", u"aben"),  (u"ach", u"ächer"), (u"ade", u"aden"),  
    (u"age", u"agen"),   (u"ahn", u"ahnen"), (u"ahr", u"ahre"),  (u"akt", u"akte"),  (u"ale", u"alen"),  
    (u"ame", u"amen"),   (u"amt", u"ämter"), (u"ane", u"anen"),  (u"ang", u"änge"),  (u"ank", u"änke"),  
    (u"ann", u"änner"),  (u"ant", u"anten"), (u"aph", u"aphen"), (u"are", u"aren"),  (u"arn", u"arne"),  
    (u"ase", u"asen"),   (u"ate", u"aten"),  (u"att", u"ätter"), (u"atz", u"ätze"),  (u"aum", u"äume"),  
    (u"aus", u"äuser"),  (u"bad", u"bäder"), (u"bel", u"bel"),   (u"ben", u"ben"),   (u"ber", u"ber"),  
    (u"bot", u"bote"),   (u"che", u"chen"),  (u"chs", u"chse"),  (u"cke", u"cken"),  (u"del", u"del"),  
    (u"den", u"den"),    (u"der", u"der"),   (u"ebe", u"ebe"),   (u"ede", u"eden"),  (u"ehl", u"ehle"),  
    (u"ehr", u"ehr"),    (u"eil", u"eile"),  (u"eim", u"eime"),  (u"eis", u"eise"),  (u"eit", u"eit"),  
    (u"ekt", u"ekte"),   (u"eld", u"elder"), (u"ell", u"elle"),  (u"ene", u"enen"),  (u"enz", u"enzen"),  
    (u"erd", u"erde"),   (u"ere", u"eren"),  (u"erk", u"erke"),  (u"ern", u"erne"),  (u"ert", u"erte"),  
    (u"ese", u"esen"),   (u"ess", u"esse"),  (u"est", u"este"),  (u"etz", u"etze"),  (u"eug", u"euge"),  
    (u"eur", u"eure"),   (u"fel", u"fel"),   (u"fen", u"fen"),   (u"fer", u"fer"),   (u"ffe", u"ffen"),  
    (u"gel", u"gel"),    (u"gen", u"gen"),   (u"ger", u"ger"),   (u"gie", u"gie"),   (u"hen", u"hen"),  
    (u"her", u"her"),    (u"hie", u"hien"),  (u"hle", u"hlen"),  (u"hme", u"hmen"),  (u"hne", u"hnen"),  
    (u"hof", u"höfe"),   (u"hre", u"hren"),  (u"hrt", u"hrten"), (u"hse", u"hsen"),  (u"hte", u"hten"),  
    (u"ich", u"iche"),   (u"ick", u"icke"),  (u"ide", u"iden"),  (u"ieb", u"iebe"),  (u"ief", u"iefe"),  
    (u"ieg", u"iege"),   (u"iel", u"iele"),  (u"ien", u"ium"),   (u"iet", u"iete"),  (u"ife", u"ifen"),  
    (u"iff", u"iffe"),   (u"ift", u"iften"), (u"ige", u"igen"),  (u"ika", u"ikum"),  (u"ild", u"ilder"),  
    (u"ilm", u"ilme"),   (u"ine", u"inen"),  (u"ing", u"inge"),  (u"ion", u"ionen"), (u"ise", u"isen"),  
    (u"iss", u"isse"),   (u"ist", u"isten"), (u"ite", u"iten"),  (u"itt", u"itte"),  (u"itz", u"itze"),  
    (u"ium", u"ium"),    (u"kel", u"kel"),   (u"ken", u"ken"),   (u"ker", u"ker"),   (u"lag", u"läge"),  
    (u"lan", u"läne"),   (u"lar", u"lare"),  (u"lei", u"leien"), (u"len", u"len"),   (u"ler", u"ler"),  
    (u"lge", u"lgen"),   (u"lie", u"lien"),  (u"lle", u"llen"),  (u"mel", u"mel"),   (u"mer", u"mer"),  
    (u"mme", u"mmen"),   (u"mpe", u"mpen"),  (u"mpf", u"mpfe"),  (u"mus", u"mus"),   (u"mut", u"mut"),  
    (u"nat", u"nate"),   (u"nde", u"nden"),  (u"nen", u"nen"),   (u"ner", u"ner"),   (u"nge", u"ngen"),  
    (u"nie", u"nien"),   (u"nis", u"nisse"), (u"nke", u"nken"),  (u"nkt", u"nkte"),  (u"nne", u"nnen"),  
    (u"nst", u"nste"),   (u"nte", u"nten"),  (u"nze", u"nzen"),  (u"ock", u"öcke"),  (u"ode", u"oden"),  
    (u"off", u"offe"),   (u"oge", u"ogen"),  (u"ohn", u"öhne"),  (u"ohr", u"ohre"),  (u"olz", u"ölzer"),  
    (u"one", u"onen"),   (u"oot", u"oote"),  (u"opf", u"öpfe"),  (u"ord", u"orde"),  (u"orm", u"ormen"),  
    (u"orn", u"örner"),  (u"ose", u"osen"),  (u"ote", u"oten"),  (u"pel", u"pel"),   (u"pen", u"pen"),  
    (u"per", u"per"),    (u"pie", u"pien"),  (u"ppe", u"ppen"),  (u"rag", u"räge"),  (u"rau", u"raün"),  
    (u"rbe", u"rben"),   (u"rde", u"rden"),  (u"rei", u"reien"), (u"rer", u"rer"),   (u"rie", u"rien"),  
    (u"rin", u"rinnen"), (u"rke", u"rken"),  (u"rot", u"rote"),  (u"rre", u"rren"),  (u"rte", u"rten"),  
    (u"ruf", u"rufe"),   (u"rzt", u"rzte"),  (u"sel", u"sel"),   (u"sen", u"sen"),   (u"ser", u"ser"),  
    (u"sie", u"sien"),   (u"sik", u"sik"),   (u"sse", u"ssen"),  (u"ste", u"sten"),  (u"tag", u"tage"),  
    (u"tel", u"tel"),    (u"ten", u"ten"),   (u"ter", u"ter"),   (u"tie", u"tien"),  (u"tin", u"tinnen"),  
    (u"tiv", u"tive"),   (u"tor", u"toren"), (u"tte", u"tten"),  (u"tum", u"tum"),   (u"tur", u"turen"),  
    (u"tze", u"tzen"),   (u"ube", u"uben"),  (u"ude", u"uden"),  (u"ufe", u"ufen"),  (u"uge", u"ugen"),  
    (u"uhr", u"uhren"),  (u"ule", u"ulen"),  (u"ume", u"umen"),  (u"ung", u"ungen"), (u"use", u"usen"),  
    (u"uss", u"üsse"),   (u"ute", u"uten"),  (u"utz", u"utz"),   (u"ver", u"ver"),   (u"weg", u"wege"),  
    (u"zer", u"zer"),    (u"zug", u"züge"),  (u"ück", u"ücke")
]

def pluralize(word, pos=NOUN, gender=MALE, role=SUBJECT, custom={}):
    """ Returns the plural of a given word.
        The inflection is based on probability rather than gender and role.
    """
    w = word.lower().capitalize()
    if pos == NOUN:
        for a, b in plural_inflections:
            if w.endswith(a):
                return w[:-len(a)] + b
        # Default rules (baseline = 69%).
        if w.startswith("ge"):
            return w
        if w.endswith("gie"):
            return w
        if w.endswith("e"):
            return w + "n"
        if w.endswith("ien"):
            return w[:-2] + "um"
        if w.endswith(("au", "ein", "eit", "er", "en", "el", "chen", "mus", u"tät", "tik", "tum", "u")):
            return w
        if w.endswith(("ant", "ei", "enz", "ion", "ist", "or", "schaft", "tur", "ung")):
            return w + "en"
        if w.endswith("in"):
            return w + "nen"
        if w.endswith("nis"):
            return w + "se"
        if w.endswith(("eld", "ild", "ind")):
            return w + "er"
        if w.endswith("o"):
            return w + "s"
        if w.endswith("a"):
            return w[:-1] + "en"
        # Inflect common umlaut vowels: Kopf => Köpfe.
        if w.endswith(("all", "and", "ang", "ank", "atz", "auf", "ock", "opf", "uch", "uss")):
            umlaut = w[-3]
            umlaut = umlaut.replace("a", u"ä")
            umlaut = umlaut.replace("o", u"ö")
            umlaut = umlaut.replace("u", u"ü")
            return w[:-3] + umlaut + w[-2:] + "e"
        for a, b in (
          ("ag",  u"äge"), 
          ("ann", u"änner"), 
          ("aum", u"äume"), 
          ("aus", u"äuser"), 
          ("zug", u"züge")):
            if w.endswith(a):
                return w[:-len(a)] + b
        return w + "e"
    return w

#### SINGULARIZE ###################################################################################

singular_inflections = [
    (u"innen", u"in"),  (u"täten", u"tät"), (u"ahnen", u"ahn"), (u"enten", u"ent"), (u"räser", u"ras"), 
    (u"hrten", u"hrt"), (u"ücher", u"uch"), (u"örner", u"orn"), (u"änder", u"and"), (u"ürmer", u"urm"), 
    (u"ahlen", u"ahl"), (u"uhren", u"uhr"), (u"ätter", u"att"), (u"suren", u"sur"), (u"chten", u"cht"), 
    (u"kuren", u"kur"), (u"erzen", u"erz"), (u"güter", u"gut"), (u"soren", u"sor"), (u"änner", u"ann"), 
    (u"äuser", u"aus"), (u"taten", u"tat"), (u"isten", u"ist"), (u"bäder", u"bad"), (u"ämter", u"amt"), 
    (u"eiten", u"eit"), (u"raten", u"rat"), (u"ormen", u"orm"), (u"ionen", u"ion"), (u"nisse", u"nis"), 
    (u"ölzer", u"olz"), (u"ungen", u"ung"), (u"läser", u"las"), (u"ächer", u"ach"), (u"urten", u"urt"), 
    (u"enzen", u"enz"), (u"aaten", u"aat"), (u"aphen", u"aph"), (u"öcher", u"och"), (u"türen", u"tür"), 
    (u"sonen", u"son"), (u"ühren", u"ühr"), (u"ühner", u"uhn"), (u"toren", u"tor"), (u"örter", u"ort"), 
    (u"anten", u"ant"), (u"räder", u"rad"), (u"turen", u"tur"), (u"äuler", u"aul"), (u"änze", u"anz"),  
    (u"tten", u"tte"),  (u"mben", u"mbe"),  (u"ädte", u"adt"),  (u"llen", u"lle"),  (u"ysen", u"yse"),  
    (u"rben", u"rbe"),  (u"hsen", u"hse"),  (u"raün", u"rau"),  (u"rven", u"rve"),  (u"rken", u"rke"),  
    (u"ünge", u"ung"),  (u"üten", u"üte"),  (u"usen", u"use"),  (u"tien", u"tie"),  (u"läne", u"lan"),  
    (u"iben", u"ibe"),  (u"ifen", u"ife"),  (u"ssen", u"sse"),  (u"gien", u"gie"),  (u"eten", u"ete"),  
    (u"rden", u"rde"),  (u"öhne", u"ohn"),  (u"ärte", u"art"),  (u"ncen", u"nce"),  (u"ünde", u"und"),  
    (u"uben", u"ube"),  (u"lben", u"lbe"),  (u"üsse", u"uss"),  (u"agen", u"age"),  (u"räge", u"rag"),  
    (u"ogen", u"oge"),  (u"anen", u"ane"),  (u"sken", u"ske"),  (u"eden", u"ede"),  (u"össe", u"oss"),  
    (u"ürme", u"urm"),  (u"ggen", u"gge"),  (u"üren", u"üre"),  (u"nten", u"nte"),  (u"ühle", u"ühl"),  
    (u"änge", u"ang"),  (u"mmen", u"mme"),  (u"igen", u"ige"),  (u"nken", u"nke"),  (u"äcke", u"ack"),  
    (u"oden", u"ode"),  (u"oben", u"obe"),  (u"ähne", u"ahn"),  (u"änke", u"ank"),  (u"inen", u"ine"),  
    (u"seen", u"see"),  (u"äfte", u"aft"),  (u"ulen", u"ule"),  (u"äste", u"ast"),  (u"hren", u"hre"),  
    (u"öcke", u"ock"),  (u"aben", u"abe"),  (u"öpfe", u"opf"),  (u"ugen", u"uge"),  (u"lien", u"lie"),  
    (u"ände", u"and"),  (u"ücke", u"ück"),  (u"asen", u"ase"),  (u"aden", u"ade"),  (u"dien", u"die"),  
    (u"aren", u"are"),  (u"tzen", u"tze"),  (u"züge", u"zug"),  (u"üfte", u"uft"),  (u"hien", u"hie"),  
    (u"nden", u"nde"),  (u"älle", u"all"),  (u"hmen", u"hme"),  (u"ffen", u"ffe"),  (u"rmen", u"rma"),  
    (u"olen", u"ole"),  (u"sten", u"ste"),  (u"amen", u"ame"),  (u"höfe", u"hof"),  (u"üste", u"ust"),  
    (u"hnen", u"hne"),  (u"ähte", u"aht"),  (u"umen", u"ume"),  (u"nnen", u"nne"),  (u"alen", u"ale"),  
    (u"mpen", u"mpe"),  (u"mien", u"mie"),  (u"rten", u"rte"),  (u"rien", u"rie"),  (u"äute", u"aut"),  
    (u"uden", u"ude"),  (u"lgen", u"lge"),  (u"ngen", u"nge"),  (u"iden", u"ide"),  (u"ässe", u"ass"),  
    (u"osen", u"ose"),  (u"lken", u"lke"),  (u"eren", u"ere"),  (u"üche", u"uch"),  (u"lüge", u"lug"),  
    (u"hlen", u"hle"),  (u"isen", u"ise"),  (u"ären", u"äre"),  (u"töne", u"ton"),  (u"onen", u"one"),  
    (u"rnen", u"rne"),  (u"üsen", u"üse"),  (u"haün", u"hau"),  (u"pien", u"pie"),  (u"ihen", u"ihe"),  
    (u"ürfe", u"urf"),  (u"esen", u"ese"),  (u"ätze", u"atz"),  (u"sien", u"sie"),  (u"läge", u"lag"),  
    (u"iven", u"ive"),  (u"ämme", u"amm"),  (u"äufe", u"auf"),  (u"ppen", u"ppe"),  (u"enen", u"ene"),  
    (u"lfen", u"lfe"),  (u"äume", u"aum"),  (u"nien", u"nie"),  (u"unen", u"une"),  (u"cken", u"cke"),  
    (u"oten", u"ote"),  (u"mie", u"mie"),   (u"rie", u"rie"),   (u"sis", u"sen"),   (u"rin", u"rin"),   
    (u"ein", u"ein"),   (u"age", u"age"),   (u"ern", u"ern"),   (u"ber", u"ber"),   (u"ion", u"ion"),   
    (u"inn", u"inn"),   (u"ben", u"ben"),   (u"äse", u"äse"),   (u"eis", u"eis"),   (u"hme", u"hme"), 
    (u"iss", u"iss"),   (u"hen", u"hen"),   (u"fer", u"fer"),   (u"gie", u"gie"),   (u"fen", u"fen"), 
    (u"her", u"her"),   (u"ker", u"ker"),   (u"nie", u"nie"),   (u"mer", u"mer"),   (u"ler", u"ler"), 
    (u"men", u"men"),   (u"ass", u"ass"),   (u"ner", u"ner"),   (u"per", u"per"),   (u"rer", u"rer"), 
    (u"mus", u"mus"),   (u"abe", u"abe"),   (u"ter", u"ter"),   (u"ser", u"ser"),   (u"äle", u"aal"), 
    (u"hie", u"hie"),   (u"ger", u"ger"),   (u"tus", u"tus"),   (u"gen", u"gen"),   (u"ier", u"ier"), 
    (u"ver", u"ver"),   (u"zer", u"zer"), 
]

def singularize(word, pos=NOUN, gender=MALE, role=SUBJECT, custom={}):
    """ Returns the singular of a given word.
        The inflection is based on probability rather than gender and role.
    """
    w = word.lower().capitalize()
    if pos == NOUN:
        for a, b in singular_inflections:
            if w.endswith(a):
                return w[:-len(a)] + b
        # Default rule: strip known plural suffixes (baseline = 51%).
        for suffix in ("nen", "en", "n", "e", "er", "s"):
            if w.endswith(suffix):
                return w[:-len(suffix)]
        return w
    return w

#### VERB CONJUGATION ##############################################################################

import sys; sys.path.insert(0, os.path.join(MODULE, "..", ".."))
from en.inflect import Verbs
from en.inflect import \
    INFINITIVE, PRESENT, PAST, FUTURE, \
    FIRST, SECOND, THIRD, \
    SINGULAR, PLURAL, SG, PL, \
    INDICATIVE, IMPERATIVE, SUBJUNCTIVE, \
    PROGRESSIVE, \
    PARTICIPLE, GERUND

# Defines the tenses on each line in verbs.txt (see pattern.en.inflect.TENSES).
FORMAT  = [0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 16, 19, 22, 21, 24, 25, 27, 28, 30, 31, 33, 34]
DEFAULT = {6:4, 14:12, 26:24, 29:27, 32:30, 35:33}

# Load the pattern.en.Verbs class, with a German lexicon instead.
# Lexicon was trained on CELEX and contains the top 2000 most frequent verbs.
_verbs = VERBS = Verbs(os.path.join(MODULE, "verbs.txt"), FORMAT, DEFAULT, language="de")

conjugate, lemma, lexeme, tenses = \
    _verbs.conjugate, _verbs.lemma, _verbs.lexeme, _verbs.tenses

prefix_inseparable = (
    "be", "emp", "ent", "er", "ge", "miss", "ueber", "unter", "ver", "voll", "wider", "zer"
)
prefix_separable = (
    "ab", "an", "auf", "aus", "bei", "durch", "ein", "fort", "mit", "nach", "vor", "weg",
    "zurueck", "zusammen", "zu", "dabei", "daran", "da", "empor", "entgegen", "entlang", 
    "fehl", "fest", "gegenueber", "gleich", "herab", "heran", "herauf", "heraus", "herum", 
    "her", "hinweg", "hinzu", "hin", "los", "nieder", "statt", "umher", "um", "weg", 
    "weiter", "wieder", "zwischen"
) + (
     # There are many more...
     "dort", "fertig", "frei", "gut", "heim", "hoch", "klein", "klar", "nahe", 
     "offen", "richtig", "tot"
)
prefixes = prefix_inseparable + prefix_separable

def encode_sz(s):
    return s.replace(u"ß", "ss")
def decode_sz(s):
    return s.replace("ss", u"ß")
    
def tenses(verb, parse=True):
    tenses = _verbs.tenses(verb, parse)
    if len(tenses) == 0:
        # auswirkte => wirkte aus
        for prefix in prefix_separable:
            if verb.startswith(prefix):
                tenses = _verbs.tenses(verb[len(prefix):]+" "+prefix, parse)
                break
    return tenses

def _parse_lemma(verb):
    """ Returns the base form of the given inflected verb, using a rule-based approach.
    """
    v = verb.lower()
    # Common prefixes: be-finden and emp-finden probably inflect like finden.
    for prefix in prefixes:
        if v.startswith(prefix) and v[len(prefix):] in _verbs._lemmas:
            return prefix + _verbs._lemmas[v[len(prefix):]]
    # Common sufixes: setze nieder => niedersetzen.
    b, suffix = " " in v and v.split()[:2] or  (v, "")
    # Infinitive -ln: trommeln.
    if b.endswith(("ln", "rn")):
        return b
    # Lemmatize regular inflections.
    for x in ("test", "est", "end", "ten", "tet", "en", "et", "te", "st", "e", "t"):
        if b.endswith(x): b = b[:-len(x)]; break
    # Subjunctive: hielte => halten, schnitte => schneiden.
    for x, y in (
      ("ieb", "eib"), ("ied", "eid"), ("ief", "auf"), ("ieg", "eig"), ("iel", "alt"), 
      ("ien", "ein"), ("iess", "ass"), (u"ieß", u"aß"), ("iff", "eif"), ("iss", "eiss"), 
      (u"iß", u"eiß"), ("it", "eid"), ("oss", "iess"), (u"öss", "iess")):
        if b.endswith(x): b = b[:-len(x)] + y; break
    # Subjunctive: wechselte => wechseln
    if not b.endswith(("e", "l")) and not (b.endswith("er") and not b[-3] in VOWELS):
        b = b + "e"
    # abknallst != abknalln => abknallen
    if b.endswith(("hl", "ll", "ul", "eil")):
        b = b + "e"
    return suffix + b + "n"

def _parse_lexeme(verb):
    """ For a regular verb (base form), returns the forms using a rule-based approach.
    """
    v = verb.lower()
    # Stem = infinitive minus -en, -ln, -rn.
    b = b0 = re.sub("en$", "", re.sub("ln$", "l", re.sub("rn$", "r", v)))
    # Split common prefixes.
    x, x1, x2 = "", "", ""
    for prefix in prefix_separable:
        if v.startswith(prefix):
            b, x = b[len(prefix):], prefix
            x1 = (" " + x).rstrip()
            x2 = x + "ge"
            break
    # Present tense 1sg and subjunctive -el: handeln => ich handle, du handlest.
    pl = b.endswith("el") and b[:-2]+"l" or b
    # Present tense 1pl -el: handeln => wir handeln
    pw = v.endswith(("ln", "rn")) and v or b+"en"
    # Present tense ending in -d or -t gets -e:
    pr = b.endswith(("d", "t")) and b+"e" or b
    # Present tense 2sg gets -st, unless stem ends with -s or -z.
    p2 = pr.endswith(("s","z")) and pr+"t" or pr+"st"
    # Present participle: spiel + -end, arbeiten + -d:
    pp = v.endswith(("en", "ln", "rn")) and v+"d" or v+"end"
    # Past tense regular:
    pt = encode_sz(pr) + "t"
    # Past participle: haushalten => hausgehalten
    ge = (v.startswith(prefix_inseparable) or b.endswith(("r","t"))) and pt or "ge"+pt
    ge = x and x+"ge"+pt or ge
    # Present subjunctive: stem + -e, -est, -en, -et:
    s1 = encode_sz(pl)
    # Past subjunctive: past (usually with Umlaut) + -e, -est, -en, -et:
    s2 = encode_sz(pt)
    # Construct the lexeme:
    lexeme = a = [
        v, 
        pl+"e"+x1, p2+x1, pr+"t"+x1, pw+x1, pr+"t"+x1, pp,             # present
        pt+"e"+x1, pt+"est"+x1, pt+"e"+x1, pt+"en"+x1, pt+"et"+x1, ge, # past
        b+"e"+x1, pr+"t"+x1, x+pw,                                     # imperative
        s1+"e"+x1, s1+"est"+x1, s1+"en"+x1, s1+"et"+x1,                # subjunctive I
        s2+"e"+x1, s2+"est"+x1, s2+"en"+x1, s2+"et"+x1                 # subjunctive II
    ]
    # Encode Eszett (ß) and attempt to retrieve from the lexicon.
    # Decode Eszett for present and imperative.
    if encode_sz(v) in _verbs.infinitives:
        a = _verbs._tenses[encode_sz(v)]
        a = [decode_sz(v) for v in a[:7]] + a[7:13] + [decode_sz(v) for v in a[13:20]] + a[20:]
    # Since the lexicon does not contain imperative for all verbs, don't simply return it.
    # Instead, update the rule-based lexeme with inflections from the lexicon.
    return [a[i] or lexeme[i] for i in range(len(a))]
    
_verbs.parse_lemma  = _parse_lemma
_verbs.parse_lexeme = _parse_lexeme

#### ATTRIBUTIVE & PREDICATIVE #####################################################################

# Strong inflection: no article.
adjectives_strong = {
    ("m", "nom"): "er", ("f", "nom"): "e" , ("n", "nom"): "es", ("p", "nom"): "e",
    ("m", "acc"): "en", ("f", "acc"): "e" , ("n", "acc"): "es", ("p", "acc"): "e",
    ("m", "dat"): "em", ("f", "dat"): "er", ("n", "dat"): "em", ("p", "dat"): "en",
    ("m", "gen"): "en", ("f", "gen"): "er", ("n", "gen"): "en", ("p", "gen"): "er",
}

# Mixed inflection: after indefinite article ein & kein and possessive determiners.
adjectives_mixed = {
    ("m", "nom"): "er", ("f", "nom"): "e" , ("n", "nom"): "es", ("p", "nom"): "en",
    ("m", "acc"): "en", ("f", "acc"): "e" , ("n", "acc"): "es", ("p", "acc"): "en",
    ("m", "dat"): "en", ("f", "dat"): "en", ("n", "dat"): "en", ("p", "dat"): "en",
    ("m", "gen"): "en", ("f", "gen"): "en", ("n", "gen"): "en", ("p", "gen"): "en",
}

# Weak inflection: after definite article.
adjectives_weak = {
    ("m", "nom"): "e",  ("f", "nom"): "e" , ("n", "nom"): "e",  ("p", "nom"): "en",
    ("m", "acc"): "en", ("f", "acc"): "e" , ("n", "acc"): "e",  ("p", "acc"): "en",
    ("m", "dat"): "en", ("f", "dat"): "en", ("n", "dat"): "en", ("p", "dat"): "en",
    ("m", "gen"): "en", ("f", "gen"): "en", ("n", "gen"): "en", ("p", "gen"): "en",
}

# Uninflected + exceptions.
adjective_attributive = {
    "etwas" : "etwas",
    "genug" : "genug",
    "viel"  : "viel",
    "wenig" : "wenig"
}

def attributive(adjective, gender=MALE, role=SUBJECT, article=None):
    """ For a predicative adjective, returns the attributive form (lowercase).
        In German, the attributive is formed with -e, -em, -en, -er or -es,
        depending on gender (masculine, feminine, neuter or plural) and role
        (nominative, accusative, dative, genitive).
    """
    w, g, c, a = \
        adjective.lower(), gender[:1].lower(), role[:3].lower(), article and article.lower() or None
    if w in adjective_attributive:
        return adjective_attributive[w]
    if a is None \
    or a in ("mir", "dir", "ihm") \
    or a in ("ein", "etwas", "mehr") \
    or a.startswith(("all", "mehrer", "wenig", "viel")):
        return w + adjectives_strong.get((g, c), "")
    if a.startswith(("ein", "kein")) \
    or a.startswith(("mein", "dein", "sein", "ihr", "Ihr", "unser", "euer")):
        return w + adjectives_mixed.get((g, c), "")
    if a in ("arm", "alt", "all", "der", "die", "das", "den", "dem", "des") \
    or a.startswith((
      "derselb", "derjenig", "jed", "jeglich", "jen", "manch", 
      "dies", "solch", "welch")):
        return w + adjectives_weak.get((g, c), "")
    # Default to strong inflection.
    return w + adjectives_strong.get((g, c), "")

def predicative(adjective):
    """ Returns the predicative adjective (lowercase).
        In German, the attributive form preceding a noun is always used:
        "ein kleiner Junge" => strong, masculine, nominative,
        "eine schöne Frau" => mixed, feminine, nominative,
        "der kleine Prinz" => weak, masculine, nominative, etc.
        The predicative is useful for lemmatization.
    """
    w = adjective.lower()
    if len(w) > 3:
        for suffix in ("em", "en", "er", "es", "e"):
            if w.endswith(suffix):
                b = w[:max(-len(suffix), -(len(w)-3))]
                if b.endswith("bl"): # plausibles => plausibel
                    b = b[:-1] + "el"
                if b.endswith("pr"): # propres => proper
                    b = b[:-1] + "er"
                return b
    return w

#### COMPARATIVE & SUPERLATIVE #####################################################################

COMPARATIVE = "er"
SUPERLATIVE = "st"

def grade(adjective, suffix=COMPARATIVE):
    """ Returns the comparative or superlative form of the given (inflected) adjective.
    """
    b = predicative(adjective)
    # groß => großt, schön => schönst
    if suffix == SUPERLATIVE and b.endswith(("s", u"ß")):
        suffix = suffix[1:]
    # große => großere, schönes => schöneres
    return adjective[:len(b)] + suffix + adjective[len(b):]

def comparative(adjective):
    return grade(adjective, COMPARATIVE)

def superlative(adjective):
    return grade(adjective, SUPERLATIVE)

#print comparative(u"schönes")
#print superlative(u"schönes")
#print superlative(u"große")