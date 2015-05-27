import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.search import search
from pattern.en     import parsetree

# Constraints ending in "+" match one or more words.
# Pattern.search() uses a "greedy" approach:
# it will attempt to match as many words as possible.

# The following pattern means:
# one or more words starting with "t",
# followed by one or more words starting with "f".
t = parsetree("one two three four five six")
m = search("t*+ f*+", t)
print(t)
print(m)
print("")

for w in m[0].words:
    print("%s matches %s" % (w, m[0].constraint(w)))

# "*" matches each word in the sentence.
# This yields a list with a Match object for each word.
print("")
print("* => %s" %  search("*", t))

# "*+" matches all words.
# This yields a list with one Match object containing all words.
print("")
print("*+ => %s" % search("*+", t))
