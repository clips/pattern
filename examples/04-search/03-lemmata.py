import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.search import search, Pattern, Constraint
from pattern.en     import Sentence, parse

# This example demonstrates an interesting search pattern that mines for comparisons.
# Notice the use of the constraint "be".
# If the output from the parser includes word lemmas (e.g. "doing" => "do")
# these will also be matched. Using "be" then matches "is", "being", "are", ...
# and if underspecification is used "could be", "will be", "definitely was", ...

p = Pattern.fromstring("NP be ADJP|ADVP than NP")

for s in (
  "the turtle was faster than the hare",
  "Arnold Schwarzenegger is more dangerous than Dolph Lundgren"):
    s = s = Sentence(parse(s, lemmata=True)) # parse lemmas
    m = p.search(s)
    print s
    print
    print m
    print
    if m:
        print m[0].constituents()                   # Words grouped by chunk whenever possible.
        print m[0].constraints(chunk=s.chunks[0])   # The constraints that match the given chunk.
        print m[0].constituents(constraint=p[0])    # Constituents for the given constraint.
        print m[0].constituents(constraint=[0,2,4]) # Constituents for the given constraint indices.
        print
        print
        print
        
        
p = Pattern.fromstring("NP be ADJP|ADVP than NP")
s = Sentence(parse("the turtle was faster than the hare", lemmata=True))
m = p.match(s)
print s
for w in m.words:
    print w, " \t=>", m.constraint(w)
