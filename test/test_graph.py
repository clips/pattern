# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest

from pattern import graph
from pattern.graph import commonsense

from builtins import str, bytes, int, dict
from builtins import map, zip, filter
from builtins import object, range

#---------------------------------------------------------------------------------------------------


class TestUtilityFunctions(unittest.TestCase):

    def setUp(self):
        pass

    def test_deepcopy(self):
        # Object with a copy() method are responsible for deep-copying themselves.
        class MyObject(object):
            def __init__(self, i):
                self.i = i

            def copy(self):
                return MyObject(graph.deepcopy(self.i))
        # Assert deep copy for different types.
        for o1 in (
          None, True, False,
          "a",
          1, 1.0, int(1), complex(1),
          list([1]), tuple([1]), set([1]), frozenset([1]),
          dict(a=1), {frozenset(["a"]): 1}, {MyObject(1): 1},
          MyObject(1)):
            o2 = graph.deepcopy(o1)
            if isinstance(o2, (list, tuple, set, dict, MyObject)):
                self.assertTrue(id(o1) != id(o2))
        print("pattern.graph.deepcopy()")

    def test_unique(self):
        # Assert list copy with unique items.
        v = graph.unique([1, 1, 1])
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], 1)
        print("pattern.graph.unique()")

    def test_coordinates(self):
        # Assert 2D coordinates.
        x, y = graph.coordinates(10, 10, 100, 30)
        self.assertAlmostEqual(x, 96.60, places=2)
        self.assertAlmostEqual(y, 60.00, places=2)
        print("pattern.graph.coordinates()")

#---------------------------------------------------------------------------------------------------


class TestNode(unittest.TestCase):

    def setUp(self):
        # Create test graph.
        self.g = graph.Graph()
        self.g.add_node("a", radius=5, stroke=(0, 0, 0, 1), strokewidth=1, fill=None, text=(0, 0, 0, 1))
        self.g.add_node("b", radius=5)
        self.g.add_node("c", radius=5)
        self.g.add_edge("a", "b")
        self.g.add_edge("b", "c")

    def test_node(self):
        # Assert node properties.
        n = self.g["a"]
        self.assertTrue(isinstance(n, graph.Node))
        self.assertTrue(n               == self.g["a"])
        self.assertTrue(n               != self.g["b"])
        self.assertTrue(n.graph         == self.g)
        self.assertTrue(n._distance     == self.g.distance)
        self.assertTrue(n.id            == "a")
        self.assertTrue(n.x             == 0.0)
        self.assertTrue(n.y             == 0.0)
        self.assertTrue(n.force.x       == graph.Vector(0.0, 0.0).x)
        self.assertTrue(n.force.y       == graph.Vector(0.0, 0.0).y)
        self.assertTrue(n.radius        == 5)
        self.assertTrue(n.fill is None)
        self.assertTrue(n.stroke        == (0, 0, 0, 1))
        self.assertTrue(n.strokewidth   == 1)
        self.assertTrue(n.text.string   == "a")
        self.assertTrue(n.text.width    == 85)
        self.assertTrue(n.text.fill     == (0, 0, 0, 1))
        self.assertTrue(n.text.fontsize == 11)
        self.assertTrue(n.fixed         == False)
        self.assertTrue(n.weight        == 0)
        self.assertTrue(n.centrality    == 0)
        print("pattern.graph.Node")

    def test_edge(self):
        # Assert node edges.
        n1 = self.g["a"]
        n2 = self.g["b"]
        self.assertTrue(n1.edges[0].node1.id == "a")
        self.assertTrue(n1.edges[0].node2.id == "b")
        self.assertTrue(n1.links[0].id == "b")
        self.assertTrue(n1.links[0] == self.g.edges[0].node2)
        self.assertTrue(n1.links.edge("b") == self.g.edges[0])
        self.assertTrue(n1.links.edge(n2) == self.g.edges[0])
        print("pattern.graph.Node.links")
        print("pattern.graph.Node.edges")

    def test_flatten(self):
        # Assert node spreading activation.
        n = self.g["a"]
        self.assertTrue(set(n.flatten(depth=0)) == set([n]))
        self.assertTrue(set(n.flatten(depth=1)) == set([n, n.links[0]]))
        self.assertTrue(set(n.flatten(depth=2)) == set(self.g.nodes))
        print("pattern.graph.Node.flatten()")

    def test_text(self):
        n = self.g.add_node("d", text=None)
        self.assertTrue(n.text is None)
        print("pattern.graph.Node.text")

#---------------------------------------------------------------------------------------------------


class TestEdge(unittest.TestCase):

    def setUp(self):
        # Create test graph.
        self.g = graph.Graph()
        self.g.add_node("a")
        self.g.add_node("b")
        self.g.add_edge("a", "b", weight=0.0, length=1.0, type="is-a", stroke=(0, 0, 0, 1), strokewidth=1)

    def test_edge(self):
        # Assert edge properties.
        e = self.g.edges[0]
        self.assertTrue(isinstance(e, graph.Edge))
        self.assertTrue(e.node1 == self.g["a"])
        self.assertTrue(e.node2 == self.g["b"])
        self.assertTrue(e.weight == 0.0)
        self.assertTrue(e.length == 1.0)
        self.assertTrue(e.type == "is-a")
        self.assertTrue(e.stroke == (0, 0, 0, 1))
        self.assertTrue(e.strokewidth == 1)
        print("pattern.graph.Edge")

#---------------------------------------------------------------------------------------------------


class TestGraph(unittest.TestCase):

    def setUp(self):
        # Create test graph.
        self.g = graph.Graph(layout=graph.SPRING, distance=10.0)
        self.g.add_node("a")
        self.g.add_node("b")
        self.g.add_node("c")
        self.g.add_edge("a", "b")
        self.g.add_edge("b", "c")

    def test_graph(self):
        # Assert graph properties.
        g = self.g.copy()
        self.assertTrue(len(g.nodes) == 3)
        self.assertTrue(len(g.edges) == 2)
        self.assertTrue(g.distance == 10.0)
        self.assertTrue(g.density == 2 / 3.0)
        self.assertTrue(g.is_complete == False)
        self.assertTrue(g.is_sparse == False)
        self.assertTrue(g.is_dense)
        self.assertTrue(g._adjacency is None)
        self.assertTrue(isinstance(g.layout, graph.GraphLayout))
        self.assertTrue(isinstance(g.layout, graph.GraphSpringLayout))
        print("pattern.graph.Graph")

    def test_graph_nodes(self):
        # Assert graph nodes.
        g = self.g.copy()
        g.append(graph.Node, "d")
        g.add_node("e", base=graph.Node, root=True)
        self.assertTrue("d" in g)
        self.assertTrue("e" in g)
        self.assertTrue(g.root == g["e"])
        self.assertTrue(g["e"] == g.node("e") == g.nodes[-1])
        g.remove(g["d"])
        g.remove(g["e"])
        self.assertTrue("d" not in g)
        self.assertTrue("e" not in g)
        print("pattern.graph.Graph.add_node()")

    def test_graph_edges(self):
        # Assert graph edges.
        g = self.g.copy()
        v1 = g.add_edge("d", "e") # Automatically create Node(d) and Node(e).
        v2 = g.add_edge("d", "e") # Yields existing edge.
        v3 = g.add_edge("e", "d") # Opposite direction.
        self.assertEqual(v1, v2)
        self.assertEqual(v2, g.edge("d", "e"))
        self.assertEqual(v3, g.edge("e", "d"))
        self.assertEqual(g["d"].links.edge(g["e"]), v2)
        self.assertEqual(g["e"].links.edge(g["d"]), v3)
        g.remove(g["d"])
        g.remove(g["e"])
        # Edges d->e and e->d should now be removed automatically.
        self.assertEqual(len(g.edges), 2)
        print("pattern.graph.Graph.add_edge()")

    def test_cache(self):
        # Assert adjacency cache is flushed when nodes, edges or direction changes.
        g = self.g.copy()
        g.eigenvector_centrality()
        self.assertEqual(g._adjacency[0]["a"], {})
        self.assertEqual(g._adjacency[0]["b"]["a"], 1.0)
        g.add_node("d")
        g.add_node("e")
        self.assertEqual(g._adjacency, None)
        g.betweenness_centrality()
        self.assertEqual(g._adjacency[0]["a"]["b"], 1.0)
        self.assertEqual(g._adjacency[0]["b"]["a"], 1.0)
        g.add_edge("d", "e", weight=0.0)
        g.remove(g.node("d"))
        g.remove(g.node("e"))
        print("pattern.graph.Graph._adjacency")

    def test_paths(self):
        # Assert node paths.
        g = self.g.copy()
        self.assertEqual(g.paths("a", "c"), g.paths(g["a"], g["c"]))
        self.assertEqual(g.paths("a", "c"), [[g["a"], g["b"], g["c"]]])
        self.assertEqual(g.paths("a", "c", length=2), [])
        # Assert node shortest paths.
        g.add_edge("a", "c")
        self.assertEqual(g.paths("a", "c", length=2), [[g["a"], g["c"]]])
        self.assertEqual(g.shortest_path("a", "c"), [g["a"], g["c"]])
        self.assertEqual(g.shortest_path("c", "a"), [g["c"], g["a"]])
        self.assertEqual(g.shortest_path("c", "a", directed=True), None)
        g.remove(g.edge("a", "c"))
        g.add_node("d")
        self.assertEqual(g.shortest_path("a", "d"), None)
        self.assertEqual(g.shortest_paths("a")["b"], [g["a"], g["b"]])
        self.assertEqual(g.shortest_paths("a")["c"], [g["a"], g["b"], g["c"]])
        self.assertEqual(g.shortest_paths("a")["d"], None)
        self.assertEqual(g.shortest_paths("c", directed=True)["a"], None)
        g.remove(g["d"])
        print("pattern.graph.Graph.paths()")
        print("pattern.graph.Graph.shortest_path()")
        print("pattern.graph.Graph.shortest_paths()")

    def test_eigenvector_centrality(self):
        # Assert eigenvector centrality.
        self.assertEqual(self.g["a"]._weight, None)
        v = self.g.eigenvector_centrality()
        self.assertTrue(isinstance(v["a"], float))
        self.assertTrue(v["a"] == v[self.g.node("a")])
        self.assertTrue(v["a"] < v["c"])
        self.assertTrue(v["b"] < v["c"])
        print("pattern.graph.Graph.eigenvector_centrality()")

    def test_betweenness_centrality(self):
        # Assert betweenness centrality.
        self.assertEqual(self.g["a"]._centrality, None)
        v = self.g.betweenness_centrality()
        self.assertTrue(isinstance(v["a"], float))
        self.assertTrue(v["a"] == v[self.g.node("a")])
        self.assertTrue(v["a"] < v["b"])
        self.assertTrue(v["c"] < v["b"])
        print("pattern.graph.Graph.betweenness_centrality()")

    def test_sorted(self):
        # Assert graph node sorting
        o1 = self.g.sorted(order=graph.WEIGHT, threshold=0.0)
        o2 = self.g.sorted(order=graph.CENTRALITY, threshold=0.0)
        self.assertEqual(o1[0], self.g["c"])
        self.assertEqual(o2[0], self.g["b"])
        print("pattern.graph.Graph.sorted()")

    def test_prune(self):
        # Assert leaf pruning.
        g = self.g.copy()
        g.prune(1)
        self.assertEqual(len(g), 1)
        self.assertEqual(g.nodes, [g["b"]])
        print("pattern.graph.Graph.prune()")

    def test_fringe(self):
        # Assert leaf fetching.
        g = self.g.copy()
        self.assertEqual(g.fringe(0), [g["a"], g["c"]])
        self.assertEqual(g.fringe(1), [g["a"], g["b"], g["c"]])
        print("pattern.graph.Graph.fringe()")

    def test_split(self):
        # Asset subgraph splitting.
        self.assertTrue(isinstance(self.g.split(), list))
        self.assertTrue(isinstance(self.g.split()[0], graph.Graph))
        print("pattern.graph.Graph.split()")

    def test_update(self):
        # Assert node position after updating layout algorithm.
        self.g.update()
        for n in self.g.nodes:
            self.assertTrue(n.x != 0)
            self.assertTrue(n.y != 0)
        self.g.layout.reset()
        for n in self.g.nodes:
            self.assertTrue(n.x == 0)
            self.assertTrue(n.y == 0)
        print("pattern.graph.Graph.update()")

    def test_copy(self):
        # Assert deep copy of Graph.
        g1 = self.g
        g2 = self.g.copy()
        self.assertTrue(set(g1) == set(g2))         # Same node id's.
        self.assertTrue(id(g1["a"]) != id(g2["b"])) # Different node objects.
        g3 = self.g.copy(nodes=[self.g["a"], self.g["b"]])
        g3 = self.g.copy(nodes=["a", "b"])
        self.assertTrue(len(g3.nodes), 2)
        self.assertTrue(len(g3.edges), 1)
        # Assert copy with subclasses of Node and Edge.

        class MyNode(graph.Node):
            pass

        class MyEdge(graph.Edge):
            pass
        g4 = graph.Graph()
        g4.append(MyNode, "a")
        g4.append(MyNode, "b")
        g4.append(MyEdge, "a", "b")
        g4 = g4.copy()
        self.assertTrue(isinstance(g4.nodes[0], MyNode))
        self.assertTrue(isinstance(g4.edges[0], MyEdge))
        print("pattern.graph.Graph.copy()")

#---------------------------------------------------------------------------------------------------


class TestGraphLayout(unittest.TestCase):

    def setUp(self):
        # Create test graph.
        self.g = graph.Graph(layout=graph.SPRING, distance=10.0)
        self.g.add_node("a")
        self.g.add_node("b")
        self.g.add_node("c")
        self.g.add_edge("a", "b")
        self.g.add_edge("b", "c")

    def test_layout(self):
        # Assert GraphLayout properties.
        gl = graph.GraphLayout(graph=self.g)
        self.assertTrue(gl.graph == self.g)
        self.assertTrue(gl.bounds == (0, 0, 0, 0))
        self.assertTrue(gl.iterations == 0)
        gl.update()
        self.assertTrue(gl.iterations == 1)
        print("pattern.graph.GraphLayout")


class TestGraphSpringLayout(TestGraphLayout):

    def test_layout(self):
        # Assert GraphSpringLayout properties.
        gl = self.g.layout
        self.assertTrue(gl.graph == self.g)
        self.assertTrue(gl.k == 4.0)
        self.assertTrue(gl.force == 0.01)
        self.assertTrue(gl.repulsion == 50)
        self.assertTrue(gl.bounds == (0, 0, 0, 0))
        self.assertTrue(gl.iterations == 0)
        gl.update()
        self.assertTrue(gl.iterations == 1)
        self.assertTrue(gl.bounds[0] < 0)
        self.assertTrue(gl.bounds[1] < 0)
        self.assertTrue(gl.bounds[2] > 0)
        self.assertTrue(gl.bounds[3] > 0)
        print("pattern.graph.GraphSpringLayout")

    def test_distance(self):
        # Assert 2D distance.
        n1 = graph.Node()
        n2 = graph.Node()
        n1.x = -100
        n2.x = +100
        d = self.g.layout._distance(n1, n2)
        self.assertEqual(d, (200.0, 0.0, 200.0, 40000.0))
        print("pattern.graph.GraphSpringLayout._distance")

    def test_repulsion(self):
        # Assert repulsive node force.
        gl = self.g.layout
        d1 = gl._distance(self.g["a"], self.g["c"])[2]
        gl.update()
        d2 = gl._distance(self.g["a"], self.g["c"])[2]
        self.assertTrue(d2 > d1)
        self.g.layout.reset()
        print("pattern.graph.GraphSpringLayout._repulse()")

    def test_attraction(self):
        # Assert attractive edge force.
        gl = self.g.layout
        self.g["a"].x = -100
        self.g["b"].y = +100
        d1 = gl._distance(self.g["a"], self.g["b"])[2]
        gl.update()
        d2 = gl._distance(self.g["a"], self.g["b"])[2]
        self.assertTrue(d2 < d1)
        print("pattern.graph.GraphSpringLayout._attract()")

#---------------------------------------------------------------------------------------------------


class TestGraphTraversal(unittest.TestCase):

    def setUp(self):
        # Create test graph.
        self.g = graph.Graph()
        self.g.add_edge("a", "b", weight=0.5)
        self.g.add_edge("a", "c")
        self.g.add_edge("b", "d")
        self.g.add_edge("d", "e")
        self.g.add_node("x")

    def test_search(self):
        # Assert depth-first vs. breadth-first search.
        def visit(node):
            a.append(node)

        def traversable(node, edge):
            if edge.node2.id == "e":
                return False
        g = self.g
        a = []
        graph.depth_first_search(g["a"], visit, traversable)
        self.assertEqual(a, [g["a"], g["b"], g["d"], g["c"]])
        a = []
        graph.breadth_first_search(g["a"], visit, traversable)
        self.assertEqual(a, [g["a"], g["b"], g["c"], g["d"]])
        print("pattern.graph.depth_first_search()")
        print("pattern.graph.breadth_first_search()")

    def test_paths(self):
        # Assert depth-first all paths.
        g = self.g.copy()
        g.add_edge("a", "d")
        for id1, id2, length, path in (
          ("a", "a", 1, [["a"]]),
          ("a", "d", 3, [["a", "d"], ["a", "b", "d"]]),
          ("a", "d", 2, [["a", "d"]]),
          ("a", "d", 1, []),
          ("a", "x", 1, [])):
            p = graph.paths(g, id1, id2, length)
            self.assertEqual(p, path)
        print("pattern.graph.paths()")

    def test_edges(self):
        # Assert path of nodes to edges.
        g = self.g
        p = [g["a"], g["b"], g["d"], g["x"]]
        e = list(graph.edges(p))
        self.assertEqual(e, [g.edge("a", "b"), g.edge("b", "d"), None])
        print("pattern.graph.edges()")

    def test_adjacency(self):
        # Assert adjacency map with different settings.
        a = [
            graph.adjacency(self.g),
            graph.adjacency(self.g, directed=True),
            graph.adjacency(self.g, directed=True, reversed=True),
            graph.adjacency(self.g, stochastic=True),
            graph.adjacency(self.g, heuristic=lambda id1, id2: 0.1),
        ]
        for i in range(len(a)):
            a[i] = sorted((id1, sorted((id2, round(w, 2)) for id2, w in p.items())) for id1, p in a[i].items())
        self.assertEqual(a[0], [
            ("a", [("b", 0.75), ("c", 1.0)]),
            ("b", [("a", 0.75), ("d", 1.0)]),
            ("c", [("a", 1.0)]),
            ("d", [("b", 1.0), ("e", 1.0)]),
            ("e", [("d", 1.0)]),
            ("x", [])])
        self.assertEqual(a[1], [
            ("a", [("b", 0.75), ("c", 1.0)]),
            ("b", [("d", 1.0)]),
            ("c", []),
            ("d", [("e", 1.0)]),
            ("e", []),
            ("x", [])])
        self.assertEqual(a[2], [
            ("a", []),
            ("b", [("a", 0.75)]),
            ("c", [("a", 1.0)]),
            ("d", [("b", 1.0)]),
            ("e", [("d", 1.0)]),
            ("x", [])])
        self.assertEqual(a[3], [
            ("a", [("b", 0.43), ("c", 0.57)]),
            ("b", [("a", 0.43), ("d", 0.57)]),
            ("c", [("a", 1.0)]),
            ("d", [("b", 0.5), ("e", 0.5)]),
            ("e", [("d", 1.0)]),
            ("x", [])])
        self.assertEqual(a[4], [
            ("a", [("b", 0.85), ("c", 1.1)]),
            ("b", [("a", 0.85), ("d", 1.1)]),
            ("c", [("a", 1.1)]),
            ("d", [("b", 1.1), ("e", 1.1)]),
            ("e", [("d", 1.1)]),
            ("x", [])])
        print("pattern.graph.adjacency()")

    def test_dijkstra_shortest_path(self):
        # Assert Dijkstra's algorithm (node1 -> node2).
        g = self.g.copy()
        g.add_edge("d", "a")
        for id1, id2, heuristic, directed, path in (
          ("a", "d", None, False, ["a", "d"]),
          ("a", "d", None, True, ["a", "b", "d"]),
          ("a", "d", lambda id1, id2: id1 == "d" and id2 == "a" and 1 or 0, False, ["a", "b", "d"])):
            p = graph.dijkstra_shortest_path(g, id1, id2, heuristic, directed)
            self.assertEqual(p, path)
        print("pattern.graph.dijkstra_shortest_path()")

    def test_dijkstra_shortest_paths(self):
        # Assert Dijkstra's algorithm (node1 -> all).
        g = self.g.copy()
        g.add_edge("d", "a")
        a = [
            graph.dijkstra_shortest_paths(g, "a"),
            graph.dijkstra_shortest_paths(g, "a", directed=True),
            graph.dijkstra_shortest_paths(g, "a", heuristic=lambda id1, id2: id1 == "d" and id2 == "a" and 1 or 0)
        ]
        for i in range(len(a)):
            a[i] = sorted(a[i].items())
        self.assertEqual(a[0], [
            ("a", ["a"]),
            ("b", ["a", "b"]),
            ("c", ["a", "c"]),
            ("d", ["a", "d"]),
            ("e", ["a", "d", "e"]),
            ("x", None)])
        self.assertEqual(a[1], [
            ("a", ["a"]),
            ("b", ["a", "b"]),
            ("c", ["a", "c"]),
            ("d", ["a", "b", "d"]),
            ("e", ["a", "b", "d", "e"]),
            ("x", None)])
        self.assertEqual(a[2], [
            ("a", ["a"]),
            ("b", ["a", "b"]),
            ("c", ["a", "c"]),
            ("d", ["a", "b", "d"]),
            ("e", ["a", "b", "d", "e"]),
            ("x", None)])
        print("pattern.graph.dijkstra_shortest_paths()")

    def test_floyd_warshall_all_pairs_distance(self):
        # Assert all pairs path distance.
        p1 = graph.floyd_warshall_all_pairs_distance(self.g)
        p2 = sorted((id1, sorted((id2, round(w, 2)) for id2, w in p.items())) for id1, p in p1.items())
        self.assertEqual(p2, [
            ("a", [("a", 0.00), ("b", 0.75), ("c", 1.00), ("d", 1.75), ("e", 2.75)]),
            ("b", [("a", 0.75), ("b", 0.00), ("c", 1.75), ("d", 1.00), ("e", 2.00)]),
            ("c", [("a", 1.00), ("b", 1.75), ("c", 2.00), ("d", 2.75), ("e", 3.75)]),
            ("d", [("a", 1.75), ("b", 1.00), ("c", 2.75), ("d", 0.00), ("e", 1.00)]),
            ("e", [("a", 2.75), ("b", 2.00), ("c", 3.75), ("d", 1.00), ("e", 2.00)]),
            ("x", [])])
        # Assert predecessor tree.
        self.assertEqual(graph.predecessor_path(p1.predecessors, "a", "d"), ["a", "b", "d"])
        print("pattern.graph.floyd_warshall_all_pairs_distance()")

#---------------------------------------------------------------------------------------------------


class TestGraphPartitioning(unittest.TestCase):

    def setUp(self):
        # Create test graph.
        self.g = graph.Graph()
        self.g.add_edge("a", "b", weight=0.5)
        self.g.add_edge("a", "c")
        self.g.add_edge("b", "d")
        self.g.add_edge("d", "e")
        self.g.add_edge("x", "y")
        self.g.add_node("z")

    def test_union(self):
        self.assertEqual(graph.union([1, 2], [2, 3]), [1, 2, 3])

    def test_intersection(self):
        self.assertEqual(graph.intersection([1, 2], [2, 3]), [2])

    def test_difference(self):
        self.assertEqual(graph.difference([1, 2], [2, 3]), [1])

    def test_partition(self):
        # Assert unconnected subgraph partitioning.
        g = graph.partition(self.g)
        self.assertTrue(len(g) == 3)
        self.assertTrue(isinstance(g[0], graph.Graph))
        self.assertTrue(sorted(g[0].keys()), ["a", "b", "c", "d", "e"])
        self.assertTrue(sorted(g[1].keys()), ["x", "y"])
        self.assertTrue(sorted(g[2].keys()), ["z"])
        print("pattern.graph.partition()")

    def test_clique(self):
        # Assert node cliques.
        v = graph.clique(self.g, "a")
        self.assertEqual(v, ["a", "b"])
        self.g.add_edge("b", "c")
        v = graph.clique(self.g, "a")
        self.assertEqual(v, ["a", "b", "c"])
        v = graph.cliques(self.g, 2)
        self.assertEqual(v, [["a", "b", "c"], ["b", "d"], ["d", "e"], ["x", "y"]])
        print("pattern.graph.clique()")
        print("pattern.graph.cliques()")

#---------------------------------------------------------------------------------------------------


class TestGraphMaintenance(unittest.TestCase):

    def setUp(self):
        pass

    def test_unlink(self):
        # Assert remove all edges to/from Node(a).
        g = graph.Graph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        graph.unlink(g, g["a"])
        self.assertTrue(len(g.edges) == 0)
        # Assert remove edges between Node(a) and Node(b)
        g = graph.Graph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        graph.unlink(g, g["a"], "b")
        self.assertTrue(len(g.edges) == 1)
        print("pattern.graph.unlink()")

    def test_redirect(self):
        # Assert transfer connections of Node(a) to Node(d).
        g = graph.Graph()
        g.add_edge("a", "b")
        g.add_edge("c", "a")
        g.add_node("d")
        graph.redirect(g, g["a"], "d")
        self.assertTrue(len(g["a"].edges) == 0)
        self.assertTrue(len(g["d"].edges) == 2)
        self.assertTrue(g.edge("d", "c").node1 == g["c"])
        print("pattern.graph.redirect()")

    def test_cut(self):
        # Assert unlink Node(b) and redirect a->c and a->d.
        g = graph.Graph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("b", "d")
        graph.cut(g, g["b"])
        self.assertTrue(len(g["b"].edges) == 0)
        self.assertTrue(g.edge("a", "c") is not None)
        self.assertTrue(g.edge("a", "d") is not None)
        print("pattern.graph.cut()")

    def test_insert(self):
        g = graph.Graph()
        g.add_edge("a", "b")
        g.add_node("c")
        graph.insert(g, g["c"], g["a"], g["b"])
        self.assertTrue(g.edge("a", "b") is None)
        self.assertTrue(g.edge("a", "c") is not None)
        self.assertTrue(g.edge("c", "b") is not None)
        print("pattern.graph.insert()")

#---------------------------------------------------------------------------------------------------


class TestGraphCommonsense(unittest.TestCase):

    def setUp(self):
        pass

    def test_halo(self):
        # Assert concept halo (e.g., latent related concepts).
        g = commonsense.Commonsense()
        v = [concept.id for concept in g["rose"].halo]
        self.assertTrue("red" in v)
        self.assertTrue("romance" in v)
        # Concept.properties is the list of properties (adjectives) in the halo.
        v = g["rose"].properties
        self.assertTrue("red" in v)
        self.assertTrue("romance" not in v)
        print("pattern.graph.commonsense.Concept.halo")
        print("pattern.graph.commonsense.Concept.properties")

    def test_field(self):
        # Assert semantic field (e.g., concept taxonomy).
        g = commonsense.Commonsense()
        v = [concept.id for concept in g.field("color")]
        self.assertTrue("red" in v)
        self.assertTrue("green" in v)
        self.assertTrue("blue" in v)
        print("pattern.graph.commonsense.Commonsense.field()")

    def test_similarity(self):
        # Assert that tiger is more similar to lion than to spoon
        # (which is common sense).
        g = commonsense.Commonsense()
        w1 = g.similarity("tiger", "lion")
        w2 = g.similarity("tiger", "spoon")
        self.assertTrue(w1 > w2)
        print("pattern.graph.commonsense.Commonsense.similarity()")

#---------------------------------------------------------------------------------------------------


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestNode))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEdge))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGraph))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGraphLayout))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGraphSpringLayout))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGraphTraversal))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGraphPartitioning))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGraphMaintenance))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGraphCommonsense))
    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
