import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.graph import Graph, WEIGHT, CENTRALITY, DEGREE, DEFAULT
from random        import choice, random

# This example demonstrates how a graph visualization can be exported to HTML,
# using the HTML5 <canvas> tag and Javascript.
# All properties (e.g., stroke color) of nodes and edges are ported.

g = Graph()
# Random nodes.
for i in range(50):
    g.add_node(i)
# Random edges.
for i in range(75):
    node1 = choice(g.nodes)
    node2 = choice(g.nodes)
    g.add_edge(node1, node2, 
               weight = random())

g.prune(0)

# This node's label is different from its id.
g[1].text.string = "home"

# The writer is determined from the file extension.
g.write("test.graphml")
