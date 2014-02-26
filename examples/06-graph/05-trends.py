import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Twitter
from pattern.graph import Graph

# This example demonstrates a simple Twitter miner + visualizer.
# We collect tweets containing "A is the new B", 
# mine A and B and use them as connected nodes in a graph.
# Then we export the graph as a browser visualization.

comparisons = []

for i in range(1,10):
    # Set cached=False for live results:
    for result in Twitter(language="en").search("\"is the new\"", start=i, count=100, cached=True):
        s = result.text
        s = s.replace("\n", " ")
        s = s.lower()
        s = s.replace("is the new", "NEW")
        s = s.split(" ")
        try:
            i = s.index("NEW")
            A = s[i-1].strip("?!.:;,#@\"'")
            B = s[i+1].strip("?!.:;,#@\"'")
            # Exclude common phrases such as "this is the new thing".
            if A and B and A not in ("it", "this", "here", "what", "why", "where"):
                comparisons.append((A,B))
        except:
            pass

g = Graph()
for A, B in comparisons:
    e = g.add_edge(B, A) # "A is the new B": A <= B
    e.weight += 0.1
    print B, "=>", A

# Not all nodes will be connected, there will be multiple subgraphs.
# Simply take the largest subgraph for our visualization.
g = g.split()[0]

g.export("trends", weighted=True, directed=True)