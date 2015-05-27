import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.search import search
from pattern.en     import parsetree

# Constraints ending in "?" are optional, matching one or no word.
# Pattern.search() uses a "greedy" approach:
# it will attempt to include as many optional constraints as possible.

# The following pattern scans for words whose part-of-speech tag is NN (i.e. nouns).
# A preceding adjective, adverb or determiner are picked up as well.
for s in (
  "the cat",              # DT NN
  "the very black cat",   # DT RB JJ NN
  "tasty cat food",       # JJ NN NN
  "the funny black cat",  # JJ NN
  "very funny",           # RB JJ => no match, since there is no noun.
  "my cat is black and your cat is white"):  # NN + NN  
    t = parsetree(s)
    m = search("DT? RB? JJ? NN+", t)
    print("")
    print(t)
    print(m)
    if m:
        for w in m[0].words:
            print("%s matches %s" % (w, m[0].constraint(w)))

# Before Pattern 2.4, "( )" was used instead of "?".
# For example: "(JJ)" instead of "JJ?".
# The syntax was changed to resemble regular expressions, which use "?".
# The old syntax "(JJ)" still works in Pattern 2.4, but it may change later.

# Note: the above pattern could also be written as "DT|RB|JJ?+ NN+"
# to include multiple adverbs/adjectives.
# By combining "*", "?" and "+" patterns can become quite complex.
# Optional constraints are useful for very specific patterns, but slow.
# Also, depending on which parser you use (e.g. MBSP), words can be tagged differently
# and may not match in the way you expect.
# Consider using a simple, robust "NP" search pattern.
