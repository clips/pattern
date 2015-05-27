# coding: utf-8
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# By default, parse() uses part-of-speech tags from the Penn Treebank tagset:
# http://www.clips.ua.ac.be/pages/penn-treebank-tagset

# It is a good idea to study the tagset and its abbreviations for a few minutes.

from pattern.en import parse as parse_en
print(parse_en("the black cats", chunks=False))        # the/DT black/JJ cat/NNS
print("")


# ... where DT = determiner, JJ = adjective, NN = noun.
# This is true for all languages that Pattern supports:

from pattern.de import parse as parse_de
from pattern.es import parse as parse_es
from pattern.fr import parse as parse_fr
from pattern.it import parse as parse_it
from pattern.nl import parse as parse_nl

print(parse_de("die schwarzen Katzen", chunks=False))  # die/DT schwarze/JJ Katzen/NNS
print(parse_es("los gatos negros"    , chunks=False))  # los/DT gatos/NNS negros/JJ
print(parse_fr("les chats noirs"     , chunks=False))  # les/DT chats/NNS noirs/JJ
print(parse_it("i gatti neri"        , chunks=False))  # i/DT gatti/NNS neri/JJ
print(parse_nl("de zwarte katten"    , chunks=False))  # de/DT zwarte/JJ katten/NNS
print("")

# In some cases, this means the original tagset is mapped to Penn Treebank:
# e.g., for German (STTS), Spanish (PAROLE), Dutch (WOTAN).

from pattern.de import STTS
from pattern.es import PAROLE
from pattern.nl import WOTAN

print(parse_de("die schwarzen Katzen", chunks=False, tagset=STTS))
print(parse_es("los gatos negros"    , chunks=False, tagset=PAROLE))
print(parse_nl("de zwarte katten"    , chunks=False, tagset=WOTAN))
print("")

# Not all languages are equally suited to Penn Treebank,
# which was originally developed for English.

# This becomes more problematic as more languages are added to Pattern.
# It is sometimes difficult to fit determiners, pronouns, prepositions 
# in a particular language to Penn Treebank tags (e.g., Italian "che").
# With parse(tagset=UNIVERSAL), a simplified universal tagset is used,
# loosely corresponding to the recommendations of Petrov (2012):
# http://www.petrovi.de/data/lrec.pdf

# This simplified tagset will still contain all the information that most users require.

from pattern.text import UNIVERSAL
from pattern.text import NOUN, VERB, ADJ, ADV, PRON, DET, PREP, NUM, CONJ, INTJ, PRT, PUNC, X

# NOUN = "NN" (noun)
# VERB = "VB" (verb)
#  ADJ = "JJ" (adjective)
#  ADV = "RB" (adverb)
# PRON = "PR" (pronoun)
#  DET = "DT" (determiner)
# PREP = "PP" (preposition)
#  NUM = "NO" (number)
# CONJ = "CJ" (conjunction)
# INTJ = "UH" (interjection)
#  PRT = "PT" (particle)
# PUNC = "."  (punctuation)
#    X = "X"  (foreign word, abbreviation)

# We can combine this with the multilingual pattern.text.parse() function,
# when we need to deal with code that handles many languages at once:

from pattern.text import parse

print(parse("die schwarzen Katzen", chunks=False, language="de", tagset=UNIVERSAL))
print(parse("the black cats"      , chunks=False, language="en", tagset=UNIVERSAL))
print(parse("los gatos negros"    , chunks=False, language="es", tagset=UNIVERSAL))
print(parse("les chats noirs"     , chunks=False, language="fr", tagset=UNIVERSAL))
print(parse("i gatti neri"        , chunks=False, language="it", tagset=UNIVERSAL))
print(parse("de zwarte katten"    , chunks=False, language="nl", tagset=UNIVERSAL))
print("")

# This comes at the expense of (in this example) losing information about plural nouns (NNS => NN).
# But it may be more comfortable for you to build multilingual apps
# using the universal constants (e.g., PRON, PREP, CONJ), 
# instead of learning the Penn Treebank tagset by heart,
# or wonder why the Italian "che" is tagged "PRP", "IN" or "CC"
# (in the universal tagset it is a PRON or a CONJ).

from pattern.text import parsetree

for sentence in parsetree("i gatti neri che sono la mia", language="it", tagset=UNIVERSAL):
    for word in sentence.words:
        if word.tag == PRON:
            print(word)
            
# The language() function in pattern.text can be used to guess the language of a text.
# It returns a (language code, confidence)-tuple.
# It can guess en, es, de, fr, it, nl.

from pattern.text import language

print("")
print(language(u"the cat sat on the mat"))              # ("en", 1.00)
print(language(u"de kat zat op de mat"))                # ("nl", 0.80)
print(language(u"le chat s'était assis sur le tapis"))  # ("fr", 0.86)