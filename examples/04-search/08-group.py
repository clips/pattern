import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.search import match
from pattern.en     import parsetree

# This example demonstrates how to create match groups.
# A match group is a number of consecutive constraints,
# for which matching words can easily be retrieved from a Match object.

# Suppose we are looking for adjectives preceding nouns.
# A simple pattern is: "JJ?+ NN",
# which matches nouns preceded by any number of adjectives.
# Since the number of nouns can be 0, 1 or 23 it is not so easy
# to fetch the adjectives from a Match. This can be achieved with a group:

s = "The big black cat"
t = parsetree(s)
print(match("{JJ?+} NN", t).group(1))
print("")

# Note the { } wrapper, indicating a group.
# The group can be retrieved from the match as a list of words.

# Suppose we are looking for prepositional noun phrases,
# e.g., on the mat, with a fork, under the hood, etc...
# The preposition is always one word (on, with, under),
# but the actual noun phrase can have many words (a shiny silver fork),
# so it is a hassle to retrieve it from the match.

# Normally, we would do it like this:

s = "The big black cat sat on the mat."
t = parsetree(s)
m = match("NP VP PP NP", t)
for w in m:
    if m.constraint(w).index == 2:
        print("This is the PP: %s" % w)
    if m.constraint(w).index == 3:
        print("This is the NP: %s" % w)

# In other words, iterate over each word in the match,
# checking which constraint it matched and filtering out what we need.

# It is easier with a group:

m = match("NP VP {PP} {NP}", t)
print("")
print("This is the PP: %s" % m.group(1))
print("This is the NP: %s" % m.group(2))
print("")

# Match.group(0) refers to the full search pattern:
print(m.group(0))