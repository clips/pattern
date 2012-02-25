import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.graph import Graph, render, STYLE, CANVAS

# This example demonstrates how to roll dynamic HTML graphs.
# The webpage() below command takes a Graph and returns HTML source code.
# This is useful if there is a central location of graph.js on the server,
# and when the graph data changes dynamically, e.g. the user clicks on a node
# and is taken to a new subgraph that is generated on the server on-the-fly.

template = '''
<!DOCTYPE html> 
<html>
<head>%s
\t<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
\t<script type="text/javascript" src="canvas.js"></script>
\t<script type="text/javascript" src="graph.js"></script>
\t<style type="text/css">
\t\t%s%s
\t</style>
</head>
<body> 
\t%s%s%s
</body>
</html>
'''.strip()

def webpage(graph, head="", style="", body=("",""), **kwargs):
    """ The head, style and body parameters can be used to insert custom HTML in the template.
        You can pass any optional parameter that can also be passed to render().
    """
    s1 = render(graph, type=STYLE,  **kwargs)
    s2 = render(graph, type=CANVAS, **kwargs)
    # Fix HTML source indentation:
    # f1 = indent each line
    # f2 = indent first line
    f1 = lambda s, t="\t": s.replace("\n","\n"+t)
    f2 = lambda s, t="\t": ("\n%s%s" % (t,s.lstrip())).rstrip()
    return template % (
        f2(head), f1(s1), f2(style, "\t\t"), f1(body[0]), f1("\n"+s2), f2(body[1]))

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

print webpage(g, width=300, height=300)
