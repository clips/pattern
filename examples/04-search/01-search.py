import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.search import search
from pattern.en     import parsetree

# The pattern.search module contains a number of pattern matching tools
# to search a string syntactically (word function) or semantically (word meaning).
# If you only need to match string characters, regular expressions are faster.
# However, if you are scanning a sentence for concept types (e.g. all flowers)
# or parts-of-speech (e.g. all adjectives), this module provides the functionality.

# In the simplest case, the search() function
# takes a word (or a sequence of words) that you want to retrieve:
print(search("rabbit", "big white rabbit"))
print("")

# Search words can contain wildcard characters:
print(search("rabbit*", "big white rabbit"))
print(search("rabbit*", "big white rabbits"))
print("")

# Search words can contain different options:
print(search("rabbit|cony|bunny", "big black bunny"))
print("")

# Things become more interesting if we involve the pattern.en.parser module.
# The parser takes a string, identifies words, and assigns a part-of-speech tag
# to each word, for example NN (noun) or JJ (adjective).
# A parsed sentence can be scanned for part-of-speech tags:
s = parsetree("big white rabbit")
print(search("JJ", s))  # all adjectives
print(search("NN", s))  # all nouns
print(search("NP", s))  # all noun phrases
print("")

# Since the search() is case-insensitive, uppercase search words
# are always considered to be tags (or taxonomy terms - see further examples).

# The return value is a Match object,
# where Match.words is a list of Word objects that matched:
m = search("NP", s)
for word in m[0].words:
    print(word.string, word.tag)
