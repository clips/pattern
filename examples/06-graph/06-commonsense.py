import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.graph.commonsense import Commonsense

# A semantic network is a graph in which each node represents a concept
# (e.g., flower, red, rose) and each edge represents a relation between
# concepts, for example rose is-a flower, red is-property-of rose.

# Module pattern.graph.commonsense implements a semantic network of commonsense.
# It contains a Concept class (Node subclass), Relation class (Edge subclass),
# and a Commonsense class (Graph subclass). 
# It contains about 10,000 manually annotated relations between mundane concepts,
# for example gondola is-related-to romance, or spoon is-related-to soup.
# This is the PERCEPTION dataset. See the visualizer at: 
# http://nodebox.net/perception/

# Relation.type can be:
# - is-a,
# - is-part-of,
# - is-opposite-of,
# - is-property-of,
# - is-related-to,
# - is-same-as,
# - is-effect-of.

g = Commonsense()
g.add_node("spork")
g.add_edge("spork", "spoon", type="is-a")

# Concept.halo a list of concepts surrounding the given concept,
# and as such reinforce its meaning:
print
print g["spoon"].halo # fork, etiquette, slurp, hot, soup, mouth, etc.

# Concept.properties is a list of properties (= adjectives) in the halo,
# sorted by betweenness centrality:
print
print g["spoon"].properties # hot


# Commonsense.field() returns a list of concepts 
# that belong to the given class (or "semantic field"):
print
print g.field("color", depth=3, fringe=2) # brown, orange, blue, ...
#print g.field("person") # Leonard Nimoy, Al Capone, ...
#print g.field("building") # opera house, supermarket, ...

# Commonsense.similarity() calculates the similarity between two concepts,
# based on common properties between both 
# (e.g., tigers and zebras are both striped).
print
print g.similarity("tiger", "zebra")
print g.similarity("tiger", "amoeba")

# Commonsense.nearest_neighbors() compares the properties of a given concept
# to a list of other concepts, and selects the concept from the list that
# is most similar to the given concept.
# This will take some time to calculate (thinking is hard).
print
print "Creepy animals:"
print g.nearest_neighbors("creepy", g.field("animal"))[:10]
print
print "Party animals:"
print g.nearest_neighbors("party", g.field("animal"))[:10]

# Creepy animals are: owl, vulture, octopus, bat, raven, ...
# Party animals are: puppy, grasshopper, reindeer, dog, ...