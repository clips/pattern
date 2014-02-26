import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.graph import Graph, WEIGHT, CENTRALITY, DEGREE, DEFAULT
from random        import choice, random

# This example demonstrates how a graph visualization can be exported to HTML,
# using the HTML5 <canvas> tag and Javascript.
# All properties (e.g., stroke color) of nodes and edges are ported.

g = Graph()
# Random nodes.
for i in range(50):
    g.add_node(id=str(i+1), 
        radius = 5,
        stroke = (0,0,0,1), 
          text = (0,0,0,1))
# Random edges.
for i in range(75):
    node1 = choice(g.nodes)
    node2 = choice(g.nodes)
    g.add_edge(node1, node2, 
        length = 1.0, 
        weight = random(), 
        stroke = (0,0,0,1))

for node in g.sorted()[:20]:
    # More blue = more important.
    node.fill = (0.6, 0.8, 1.0, 0.8 * node.weight)

g.prune(0)

# This node's label is different from its id.
# We'll make it a hyperlink, see the href attribute at the bottom.
g["1"].text.string = "home"

# The export() command generates a folder with an index.html,
# that displays the graph using an interactive, force-based spring layout.
# You can drag the nodes around - open index.html in a browser and try it out!
# The layout can be tweaked in many ways:

g.export(os.path.join(os.path.dirname(__file__), "test"), 
        width = 700,     # <canvas> width.
       height = 500,     # <canvas> height.
       frames = 500,     # Number of frames of animation.
     directed = True,    # Visualize eigenvector centrality as an edge arrow?
     weighted = 0.5,     # Visualize betweenness centrality as a node shadow?
         pack = True,    # Keep clusters close together + visualize node weight as node radius?
     distance = 10,      # Average edge length.
            k = 4.0,     # Force constant.
        force = 0.01,    # Force dampener.
    repulsion = 50,      # Force radius.
   stylesheet = DEFAULT, # INLINE, DEFAULT, None or the path to your own stylesheet.
   javascript = None,
         href = {"1": "http://www.clips.ua.ac.be/pages/pattern-graph"}, # Node.id => URL
          css = {"1": "node-link-docs"} # Node.id => CSS class.
)
