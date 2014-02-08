import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.graph import Graph, CENTRALITY

# A graph is a network of nodes (or concepts)
# connected to each other with edges (or links).

g = Graph()
for n in ("tree", "nest", "bird", "fly", "insect", "ant"):
    g.add_node(n)
    
g.add_edge("tree", "nest")  # Trees have bird nests.
g.add_edge("nest", "bird")  # Birds live in nests.
g.add_edge("bird", "fly")   # Birds eat flies.
g.add_edge("ant", "bird")   # Birds eat ants.
g.add_edge("fly", "insect") # Flies are insects.
g.add_edge("insect", "ant") # Ants are insects.
g.add_edge("ant", "tree")   # Ants crawl on trees.

# From tree => fly: tree => ant => bird => fly
print g.shortest_path(g.node("tree"), g.node("fly"))
print g.shortest_path(g.node("nest"), g.node("ant"))
print

# Which nodes get the most traffic?
for n in sorted(g.nodes, key=lambda n: n.centrality, reverse=True):
    print '%.2f' % n.centrality, n