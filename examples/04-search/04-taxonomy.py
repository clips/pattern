import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.search import search, taxonomy, Classifier
from pattern.en     import parsetree

# The search module includes a Taxonomy class 
# that can be used to define semantic word types.
# For example, consider that you want to extract flower names from a text.
# This would make search patterns somewhat unwieldy:
# search("rose|lily|daisy|daffodil|begonia", txt).

# A better approach is to use the taxonomy:
for flower in ("rose", "lily", "daisy", "daffodil", "begonia"):
    taxonomy.append(flower, type="flower")
    
print(taxonomy.children("flower"))
print(taxonomy.parents("rose"))
print(taxonomy.classify("rose"))  # Yields the most recently added parent.
print("")
    
# Taxonomy terms can be included in a pattern by using uppercase:
t = parsetree("A field of white daffodils.", lemmata=True)
m = search("FLOWER", t)
print(t)
print(m)
print("")

# Another example:
taxonomy.append("chicken", type="food")
taxonomy.append("chicken", type="bird")
taxonomy.append("penguin", type="bird")
taxonomy.append("bird", type="animal")
print(taxonomy.parents("chicken"))
print(taxonomy.children("animal", recursive=True))
print(search("FOOD", "I'm eating chicken."))
print("")

# The advantage is that the taxonomy can hold an entire hierarchy.
# For example, "flower" could be classified as "organism".
# Other organisms could be defined as well (insects, trees, mammals, ...)
# The ORGANISM constraint then matches everything that is an organism.

# A taxonomy entry can also be a proper name containing spaces
# (e.g. "windows vista", case insensitive).
# It will be detected as long as it is contained in a single chunk:
taxonomy.append("windows vista", type="operating system")
taxonomy.append("ubuntu", type="operating system")

t = parsetree("Which do you like more, Windows Vista, or Ubuntu?")
m = search("OPERATING_SYSTEM", t)
print(t)
print(m)
print(m[0].constituents())
print("")

# Taxonomy entries cannot have wildcards (*),
# but you can use a classifier to simulate this.
# Classifiers are quite slow but useful in many ways.
# For example, a classifier could be written to dynamically
# retrieve word categories from WordNet.

def find_parents(word):
    if word.startswith(("mac os", "windows", "ubuntu")):
        return ["operating system"]
c = Classifier(parents=find_parents)
taxonomy.classifiers.append(c)

t = parsetree("I like Mac OS X 10.5 better than Windows XP or Ubuntu.")
m = search("OPERATING_SYSTEM", t)
print(t)
print(m)
print(m[0].constituents())
print(m[1].constituents())
print("")
