import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest
import time
import re

from pattern    import search
from pattern.en import Sentence, parse

#-----------------------------------------------------------------------------------------------------

class TestUtilityFunctions(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_combinations(self):
        self.assertEqual(list(search.combinations([ ], 2)), [])   # No possibilities.
        self.assertEqual(list(search.combinations([1], 0)), [[]]) # One possibility: the empty list.
        self.assertEqual(list(search.combinations([1,2,3], 2)), 
            [[1,1], [1,2], [1,3], [2,1], [2,2], [2,3], [3,1], [3,2], [3,3]])
        for n, m in ((1,9), (2,81), (3,729), (4,6561)):
            v = search.combinations([1,2,3,4,5,6,7,8,9], n)
            self.assertEqual(len(list(v)), m)
        print "pattern.search.combinations()"
            
    def test_variations(self):
        # Assert Variations include the original input (the empty list has one variation = itself).
        v = search.variations([])
        self.assertEqual(v, [[]])
        # Assert variations = [1] and [].
        v = search.variations([1], optional=lambda item: item == 1)
        self.assertEqual(v, [[1], []])
        # Assert variations = the original input, [1], [2] and [].
        v = search.variations([1,2], optional=lambda item: item in (1,2))
        self.assertEqual(v, [[1,2], [2], [1], []])
        # Assert variations are sorted longest-first.
        v = search.variations([1,2,3,4], optional=lambda item: item in (1,2))
        self.assertEqual(v, [[1,2,3,4], [2,3,4], [1,3,4], [3,4]])
        self.assertTrue(len(v[0]) >= len(v[1]) >= len(v[2]), len(v[3]))
        print "pattern.search.variations()"

#-----------------------------------------------------------------------------------------------------

class TestConstraint(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def _test_constraint(self, constraint, **kwargs):
        # Assert Constraint property values with given optional parameters.
        self.assertEqual(constraint.words,    kwargs.get("words",    []))
        self.assertEqual(constraint.tags,     kwargs.get("tags",     []))
        self.assertEqual(constraint.chunks,   kwargs.get("chunks",   []))
        self.assertEqual(constraint.roles,    kwargs.get("roles",    []))
        self.assertEqual(constraint.taxa,     kwargs.get("taxa",     []))
        self.assertEqual(constraint.optional, kwargs.get("optional", False))
        self.assertEqual(constraint.multiple, kwargs.get("multiple", False))
        self.assertEqual(constraint.first,    kwargs.get("first",    False))
        self.assertEqual(constraint.exclude,  kwargs.get("exclude",  None))
        self.assertEqual(constraint.taxonomy, kwargs.get("taxonomy", search.taxonomy))
    
    def test_fromstring(self):
        # Assert Constraint string syntax.
        for s, kwargs in (
          (        "cats", dict( words = ["cats"])),
          (        "Cat*", dict( words = ["cat*"])),
          (   "\\[cat\\]", dict( words = ["[cat]"])),
          ("[black cats]", dict( words = ["black cats"])),
          (  "black_cats", dict( words = ["black cats"])),
          ("black\\_cats", dict( words = ["black_cats"])),
          (         "NNS", dict(  tags = ["NNS"])),
          (     "NN*|VB*", dict(  tags = ["NN*", "VB*"])),
          (          "NP", dict(chunks = ["NP"])),
          (         "SBJ", dict( roles = ["SBJ"])),
          (        "CATS", dict(  taxa = ["cats"])),
          (      "(cats)", dict( words = ["cats"], optional=True)),
          (  "\\(cats\\)", dict( words = ["(cats)"])),
          (       "cats+", dict( words = ["cats"], multiple=True)),
          (     "cats\\+", dict( words = ["cats+"])),
          (   "cats+dogs", dict( words = ["cats+dogs"])),
          (     "(cats+)", dict( words = ["cats+"], optional=True)),
          ( "cats\\|dogs", dict( words = ["cats|dogs"])),
          (   "cats|dogs", dict( words = ["cats", "dogs"])),
          (        "^cat", dict( words = ["cat"], first=True)),
          (      "\\^cat", dict( words = ["^cat"])),
          (     "(cat*)+", dict( words = ["cat*"], optional=True, multiple=True)),
          ( "^black_cat+", dict( words = ["black cat"], multiple=True, first=True)),
          (    "cats|NN*", dict( words = ["cats"], tags=["NN*"]))):
            self._test_constraint(search.Constraint.fromstring(s), **kwargs)
        # Assert non-alpha taxonomy items.
        t = search.Taxonomy()
        t.append("0.5", type="0.5")
        t.append("half", type="0.5")
        v = search.Constraint.fromstring("0.5", taxonomy=t)
        # Assert non-alpha words without taxonomy.
        self.assertTrue(v.taxa == ["0.5"])
        v = search.Constraint.fromstring("0.5")
        # Assert exclude Constraint.
        self.assertTrue(v.words == ["0.5"])
        v = search.Constraint.fromstring("\\!cats|!dogs|!fish")
        self.assertTrue(v.words == ["!cats"])
        self.assertTrue(v.exclude.words == ["dogs", "fish"])
        print "pattern.search.Constraint.fromstring"
        print "pattern.search.Constraint.fromstring"
        
    def test_match(self):
        # Assert Constraint-Word matching.
        R = search.Constraint.fromstring
        S = lambda s: Sentence(parse(s, relations=True, lemmata=True))
        W = lambda s, tag=None, index=0: search.Word(None, s, tag, index)
        for constraint, tests in (
          (R("cat|dog"),  [(W("cat"), 1), (W("dog"), 1), (W("fish"), 0)]),
          (R("cat*"),     [(W("cats"), 1)]),
          (R("*cat"),     [(W("tomcat"), 1)]),
          (R("c*t|d*g"),  [(W("cat"), 1), (W("cut"), 1), (W("dog"), 1), (W("dig"), 1)]),
          (R("cats|NN*"), [(W("cats", "NNS"), 1), (W("cats"), 0)]),
          (R("^cat"),     [(W("cat", "NN", index=0), 1),(W("cat", "NN", index=1), 0)]),
          (R("*|!cat"),   [(W("cat"), 0), (W("dog"), 1), (W("fish"), 1)]),
          (R("my cat"),   [(W("cat"), 0)]),
          (R("my cat"),   [(S("my cat").words[1], 1)]),  # "my cat" is an overspecification of "cat"
          (R("my_cat"),   [(S("my cat").words[1], 1)]),
          (R("cat|NP"),   [(S("my cat").words[1], 1)]),
          (R("dog|VP"),   [(S("my dog").words[1], 0)]),
          (R("cat|SBJ"),  [(S("the cat is sleeping").words[1], 1)]),
          (R("dog"),      [(S("MY DOGS").words[1], 1)]), # lemma matches
          (R("dog"),      [(S("MY DOG").words[1], 1)])): # case-insensitive
            for test, b in tests:
                self.assertEqual(constraint.match(test), bool(b))
        # Assert Constraint-Taxa matching.
        t = search.Taxonomy()
        t.append("Tweety", type="bird")
        t.append("Steven", type="bird")
        v = search.Constraint.fromstring("BIRD", taxonomy=t)
        self.assertTrue(v.match(W("bird")))
        self.assertTrue(v.match(S("tweeties")[0]))
        self.assertTrue(v.match(W("Steven")))
        print "pattern.search.Constraint.match()"

#-----------------------------------------------------------------------------------------------------

class TestPattern(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_pattern(self):
        # Assert Pattern properties.
        v = search.Pattern([
            search.Constraint("a|an|the"),
            search.Constraint("JJ*"),
            search.Constraint("cat")], search.STRICT)
        self.assertEqual(len(v), 3)
        self.assertEqual(v.strict, True)
        print "pattern.search.Pattern"
        
    def test_fromstring(self):
        # Assert Pattern string syntax.
        v = search.Pattern.fromstring("a|an|the (JJ*) cat*")
        self.assertEqual(v[0].words,    ["a", "an", "the"])
        self.assertEqual(v[1].tags,     ["JJ*"])
        self.assertEqual(v[1].optional, True)
        self.assertEqual(v[2].words,    ["cat*"])
        # Assert escaped control characters.
        v = search.Pattern.fromstring("[\\[Figure 1\\]] VP")
        self.assertEqual(v[0].words,    ["[figure 1]"])
        self.assertEqual(v[1].chunks,   ["VP"])
        # Assert messy syntax (fix brackets and whitespace, don't fix empty options).
        v = search.Pattern.fromstring("[avoid][|!|messy  |syntax |]")
        self.assertEqual(v[0].words,    ["avoid"])
        self.assertEqual(v[1].words,    ["", "messy", "syntax", ""])
        self.assertEqual(v[1].exclude.words, [""]) # "!" = exclude everything
        print "pattern.search.Pattern.fromstring()"
        
    def test_match(self):
        # Assert Pattern.match()
        P = search.Pattern.fromstring
        X = search.STRICT
        S = lambda s: Sentence(parse(s, relations=True, lemmata=True))
        for i, (pattern, test, match) in enumerate((
          (P("^rabbit"),                  "white rabbit",     None),                  #  0
          (P("^rabbit"),                        "rabbit",     "rabbit"),              #  1
          (P("rabbit"),               "big white rabbit",     "rabbit"),              #  2
          (P("rabbit*"),              "big white rabbits",    "rabbits"),             #  3
          (P("JJ|NN"),              S("big white rabbits"),   "big"),                 #  4
          (P("JJ+"),                S("big white rabbits"),   "big white"),           #  5
          (P("JJ+ NN*"),            S("big white rabbits"),   "big white rabbits"),   #  6
          (P("JJ black|white NN*"), S("big white rabbits"),   "big white rabbits"),   #  7
          (P("NP"),                 S("big white rabbit"),    "big white rabbit"),    #  8
          (P("(big) rabbit", X),    S("big white rabbit"),    "rabbit"),              #  9 strict
          (P("(big) rabbit|NN"),    S("big white rabbit"),    "rabbit"),              # 10 explicit
          (P("(big) rabbit"),       S("big white rabbit"),    "big white rabbit"),    # 11 greedy
          (P("rabbit VP JJ"),       S("the rabbit was huge"), "the rabbit was huge"), # 12
          (P("rabbit be JJ"),       S("the rabbit was huge"), "the rabbit was huge"), # 13 lemma
          (P("rabbit be JJ", X),    S("the rabbit was huge"), "rabbit was huge"),     # 14
          (P("rabbit is JJ"),       S("the rabbit was huge"), None),                  # 15
          (P("the NP"),             S("the rabid rodents"),   "the rabid rodents"),   # 16 overlap
          (P("t*|r*+"),             S("the rabid rodents"),   "the rabid rodents"),   # 17
          (P("(DT) (JJ) NN*"),      S("the rabid rodents"),   "the rabid rodents"),   # 18
          (P("(DT) (JJ) NN*"),      S("the rabbit"),          "the rabbit"),          # 19
          (P("rabbit"),             S("the big rabbit"),      "the big rabbit"),      # 20 greedy
          (P("eat carrot"),         S("is eating a carrot"),  "is eating a carrot"),  # 21
          (P("eat carrot|NP"),      S("is eating a carrot"),  "is eating a carrot"),  # 22
          (P("eat NP"),             S("is eating a carrot"),  "is eating a carrot"),  # 23
          (P("eat a"),              S("is eating a carrot"),  "is eating a"),         # 24
          (P("!NP carrot"),         S("is eating a carrot"),  "is eating a carrot"),  # 25
          (P("eat !pizza"),         S("is eating a carrot"),  "is eating a carrot"),  # 26
          (P("eating a"),           S("is eating a carrot"),  "is eating a"),         # 27
          (P("eating !carrot", X),  S("is eating a carrot"),  "eating a"),            # 28
          (P("eat !carrot"),        S("is eating a carrot"),  None),                  # 28 NP chunk is a carrot
          (P("eat !DT"),            S("is eating a carrot"),  None),                  # 30 eat followed by DT
          (P("eat !NN"),            S("is eating a carrot"),  "is eating a"),         # 31 a/DT is not NN
          (P("!be carrot"),         S("is eating a carrot"),  "is eating a carrot"),  # 32 is eating == eat != is
          (P("!eat|VP carrot"),     S("is eating a carrot"),  None),                  # 33 VP chunk == eat
          (P("white_rabbit"),       S("big white rabbit"),    None),                  # 34
          (P("[white rabbit]"),     S("big white rabbit"),    None),                  # 35
          (P("[* white rabbit]"),   S("big white rabbit"),    "big white rabbit"),    # 36
          (P("[big * rabbit]"),     S("big white rabbit"),    "big white rabbit"),    # 37
          (P("big [big * rabbit]"), S("big white rabbit"),    "big white rabbit"),    # 38
          (P("[*+ rabbit]"),        S("big white rabbit"),    None),                  # 39 bad pattern: "+" is literal
        )):
            m = pattern.match(test)
            #print i, match, "<=>", m and m.string or None
            self.assertTrue(getattr(m, "string", None) == match)
        # Assert chunk with head at the front.
        s = S("Felix the cat")
        s.chunks[0].head = s.chunks[0][0] # head = "Felix"
        self.assertEqual(P("felix").match(s).string, "Felix the cat")
        # Assert negation + custom greedy() function.
        s = S("the big white rabbit")
        g = lambda chunk, constraint: len([w for w in chunk if not constraint.match(w)]) == 0
        self.assertEqual(P("!white").match(s).string, "the big white rabbit") # a rabbit != white
        self.assertEqual(P("!white", greedy=g).match(s), None)                # a white rabbit == white
        # Assert regular expressions.
        s = S("a sack with 3.5 rabbits")
        p = search.Pattern.fromstring("[] NNS")
        p[0].words.append(re.compile(r"[0-9|\.]+"))
        self.assertEqual(p.match(s).string, "3.5 rabbits")
        print "pattern.search.Pattern.match()"
        
    def test_search(self):
        # Assert one match containing all words.
        v = search.Pattern.fromstring("*+")
        v = v.search("one two three")
        self.assertEqual(v[0].string, "one two three")
        # Assert one match for each word.
        v = search.Pattern.fromstring("*")
        v = v.search("one two three")
        self.assertEqual(v[0].string, "one")
        self.assertEqual(v[1].string, "two")
        self.assertEqual(v[2].string, "three")
        # Assert all variations are matched.
        v = search.Pattern.fromstring("(DT) (JJ)+ NN*")
        v = v.search(Sentence(parse("dogs, black cats and a big white rabbit")))
        self.assertEqual(v[0].string, "dogs")
        self.assertEqual(v[1].string, "black cats")
        self.assertEqual(v[2].string, "a big white rabbit")
        print "pattern.search.Pattern.search()"

#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConstraint))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPattern))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())