#### PATTERN | COMMONSENSE #########################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

from codecs    import BOM_UTF8
from urllib    import urlopen
from itertools import chain

from __init__ import Graph, Node, Edge, bfs
from __init__ import WEIGHT, CENTRALITY, EIGENVECTOR, BETWEENNESS

import os

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

#### COMMONSENSE SEMANTIC NETWORK ##################################################################

#--- CONCEPT ---------------------------------------------------------------------------------------

class Concept(Node):
    
    def __init__(self, *args, **kwargs):
        """ A concept in the sematic network.
        """
        Node.__init__(self, *args, **kwargs)
        self._properties = None
    
    @property
    def halo(self, depth=2):
        """ Returns the concept halo: a list with this concept + surrounding concepts.
            This is useful to reason more fluidly about the concept,
            since the halo will include latent properties linked to nearby concepts.
        """
        return self.flatten(depth=depth)
        
    @property
    def properties(self):
        """ Returns the top properties in the concept halo, sorted by betweenness centrality.
            The return value is a list of concept id's instead of Concepts (for performance).
        """
        if self._properties is None:
            g = self.graph.copy(nodes=self.halo)
            p = (n for n in g.nodes if n.id in self.graph.properties)
            p = [n.id for n in reversed(sorted(p, key=lambda n: n.centrality))]
            self._properties = p
        return self._properties

def halo(concept, depth=2):
    return concept.flatten(depth=depth)

def properties(concept, depth=2, centrality=BETWEENNESS):
    g = concept.graph.copy(nodes=halo(concept, depth))
    p = (n for n in g.nodes if n.id in concept.graph.properties)
    p = [n.id for n in reversed(sorted(p, key=lambda n: getattr(n, centrality)))]
    return p

#--- RELATION --------------------------------------------------------------------------------------

class Relation(Edge):
    
    def __init__(self, *args, **kwargs):
        """ A relation between two concepts, with an optional context.
            For example, "Felix is-a cat" is in the "media" context, "tiger is-a cat" in "nature".
        """
        self.context = kwargs.pop("context", None)
        Edge.__init__(self, *args, **kwargs)

#--- HEURISTICS ------------------------------------------------------------------------------------
# Similarity between concepts is measured using a featural approach:
# a comparison of the features/properties that are salient in each concept's halo.
# Commonsense.similarity() takes an optional "heuristic" parameter to tweak this behavior.
# It is a tuple of two functions:
# 1) function(concept) returns a list of salient properties (or other),
# 2) function(concept1, concept2) returns the cost to traverse this edge (0.0-1.0).

COMMONALITY = (
    # Similarity heuristic that only traverses relations between properties.
    lambda concept: concept.properties,
    lambda edge: 1 - int(edge.context == "properties" and \
                         edge.type != "is-opposite-of"))

#--- COMMONSENSE -----------------------------------------------------------------------------------

class Commonsense(Graph):
    
    def __init__(self, data=os.path.join(MODULE, "commonsense.csv"), **kwargs):
        """ A semantic network of commonsense, using different relation types:
            - is-a,
            - is-part-of,
            - is-opposite-of,
            - is-property-of,
            - is-related-to,
            - is-same-as,
            - is-effect-of.
        """
        Graph.__init__(self, **kwargs)
        self._properties = None
        # Load data from the given path,
        # a CSV-file of (concept1, relation, concept2, context, weight)-items.
        if data is not None:
            s = open(data).read()
            s = s.strip(BOM_UTF8)
            s = s.decode("utf-8")
            s = ((v.strip("\"") for v in r.split(",")) for r in s.splitlines())
            for concept1, relation, concept2, context, weight in s:
                self.add_edge(concept1, concept2, 
                    type = relation, 
                 context = context, 
                  weight = min(int(weight)*0.1, 1.0))

    @property
    def concepts(self):
        return self.nodes
        
    @property
    def relations(self):
        return self.edges
        
    @property
    def properties(self):
        """ Yields all concepts that are properties (i.e., adjectives).
            For example: "cold is-property-of winter" => "cold".
        """
        if self._properties is None:
            #self._properties = set(e.node1.id for e in self.edges if e.type == "is-property-of")
            self._properties = (e for e in self.edges if e.context == "properties")
            self._properties = set(chain(*((e.node1.id, e.node2.id) for e in self._properties)))
        return self._properties
    
    def add_node(self, id, *args, **kwargs):
        """ Returns a Concept (Node subclass).
        """
        self._properties = None
        kwargs.setdefault("base", Concept)
        return Graph.add_node(self, id, *args, **kwargs)
        
    def add_edge(self, id1, id2, *args, **kwargs):
        """ Returns a Relation between two concepts (Edge subclass).
        """
        self._properties = None
        kwargs.setdefault("base", Relation)
        return Graph.add_edge(self, id1, id2, *args, **kwargs)
        
    def remove(self, x):
        self._properties = None
        Graph.remove(self, x)

    def similarity(self, concept1, concept2, k=3, heuristic=COMMONALITY):
        """ Returns the similarity of the given concepts,
            by cross-comparing shortest path distance between k concept properties.
            A given concept can also be a flat list of properties, e.g. ["creepy"].
            The given heuristic is a tuple of two functions:
            1) function(concept) returns a list of salient properties,
            2) function(edge) returns the cost for traversing this edge (0.0-1.0).
        """
        if isinstance(concept1, basestring):
            concept1 = self[concept1]
        if isinstance(concept2, basestring):
            concept2 = self[concept2]
        if isinstance(concept1, Node):
            concept1 = heuristic[0](concept1)
        if isinstance(concept2, Node):
            concept2 = heuristic[0](concept2)
        if isinstance(concept1, list):
            concept1 = [isinstance(n, Node) and n or self[n] for n in concept1]
        if isinstance(concept2, list):
            concept2 = [isinstance(n, Node) and n or self[n] for n in concept2]
        h = lambda id1, id2: heuristic[1](self.edge(id1, id2))
        w = 0.0
        for p1 in concept1[:k]:
            for p2 in concept2[:k]:
                p = self.shortest_path(p1, p2, heuristic=h)
                w += 1.0 / (p is None and 1e10 or len(p))
        return w / k
        
    def nearest_neighbors(self, concept, concepts=[], k=3):
        """ Returns the k most similar concepts from the given list.
        """
        return sorted(concepts, key=lambda candidate: self.similarity(concept, candidate, k), reverse=True)
        
    similar = neighbors = nn = nearest_neighbors

    def taxonomy(self, concept, depth=3, fringe=2):
        """ Returns a list of concepts that are descendants of the given concept, using "is-a" relations.
            Creates a subgraph of "is-a" related concepts up to the given depth,
            then takes the fringe (i.e., leaves) of the subgraph.
        """
        def traversable(node, edge):
            # Follow parent-child edges.
            return edge.node2 == node and edge.type == "is-a"
        if not isinstance(concept, Node):
            concept = self[concept]
        g = self.copy(nodes=concept.flatten(depth, traversable))
        g = g.fringe(depth=fringe)
        g = [self[n.id] for n in g if n != concept]
        return g
        
    field = semantic_field = taxonomy

#g = Commonsense()
#print(g.nn("party", g.field("animal")))
#print(g.nn("creepy", g.field("animal")))

#### COMMONSENSE DATA ##############################################################################

#--- NODEBOX.NET/PERCEPTION ------------------------------------------------------------------------

def download(path=os.path.join(MODULE, "commonsense.csv"), threshold=50):
    """ Downloads commonsense data from http://nodebox.net/perception.
        Saves the data as commonsense.csv which can be the input for Commonsense.load().
    """
    s = "http://nodebox.net/perception?format=txt&robots=1"
    s = urlopen(s).read()
    s = s.decode("utf-8")
    s = s.replace("\\'", "'")
    # Group relations by author.
    a = {}
    for r in ([v.strip("'") for v in r.split(", ")] for r in s.split("\n")):
        if len(r) == 7:
            a.setdefault(r[-2], []).append(r)
    # Iterate authors sorted by number of contributions.
    # 1) Authors with 50+ contributions can define new relations and context.
    # 2) Authors with 50- contributions (or robots) can only reinforce existing relations.
    a = sorted(a.items(), cmp=lambda v1, v2: len(v2[1]) - len(v1[1]))
    r = {}
    for author, relations in a:
        if author == "" or author.startswith("robots@"):
            continue
        if len(relations) < threshold:
            break
        # Sort latest-first (we prefer more recent relation types).
        relations = sorted(relations, cmp=lambda r1, r2: r1[-1] > r2[-1])
        # 1) Define new relations.
        for concept1, relation, concept2, context, weight, author, date in relations:
            id = (concept1, relation, concept2)
            if id not in r:
                r[id] = [None, 0]
            if r[id][0] is None and context is not None:
                r[id][0] = context
    for author, relations in a:
        # 2) Reinforce existing relations.
        for concept1, relation, concept2, context, weight, author, date in relations:
            id = (concept1, relation, concept2)
            if id in r:
                r[id][1] += int(weight)
    # Export CSV-file.
    s = []
    for (concept1, relation, concept2), (context, weight) in r.items():
        s.append("\"%s\",\"%s\",\"%s\",\"%s\",%s" % (
            concept1, relation, concept2, context, weight))
    f = open(path, "w")
    f.write(BOM_UTF8)
    f.write("\n".join(s).encode("utf-8"))
    f.close()
    
def json():
    """ Returns a JSON-string with the data from commonsense.csv.
        Each relation is encoded as a [concept1, relation, concept2, context, weight] list.
    """
    f = lambda s: s.replace("'", "\\'").encode("utf-8")
    s = []
    g = Commonsense()
    for e in g.edges:
        s.append("\n\t['%s', '%s', '%s', '%s', %.2f]" % (
            f(e.node1.id),
            f(e.type),
            f(e.node2.id),
            f(e.context),
              e.weight
        ))
    return "commonsense = [%s];" % ", ".join(s)

#download("commonsense.csv", threshold=50)
#open("commonsense.js", "w").write(json())
