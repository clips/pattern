from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
import time
import re
import random

from pattern import search
from pattern.en import Sentence, parse

#---------------------------------------------------------------------------------------------------


class TestUtilityFunctions(unittest.TestCase):

    def setUp(self):
        pass

    def test_match(self):
        # Assert search._match() wildcard matching.
        for s, p, b in (
          ("rabbit" , "rabbit", True),
          ("rabbits", "rabbit*", True),
          ("rabbits", "*abbits", True),
          ("rabbits", "*abbit*", True),
          ("rabbits", "rab*its", True),
          ("rabbits", re.compile(r"ra.*?"), True)):
            self.assertEqual(search._match(s, p), b)
        print("pattern.search._match()")

    def test_unique(self):
        self.assertEqual(search.unique([1, 1, 2, 2]), [1, 2])

    def test_find(self):
        self.assertEqual(search.find(lambda v: v > 2, [1, 2, 3, 4, 5]), 3)

    def test_product(self):
        # Assert combinations of list items.
        self.assertEqual(list(search.product([], repeat=2)), [])   # No possibilities.
        self.assertEqual(list(search.product([1], repeat=0)), [()]) # One possibility: the empty set.
        self.assertEqual(list(search.product([1, 2, 3], repeat=2)),
            [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)])
        for n, m in ((1, 9), (2, 81), (3, 729), (4, 6561)):
            v = search.product([1, 2, 3, 4, 5, 6, 7, 8, 9], repeat=n)
            self.assertEqual(len(list(v)), m)
        print("pattern.search.product()")

    def test_variations(self):
        # Assert variations include the original input (the empty list has one variation = itself).
        v = search.variations([])
        self.assertEqual(v, [()])
        # Assert variations = (1,) and ().
        v = search.variations([1], optional=lambda item: item == 1)
        self.assertEqual(v, [(1,), ()])
        # Assert variations = the original input, (2,), (1,) and ().
        v = search.variations([1, 2], optional=lambda item: item in (1, 2))
        self.assertEqual(v, [(1, 2), (2,), (1,), ()])
        # Assert variations are sorted longest-first.
        v = search.variations([1, 2, 3, 4], optional=lambda item: item in (1, 2))
        self.assertEqual(v, [(1, 2, 3, 4), (2, 3, 4), (1, 3, 4), (3, 4)])
        self.assertTrue(len(v[0]) >= len(v[1]) >= len(v[2]), len(v[3]))
        print("pattern.search.variations()")

    def test_odict(self):
        # Assert odict.append() which must be order-preserving.
        v = search.odict()
        v.push(("a", 1))
        v.push(("b", 2))
        v.push(("c", 3))
        v.push(("a", 0))
        v = v.copy()
        self.assertTrue(isinstance(v, dict))
        self.assertEqual(v.keys(), ["a", "c", "b"])
        print("pattern.search.odict()")

#---------------------------------------------------------------------------------------------------


class TestTaxonomy(unittest.TestCase):

    def setUp(self):
        pass

    def test_taxonomy(self):
        # Assert Taxonomy search.
        t = search.Taxonomy()
        t.append("King Arthur", type="knight", value=1)
        t.append("Sir Bedevere", type="knight", value=2)
        t.append("Sir Lancelot", type="knight", value=3)
        t.append("Sir Gallahad", type="knight", value=4)
        t.append("Sir Robin", type="knight", value=5)
        t.append("John Cleese", type="Sir Lancelot")
        t.append("John Cleese", type="Basil Fawlty")
        # Matching is case-insensitive, results are lowercase.
        self.assertTrue("John Cleese" in t)
        self.assertTrue("john cleese" in t)
        self.assertEqual(t.classify("King Arthur"), "knight")
        self.assertEqual(t.value("King Arthur"), 1)
        self.assertEqual(t.parents("John Cleese"), ["basil fawlty", "sir lancelot"])
        self.assertEqual(t.parents("John Cleese", recursive=True), [
            "basil fawlty",
            "sir lancelot",
            "knight"])
        self.assertEqual(t.children("knight"), [
            "sir robin",
            "sir gallahad",
            "sir lancelot",
            "sir bedevere",
            "king arthur"])
        self.assertEqual(t.children("knight", recursive=True), [
            "sir robin",
            "sir gallahad",
            "sir lancelot",
            "sir bedevere",
            "king arthur",
            "john cleese"])
        print("pattern.search.Taxonomy")

    def test_classifier(self):
        # Assert taxonomy classifier + keyword arguments.
        c1 = search.Classifier(parents=lambda word, chunk=None: word.endswith("ness") and ["quality"] or [])
        c2 = search.Classifier(parents=lambda word, chunk=None: chunk == "VP" and ["action"] or [])
        t = search.Taxonomy()
        t.classifiers.append(c1)
        t.classifiers.append(c2)
        self.assertEqual(t.classify("fuzziness"), "quality")
        self.assertEqual(t.classify("run", chunk="VP"), "action")
        print("pattern.search.Classifier")

    def test_wordnet_classifier(self):
        # Assert WordNet classifier parents & children.
        c = search.WordNetClassifier()
        t = search.Taxonomy()
        t.classifiers.append(c)
        self.assertEqual(t.classify("cat"), "feline")
        self.assertEqual(t.classify("dog"), "canine")
        self.assertTrue("domestic_cat" in t.children("cat"))
        self.assertTrue("puppy" in t.children("dog"))
        print("pattern.search.WordNetClassifier")

#---------------------------------------------------------------------------------------------------


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
          (       "cats?", dict( words = ["cats"], optional=True)),
          (      "(cats)", dict( words = ["cats"], optional=True)),
          (  "\\(cats\\)", dict( words = ["(cats)"])),
          (       "cats+", dict( words = ["cats"], multiple=True)),
          (     "cats\\+", dict( words = ["cats+"])),
          (   "cats+dogs", dict( words = ["cats+dogs"])),
          (     "(cats+)", dict( words = ["cats"], optional=True, multiple=True)),
          (     "(cats)+", dict( words = ["cats"], optional=True, multiple=True)),
          (      "cats+?", dict( words = ["cats"], optional=True, multiple=True)),
          (      "cats?+", dict( words = ["cats"], optional=True, multiple=True)),
          ( "^[fat cat]?", dict( words = ["fat cat"], first=True, optional=True)),
          ( "[^fat cat?]", dict( words = ["fat cat"], first=True, optional=True)),
          ( "cats\\|dogs", dict( words = ["cats|dogs"])),
          (   "cats|dogs", dict( words = ["cats", "dogs"])),
          (        "^cat", dict( words = ["cat"], first=True)),
          (      "\\^cat", dict( words = ["^cat"])),
          (     "(cat*)+", dict( words = ["cat*"], optional=True, multiple=True)),
          ( "^black_cat+", dict( words = ["black cat"], multiple=True, first=True)),
          (  "black\[cat", dict( words = ["black[cat"])),
          (  "black\(cat", dict( words = ["black(cat"])),
          (  "black\{cat", dict( words = ["black{cat"])),
          (  "black\|cat", dict( words = ["black|cat"])),
          (  "black\!cat", dict( words = ["black!cat"])),
          (  "black\^cat", dict( words = ["black^cat"])),
          (  "black\+cat", dict( words = ["black+cat"])),
          (  "black\?cat", dict( words = ["black?cat"])),
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
        print("pattern.search.Constraint.fromstring")
        print("pattern.search.Constraint.fromstring")

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
          (R("^cat"),     [(W("cat", "NN", index=0), 1), (W("cat", "NN", index=1), 0)]),
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
        print("pattern.search.Constraint.match()")

    def test_string(self):
        # Assert Constraint.string.
        v = search.Constraint()
        v.words = ["Steven\\*"]
        v.tags = ["NN*"]
        v.roles = ["SBJ"]
        v.taxa = ["(associate) professor"]
        v.exclude = search.Constraint(["bird"])
        v.multiple = True
        v.first = True
        self.assertEqual(v.string, "^[Steven\\*|NN*|SBJ|\(ASSOCIATE\)_PROFESSOR|!bird]+")
        print("pattern.search.Constraint.string")

#---------------------------------------------------------------------------------------------------


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
        print("pattern.search.Pattern")

    def test_fromstring(self):
        # Assert Pattern string syntax.
        v = search.Pattern.fromstring("a|an|the JJ*? cat*")
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
        print("pattern.search.Pattern.fromstring()")

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
          (P("big? rabbit", X),     S("big white rabbit"),    "rabbit"),              #  9 strict
          (P("big? rabbit|NN"),     S("big white rabbit"),    "rabbit"),              # 10 explicit
          (P("big? rabbit"),        S("big white rabbit"),    "big white rabbit"),    # 11 greedy
          (P("rabbit VP JJ"),       S("the rabbit was huge"), "the rabbit was huge"), # 12
          (P("rabbit be JJ"),       S("the rabbit was huge"), "the rabbit was huge"), # 13 lemma
          (P("rabbit be JJ", X),    S("the rabbit was huge"), "rabbit was huge"),     # 14
          (P("rabbit is JJ"),       S("the rabbit was huge"), None),                  # 15
          (P("the NP"),             S("the rabid rodents"),   "the rabid rodents"),   # 16 overlap
          (P("t*|r*+"),             S("the rabid rodents"),   "the rabid rodents"),   # 17
          (P("(DT) JJ? NN*"),       S("the rabid rodents"),   "the rabid rodents"),   # 18
          (P("(DT) JJ? NN*"),       S("the rabbit"),          "the rabbit"),          # 19
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
            self.assertTrue(getattr(m, "string", None) == match)
        # Assert chunk with head at the front.
        s = S("Felix the cat")
        self.assertEqual(P("felix").match(s).string, "Felix the cat")
        # Assert negation + custom greedy() function.
        s = S("the big white rabbit")
        g = lambda chunk, constraint: len([w for w in chunk if not constraint.match(w)]) == 0
        self.assertEqual(P("!white").match(s).string, "the big white rabbit") # a rabbit != white
        self.assertEqual(P("!white", greedy=g).match(s), None)                # a white rabbit == white
        # Assert taxonomy items with spaces.
        s = S("Bugs Bunny is a giant talking rabbit.")
        t = search.Taxonomy()
        t.append("rabbit", type="rodent")
        t.append("Bugs Bunny", type="rabbit")
        self.assertEqual(P("RABBIT", taxonomy=t).match(s).string, "Bugs Bunny")
        # Assert None, the syntax cannot handle taxonomy items that span multiple chunks.
        s = S("Elmer Fudd fires a cannon")
        t = search.Taxonomy()
        t.append("fire cannon", type="violence")
        self.assertEqual(P("VIOLENCE").match(s), None)
        # Assert regular expressions.
        s = S("a sack with 3.5 rabbits")
        p = search.Pattern.fromstring("[] NNS")
        p[0].words.append(re.compile(r"[0-9|\.]+"))
        self.assertEqual(p.match(s).string, "3.5 rabbits")
        print("pattern.search.Pattern.match()")

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
        # Assert all variations are matched (sentence starts with a NN* which must be caught).
        v = search.Pattern.fromstring("(DT) JJ?+ NN*")
        v = v.search(Sentence(parse("dogs, black cats and a big white rabbit")))
        self.assertEqual(v[0].string, "dogs")
        self.assertEqual(v[1].string, "black cats")
        self.assertEqual(v[2].string, "a big white rabbit")
        v = search.Pattern.fromstring("NN*")
        print("pattern.search.Pattern.search()")

    def test_convergence(self):
        # Test with random sentences and random patterns to see if it crashes.
        w = ("big", "white", "rabbit", "black", "cats", "is", "was", "going", "to", "sleep", "sleepy", "very", "or")
        x = ("DT?", "JJ?+", "NN*", "VP?", "cat", "[*]")
        for i in range(100):
            s = " ".join(random.choice(w) for i in range(20))
            s = Sentence(parse(s, lemmata=True))
            p = " ".join(random.choice(x) for i in range(5))
            p = search.Pattern.fromstring(p)
            p.search(s)

    def test_compile_function(self):
        # Assert creating and caching Pattern with compile().
        t = search.Taxonomy()
        p = search.compile("JJ?+ NN*", search.STRICT, taxonomy=t)
        self.assertEqual(p.strict, True)
        self.assertEqual(p[0].optional, True)
        self.assertEqual(p[0].tags, ["JJ"])
        self.assertEqual(p[1].tags, ["NN*"])
        self.assertEqual(p[1].taxonomy, t)
        # Assert regular expression input.
        p = search.compile(re.compile(r"[0-9|\.]+"))
        self.assertTrue(isinstance(p[0].words[0], search.regexp))
        # Assert TypeError for other input.
        self.assertRaises(TypeError, search.compile, 1)
        print("pattern.search.compile()")

    def test_match_function(self):
        # Assert match() function.
        s = Sentence(parse("Go on Bors, chop his head off!"))
        m1 = search.match("chop NP off", s, strict=False)
        m2 = search.match("chop NP+ off", s, strict=True)
        self.assertEqual(m1.constituents()[1].string, "his head")
        self.assertEqual(m2.constituents()[1].string, "his head")
        print("pattern.search.match()")

    def test_search_function(self):
        # Assert search() function.
        s = Sentence(parse("Go on Bors, chop his head off!"))
        m = search.search("PRP*? NN*", s)
        self.assertEqual(m[0].string, "Bors")
        self.assertEqual(m[1].string, "his head")
        print("pattern.search.search()")

    def test_escape(self):
        # Assert escape() function.
        self.assertEqual(search.escape("{}[]()_|!*+^."), "\\{\\}\\[\\]\\(\\)\\_\\|\\!\\*\\+\\^.")
        print("pattern.search.escape()")

#---------------------------------------------------------------------------------------------------


class TestMatch(unittest.TestCase):

    def setUp(self):
        pass

    def test_match(self):
        # Assert Match properties.
        s = Sentence(parse("Death awaits you all with nasty, big, pointy teeth."))
        p = search.Pattern(sequence=[
            search.Constraint(tags=["JJ"], optional=True),
            search.Constraint(tags=["NN*"])])
        m = p.search(s)
        self.assertTrue(isinstance(m, list))
        self.assertEqual(m[0].pattern, p)
        self.assertEqual(m[1].pattern, p)
        self.assertEqual(m[0].words, [s.words[0]])
        self.assertEqual(m[1].words, [s.words[-3], s.words[-2]])
        # Assert contraint "NN*" links to "Death" and "teeth", and "JJ" to "pointy".
        self.assertEqual(m[0].constraint(s.words[0]), p[1])
        self.assertEqual(m[1].constraint(s.words[-3]), p[0])
        self.assertEqual(m[1].constraint(s.words[-2]), p[1])
        # Assert constraints "JJ NN*" links to chunk "pointy teeth".
        self.assertEqual(m[1].constraints(s.chunks[-1]), [p[0], p[1]])
        # Assert Match.constituents() by constraint, constraint index and list of indices.
        self.assertEqual(m[1].constituents(), [s.words[-3], s.words[-2]])
        self.assertEqual(m[1].constituents(constraint=p[0]), [s.words[-3]])
        self.assertEqual(m[1].constituents(constraint=1), [s.words[-2]])
        self.assertEqual(m[1].constituents(constraint=(0, 1)), [s.words[-3], s.words[-2]])
        # Assert Match.string.
        self.assertEqual(m[1].string, "pointy teeth")
        print("pattern.search.Match")

    def test_group(self):
        # Assert Match groups.
        s = Sentence(parse("the big black cat eats a tasty fish"))
        m = search.search("DT {JJ+} NN", s)
        self.assertEqual(m[0].group(1).string, "big black")
        self.assertEqual(m[1].group(1).string, "tasty")
        # Assert nested groups (and syntax with additional spaces).
        m = search.search("DT { JJ { JJ { NN }}}", s)
        self.assertEqual(m[0].group(1).string, "big black cat")
        self.assertEqual(m[0].group(2).string, "black cat")
        self.assertEqual(m[0].group(3).string, "cat")
        # Assert chunked groups.
        m = search.search("NP {VP NP}", s)
        v = m[0].group(1, chunked=True)
        self.assertEqual(v[0].string, "eats")
        self.assertEqual(v[1].string, "a tasty fish")
        print("pattern.search.Match.group()")

    def test_group_ordering(self):
        # Assert group parser ordering (opened-first).
        c1 = search.Constraint("1")
        c2 = search.Constraint("2")
        c3 = search.Constraint("3")
        c4 = search.Constraint("4")
        p = search.Pattern([c1, [c2, [[c3], c4]]])
        self.assertEqual(p.groups[0][0].words[0], "2")
        self.assertEqual(p.groups[0][1].words[0], "3")
        self.assertEqual(p.groups[0][2].words[0], "4")
        self.assertEqual(p.groups[1][0].words[0], "3")
        self.assertEqual(p.groups[1][1].words[0], "4")
        self.assertEqual(p.groups[2][0].words[0], "3")
        p = search.Pattern.fromstring("1 {2 {{3} 4}}")
        self.assertEqual(p.groups[0][0].words[0], "2")
        self.assertEqual(p.groups[0][1].words[0], "3")
        self.assertEqual(p.groups[0][2].words[0], "4")
        self.assertEqual(p.groups[1][0].words[0], "3")
        self.assertEqual(p.groups[1][1].words[0], "4")
        self.assertEqual(p.groups[2][0].words[0], "3")
        p = search.Pattern.fromstring("1 {2} {3} 4")
        self.assertEqual(p.groups[0][0].words[0], "2")
        self.assertEqual(p.groups[1][0].words[0], "3")

#---------------------------------------------------------------------------------------------------


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestTaxonomy))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConstraint))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPattern))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMatch))
    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
