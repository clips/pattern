# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest

from pattern import graph

#-----------------------------------------------------------------------------------------------------

class TestNode(unittest.TestCase):
    
    def setUp(self):
        # Create test graph.
        self.g = graph.Graph()
        self.g.add_node("a", radius=5, stroke=(0,0,0,1), strokewidth=1, fill=None, text=(0,0,0,1))
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
        self.assertTrue(n.fill          == None)
        self.assertTrue(n.stroke        == (0,0,0,1))
        self.assertTrue(n.strokewidth   == 1)
        self.assertTrue(n.text.string   == u"a")
        self.assertTrue(n.text.width    == 85)
        self.assertTrue(n.text.fill     == (0,0,0,1))
        self.assertTrue(n.text.fontsize == 11)
        self.assertTrue(n.fixed         == False)
        self.assertTrue(n.weight        == 0)
        self.assertTrue(n.centrality    == 0)
        print "pattern.graph.Node"
        
    def test_edge(self):
        # Assert node edges.
        n1 = self.g["a"]
        n2 = self.g["b"]
        self.assertTrue(n1.edges[0].node1.id == "a")
        self.assertTrue(n1.edges[0].node2.id == "b")
        self.assertTrue(n1.links[0].id       == "b")
        self.assertTrue(n1.links[0]          == self.g.edges[0].node2)
        self.assertTrue(n1.links.edge("b")   == self.g.edges[0])
        self.assertTrue(n1.links.edge(n2)    == self.g.edges[0])
        print "pattern.graph.Node.links"
        print "pattern.graph.Node.edges"
        
    def test_flatten(self):
        # Assert node spreading activation.
        n = self.g["a"]
        self.assertTrue(set(n.flatten(depth=0)) == set([n]))
        self.assertTrue(set(n.flatten(depth=1)) == set([n, n.links[0]]))
        self.assertTrue(set(n.flatten(depth=2)) == set(self.g.nodes))
        print "pattern.graph.Node.flatten()"
        
    def test_text(self):
        n = self.g.add_node("d", text=None)
        self.assertTrue(n.text == None)
        print "pattern.graph.Node.text"

#-----------------------------------------------------------------------------------------------------

class TestEdge(unittest.TestCase):
    
    def setUp(self):
        # Create test graph.
        self.g = graph.Graph()
        self.g.add_node("a")
        self.g.add_node("b")
        self.g.add_edge("a", "b", weight=0.0, length=1.0, type="is-a", stroke=(0,0,0,1), strokewidth=1)
        
    def test_edge(self):
        # Assert edge properties.
        e = self.g.edges[0]
        self.assertTrue(isinstance(e, graph.Edge))
        self.assertTrue(e.node1       == self.g["a"])
        self.assertTrue(e.node2       == self.g["b"])
        self.assertTrue(e.weight      == 0.0)
        self.assertTrue(e.length      == 1.0)
        self.assertTrue(e.type        == "is-a")
        self.assertTrue(e.stroke      == (0,0,0,1))
        self.assertTrue(e.strokewidth == 1)
        print "pattern.graph.Edge"

#-----------------------------------------------------------------------------------------------------

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
        self.assertTrue(len(g.nodes)  == 3)
        self.assertTrue(len(g.edges)  == 2)
        self.assertTrue(g.distance    == 10.0)
        self.assertTrue(g.density     == 2 / 3.0)
        self.assertTrue(g.is_complete == False)
        self.assertTrue(g.is_sparse   == False)
        self.assertTrue(g.is_dense    == True)
        self.assertTrue(g._adjacency  == None)
        self.assertTrue(isinstance(g.layout, graph.GraphLayout))
        self.assertTrue(isinstance(g.layout, graph.GraphSpringLayout))
        print "pattern.graph.Graph"
        
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
        print "pattern.graph.Graph.add_node()"
        
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
        print "pattern.graph.Graph.add_edge()"
        
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
        print "pattern.graph.Graph._adjacency"
        
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
        print "pattern.graph.Graph.paths()"
        print "pattern.graph.Graph.shortest_path()"
        print "pattern.graph.Graph.shortest_paths()"
        
    def test_prune(self):
        # Assert leaf pruning.
        g = self.g.copy()
        g.prune(1)
        self.assertEqual(len(g), 1)
        self.assertEqual(g.nodes, [g["b"]])
        print "pattern.graph.Graph.prune()"
        
    def test_fringe(self):
        # Assert leaf fetching.
        g = self.g.copy()
        self.assertEqual(g.fringe(0), [g["a"], g["c"]])
        self.assertEqual(g.fringe(1), [g["a"], g["b"], g["c"]])
        print "pattern.graph.Graph.fringe()"
        
    def test_copy(self):
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
        print "pattern.graph.Graph.copy()"

#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestNode))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEdge))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGraph))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
