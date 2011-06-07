import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.graph import Graph, render, SCRIPT, STYLE, CANVAS

# This example demonstrates how to roll dynamic HTML graphs.
# The webpage() command takes a Graph and returns HTML source code.
# This is useful if there is a central location of graph.js on the server,
# and when the graph data changes dynamically, e.g. the user clicks on a node
# and is taken to a new subgraph that is generated on the server on-the-fly.

template = '''
<!DOCTYPE html> 
<html>
<head> 
\t<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
\t<!--[if lte IE 8]><script type="text/javascript" src="excanvas.js"></script><![endif]-->%s
\t<script type="text/javascript" src="graph.js"></script>
\t<script type="text/javascript">
\tfunction init_graph() {
\t\t%s
\t}
\t</script>
\t<style type="text/css">
\t\t%s%s
\t</style>
\t</head>
\t<body onload="javascript:init_graph();"> 
\t\t%s%s%s
\t</body>
</html>
'''.strip()

def webpage(graph, head="", style="", body=("",""), **kwargs):
    """ The head, style and body parameters can be used to insert custom HTML in the template.
        You can pass any optional parameter that can also be passed to render().
    """
    s1 = render(graph, type=SCRIPT, **kwargs)
    s2 = render(graph, type=STYLE,  **kwargs)
    s3 = render(graph, type=CANVAS, **kwargs)
    # Fix HTML source indentation:
    f1 = lambda s, t="\t\t": s.replace("\n","\n"+t)
    f2 = lambda s, t="\t\t": ("\n%s%s" % (t,s.lstrip())).rstrip()
    return template % (
        f2(head,t="\t"), f1(s1), f1(s2), f2(style,t="\t"), f2(body[0]), f1(s3), f2(body[1]))

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
