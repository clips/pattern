import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.search import Pattern
from pattern.en     import Sentence, parse

# Constraints wrapped in () are optional, matching one or no word.
# Pattern.search() uses a "greedy" approach: 
# it will attempt to include as many optional constraints as possible.

# The following pattern scans for words whose part-of-speech tag is NN (i.e. nouns).
# A preceding adjective, adverb or determiner are picked up as well. 
p = Pattern.fromstring("(DT) (RB) (JJ) NN+")
for s in (
  "the cat",             # DT NN
  "the very black cat",  # DT RB JJ NN
  "tasty cat food",      # JJ NN NN
  "the funny black cat", # JJ NN
  "very funny",          # RB JJ => no match, since there is no noun.
  "my cat is black and your cat is white"): # NN + NN  
    s = Sentence(parse(s))
    m = p.search(s)
    print
    print s
    print m
    if m:
        for w in m[0].words:
            print w, "matches", m[0].constraint(w)

# Note: the above pattern could also be written as "(DT|RB|JJ)+ NN+"
# to include multiple adverbs/adjectives.
# By combining * () and + patterns can become quite complex.
# Optional constraints are useful for very specific patterns, but slow.
# Also, depending on which parser you use (e.g. MBSP), words can be tagged differently
# and may not match in the way you expect.
# Consider using a robust Pattern.fromstring("NP").

print
print "-------------------------------------------------------------"
# This is just a stress test included for debugging purposes:
s = Sentence(parse("I was looking at the big cat, and the big cat was staring back", lemmata=True))
p = Pattern.fromstring("(*_look*|)+ (at|)+ (DT|)+ (*big_cat*)+")
m = p.search(s)
print
print s
print
for m in m:
    print m
