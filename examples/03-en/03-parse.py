import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.en import parse, pprint, tag

# The en module contains a fast regular expressions-based parser.
# A parser identifies words in a sentence, word part-of-speech tags (e.g. noun, verb)
# and groups of words that belong together (e.g. noun phrases).
# Common part-of-speech tags: NN (noun), VB (verb), JJ (adjective), PP (preposition).
# A tag can have a suffix, for example NNS (plural noun) or VBG (gerund verb).
# Overview of tags: http://www.clips.ua.ac.be/pages/mbsp-tags
s = "I eat pizza with a fork."
s = parse(s,
     tokenize = True,  # Tokenize the input, i.e. split punctuation from words.
         tags = True,  # Find part-of-speech tags.
       chunks = True,  # Find chunk tags, e.g. "the black cat" = NP = noun phrase.
    relations = True,  # Find relations between chunks.
      lemmata = True,  # Find word lemmata.
        light = False)

# The light parameter determines how unknown words are handled.
# By default, unknown words are tagged NN and then improved with a set of rules.
# light=False uses Brill's lexical and contextual rules,
# light=True uses a set of custom rules that is less accurate but faster (5x-10x).

# The output is a string with each sentence on a new line.
# Words in a sentence have been annotated with tags,
# for example: fork/NN/I-NP/I-PNP
# NN = noun, NP = part of a noun phrase, PNP = part of a prepositional phrase.
print(s)
print("")

# Prettier output can be obtained with the pprint() command:
pprint(s)
print("")

# The string's split() method will (unless a split character is given),
# split into a list of sentences, where each sentence is a list of words
# and each word is a list with the word + its tags.
print(s.split())
print("")

# The tag() command returns a list of (word, POS-tag)-tuples.
# With light=True, this is the fastest and simplest way to get an idea
# of a sentence's constituents:
s = "I eat pizza with a fork."
s = tag(s)
print(s)
for word, tag in s:
    if tag == "NN":  # Find all nouns in the input string.
        print(word)
