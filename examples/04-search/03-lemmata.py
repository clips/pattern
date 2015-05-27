import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.search import search, match
from pattern.en     import parsetree

# This example demonstrates an interesting search pattern that mines for comparisons.
# Notice the use of the constraint "be".
# If the output from the parser includes word lemmas (e.g., "doing" => "do")
# these will also be matched. Using "be" then matches "is", "being", "are", ...
# and if underspecification is used "could be", "will be", "definitely was", ...

p = "NP be ADJP|ADVP than NP"

for s in (
  "the turtle was faster than the hare",
  "Arnold Schwarzenegger is more dangerous than Dolph Lundgren"):
    t = parsetree(s, lemmata=True)  # parse lemmas
    m = search(p, t)
    if m:
        # Constituents for the given constraint indices:
        # 0 = NP, 2 = ADJP|ADVP, 4 = NP
        print(m[0].constituents(constraint=[0, 2, 4]))
        print("")


p = "NP be ADJP|ADVP than NP"
t = parsetree("the turtle was faster than the hare", lemmata=True)
m = match(p, t)
print(t)
print("")
for w in m.words:
    print("%s\t=> %s" % (w, m.constraint(w)))
