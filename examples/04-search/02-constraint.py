import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.search import search, Pattern, Constraint
from pattern.en     import parsetree, parse, Sentence

# What we call a "search word" in example 01-search.py
# is actually called a constraint, because it can contain different options.
# Options are separated by "|".
# The next search pattern retrieves words that are a noun OR an adjective:
s = parsetree("big white rabbit")
print(search("NN|JJ", s))
print("")

# This pattern yields phrases containing an adjective followed by a noun.
# Consecutive constraints are separated by a space:
print(search("JJ NN", s))
print("")

# Or a noun preceded by any number of adjectives:
print(search("JJ?+ NN", s))
print("")

# Note: NN marks singular nouns, NNS marks plural nouns.
# If you want to include both, use "NN*" as a constraint.
# This works for NN*, VB*, JJ*, RB*.

s = parsetree("When I sleep the big white rabbit will stare at my feet.")
m = search("rabbit stare at feet", s)
print(s)
print(m)
print("")
# Why does this work?
# The word "will" is included in the result, even if the pattern does not define it.
# The pattern should break when it does not encounter "stare" after "rabbit."
# It works because "will stare" is one verb chunk.
# The "stare" constraint matches the head word of the chunk ("stare"),
# so "will stare" is considered an overspecified version of "stare".
# The same happens with "my feet" and the "rabbit" constraint,
# which matches the overspecified chunk "the big white rabbit".

p = Pattern.fromstring("rabbit stare at feet", s)
p.strict = True  # Now it matches only what the pattern explicitly defines (=no match).
m = p.search(s)
print m
print("")

# Sentence chunks can be matched by tag (e.g. NP, VP, ADJP).
# The pattern below matches anything from
# "the rabbit gnaws at your fingers" to
# "the white rabbit looks at the carrots":
p = Pattern.fromstring("rabbit VP at NP", s)
m = p.search(s)
print(m)
print("")

if m:
    for w in m[0].words:
        print("%s\t=> %s" % (w, m[0].constraint(w)))

print("")
print("-------------------------------------------------------------")
# Finally, constraints can also include regular expressions.
# To include them we need to use the full syntax instead of the search() function:
import re
r = re.compile(r"[0-9|\.]+") # all numbers
p = Pattern()
p.sequence.append(Constraint(words=[r]))
p.sequence.append(Constraint(tags=["NN*"]))

s = Sentence(parse("I have 9.5 rabbits."))
print(s)
print(p.search(s))
print("")