import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.graph import Graph, CSS, CANVAS

# This example demonstrates how to roll dynamic HTML graphs.
# We have a HTML template in which content is inserted on-the-fly.

# This is useful if the graph data changes dynamically, 
# e.g., the user clicks on a node and is taken to a webpage with a new subgraph.

template = '''
<!doctype html> 
<html>
<head>
\t<meta charset="utf-8">
\t<script type="text/javascript" src="canvas.js"></script>
\t<script type="text/javascript" src="graph.js"></script>
\t<style type="text/css">
\t\t%s
\t</style>
</head>
<body> 
\t%s
</body>
</html>
'''.strip()

def webpage(graph, **kwargs):
    s1 = graph.serialize(CSS, **kwargs)
    s2 = graph.serialize(CANVAS, **kwargs)
    return template % (
        s1.replace("\n", "\n\t\t"),
        s2.replace("\n", "\n\t")
    )

# Create a graph:
g = Graph()
g.add_node("cat")
g.add_node("dog")
g.add_edge("cat", "dog")

# To make this work as a cgi-bin script, uncomment the following lines:
##!/usr/bin/env python
#import cgi
#import cgitb; cgitb.enable() # Debug mode.
#print "Content-type: text/html"

print webpage(g, width=500, height=500)
