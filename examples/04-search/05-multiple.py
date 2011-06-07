import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.search import Pattern
from pattern.en     import Sentence, parse

# Constraints ending in + match one or more words.
# Pattern.search() uses a "greedy" approach: 
# it will attempt to match as many words as possible.

# The following pattern means:
# one or more words starting with "t", 
# followed by one or more words starting with "f".
p = Pattern.fromstring("t*+ f*+")
s = Sentence(parse("one two three four five six"))
m = p.search(s)
print s
print m
print

for w in m[0].words:
    print w, "matches", m[0].constraint(w)

# Pattern.fromstring("*") matches each word in the sentence.
# This yields a list with a Match object for each word.
print
print "* =>",  Pattern.fromstring("*").search(s)

# Pattern.fromstring("*+") matches all words.
# This yields a list with one Match object containing all words.
print
print "*+ =>", Pattern.fromstring("*+").search(s)
