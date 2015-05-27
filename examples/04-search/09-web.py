import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web    import Bing, plaintext
from pattern.en     import parsetree
from pattern.search import Pattern
from pattern.db     import Datasheet, pprint

# "X IS MORE IMPORTANT THAN Y"
# Here is a rough example of how to build a web miner.
# It mines comparative statements from Bing and stores the results in a table,
# which can be saved as a text file for further processing later on.

# Pattern matching also works with Sentence objects from the MBSP module.
# MBSP's parser is much more robust (but also slower).
#from MBSP import Sentence, parse

q = '"more important than"'          # Bing search query
p = "NP VP? more important than NP"  # Search pattern.
p = Pattern.fromstring(p)
d = Datasheet()

engine = Bing(license=None)
for i in range(1):  # max=10
    for result in engine.search(q, start=i+1, count=100, cached=True):
        s = result.description
        s = plaintext(s)
        t = parsetree(s)
        for m in p.search(t):
            a = m.constituents(constraint=0)[-1]  # Left NP.
            b = m.constituents(constraint=5)[ 0]  # Right NP.
            d.append((
                a.string.lower(), 
                b.string.lower()))

pprint(d)

print("")
print("%s results." % len(d))