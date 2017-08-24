#### PATTERN | DE | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# Regular expressions-based rules for German word inflection:
# - pluralization and singularization of nouns and adjectives,
# - conjugation of verbs,
# - attributive and predicative of adjectives,
# - comparative and superlative of adjectives.

# Accuracy (measured on CELEX German morphology word forms):
# 75% for gender()
# 72% for pluralize()
# 84% for singularize() (for nominative)
# 87% for Verbs.find_lemma()
# 87% for Verbs.find_lexeme()
# 98% for predicative

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
    INDICATIVE, IMPERATIVE, SUBJUNCTIVE,
    PROGRESSIVE,
    PARTICIPLE, GERUND
)

sys.path.pop(0)

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"

VOWELS = "aeiouy"
re_vowel = re.compile(r"a|e|i|o|u|y", re.I)
is_vowel = lambda ch: ch in VOWELS

#### ARTICLE #######################################################################################
# German inflection of depends on gender, role and number + the determiner (if any).

# Inflection gender.
# Masculine is the most common, so it is the default for all functions.
MASCULINE, FEMININE, NEUTER, PLURAL = \
    MALE, FEMALE, NEUTRAL, PLURAL = \
        M, F, N, PL = "m", "f", "n", "p"

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
    ("m", "nom"): "ein"  , ("f", "nom"): "eine" , ("n", "nom"): "ein"  , ("p", "nom"): "eine",
    ("m", "acc"): "einen", ("f", "acc"): "eine" , ("n", "acc"): "ein"  , ("p", "acc"): "eine",
    ("m", "dat"): "einem", ("f", "dat"): "einer", ("n", "dat"): "einem", ("p", "dat"): "einen",
    ("m", "gen"): "eines", ("f", "gen"): "einer", ("n", "gen"): "eines", ("p", "gen"): "einer",
}


def definite_article(word, gender=MALE, role=SUBJECT):
    """ Returns the definite article (der/die/das/die) for a given word.
    """
    return article_definite.get((gender[:1].lower(), role[:3].lower()))


def indefinite_article(word, gender=MALE, role=SUBJECT):
    """ Returns the indefinite article (ein) for a given word.
    """
    return article_indefinite.get((gender[:1].lower(), role[:3].lower()))

DEFINITE = "definite"
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
    "tät", "tion", "ung", "ur"
)
gender_neuter = (
    "chen", "icht", "il", "it", "lein", "ma", "ment", "tel", "tum", "um", "al", "an", "ar",
    "ät", "ent", "ett", "ier", "iv", "o", "on", "nis", "sal"
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
    ("aal", "äle"   ), ("aat", "aaten"), ("abe", "aben" ), ("ach", "ächer"), ("ade", "aden"  ),
    ("age", "agen"  ), ("ahn", "ahnen"), ("ahr", "ahre" ), ("akt", "akte" ), ("ale", "alen"  ),
    ("ame", "amen"  ), ("amt", "ämter"), ("ane", "anen" ), ("ang", "änge" ), ("ank", "änke"  ),
    ("ann", "änner" ), ("ant", "anten"), ("aph", "aphen"), ("are", "aren" ), ("arn", "arne"  ),
    ("ase", "asen"  ), ("ate", "aten" ), ("att", "ätter"), ("atz", "ätze" ), ("aum", "äume"  ),
    ("aus", "äuser" ), ("bad", "bäder"), ("bel", "bel"  ), ("ben", "ben"  ), ("ber", "ber"   ),
    ("bot", "bote"  ), ("che", "chen" ), ("chs", "chse" ), ("cke", "cken" ), ("del", "del"   ),
    ("den", "den"   ), ("der", "der"  ), ("ebe", "ebe"  ), ("ede", "eden" ), ("ehl", "ehle"  ),
    ("ehr", "ehr"   ), ("eil", "eile" ), ("eim", "eime" ), ("eis", "eise" ), ("eit", "eit"   ),
    ("ekt", "ekte"  ), ("eld", "elder"), ("ell", "elle" ), ("ene", "enen" ), ("enz", "enzen" ),
    ("erd", "erde"  ), ("ere", "eren" ), ("erk", "erke" ), ("ern", "erne" ), ("ert", "erte"  ),
    ("ese", "esen"  ), ("ess", "esse" ), ("est", "este" ), ("etz", "etze" ), ("eug", "euge"  ),
    ("eur", "eure"  ), ("fel", "fel"  ), ("fen", "fen"  ), ("fer", "fer"  ), ("ffe", "ffen"  ),
    ("gel", "gel"   ), ("gen", "gen"  ), ("ger", "ger"  ), ("gie", "gie"  ), ("hen", "hen"   ),
    ("her", "her"   ), ("hie", "hien" ), ("hle", "hlen" ), ("hme", "hmen" ), ("hne", "hnen"  ),
    ("hof", "höfe"  ), ("hre", "hren" ), ("hrt", "hrten"), ("hse", "hsen" ), ("hte", "hten"  ),
    ("ich", "iche"  ), ("ick", "icke" ), ("ide", "iden" ), ("ieb", "iebe" ), ("ief", "iefe"  ),
    ("ieg", "iege"  ), ("iel", "iele" ), ("ien", "ium"  ), ("iet", "iete" ), ("ife", "ifen"  ),
    ("iff", "iffe"  ), ("ift", "iften"), ("ige", "igen" ), ("ika", "ikum" ), ("ild", "ilder" ),
    ("ilm", "ilme"  ), ("ine", "inen" ), ("ing", "inge" ), ("ion", "ionen"), ("ise", "isen"  ),
    ("iss", "isse"  ), ("ist", "isten"), ("ite", "iten" ), ("itt", "itte" ), ("itz", "itze"  ),
    ("ium", "ium"   ), ("kel", "kel"  ), ("ken", "ken"  ), ("ker", "ker"  ), ("lag", "läge"  ),
    ("lan", "läne"  ), ("lar", "lare" ), ("lei", "leien"), ("len", "len"  ), ("ler", "ler"   ),
    ("lge", "lgen"  ), ("lie", "lien" ), ("lle", "llen" ), ("mel", "mel"  ), ("mer", "mer"   ),
    ("mme", "mmen"  ), ("mpe", "mpen" ), ("mpf", "mpfe" ), ("mus", "mus"  ), ("mut", "mut"   ),
    ("nat", "nate"  ), ("nde", "nden" ), ("nen", "nen"  ), ("ner", "ner"  ), ("nge", "ngen"  ),
    ("nie", "nien"  ), ("nis", "nisse"), ("nke", "nken" ), ("nkt", "nkte" ), ("nne", "nnen"  ),
    ("nst", "nste"  ), ("nte", "nten" ), ("nze", "nzen" ), ("ock", "öcke" ), ("ode", "oden"  ),
    ("off", "offe"  ), ("oge", "ogen" ), ("ohn", "öhne" ), ("ohr", "ohre" ), ("olz", "ölzer" ),
    ("one", "onen"  ), ("oot", "oote" ), ("opf", "öpfe" ), ("ord", "orde" ), ("orm", "ormen" ),
    ("orn", "örner" ), ("ose", "osen" ), ("ote", "oten" ), ("pel", "pel"  ), ("pen", "pen"   ),
    ("per", "per"   ), ("pie", "pien" ), ("ppe", "ppen" ), ("rag", "räge" ), ("rau", "raün"  ),
    ("rbe", "rben"  ), ("rde", "rden" ), ("rei", "reien"), ("rer", "rer"  ), ("rie", "rien"  ),
    ("rin", "rinnen"), ("rke", "rken" ), ("rot", "rote" ), ("rre", "rren" ), ("rte", "rten"  ),
    ("ruf", "rufe"  ), ("rzt", "rzte" ), ("sel", "sel"  ), ("sen", "sen"  ), ("ser", "ser"   ),
    ("sie", "sien"  ), ("sik", "sik"  ), ("sse", "ssen" ), ("ste", "sten" ), ("tag", "tage"  ),
    ("tel", "tel"   ), ("ten", "ten"  ), ("ter", "ter"  ), ("tie", "tien" ), ("tin", "tinnen"),
    ("tiv", "tive"  ), ("tor", "toren"), ("tte", "tten" ), ("tum", "tum"  ), ("tur", "turen" ),
    ("tze", "tzen"  ), ("ube", "uben" ), ("ude", "uden" ), ("ufe", "ufen" ), ("uge", "ugen"  ),
    ("uhr", "uhren" ), ("ule", "ulen" ), ("ume", "umen" ), ("ung", "ungen"), ("use", "usen"  ),
    ("uss", "üsse"  ), ("ute", "uten" ), ("utz", "utz"  ), ("ver", "ver"  ), ("weg", "wege"  ),
    ("zer", "zer"   ), ("zug", "züge" ), ("ück", "ücke" )
]


def pluralize(word, pos=NOUN, gender=MALE, role=SUBJECT, custom={}):
    """ Returns the plural of a given word.
        The inflection is based on probability rather than gender and role.
    """
    w = word.lower().capitalize()
    if word in custom:
        return custom[word]
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
        if w.endswith(("au", "ein", "eit", "er", "en", "el", "chen", "mus", "tät", "tik", "tum", "u")):
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
            umlaut = umlaut.replace("a", "ä")
            umlaut = umlaut.replace("o", "ö")
            umlaut = umlaut.replace("u", "ü")
            return w[:-3] + umlaut + w[-2:] + "e"
        for a, b in (
          ("ag",  "äge"),
          ("ann", "änner"),
          ("aum", "äume"),
          ("aus", "äuser"),
          ("zug", "züge")):
            if w.endswith(a):
                return w[:-len(a)] + b
        return w + "e"
    return w

#### SINGULARIZE ###################################################################################

singular_inflections = [
    ( "innen", "in" ), ( "täten", "tät"), ( "ahnen", "ahn"), ( "enten", "ent"), ( "räser", "ras"),
    ( "hrten", "hrt"), ( "ücher", "uch"), ( "örner", "orn"), ( "änder", "and"), ( "ürmer", "urm"),
    ( "ahlen", "ahl"), ( "uhren", "uhr"), ( "ätter", "att"), ( "suren", "sur"), ( "chten", "cht"),
    ( "kuren", "kur"), ( "erzen", "erz"), ( "güter", "gut"), ( "soren", "sor"), ( "änner", "ann"),
    ( "äuser", "aus"), ( "taten", "tat"), ( "isten", "ist"), ( "bäder", "bad"), ( "ämter", "amt"),
    ( "eiten", "eit"), ( "raten", "rat"), ( "ormen", "orm"), ( "ionen", "ion"), ( "nisse", "nis"),
    ( "ölzer", "olz"), ( "ungen", "ung"), ( "läser", "las"), ( "ächer", "ach"), ( "urten", "urt"),
    ( "enzen", "enz"), ( "aaten", "aat"), ( "aphen", "aph"), ( "öcher", "och"), ( "türen", "tür"),
    ( "sonen", "son"), ( "ühren", "ühr"), ( "ühner", "uhn"), ( "toren", "tor"), ( "örter", "ort"),
    ( "anten", "ant"), ( "räder", "rad"), ( "turen", "tur"), ( "äuler", "aul"), (  "änze", "anz"),
    (  "tten", "tte"), (  "mben", "mbe"), (  "ädte", "adt"), (  "llen", "lle"), (  "ysen", "yse"),
    (  "rben", "rbe"), (  "hsen", "hse"), (  "raün", "rau"), (  "rven", "rve"), (  "rken", "rke"),
    (  "ünge", "ung"), (  "üten", "üte"), (  "usen", "use"), (  "tien", "tie"), (  "läne", "lan"),
    (  "iben", "ibe"), (  "ifen", "ife"), (  "ssen", "sse"), (  "gien", "gie"), (  "eten", "ete"),
    (  "rden", "rde"), (  "öhne", "ohn"), (  "ärte", "art"), (  "ncen", "nce"), (  "ünde", "und"),
    (  "uben", "ube"), (  "lben", "lbe"), (  "üsse", "uss"), (  "agen", "age"), (  "räge", "rag"),
    (  "ogen", "oge"), (  "anen", "ane"), (  "sken", "ske"), (  "eden", "ede"), (  "össe", "oss"),
    (  "ürme", "urm"), (  "ggen", "gge"), (  "üren", "üre"), (  "nten", "nte"), (  "ühle", "ühl"),
    (  "änge", "ang"), (  "mmen", "mme"), (  "igen", "ige"), (  "nken", "nke"), (  "äcke", "ack"),
    (  "oden", "ode"), (  "oben", "obe"), (  "ähne", "ahn"), (  "änke", "ank"), (  "inen", "ine"),
    (  "seen", "see"), (  "äfte", "aft"), (  "ulen", "ule"), (  "äste", "ast"), (  "hren", "hre"),
    (  "öcke", "ock"), (  "aben", "abe"), (  "öpfe", "opf"), (  "ugen", "uge"), (  "lien", "lie"),
    (  "ände", "and"), (  "ücke", "ück"), (  "asen", "ase"), (  "aden", "ade"), (  "dien", "die"),
    (  "aren", "are"), (  "tzen", "tze"), (  "züge", "zug"), (  "üfte", "uft"), (  "hien", "hie"),
    (  "nden", "nde"), (  "älle", "all"), (  "hmen", "hme"), (  "ffen", "ffe"), (  "rmen", "rma"),
    (  "olen", "ole"), (  "sten", "ste"), (  "amen", "ame"), (  "höfe", "hof"), (  "üste", "ust"),
    (  "hnen", "hne"), (  "ähte", "aht"), (  "umen", "ume"), (  "nnen", "nne"), (  "alen", "ale"),
    (  "mpen", "mpe"), (  "mien", "mie"), (  "rten", "rte"), (  "rien", "rie"), (  "äute", "aut"),
    (  "uden", "ude"), (  "lgen", "lge"), (  "ngen", "nge"), (  "iden", "ide"), (  "ässe", "ass"),
    (  "osen", "ose"), (  "lken", "lke"), (  "eren", "ere"), (  "üche", "uch"), (  "lüge", "lug"),
    (  "hlen", "hle"), (  "isen", "ise"), (  "ären", "äre"), (  "töne", "ton"), (  "onen", "one"),
    (  "rnen", "rne"), (  "üsen", "üse"), (  "haün", "hau"), (  "pien", "pie"), (  "ihen", "ihe"),
    (  "ürfe", "urf"), (  "esen", "ese"), (  "ätze", "atz"), (  "sien", "sie"), (  "läge", "lag"),
    (  "iven", "ive"), (  "ämme", "amm"), (  "äufe", "auf"), (  "ppen", "ppe"), (  "enen", "ene"),
    (  "lfen", "lfe"), (  "äume", "aum"), (  "nien", "nie"), (  "unen", "une"), (  "cken", "cke"),
    (  "oten", "ote"), (   "mie", "mie"), (   "rie", "rie"), (   "sis", "sen"), (   "rin", "rin"),
    (   "ein", "ein"), (   "age", "age"), (   "ern", "ern"), (   "ber", "ber"), (   "ion", "ion"),
    (   "inn", "inn"), (   "ben", "ben"), (   "äse", "äse"), (   "eis", "eis"), (   "hme", "hme"),
    (   "iss", "iss"), (   "hen", "hen"), (   "fer", "fer"), (   "gie", "gie"), (   "fen", "fen"),
    (   "her", "her"), (   "ker", "ker"), (   "nie", "nie"), (   "mer", "mer"), (   "ler", "ler"),
    (   "men", "men"), (   "ass", "ass"), (   "ner", "ner"), (   "per", "per"), (   "rer", "rer"),
    (   "mus", "mus"), (   "abe", "abe"), (   "ter", "ter"), (   "ser", "ser"), (   "äle", "aal"),
    (   "hie", "hie"), (   "ger", "ger"), (   "tus", "tus"), (   "gen", "gen"), (   "ier", "ier"),
    (   "ver", "ver"), (   "zer", "zer"),
]

singular = {
    "Löwen": "Löwe",
}


def singularize(word, pos=NOUN, gender=MALE, role=SUBJECT, custom={}):
    """ Returns the singular of a given word.
        The inflection is based on probability rather than gender and role.
    """
    w = word.lower().capitalize()
    if word in custom:
        return custom[word]
    if word in singular:
        return singular[word]
    if pos == NOUN:
        for a, b in singular_inflections:
            if w.endswith(a):
                return w[:-len(a)] + b
        # Default rule: strip known plural suffixes (baseline = 51%).
        for suffix in ("nen", "en", "n", "e", "er", "s"):
            if w.endswith(suffix):
                w = w[:-len(suffix)]
                break
        # Corrections (these add about 1% accuracy):
        if w.endswith(("rr", "rv", "nz")):
            return w + "e"
        return w
    return w

#### VERB CONJUGATION ##############################################################################
# The verb table was trained on CELEX and contains the top 2000 most frequent verbs.

prefix_inseparable = (
    "be", "emp", "ent", "er", "ge", "miss", "über", "unter", "ver", "voll", "wider", "zer"
)
prefix_separable = (
    "ab", "an", "auf", "aus", "bei", "durch", "ein", "fort", "mit", "nach", "vor", "weg",
    "zurück", "zusammen", "zu", "dabei", "daran", "da", "empor", "entgegen", "entlang",
    "fehl", "fest", "gegenüber", "gleich", "herab", "heran", "herauf", "heraus", "herum",
    "her", "hinweg", "hinzu", "hin", "los", "nieder", "statt", "umher", "um", "weg",
    "weiter", "wieder", "zwischen"
) + ( # There are many more...
     "dort", "fertig", "frei", "gut", "heim", "hoch", "klein", "klar", "nahe", "offen", "richtig"
)
prefixes = prefix_inseparable + prefix_separable


def encode_sz(s):
    return s.replace("ß", "ss")


def decode_sz(s):
    return s.replace("ss", "ß")


class Verbs(_Verbs):

    def __init__(self):
        _Verbs.__init__(self, os.path.join(MODULE, "de-verbs.txt"),
            language = "de",
              format = [0, 1, 2, 3, 4, 5, 8, 17, 18, 19, 20, 21, 24, 52, 54, 53, 55, 56, 58, 59, 67, 68, 70, 71],
             default = {6: 4, 22: 20, 57: 55, 60: 58, 69: 67, 72: 70}
            )

    def find_lemma(self, verb):
        """ Returns the base form of the given inflected verb, using a rule-based approach.
        """
        v = verb.lower()
        # Common prefixes: be-finden and emp-finden probably inflect like finden.
        if not (v.startswith("ge") and v.endswith("t")): # Probably gerund.
            for prefix in prefixes:
                if v.startswith(prefix) and v[len(prefix):] in self.inflections:
                    return prefix + self.inflections[v[len(prefix):]]
        # Common sufixes: setze nieder => niedersetzen.
        b, suffix = " " in v and v.split()[:2] or (v, "")
        # Infinitive -ln: trommeln.
        if b.endswith(("ln", "rn")):
            return b
        # Lemmatize regular inflections.
        for x in ("test", "est", "end", "ten", "tet", "en", "et", "te", "st", "e", "t"):
            if b.endswith(x):
                b = b[:-len(x)]; break
        # Subjunctive: hielte => halten, schnitte => schneiden.
        for x, y in (
          ("ieb", "eib"), ( "ied", "eid"), ( "ief", "auf" ), ( "ieg", "eig" ), ("iel", "alt"),
          ("ien", "ein"), ("iess", "ass"), ( "ieß", "aß"  ), ( "iff", "eif" ), ("iss", "eiss"),
          ( "iß", "eiß"), (  "it", "eid"), ( "oss", "iess"), ( "öss", "iess")):
            if b.endswith(x):
                b = b[:-len(x)] + y; break
        b = b.replace("eeiss", "eiss")
        b = b.replace("eeid", "eit")
        # Subjunctive: wechselte => wechseln
        if not b.endswith(("e", "l")) and not (b.endswith("er") and len(b) >= 3 and not b[-3] in VOWELS):
            b = b + "e"
        # abknallst != abknalln => abknallen
        if b.endswith(("hl", "ll", "ul", "eil")):
            b = b + "e"
        # Strip ge- from (likely) gerund:
        if b.startswith("ge") and v.endswith("t"):
            b = b[2:]
        # Corrections (these add about 1.5% accuracy):
        if b.endswith(("lnde", "rnde")):
            b = b[:-3]
        if b.endswith(("ae", "al", "öe", "üe")):
            b = b.rstrip("e") + "te"
        if b.endswith("äl"):
            b = b + "e"
        return suffix + b + "n"

    def find_lexeme(self, verb):
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
        pl = b.endswith("el") and b[:-2] + "l" or b
        # Present tense 1pl -el: handeln => wir handeln
        pw = v.endswith(("ln", "rn")) and v or b + "en"
        # Present tense ending in -d or -t gets -e:
        pr = b.endswith(("d", "t")) and b + "e" or b
        # Present tense 2sg gets -st, unless stem ends with -s or -z.
        p2 = pr.endswith(("s", "z")) and pr + "t" or pr + "st"
        # Present participle: spiel + -end, arbeiten + -d:
        pp = v.endswith(("en", "ln", "rn")) and v + "d" or v + "end"
        # Past tense regular:
        pt = encode_sz(pr) + "t"
        # Past participle: haushalten => hausgehalten
        ge = (v.startswith(prefix_inseparable) or b.endswith(("r", "t"))) and pt or "ge" + pt
        ge = x and x + "ge" + pt or ge
        # Present subjunctive: stem + -e, -est, -en, -et:
        s1 = encode_sz(pl)
        # Past subjunctive: past (usually with Umlaut) + -e, -est, -en, -et:
        s2 = encode_sz(pt)
        # Construct the lexeme:
        lexeme = a = [
            v,
            pl + "e" + x1, p2 + x1, pr + "t" + x1, pw + x1, pr + "t" + x1, pp,                 # present
            pt + "e" + x1, pt + "est" + x1, pt + "e" + x1, pt + "en" + x1, pt + "et" + x1, ge, # past
            b + "e" + x1, pr + "t" + x1, x + pw,                                               # imperative
            s1 + "e" + x1, s1 + "est" + x1, s1 + "en" + x1, s1 + "et" + x1,                    # subjunctive I
            s2 + "e" + x1, s2 + "est" + x1, s2 + "en" + x1, s2 + "et" + x1                     # subjunctive II
        ]
        # Encode Eszett (ß) and attempt to retrieve from the lexicon.
        # Decode Eszett for present and imperative.
        if encode_sz(v) in self:
            a = self[encode_sz(v)]
            a = [decode_sz(v) for v in a[:7]] + a[7:13] + [decode_sz(v) for v in a[13:20]] + a[20:]
        # Since the lexicon does not contain imperative for all verbs, don't simply return it.
        # Instead, update the rule-based lexeme with inflections from the lexicon.
        return [a[i] or lexeme[i] for i in range(len(a))]

    def tenses(self, verb, parse=True):
        """ Returns a list of possible tenses for the given inflected verb.
        """
        tenses = _Verbs.tenses(self, verb, parse)
        if len(tenses) == 0:
            # auswirkte => wirkte aus
            for prefix in prefix_separable:
                if verb.startswith(prefix):
                    tenses = _Verbs.tenses(self, verb[len(prefix):] + " " + prefix, parse)
                    break
        return tenses

verbs = Verbs()

conjugate, lemma, lexeme, tenses = \
    verbs.conjugate, verbs.lemma, verbs.lexeme, verbs.tenses

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
                b = w[:max(-len(suffix), -(len(w) - 3))]
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
    if suffix == SUPERLATIVE and b.endswith(("s", "ß")):
        suffix = suffix[1:]
    # große => großere, schönes => schöneres
    return adjective[:len(b)] + suffix + adjective[len(b):]


def comparative(adjective):
    return grade(adjective, COMPARATIVE)


def superlative(adjective):
    return grade(adjective, SUPERLATIVE)

#print(comparative("schönes"))
#print(superlative("schönes"))
#print(superlative("große"))
