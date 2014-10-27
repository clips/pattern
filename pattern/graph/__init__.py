#### PATTERN | GRAPH ###############################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

import os
import sys

from math     import sqrt, pow
from math     import sin, cos, atan2, degrees, radians, pi
from random   import random
from heapq    import heappush, heappop
from warnings import warn
from codecs   import open
from shutil   import rmtree

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""
    
if sys.version > "3":
    long = int

# float("inf") doesn't work on windows.
INFINITE = 1e20

#--- LIST FUNCTIONS --------------------------------------------------------------------------------

def unique(iterable):
    """ Returns a list copy in which each item occurs only once (in-order).
    """
    seen = set()
    return [x for x in iterable if x not in seen and not seen.add(x)]

#--- DRAWING FUNCTIONS -----------------------------------------------------------------------------
# This module is standalone (i.e., it is not a graph rendering package).
# If you want to call Graph.draw() then line(), ellipse() and Text.draw() must be implemented.

def line(x1, y1, x2, y2, stroke=(0,0,0,1), strokewidth=1):
    """ Draws a line from (x1, y1) to (x2, y2) using the given stroke color and stroke width.
    """
    pass
    
def ellipse(x, y, width, height, fill=(0,0,0,1), stroke=None, strokewidth=1):
    """ Draws an ellipse at (x, y) with given fill and stroke color and stroke width.
    """
    pass

class Text(object):
    
    def __init__(self, string, **kwargs):
        """ Draws the node label.
            Optional properties include width, fill, font, fontsize, fontweight.
        """
        self.string = string
        self.__dict__.update(kwargs)
        
    def copy(self):
        k = self.__dict__.copy()
        k.pop("string")
        return Text(self.string, **k)
        
    def draw(self):
        pass
        
class Vector(object):
    
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        
def coordinates(x, y, distance, angle):
    return (
        (x + distance * cos(radians(angle))),
        (y + distance * sin(radians(angle)))
    )

#--- DEEPCOPY --------------------------------------------------------------------------------------

def deepcopy(o):
    """ Returns a deep (recursive) copy of the given object.
    """
    if o is None:
        return o
    if hasattr(o, "copy"):
        return o.copy()
    if isinstance(o, (basestring, bool, int, float, long, complex)):
        return o
    if isinstance(o, (list, tuple, set)):
        return o.__class__(deepcopy(v) for v in o)
    if isinstance(o, dict):
        return dict((deepcopy(k), deepcopy(v)) for k,v in o.items())
    raise Exception("don't know how to copy %s" % o.__class__.__name__)

#### NODE ##########################################################################################

#--- NODE ------------------------------------------------------------------------------------------

class Node(object):
    
    def __init__(self, id="", radius=5, **kwargs):
        """ A node with a unique id in the graph.
            Node.id is drawn as a text label, unless optional parameter text=False.
            Optional parameters include: fill, stroke, strokewidth, text, font, fontsize, fontweight.
        """
        self.graph       = None
        self.links       = Links()
        self.id          = id
        self._x          = 0.0 # Calculated by Graph.layout.update().
        self._y          = 0.0 # Calculated by Graph.layout.update().
        self.force       = Vector(0.0, 0.0)
        self.radius      = radius
        self.fixed       = kwargs.pop("fixed", False)
        self.fill        = kwargs.pop("fill", None)
        self.stroke      = kwargs.pop("stroke", (0,0,0,1))
        self.strokewidth = kwargs.pop("strokewidth", 1)
        self.text        = kwargs.get("text", True) and \
            Text(isinstance(id, unicode) and id or str(id).decode("utf-8", "ignore"), 
                   width = 85,
                    fill = kwargs.pop("text", (0,0,0,1)), 
                fontsize = kwargs.pop("fontsize", 11), **kwargs) or None
        self._weight     = None # Calculated by Graph.eigenvector_centrality().
        self._centrality = None # Calculated by Graph.betweenness_centrality().
    
    @property
    def _distance(self):
        # Graph.distance controls the (x,y) spacing between nodes.
        return self.graph and float(self.graph.distance) or 1.0
    
    def _get_x(self):
        return self._x * self._distance
    def _get_y(self):
        return self._y * self._distance
    def _set_x(self, v):
        self._x = v / self._distance
    def _set_y(self, v):
        self._y = v / self._distance

    x = property(_get_x, _set_x)
    y = property(_get_y, _set_y)

    @property
    def edges(self):
        """ Yields a list of edges from/to the node.
        """
        return self.graph is not None \
           and [e for e in self.graph.edges if self.id in (e.node1.id, e.node2.id)] \
            or []
            
    @property
    def edge(self, node, reverse=False):
        """ Yields the Edge from this node to the given node, or None.
        """
        if not isinstance(node, Node):
            node = self.graph and self.graph.get(node) or node
        if reverse:
            return node.links.edge(self)
        return self.links.edge(node)
    
    @property
    def weight(self):
        """ Yields eigenvector centrality as a number between 0.0-1.0.
        """
        if self.graph and self._weight is None:
            self.graph.eigenvector_centrality()
        return self._weight
        
    @property
    def centrality(self):
        """ Yields betweenness centrality as a number between 0.0-1.0.
        """
        if self.graph and self._centrality is None:
            self.graph.betweenness_centrality()
        return self._centrality
    
    eigenvector = eigenvector_centrality = weight
    betweenness = betweenness_centrality = centrality
    
    @property
    def degree(self):
        """ Yields degree centrality as a number between 0.0-1.0.
        """
        return self.graph and (1.0 * len(self.links) / len(self.graph)) or 0.0
        
    def flatten(self, depth=1, traversable=lambda node, edge: True, _visited=None):
        """ Recursively lists the node and nodes linked to it.
            Depth 0 returns a list with the node.
            Depth 1 returns a list with the node and all the directly linked nodes.
            Depth 2 includes the linked nodes' links, and so on.
        """
        _visited = _visited or {}
        _visited[self.id] = (self, depth)
        if depth >= 1:
            for n in self.links: 
                if n.id not in _visited or _visited[n.id][1] < depth-1:
                    if traversable(self, self.links.edges[n.id]):
                        n.flatten(depth-1, traversable, _visited)
        return [n for n,d in _visited.values()] # Fast, but not order-preserving.
    
    def draw(self, weighted=False):
        """ Draws the node as a circle with the given radius, fill, stroke and strokewidth.
            Draws the node centrality as a shadow effect when weighted=True.
            Draws the node text label.
            Override this method in a subclass for custom drawing.
        """
        # Draw the node weight as a shadow (based on node betweenness centrality).
        if weighted is not False and self.centrality > (weighted==True and -1 or weighted):
            w = self.centrality * 35
            ellipse(
                self.x, 
                self.y, 
                self.radius*2 + w, 
                self.radius*2 + w, fill=(0,0,0,0.2), stroke=None)
        # Draw the node.
        ellipse(
            self.x, 
            self.y, 
            self.radius*2, 
            self.radius*2, fill=self.fill, stroke=self.stroke, strokewidth=self.strokewidth)
        # Draw the node text label.
        if self.text:
            self.text.draw(
                self.x + self.radius, 
                self.y + self.radius)
        
    def contains(self, x, y):
        """ Returns True if the given coordinates (x, y) are inside the node radius.
        """
        return abs(self.x - x) < self.radius*2 and \
               abs(self.y - y) < self.radius*2
               
    def __repr__(self):
        return "%s(id=%s)" % (self.__class__.__name__, repr(self.id))

    def __eq__(self, node):
        return isinstance(node, Node) and self.id == node.id
    def __ne__(self, node):
        return not self.__eq__(node)

#--- NODE LINKS ------------------------------------------------------------------------------------

class Links(list):
    
    def __init__(self): 
        """ A list in which each node has an associated edge.
            The Links.edge() method returns the edge for a given node id.
        """
        self.edges = dict()
    
    def append(self, node, edge=None):
        if node.id not in self.edges:
            list.append(self, node)
        self.edges[node.id] = edge

    def remove(self, node):
        list.remove(self, node)
        self.edges.pop(node.id, None)

    def edge(self, node): 
        return self.edges.get(isinstance(node, Node) and node.id or node)

#### EDGE ##########################################################################################

class Edge(object):

    def __init__(self, node1, node2, weight=0.0, length=1.0, type=None, stroke=(0,0,0,1), strokewidth=1):
        """ A connection between two nodes.
            Its weight indicates the importance (not the cost) of the connection.
            Its type is useful in a semantic network (e.g. "is-a", "is-part-of", ...)
        """
        self.node1       = node1
        self.node2       = node2
        self._weight     = weight
        self.length      = length
        self.type        = type
        self.stroke      = stroke
        self.strokewidth = strokewidth
    
    def _get_weight(self): 
        return self._weight
    def _set_weight(self, v):
        self._weight = v
        # Clear cached adjacency map in the graph, since edge weights have changed.
        if self.node1.graph is not None: 
            self.node1.graph._adjacency = None
        if self.node2.graph is not None: 
            self.node2.graph._adjacency = None
    
    weight = property(_get_weight, _set_weight)
        
    def draw(self, weighted=False, directed=False):
        """ Draws the edge as a line with the given stroke and strokewidth (increased with Edge.weight).
            Override this method in a subclass for custom drawing.
        """
        w = weighted and self.weight or 0
        line(
            self.node1.x, 
            self.node1.y, 
            self.node2.x, 
            self.node2.y, stroke=self.stroke, strokewidth=self.strokewidth+w)
        if directed:
            self.draw_arrow(stroke=self.stroke, strokewidth=self.strokewidth+w)
            
    def draw_arrow(self, **kwargs):
        """ Draws the direction of the edge as an arrow on the rim of the receiving node.
        """
        x0, y0 = self.node1.x, self.node1.y
        x1, y1 = self.node2.x, self.node2.y
        # Find the edge's angle based on node1 and node2 position.
        a = degrees(atan2(y1-y0, x1-x0))
        # The arrow points to node2's rim instead of it's center.
        r = self.node2.radius
        d = sqrt(pow(x1-x0, 2) + pow(y1-y0, 2))
        x01, y01 = coordinates(x0, y0, d-r-1, a)
        # Find the two other arrow corners under the given angle.
        r = max(kwargs.get("strokewidth", 1) * 3, 6)
        dx1, dy1 = coordinates(x01, y01, -r, a-20)
        dx2, dy2 = coordinates(x01, y01, -r, a+20)
        line(x01, y01, dx1, dy1, **kwargs)
        line(x01, y01, dx2, dy2, **kwargs)
        line(dx1, dy1, dx2, dy2, **kwargs)
    
    def __repr__(self):
        return "%s(id1=%s, id2=%s)" % (self.__class__.__name__, repr(self.node1.id), repr(self.node2.id))

#### GRAPH #########################################################################################

#--- GRAPH NODE DICTIONARY -------------------------------------------------------------------------

class nodedict(dict):
    
    def __init__(self, graph, *args, **kwargs):
        """ Graph.shortest_paths() and Graph.eigenvector_centrality() return a nodedict,
            where dictionary values can be accessed by Node as well as by node id.
        """
        dict.__init__(self, *args, **kwargs)
        self.graph = graph
        
    def __contains__(self, node):
        return dict.__contains__(self, self.graph.get(node, node))
        
    def __getitem__(self, node):
        return dict.__getitem__(self, isinstance(node, Node) and node or self.graph[node])
        
    def get(self, node, default=None):
        return dict.get(self, self.graph.get(node, node), default)

#--- GRAPH -----------------------------------------------------------------------------------------

# Graph layouts:
SPRING = "spring"

# Graph node centrality:
EIGENVECTOR = "eigenvector"
BETWEENNESS = "betweenness"
DEGREE      = "degree"

# Graph node sort order:
WEIGHT, CENTRALITY = "weight", "centrality"

ALL = "all"

class Graph(dict):
    
    def __init__(self, layout=SPRING, distance=10.0):
        """ A network of nodes connected by edges that can be drawn with a given layout.
        """
        self.nodes      = []   # List of Node objects.
        self.edges      = []   # List of Edge objects.
        self.root       = None
        self._adjacency = None # Cached adjacency() dict.
        self.layout     = layout == SPRING and GraphSpringLayout(self) or GraphLayout(self)
        self.distance   = distance
    
    def __getitem__(self, id):
        try: 
            return dict.__getitem__(self, id)
        except KeyError:
            raise KeyError("no node with id '%s' in graph" % id)
    
    def append(self, base, *args, **kwargs):
        """ Appends a Node or Edge to the graph: Graph.append(Node, id="rabbit").
        """
        kwargs["base"] = base
        if issubclass(base, Node):
            return self.add_node(*args, **kwargs)
        if issubclass(base, Edge):
            return self.add_edge(*args, **kwargs)
    
    def add_node(self, id, *args, **kwargs):
        """ Appends a new Node to the graph.
            An optional base parameter can be used to pass a subclass of Node.
        """
        n = kwargs.pop("base", Node)
        n = isinstance(id, Node) and id or self.get(id) or n(id, *args, **kwargs)
        if n.id not in self:
            self.nodes.append(n)
            self[n.id] = n; n.graph = self
            self.root = kwargs.get("root", False) and n or self.root
            # Clear adjacency cache.
            self._adjacency = None
        return n
    
    def add_edge(self, id1, id2, *args, **kwargs):
        """ Appends a new Edge to the graph.
            An optional base parameter can be used to pass a subclass of Edge:
            Graph.add_edge("cold", "winter", base=IsPropertyOf)
        """
        # Create nodes that are not yet part of the graph.
        n1 = self.add_node(id1)
        n2 = self.add_node(id2)
        # Creates an Edge instance.
        # If an edge (in the same direction) already exists, yields that edge instead.
        e1 = n1.links.edge(n2)
        if e1 and e1.node1 == n1 and e1.node2 == n2:
            return e1
        e2 = kwargs.pop("base", Edge)
        e2 = e2(n1, n2, *args, **kwargs)
        self.edges.append(e2)
        # Synchronizes Node.links:
        # A.links.edge(B) yields edge A->B
        # B.links.edge(A) yields edge B->A
        n1.links.append(n2, edge=e2)
        n2.links.append(n1, edge=e1 or e2)
        # Clear adjacency cache.
        self._adjacency = None
        return e2        
            
    def remove(self, x):
        """ Removes the given Node (and all its edges) or Edge from the graph.
            Note: removing Edge a->b does not remove Edge b->a.
        """
        if isinstance(x, Node) and x.id in self:
            self.pop(x.id)
            self.nodes.remove(x); x.graph = None
            # Remove all edges involving the given node.
            for e in list(self.edges):
                if x in (e.node1, e.node2):
                    if x in e.node1.links: e.node1.links.remove(x)
                    if x in e.node2.links: e.node2.links.remove(x)
                    self.edges.remove(e) 
        if isinstance(x, Edge):
            self.edges.remove(x)
        # Clear adjacency cache.
        self._adjacency = None
    
    def node(self, id):
        """ Returns the node in the graph with the given id.
        """
        if isinstance(id, Node) and id.graph == self:
            return id
        return self.get(id, None)
    
    def edge(self, id1, id2):
        """ Returns the edge between the nodes with given id1 and id2.
        """
        if isinstance(id1, Node) and id1.graph == self: 
            id1 = id1.id
        if isinstance(id2, Node) and id2.graph == self: 
            id2 = id2.id
        return id1 in self and id2 in self and self[id1].links.edge(id2) or None
    
    def paths(self, node1, node2, length=4, path=[]):
        """ Returns a list of paths (shorter than or equal to given length) connecting the two nodes.
        """
        if not isinstance(node1, Node): 
            node1 = self[node1]
        if not isinstance(node2, Node): 
            node2 = self[node2]
        return [[self[id] for id in p] for p in paths(self, node1.id, node2.id, length, path)]
    
    def shortest_path(self, node1, node2, heuristic=None, directed=False):
        """ Returns a list of nodes connecting the two nodes.
        """
        if not isinstance(node1, Node): 
            node1 = self[node1]
        if not isinstance(node2, Node): 
            node2 = self[node2]
        try: 
            p = dijkstra_shortest_path(self, node1.id, node2.id, heuristic, directed)
            p = [self[id] for id in p]
            return p
        except IndexError:
            return None
            
    def shortest_paths(self, node, heuristic=None, directed=False):
        """ Returns a dictionary of nodes, each linked to a list of nodes (shortest path).
        """
        if not isinstance(node, Node): 
            node = self[node]
        p = nodedict(self)
        for id, path in dijkstra_shortest_paths(self, node.id, heuristic, directed).items():
            p[self[id]] = path and [self[id] for id in path] or None
        return p 
            
    def eigenvector_centrality(self, normalized=True, reversed=True, rating={}, iterations=100, tolerance=0.0001):
        """ Calculates eigenvector centrality and returns a node => weight dictionary.
            Node.weight is updated in the process.
            Node.weight is higher for nodes with a lot of (indirect) incoming traffic.
        """
        ec = eigenvector_centrality(self, normalized, reversed, rating, iterations, tolerance)
        ec = nodedict(self, ((self[id], w) for id, w in ec.items()))
        for n, w in ec.items(): 
            n._weight = w
        return ec
            
    def betweenness_centrality(self, normalized=True, directed=False):
        """ Calculates betweenness centrality and returns a node => weight dictionary.
            Node.centrality is updated in the process.
            Node.centrality is higher for nodes with a lot of passing traffic.
        """
        bc = brandes_betweenness_centrality(self, normalized, directed)
        bc = nodedict(self, ((self[id], w) for id, w in bc.items()))
        for n, w in bc.items(): 
            n._centrality = w
        return bc
        
    def sorted(self, order=WEIGHT, threshold=0.0):
        """ Returns a list of nodes sorted by WEIGHT or CENTRALITY.
            Nodes with a lot of traffic will be at the start of the list.
        """
        o = lambda node: getattr(node, order)
        nodes = ((o(n), n) for n in self.nodes if o(n) >= threshold)
        nodes = reversed(sorted(nodes))
        return [n for w, n in nodes]
        
    def prune(self, depth=0):
        """ Removes all nodes with less or equal links than depth.
        """
        for n in (n for n in self.nodes if len(n.links) <= depth):
            self.remove(n)
            
    def fringe(self, depth=0, traversable=lambda node, edge: True):
        """ For depth=0, returns the list of leaf nodes (nodes with only one connection).
            For depth=1, returns the list of leaf nodes and their connected nodes, and so on.
        """
        u = []; [u.extend(n.flatten(depth, traversable)) for n in self.nodes if len(n.links) == 1]
        return unique(u)
        
    @property
    def density(self):
        """ Yields the number of edges vs. the maximum number of possible edges.
            For example, <0.35 => sparse, >0.65 => dense, 1.0 => complete.
        """
        return 2.0*len(self.edges) / (len(self.nodes) * (len(self.nodes)-1))
        
    @property
    def is_complete(self):
        return self.density == 1.0
    @property
    def is_dense(self):
        return self.density > 0.65
    @property
    def is_sparse(self):
        return self.density < 0.35
        
    def split(self):
        """ Returns the list of unconnected subgraphs.
        """
        return partition(self)
    
    def update(self, iterations=10, **kwargs):
        """ Graph.layout.update() is called the given number of iterations.
        """
        for i in range(iterations):
            self.layout.update(**kwargs)
        
    def draw(self, weighted=False, directed=False):
        """ Draws all nodes and edges.
        """
        for e in self.edges: 
            e.draw(weighted, directed)
        for n in reversed(self.nodes): # New nodes (with Node._weight=None) first. 
            n.draw(weighted)
            
    def node_at(self, x, y):
        """ Returns the node at (x,y) or None.
        """
        for n in self.nodes:
            if n.contains(x, y): return n
    
    def _add_node_copy(self, n, **kwargs):
        # Magical fairy dust to copy subclasses of Node.
        # We assume that the subclass constructor takes an optional "text" parameter
        # (Text objects in NodeBox for OpenGL's implementation are expensive).
        try:
            new = self.add_node(n.id, root=kwargs.get("root",False), text=False)
        except TypeError:
            new = self.add_node(n.id, root=kwargs.get("root",False))
        new.__class__ = n.__class__
        new.__dict__.update((k, deepcopy(v)) for k,v in n.__dict__.items() 
            if k not in ("graph", "links", "_x", "_y", "force", "_weight", "_centrality"))
    
    def _add_edge_copy(self, e, **kwargs):
        if kwargs.get("node1", e.node1).id not in self \
        or kwargs.get("node2", e.node2).id not in self: 
            return
        new = self.add_edge(
            kwargs.get("node1", self[e.node1.id]), 
            kwargs.get("node2", self[e.node2.id]))
        new.__class__ = e.__class__
        new.__dict__.update((k, deepcopy(v)) for k,v in e.__dict__.items()
            if k not in ("node1", "node2"))
    
    def copy(self, nodes=ALL):
        """ Returns a copy of the graph with the given list of nodes (and connecting edges).
            The layout will be reset.
        """
        g = Graph(layout=None, distance=self.distance)
        g.layout = self.layout.copy(graph=g)
        for n in (nodes==ALL and self.nodes or (isinstance(n, Node) and n or self[n] for n in nodes)):
            g._add_node_copy(n, root=self.root==n)
        for e in self.edges: 
            g._add_edge_copy(e)
        return g
        
    def export(self, *args, **kwargs):
        export(self, *args, **kwargs)
    
    def write(self, *args, **kwargs):
        write(self, *args, **kwargs)
    
    def serialize(self, *args, **kwargs):
        return render(self, *args, **kwargs)

#--- GRAPH LAYOUT ----------------------------------------------------------------------------------
# Graph drawing or graph layout, as a branch of graph theory, 
# applies topology and geometry to derive two-dimensional representations of graphs.

class GraphLayout(object):
    
    def __init__(self, graph):
        """ Calculates node positions iteratively when GraphLayout.update() is called.
        """
        self.graph = graph
        self.iterations = 0
    
    def update(self):
        self.iterations += 1

    def reset(self):
        self.iterations = 0
        for n in self.graph.nodes:
            n._x = 0.0
            n._y = 0.0
            n.force = Vector(0.0, 0.0)
            
    @property
    def bounds(self):
        """ Returns a (x, y, width, height)-tuple of the approximate layout dimensions.
        """
        x0, y0 = +INFINITE, +INFINITE
        x1, y1 = -INFINITE, -INFINITE
        for n in self.graph.nodes:
            if (n.x < x0): x0 = n.x
            if (n.y < y0): y0 = n.y
            if (n.x > x1): x1 = n.x
            if (n.y > y1): y1 = n.y
        return (x0, y0, x1-x0, y1-y0)

    def copy(self, graph):
        return GraphLayout(self, graph)

#--- GRAPH LAYOUT: FORCE-BASED ---------------------------------------------------------------------

class GraphSpringLayout(GraphLayout):
    
    def __init__(self, graph):
        """ A force-based layout in which edges are regarded as springs.
            The forces are applied to the nodes, pulling them closer or pushing them apart.
        """
        # Based on: http://snipplr.com/view/1950/graph-javascript-framework-version-001/
        GraphLayout.__init__(self, graph)
        self.k         = 4.0  # Force constant.
        self.force     = 0.01 # Force multiplier.
        self.repulsion = 50   # Maximum repulsive force radius.

    def _distance(self, node1, node2):
        # Yields a tuple with distances (dx, dy, d, d**2).
        # Ensures that the distance is never zero (which deadlocks the animation).
        dx = node2._x - node1._x
        dy = node2._y - node1._y
        d2 = dx * dx + dy * dy
        if d2 < 0.01:
            dx = random() * 0.1 + 0.1
            dy = random() * 0.1 + 0.1
            d2 = dx * dx + dy * dy
        return dx, dy, sqrt(d2), d2

    def _repulse(self, node1, node2):
        # Updates Node.force with the repulsive force.
        dx, dy, d, d2 = self._distance(node1, node2)
        if d < self.repulsion:
            f = self.k ** 2 / d2
            node2.force.x += f * dx
            node2.force.y += f * dy
            node1.force.x -= f * dx
            node1.force.y -= f * dy
            
    def _attract(self, node1, node2, weight=0, length=1.0):
        # Updates Node.force with the attractive edge force.
        dx, dy, d, d2 = self._distance(node1, node2)
        d = min(d, self.repulsion)
        f = (d2 - self.k ** 2) / self.k * length
        f *= weight * 0.5 + 1
        f /= d
        node2.force.x -= f * dx
        node2.force.y -= f * dy
        node1.force.x += f * dx
        node1.force.y += f * dy
        
    def update(self, weight=10.0, limit=0.5):
        """ Updates the position of nodes in the graph.
            The weight parameter determines the impact of edge weight.
            The limit parameter determines the maximum movement each update().
        """
        GraphLayout.update(self)
        # Forces on all nodes due to node-node repulsions.
        for i, n1 in enumerate(self.graph.nodes):
            for j, n2 in enumerate(self.graph.nodes[i+1:]):          
                self._repulse(n1, n2)
        # Forces on nodes due to edge attractions.
        for e in self.graph.edges:
            self._attract(e.node1, e.node2, weight * e.weight, 1.0 / (e.length or 0.01))
        # Move nodes by given force.
        for n in self.graph.nodes:
            if not n.fixed:
                n._x += max(-limit, min(self.force * n.force.x, limit))
                n._y += max(-limit, min(self.force * n.force.y, limit))
            n.force.x = 0
            n.force.y = 0
            
    def copy(self, graph):
        g = GraphSpringLayout(graph)
        g.k, g.force, g.repulsion = self.k, self.force, self.repulsion
        return g

#### GRAPH ANALYSIS ################################################################################

#--- GRAPH SEARCH ----------------------------------------------------------------------------------

def depth_first_search(node, visit=lambda node: False, traversable=lambda node, edge: True, _visited=None):
    """ Visits all the nodes connected to the given root node, depth-first.
        The visit function is called on each node.
        Recursion will stop if it returns True, and subsequently dfs() will return True.
        The traversable function takes the current node and edge,
        and returns True if we are allowed to follow this connection to the next node.
        For example, the traversable for directed edges is follows:
         lambda node, edge: node == edge.node1
    """
    stop = visit(node)
    _visited = _visited or {}
    _visited[node.id] = True
    for n in node.links:
        if stop: return True
        if traversable(node, node.links.edge(n)) is False: continue
        if not n.id in _visited:
            stop = depth_first_search(n, visit, traversable, _visited)
    return stop
    
dfs = depth_first_search;

def breadth_first_search(node, visit=lambda node: False, traversable=lambda node, edge: True):
    """ Visits all the nodes connected to the given root node, breadth-first.
    """
    q = [node]
    _visited = {}
    while q:
        node = q.pop(0)
        if not node.id in _visited:
            if visit(node):
                return True
            q.extend((n for n in node.links if traversable(node, node.links.edge(n)) is not False))
            _visited[node.id] = True
    return False
        
bfs = breadth_first_search;

def paths(graph, id1, id2, length=4, path=[], _root=True):
    """ Returns a list of paths from node with id1 to node with id2.
        Only paths shorter than or equal to the given length are included.
        Uses a brute-force DFS approach (performance drops exponentially for longer paths).
    """
    if len(path) >= length:
        return []
    if id1 not in graph:
        return []
    if id1 == id2:
        return [path + [id1]]
    path = path + [id1]
    p = []
    s = set(path) # 5% speedup.
    for node in graph[id1].links:
        if node.id not in s: 
            p.extend(paths(graph, node.id, id2, length, path, False))
    return _root and sorted(p, key=len) or p

def edges(path):
    """ Returns an iterator of Edge objects for the given list of nodes.
        It yields None where two successive nodes are not connected.
    """
    # For example, the distance (i.e., edge weight sum) of a path:
    # sum(e.weight for e in edges(path))
    return len(path) > 1 and (n.links.edge(path[i+1]) for i,n in enumerate(path[:-1])) or iter(())

#--- GRAPH ADJACENCY -------------------------------------------------------------------------------

def adjacency(graph, directed=False, reversed=False, stochastic=False, heuristic=None):
    """ Returns a dictionary indexed by node id1's,
        in which each value is a dictionary of connected node id2's linking to the edge weight.
        If directed=True, edges go from id1 to id2, but not the other way.
        If stochastic=True, all the weights for the neighbors of a given node sum to 1.
        A heuristic function can be given that takes two node id's and returns
        an additional cost for movement between the two nodes.
    """
    # Caching a heuristic from a method won't work.
    # Bound method objects are transient, 
    # i.e., id(object.method) returns a new value each time.
    if graph._adjacency is not None and \
       graph._adjacency[1:] == (directed, reversed, stochastic, heuristic and heuristic.func_code):
        return graph._adjacency[0]
    map = {}
    for n in graph.nodes:
        map[n.id] = {}
    for e in graph.edges:
        id1, id2 = not reversed and (e.node1.id, e.node2.id) or (e.node2.id, e.node1.id)
        map[id1][id2] = 1.0 - 0.5 * e.weight
        if heuristic:
            map[id1][id2] += heuristic(id1, id2)
        if not directed: 
            map[id2][id1] = map[id1][id2]
    if stochastic:
        for id1 in map:
            n = sum(map[id1].values())
            for id2 in map[id1]: 
                map[id1][id2] /= n
    # Cache the adjacency map: this makes dijkstra_shortest_path() 2x faster in repeated use.
    graph._adjacency = (map, directed, reversed, stochastic, heuristic and heuristic.func_code)
    return map

def dijkstra_shortest_path(graph, id1, id2, heuristic=None, directed=False):
    """ Dijkstra algorithm for finding the shortest path between two nodes.
        Returns a list of node id's, starting with id1 and ending with id2.
        Raises an IndexError between nodes on unconnected graphs.
    """
    # Based on: Connelly Barnes, http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/119466
    def flatten(list):
        # Flattens a linked list of the form [0,[1,[2,[]]]]
        while len(list) > 0:
            yield list[0]; list=list[1]
    G = adjacency(graph, directed=directed, heuristic=heuristic)
    q = [(0, id1, ())] # Heap of (cost, path_head, path_rest).
    visited = set()    # Visited nodes.
    while True:
        (cost1, n1, path) = heappop(q)
        if n1 not in visited:
            visited.add(n1)
        if n1 == id2:
            return list(flatten(path))[::-1] + [n1]
        path = (n1, path)
        for (n2, cost2) in G[n1].items():
            if n2 not in visited:
                heappush(q, (cost1 + cost2, n2, path))

def dijkstra_shortest_paths(graph, id, heuristic=None, directed=False):
    """ Dijkstra algorithm for finding the shortest paths from the given node to all other nodes.
        Returns a dictionary of node id's, each linking to a list of node id's (i.e., the path).
    """
    # Based on: Dijkstra's algorithm for shortest paths modified from Eppstein.
    # Based on: NetworkX 1.4.1: Aric Hagberg, Dan Schult and Pieter Swart.
    # This is 5x faster than:
    # for n in g: dijkstra_shortest_path(g, id, n.id)
    W = adjacency(graph, directed=directed, heuristic=heuristic)
    Q = [] # Use Q as a heap with (distance, node id)-tuples.
    D = {} # Dictionary of final distances.
    P = {} # Dictionary of paths.
    P[id] = [id] 
    seen = {id: 0} 
    heappush(Q, (0, id))
    while Q:
        (dist, v) = heappop(Q)
        if v in D: continue
        D[v] = dist
        for w in W[v].keys():
            vw_dist = D[v] + W[v][w]
            if w not in D and (w not in seen or vw_dist < seen[w]):
                seen[w] = vw_dist
                heappush(Q, (vw_dist, w))
                P[w] = P[v] + [w]
    for n in graph:
        if n not in P: P[n]=None
    return P

def floyd_warshall_all_pairs_distance(graph, heuristic=None, directed=False):
    """ Floyd-Warshall's algorithm for finding the path length for all pairs for nodes.
        Returns a dictionary of node id's, 
        each linking to a dictionary of node id's linking to path length.
    """
    from collections import defaultdict # Requires Python 2.5+.
    g = graph.keys()
    d = defaultdict(lambda: defaultdict(lambda: 1e30)) # float('inf')
    p = defaultdict(dict) # Predecessors.
    for e in graph.edges:
        u = e.node1.id
        v = e.node2.id
        w = 1.0 - 0.5 * e.weight
        w = heuristic and heuristic(u, v) + w or w
        d[u][v] = min(w, d[u][v])
        d[u][u] = 0
        p[u][v] = u
        if not directed:
            d[v][u] = min(w, d[v][u])
            p[v][u] = v
    for w in g:
        dw = d[w]
        for u in g:
            du, duw = d[u], d[u][w]
            for v in g:
                # Performance optimization, assumes d[w][v] > 0.
                #if du[v] > duw + dw[v]:
                if du[v] > duw and du[v] > duw + dw[v]:
                    d[u][v] = duw + dw[v]
                    p[u][v] = p[w][v]
    class pdict(dict):
        def __init__(self, predecessors, *args, **kwargs):
            dict.__init__(self, *args, **kwargs)
            self.predecessors = predecessors
    return pdict(p, ((u, dict((v, w) for v,w in d[u].items() if w < 1e30)) for u in d))

def predecessor_path(tree, u, v):
    """ Returns the path between node u and node v as a list of node id's.
        The given tree is the return value of floyd_warshall_all_pairs_distance().predecessors.
    """
    def _traverse(u, v):
        w = tree[u][v]
        if w == u:
            return []
        return _traverse(u,w) + [w] + _traverse(w,v)
    return [u] + _traverse(u,v) + [v]

#--- GRAPH CENTRALITY ------------------------------------------------------------------------------

def brandes_betweenness_centrality(graph, normalized=True, directed=False):
    """ Betweenness centrality for nodes in the graph.
        Betweenness centrality is a measure of the number of shortests paths that pass through a node.
        Nodes in high-density areas will get a good score.
    """
    # Ulrik Brandes, A Faster Algorithm for Betweenness Centrality,
    # Journal of Mathematical Sociology 25(2):163-177, 2001,
    # http://www.inf.uni-konstanz.de/algo/publications/b-fabc-01.pdf
    # Based on: Dijkstra's algorithm for shortest paths modified from Eppstein.
    # Based on: NetworkX 1.0.1: Aric Hagberg, Dan Schult and Pieter Swart.
    # http://python-networkx.sourcearchive.com/documentation/1.0.1/centrality_8py-source.html
    W = adjacency(graph, directed=directed)
    b = dict.fromkeys(graph, 0.0)
    for id in graph:
        Q = [] # Use Q as a heap with (distance, node id)-tuples.
        D = {} # Dictionary of final distances.
        P = {} # Dictionary of paths.
        for n in graph: P[n]=[]
        seen = {id: 0} 
        heappush(Q, (0, id, id))
        S = []
        E = dict.fromkeys(graph, 0) # sigma
        E[id] = 1.0
        while Q:    
            (dist, pred, v) = heappop(Q) 
            if v in D: 
                continue
            D[v] = dist
            S.append(v)
            E[v] += E[pred]
            for w in W[v]:
                vw_dist = D[v] + W[v][w]
                if w not in D and (w not in seen or vw_dist < seen[w]): 
                    seen[w] = vw_dist 
                    heappush(Q, (vw_dist, v, w))
                    P[w] = [v]
                    E[w] = 0.0
                elif vw_dist == seen[w]: # Handle equal paths.
                    P[w].append(v)
                    E[w] += E[v] 
        d = dict.fromkeys(graph, 0.0)  
        for w in reversed(S):
            for v in P[w]:
                d[v] += (1.0 + d[w]) * E[v] / E[w]
            if w != id: 
                b[w] += d[w]
    # Normalize between 0.0 and 1.0.
    m = normalized and max(b.values()) or 1
    b = dict((id, w/m) for id, w in b.items())
    return b

def eigenvector_centrality(graph, normalized=True, reversed=True, rating={}, iterations=100, tolerance=0.0001):
    """ Eigenvector centrality for nodes in the graph (cfr. Google's PageRank).
        Eigenvector centrality is a measure of the importance of a node in a directed network. 
        It rewards nodes with a high potential of (indirectly) connecting to high-scoring nodes.
        Nodes with no incoming connections have a score of zero.
        If you want to measure outgoing connections, reversed should be False.        
    """
    # Based on: NetworkX, Aric Hagberg (hagberg@lanl.gov)
    # http://python-networkx.sourcearchive.com/documentation/1.0.1/centrality_8py-source.html
    # Note: much faster than betweenness centrality (which grows exponentially).
    def normalize(vector):
        w = 1.0 / (sum(vector.values()) or 1)
        for node in vector: 
            vector[node] *= w
        return vector
    G = adjacency(graph, directed=True, reversed=reversed)
    v = normalize(dict([(n, random()) for n in graph])) # Node ID => weight vector.
    # Eigenvector calculation using the power iteration method: y = Ax.
    # It has no guarantee of convergence.
    for i in range(iterations):
        v0 = v
        v  = dict.fromkeys(v0.keys(), 0)
        for n1 in v:
            for n2 in G[n1]:
                v[n1] += 0.01 + v0[n2] * G[n1][n2] * rating.get(n1, 1)
        normalize(v)
        e = sum([abs(v[n]-v0[n]) for n in v]) # Check for convergence.
        if e < len(G) * tolerance:
            # Normalize between 0.0 and 1.0.
            m = normalized and max(v.values()) or 1
            v = dict((id, w/m) for id, w in v.items())
            return v
    warn("node weight is 0 because eigenvector_centrality() did not converge.", Warning)
    return dict((n, 0) for n in G)

#--- GRAPH PARTITIONING ----------------------------------------------------------------------------

# a | b => all elements from a and all the elements from b. 
# a & b => elements that appear in a as well as in b.
# a - b => elements that appear in a but not in b.
def union(a, b):
    return list(set(a) | set(b))
def intersection(a, b):
    return list(set(a) & set(b))
def difference(a, b):
    return list(set(a) - set(b))

def partition(graph):
    """ Returns a list of unconnected subgraphs.
    """
    # Creates clusters of nodes and directly connected nodes.
    # Iteratively merges two clusters if they overlap.
    g = []
    for n in graph.nodes:
        g.append(dict.fromkeys((n.id for n in n.flatten()), True))
    for i in reversed(range(len(g))):
        for j in reversed(range(i+1, len(g))):
            if g[i] and g[j] and len(intersection(g[i], g[j])) > 0:
                g[i] = union(g[i], g[j])
                g[j] = []
    g = [graph.copy(nodes=[graph[id] for id in n]) for n in g if n]
    g.sort(lambda a, b: len(b) - len(a))
    return g

def is_clique(graph):
    """ A clique is a set of nodes in which each node is connected to all other nodes.
    """
    #for n1 in graph.nodes:
    #    for n2 in graph.nodes:
    #        if n1 != n2 and graph.edge(n1.id, n2.id) is None:
    #            return False
    return graph.density == 1.0
    
def clique(graph, id):
    """ Returns the largest possible clique for the node with given id.
    """
    if isinstance(id, Node):
        id = id.id
    a = [id]
    for n in graph.nodes:
        try:
            # Raises StopIteration if all nodes in the clique are connected to n:
            next(id for id in a if n.id==id or graph.edge(n.id, id) is None)
        except StopIteration:
            a.append(n.id)
    return a
    
def cliques(graph, threshold=3):
    """ Returns all cliques in the graph with at least the given number of nodes.
    """
    a = []
    for n in graph.nodes:
        c = clique(graph, n.id)
        if len(c) >= threshold: 
            c.sort()
            if c not in a: a.append(c)
    return a

#### GRAPH UTILITY FUNCTIONS #######################################################################
# Utility functions for safely linking and unlinking of nodes,
# with respect for the surrounding nodes.

def unlink(graph, node1, node2=None):
    """ Removes the edges between node1 and node2.
        If only node1 is given, removes all edges to and from it.
        This does not remove node1 from the graph.
    """
    if not isinstance(node1, Node):
        node1 = graph[node1]
    if not isinstance(node2, Node) and node2 is not None:
        node2 = graph[node2]
    for e in list(graph.edges):
        if node1 in (e.node1, e.node2) and node2 in (e.node1, e.node2, None):
            graph.edges.remove(e)
            try:
                node1.links.remove(node2)
                node2.links.remove(node1)
            except: # 'NoneType' object has no attribute 'links'
                pass

def redirect(graph, node1, node2):
    """ Connects all of node1's edges to node2 and unlinks node1.
    """
    if not isinstance(node1, Node):
        node1 = graph[node1]
    if not isinstance(node2, Node):
        node2 = graph[node2]
    for e in graph.edges:
        if node1 in (e.node1, e.node2):
            if e.node1 == node1 and e.node2 != node2:
                graph._add_edge_copy(e, node1=node2, node2=e.node2) 
            if e.node2 == node1 and e.node1 != node2: 
                graph._add_edge_copy(e, node1=e.node1, node2=node2) 
    unlink(graph, node1)

def cut(graph, node):
    """ Unlinks the given node, but keeps edges intact by connecting the surrounding nodes.
        If A, B, C, D are nodes and A->B, B->C, B->D, if we then cut B: A->C, A->D.
    """
    if not isinstance(node, Node):
        node = graph[node]
    for e in graph.edges:
        if node in (e.node1, e.node2):
            for n in node.links:
                if e.node1 == node and e.node2 != n: 
                    graph._add_edge_copy(e, node1=n, node2=e.node2) 
                if e.node2 == node and e.node1 != n: 
                    graph._add_edge_copy(e, node1=e.node1, node2=n) 
    unlink(graph, node)

def insert(graph, node, a, b):
    """ Inserts the given node between node a and node b.
        If A, B, C are nodes and A->B, if we then insert C: A->C, C->B.
    """
    if not isinstance(node, Node):
        node = graph[node]
    if not isinstance(a, Node): 
        a = graph[a]
    if not isinstance(b, Node): 
        b = graph[b]
    for e in graph.edges:
        if e.node1 == a and e.node2 == b: 
            graph._add_edge_copy(e, node1=a, node2=node) 
            graph._add_edge_copy(e, node1=node, node2=b) 
        if e.node1 == b and e.node2 == a: 
            graph._add_edge_copy(e, node1=b, node2=node) 
            graph._add_edge_copy(e, node1=node, node2=a) 
    unlink(graph, a, b)

#### GRAPH EXPORT ##################################################################################

class GraphRenderer(object):
    
    def __init__(self, graph):
        self.graph = graph

    def serialize(self, *args, **kwargs):
        pass

    def export(self, path, *args, **kwargs):
        pass

#--- GRAPH EXPORT: HTML5 <CANVAS> ELEMENT ---------------------------------------------------------
# Exports graphs to interactive web pages using graph.js.

def minify(js):
    """ Returns a compressed Javascript string with comments and whitespace removed.
    """
    import re
    W = (
        "\(\[\{\,\;\=\-\+\*\/",
        "\)\]\}\,\;\=\-\+\*\/"
    )
    for a, b in (
      (re.compile(r"\/\*.*?\*\/", re.S), ""),    # multi-line comments /**/
      (re.compile(r"\/\/.*"), ""),               # singe line comments //
      (re.compile(r";\n"), "; "),                # statements (correctly) terminated with ;
      (re.compile(r"[ \t]+"), " "),              # spacing and indentation
      (re.compile(r"[ \t]([\(\[\{\,\;\=\-\+\*\/])"), "\\1"),
      (re.compile(r"([\)\]\}\,\;\=\-\+\*\/])[ \t]"), "\\1"),
      (re.compile(r"\s+\n"), "\n"),
      (re.compile(r"\n+"), "\n")):
        js = a.sub(b, js)
    return js.strip()

DEFAULT, INLINE = "default", "inline"
HTML, CANVAS, STYLE, CSS, SCRIPT, DATA = \
    "html", "canvas", "style", "css", "script", "data"

class HTMLCanvasRenderer(GraphRenderer):
    
    def __init__(self, graph, **kwargs):
        self.graph    = graph
        self._source  = \
            "<!doctype html>\n" \
            "<html>\n" \
            "<head>\n" \
                "\t<title>%s</title>\n" \
                "\t<meta charset=\"utf-8\">\n" \
                "\t%s\n" \
                "\t<script type=\"text/javascript\" src=\"%scanvas.js\"></script>\n" \
                "\t<script type=\"text/javascript\" src=\"%sgraph.js\"></script>\n" \
            "</head>\n" \
            "<body>\n" \
                "\t<div id=\"%s\" style=\"width:%spx; height:%spx;\">\n" \
                    "\t\t<script type=\"text/canvas\">\n" \
                        "\t\t%s\n" \
                    "\t\t</script>\n" \
                "\t</div>\n" \
            "</body>\n" \
            "</html>"
        # HTML
        self.title      = "Graph" # <title>Graph</title>
        self.javascript = None    # Path to canvas.js + graph.js.
        self.stylesheet = INLINE  # Either None, INLINE, DEFAULT (style.css) or a custom path.
        self.id         = "graph" # <div id="graph">
        self.ctx        = "canvas.element"
        self.width      = 700     # Canvas width in pixels.
        self.height     = 500     # Canvas height in pixels.
        # JS Graph
        self.frames     = 500     # Number of frames of animation.
        self.fps        = 30      # Frames per second.
        self.ipf        = 2       # Iterations per frame.
        self.weighted   = False   # Indicate betweenness centrality as a shadow?
        self.directed   = False   # Indicate edge direction with an arrow?
        self.prune      = None    # None or int, calls Graph.prune() in Javascript.
        self.pack       = True    # Shortens leaf edges, adds eigenvector weight to node radius.
        # JS GraphLayout
        self.distance   = graph.distance         # Node spacing.
        self.k          = graph.layout.k         # Force constant.
        self.force      = graph.layout.force     # Force dampener.
        self.repulsion  = graph.layout.repulsion # Repulsive force radius.
        # Data
        self.weight     = [DEGREE, WEIGHT, CENTRALITY]
        self.href       = {}      # Dictionary of Node.id => URL.
        self.css        = {}      # Dictionary of Node.id => CSS classname.
        # Default options.
        # If a Node or Edge has one of these settings,
        # it is not passed to Javascript to save bandwidth.
        self.default = {
                "radius": 5,
                 "fixed": False,
                  "fill": None,
                "stroke": (0,0,0,1),
           "strokewidth": 1,
                  "text": (0,0,0,1),
              "fontsize": 11,
        }
        # Override settings from keyword arguments.
        self.default.update(kwargs.pop("default", {}))
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def _escape(self, s):
        if isinstance(s, basestring):
            return "\"%s\"" % s.replace("\"", "\\\"")
        return s
    
    def _rgba(self, clr):
        # Color or tuple to a CSS "rgba(255,255,255,1.0)" string.
        return "\"rgba(%s,%s,%s,%.2f)\"" % (int(clr[0]*255), int(clr[1]*255), int(clr[2]*255), clr[3])

    @property
    def data(self):
        """ Yields a string of Javascript code that loads the nodes and edges into variable g,
            which is a Javascript Graph object (see graph.js).
            This can be the response of an XMLHttpRequest, after wich you move g into your own variable.
        """
        return "".join(self._data())
    
    def _data(self):
        s = []
        s.append("g = new Graph(%s, %s);\n" % (self.ctx, self.distance))
        s.append("var n = {")
        if len(self.graph.nodes) > 0:
            s.append("\n")
        # Translate node properties to Javascript dictionary (var n).
        for n in self.graph.nodes:
            p = []
            if n._x != 0:
                p.append("x:%i" % n._x)                           # 0
            if n._y != 0:
                p.append("y:%i" % n._y)                           # 0
            if n.radius != self.default["radius"]:
                p.append("radius:%.1f" % n.radius)                # 5.0
            if n.fixed != self.default["fixed"]:
                p.append("fixed:%s" % repr(n.fixed).lower())      # false
            if n.fill != self.default["fill"]:
                p.append("fill:%s" % self._rgba(n.fill))          # [0,0,0,1.0]
            if n.stroke != self.default["stroke"]:
                p.append("stroke:%s" % self._rgba(n.stroke))      # [0,0,0,1.0]
            if n.strokewidth != self.default["strokewidth"]:
                p.append("strokewidth:%.1f" % n.strokewidth)      # 0.5
            if n.text is None:
                p.append("text:false")
            if n.text and n.text.fill != self.default["text"]:
                p.append("text:%s" % self._rgba(n.text.fill))     # [0,0,0,1.0]
            if n.text and "font" in n.text.__dict__:
                p.append("font:\"%s\"" % n.text.__dict__["font"]) # "sans-serif"
            if n.text and n.text.__dict__.get("fontsize", self.default["fontsize"]) != self.default["fontsize"]:
                p.append("fontsize:%i" % int(max(1, n.text.fontsize)))
            if n.text and "fontweight" in n.text.__dict__:        # "bold"
                p.append("fontweight:\"%s\"" % n.text.__dict__["fontweight"])
            if n.text and n.text.string != n.id:
                p.append("label:\"%s\"" % n.text.string)
            if n.id in self.href:
                p.append("href:\"%s\"" % self.href[n.id])
            if n.id in self.css:
                p.append("css:\"%s\"" % self.css[n.id])
            s.append("\t%s: {%s},\n" % (self._escape(n.id), ", ".join(p)))
        s[-1] = s[-1].rstrip(",\n") # Trailing comma breaks in IE.
        s.append("\n};\n")
        s.append("var e = [")
        if len(self.graph.edges) > 0:
            s.append("\n")
        # Translate edge properties to Javascript dictionary (var e).
        for e in self.graph.edges:
            id1, id2 = self._escape(e.node1.id), self._escape(e.node2.id)
            p = []
            if e.weight != 0:
                p.append("weight:%.2f" % e.weight)                # 0.00
            if e.length != 1:
                p.append("length:%.2f" % e.length)                # 1.00
            if e.type is not None:
                p.append("type:\"%s\"" % e.type)                  # "is-part-of"
            if e.stroke != self.default["stroke"]:
                p.append("stroke:%s" % self._rgba(e.stroke))      # [0,0,0,1.0]
            if e.strokewidth != self.default["strokewidth"]:
                p.append("strokewidth:%.2f" % e.strokewidth)      # 0.5
            s.append("\t[%s, %s, {%s}],\n" % (id1, id2, ", ".join(p)))
        s[-1] = s[-1].rstrip(",\n") # Trailing comma breaks in IE.
        s.append("\n];\n")
        # Append the nodes to graph g.
        s.append("for (var id in n) {\n"
                    "\tg.addNode(id, n[id]);\n"
                 "}\n")
        # Append the edges to graph g.
        s.append("for (var i=0; i < e.length; i++) {\n"
                    "\tvar n1 = g.nodeset[e[i][0]];\n"
                    "\tvar n2 = g.nodeset[e[i][1]];\n"
                    "\tg.addEdge(n1, n2, e[i][2]);\n"
                 "}")
        return s

    @property
    def script(self):
        """ Yields a string of canvas.js code.
            A setup() function loads the nodes and edges into variable g (Graph),
            A draw() function starts the animation and updates the layout of g.
        """
        return "".join(self._script())

    def _script(self):
        s = [];
        s.append("function setup(canvas) {\n")
        s.append(   "\tcanvas.size(%s, %s);\n" % (self.width, self.height))
        s.append(   "\tcanvas.fps = %s;\n" % (self.fps))
        s.append(   "\t" + "".join(self._data()).replace("\n", "\n\t"))
        s.append(   "\n")
        # Apply the layout settings.
        s.append(   "\tg.layout.k = %s; // Force constant (= edge length).\n"
                    "\tg.layout.force = %s; // Repulsive strength.\n"
                    "\tg.layout.repulsion = %s; // Repulsive radius.\n" % (
                        self.k, 
                        self.force, 
                        self.repulsion))
        # Apply eigenvector, betweenness and degree centrality.
        if self.weight is True: s.append(
                    "\tg.eigenvectorCentrality();\n"
                    "\tg.betweennessCentrality();\n"
                    "\tg.degreeCentrality();\n")
        if isinstance(self.weight, (list, tuple)):
            if WEIGHT in self.weight: s.append(
                    "\tg.eigenvectorCentrality();\n")
            if CENTRALITY in self.weight: s.append(
                    "\tg.betweennessCentrality();\n")
            if DEGREE in self.weight: s.append(
                    "\tg.degreeCentrality();\n")
        # Apply node weight to node radius.
        if self.pack: s.append(
                    "\t// Apply Node.weight to Node.radius.\n"
                    "\tfor (var i=0; i < g.nodes.length; i++) {\n"
                        "\t\tvar n = g.nodes[i];\n"
                        "\t\tn.radius = n.radius + n.radius * n.weight;\n"
                    "\t}\n")
        # Apply edge length (leaves get shorter edges).
        if self.pack: s.append(
                    "\t// Apply Edge.length (leaves get shorter edges).\n"
                    "\tfor (var i=0; i < g.nodes.length; i++) {\n"
                        "\t\tvar e = g.nodes[i].edges();\n"
                        "\t\tif (e.length == 1) {\n"
                        "\t\t\te[0].length *= 0.2;\n"
                        "\t\t}\n"
                    "\t}\n")
        # Apply pruning.
        if self.prune is not None: s.append(
                    "\tg.prune(%s);\n" % self.prune)
        # Implement <canvas> draw().
        s.append("}\n")
        s.append("function draw(canvas) {\n"
                    "\tif (g.layout.iterations <= %s) {\n"
                        "\t\tcanvas.clear();\n"
                        "\t\t//shadow();\n"
                        "\t\tstroke(0);\n"
                        "\t\tfill(0,0);\n"
                        "\t\tg.update(%s);\n"
                        "\t\tg.draw(%s, %s);\n"
                    "\t}\n"
                    "\tg.drag(canvas.mouse);\n"
                 "}" % (
            int(self.frames),
            int(self.ipf), 
            str(self.weighted).lower(),
            str(self.directed).lower()))
        return s
    
    @property
    def canvas(self):
        """ Yields a string of HTML with a <div id="graph"> containing a <script type="text/canvas">.
            The <div id="graph"> wrapper is required as a container for the node labels.
        """
        s = [
            "<div id=\"%s\" style=\"width:%spx; height:%spx;\">\n" % (self.id, self.width, self.height),
                "\t<script type=\"text/canvas\">\n",
                "\t\t%s\n" % self.script.replace("\n", "\n\t\t"),
                "\t</script>\n",
            "</div>"
        ]
        return "".join(s)
    
    @property
    def style(self):
        """ Yields a string of CSS for <div id="graph">.
        """
        return \
            "body { font: 11px sans-serif; }\n" \
            "a { color: dodgerblue; }\n" \
            "#%s canvas { }\n" \
            "#%s .node-label { font-size: 11px; }\n" \
            "#%s {\n" \
                "\tdisplay: inline-block;\n" \
                "\tposition: relative;\n" \
                "\toverflow: hidden;\n" \
                "\tborder: 1px solid #ccc;\n" \
            "}" % (self.id, self.id, self.id)
    
    @property
    def html(self):
        """ Yields a string of HTML to visualize the graph using a force-based spring layout.
            The js parameter sets the path to graph.js and canvas.js.
        """
        js  = self.javascript or ""
        if self.stylesheet == INLINE:
            css = self.style.replace("\n","\n\t\t").rstrip("\t")
            css = "<style type=\"text/css\">\n\t\t%s\n\t</style>" % css
        elif self.stylesheet == DEFAULT:
            css = "<link rel=\"stylesheet\" href=\"style.css\" type=\"text/css\" media=\"screen\" />"
        elif self.stylesheet is not None:
            css = "<link rel=\"stylesheet\" href=\"%s\" type=\"text/css\" media=\"screen\" />" % self.stylesheet
        else:
            css = ""
        s = self._script()
        s = "".join(s)
        s = "\t" + s.replace("\n", "\n\t\t\t")
        s = s.rstrip()
        s = self._source % (
            self.title, 
            css, 
            js, 
            js, 
            self.id, 
            self.width, 
            self.height, 
            s)
        return s

    def serialize(self, type=HTML):
        if type == HTML:
            return self.html
        if type == CANVAS:
            return self.canvas
        if type in (STYLE, CSS):
            return self.style
        if type == SCRIPT:
            return self.script
        if type == DATA:
            return self.data
    
    # Backwards compatibility.
    render = serialize

    def export(self, path, encoding="utf-8"):
        """ Generates a folder at the given path containing an index.html
            that visualizes the graph using the HTML5 <canvas> tag.
        """
        if os.path.exists(path):
            rmtree(path)
        os.mkdir(path)
        # Copy compressed graph.js + canvas.js (unless a custom path is given.)
        if self.javascript is None:
            for p, f in (("..", "canvas.js"), (".", "graph.js")):
                a = open(os.path.join(MODULE, p, f), "r")
                b = open(os.path.join(path, f), "w")
                b.write(minify(a.read()))
                b.close()
        # Create style.css.
        if self.stylesheet == DEFAULT:
            f = open(os.path.join(path, "style.css"), "w")
            f.write(self.style)
            f.close()
        # Create index.html.
        f = open(os.path.join(path, "index.html"), "w", encoding=encoding)
        f.write(self.html)
        f.close()

#--- GRAPH EXPORT: GRAPHML ------------------------------------------------------------------------
# Exports graphs as GraphML XML, which can be read by Gephi (https://gephi.org).
# Author: Frederik Elwert <frederik.elwert@web.de>, 2014.

GRAPHML = "graphml"

class GraphMLRenderer(GraphRenderer):

    def serialize(self, directed=False):
        p = "tmp.graphml"
        self.export(p, directed, encoding="utf-8")
        s = open(p, encoding="utf-8").read()
        os.unlink(p)
        return s

    def export(self, path, directed=False, encoding="utf-8"):
        """ Generates a GraphML XML file at the given path.
        """
        import xml.etree.ElementTree as etree
        ns = "{http://graphml.graphdrawing.org/xmlns}"
        etree.register_namespace("", ns.strip("{}"))
        # Define type for node labels (string).
        # Define type for node edges (float).
        root = etree.Element(ns + "graphml")
        root.insert(0, etree.Element(ns + "key", **{
            "id": "node_label", "for": "node", "attr.name": "label", "attr.type": "string"
        }))
        root.insert(0, etree.Element(ns + "key", **{
            "id": "edge_weight", "for": "edge", "attr.name": "weight", "attr.type": "double"
        }))
        # Map Node.id => GraphML node id.
        m = {}        
        g = etree.SubElement(root, ns + "graph", id="g", edgedefault=directed and "directed" or "undirected")
        # Export nodes.
        for i, n in enumerate(self.graph.nodes):
            m[n.id] = "node%s" % i
            x = etree.SubElement(g, ns + "node", id=m[n.id])
            x = etree.SubElement(x, ns + "data", key="node_label")
            if n.text and n.text.string != n.id:
                x.text = n.text.string
        # Export edges.
        for i, e in enumerate(self.graph.edges):
            x = etree.SubElement(g, ns + "edge", id="edge%s" % i, source=m[e.node1.id], target=m[e.node2.id])
            x = etree.SubElement(x, ns + "data", key="edge_weight")
            x.text = "%.3f" % e.weight
        # Export graph with pretty indented XML.
        # http://effbot.org/zone/element-lib.htm#prettyprint
        def indent(e, level=0):
            w = "\n" + level * "  "
            if len(e):
                if not e.text or not e.text.strip():
                    e.text = w + "  "
                if not e.tail or not e.tail.strip():
                    e.tail = w
                for e in e:
                    indent(e, level+1)
                if not e.tail or not e.tail.strip():
                    e.tail = w
            else:
                if level and (not e.tail or not e.tail.strip()):
                    e.tail = w
        indent(root)
        tree = etree.ElementTree(root)
        tree.write(path, encoding=encoding)

#--------------------------------------------------------------------------------------------------
# The export() and serialize() function are called from Graph.export() and Graph.serialize(),
# and are expected to handle any GraphRenderer by specifying an optional type=HTML|GRAPHML.

def export(graph, path, encoding="utf-8", **kwargs):
    type = kwargs.pop("type", HTML)
    # Export to GraphML.
    if type == GRAPHML or path.endswith(".graphml"):
        r = GraphMLRenderer(graph)
        return r.export(path, directed=kwargs.get("directed", False), encoding=encoding)
    # Export to HTML with <canvas>.
    if type == HTML:
        kwargs.setdefault("stylesheet", DEFAULT)
        r = HTMLCanvasRenderer(graph, **kwargs)
        return r.export(path, encoding)

def serialize(graph, type=HTML, **kwargs):
    # Return GraphML string.
    if type == GRAPHML:
        r = GraphMLRenderer(graph)
        return r.serialize(directed=kwargs.get("directed", False))
    # Return HTML string.
    if type in (HTML, CANVAS, STYLE, CSS, SCRIPT, DATA):
        kwargs.setdefault("stylesheet", INLINE)
        r = HTMLCanvasRenderer(graph, **kwargs)
        return r.serialize(type)
    
# Backwards compatibility.
write, render = export, serialize
