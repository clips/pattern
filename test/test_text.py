# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(".."))
import unittest
import StringIO

from pattern import text

#---------------------------------------------------------------------------------------------------

class TestLexicon(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_lazydict(self):
        # Assert lazy dictionary only has data after one of its methods is called.
        class V(text.lazydict):
            def load(self):
                dict.__setitem__(self, "a", 1)
        v = V()
        self.assertTrue(dict.__len__(v) == 0)
        self.assertTrue(dict.__contains__(v, "a") is False)
        self.assertTrue(len(v), 1)
        self.assertTrue(v["a"] == 1)
        print "pattern.text.lazydict"

    def test_lazylist(self):
        # Assert lazy list only has data after one of its methods is called.
        class V(text.lazylist):
            def load(self):
                list.append(self, "a")
        v = V()
        self.assertTrue(list.__len__(v) == 0)
        self.assertTrue(list.__contains__(v, "a") is False)
        self.assertTrue(len(v), 1)
        self.assertTrue(v[0] == "a")
        print "pattern.text.lazylist"
        
    def test_lexicon(self):
        # Assert loading and applying Brill lexicon and rules.
        f1 = u";;; Comments. \n schrödinger NNP \n cat NN"
        f2 = StringIO.StringIO(u"NN s fhassuf 1 NNS x")
        f3 = StringIO.StringIO(u"VBD VB PREVTAG TO")
        f4 = StringIO.StringIO(u"Schrödinger's cat PERS")
        v = text.Lexicon(path=f1, morphology=f2, context=f3, entities=f4)
        self.assertEqual(v[u"schrödinger"], "NNP")
        self.assertEqual(v.morphology.apply(
            ["cats", "NN"]), 
            ["cats", "NNS"])
        self.assertEqual(v.context.apply(
            [["to", "TO"], ["be", "VBD"]]), 
            [["to", "TO"], ["be", "VB"]])
        self.assertEqual(v.entities.apply(
            [[u"Schrödinger's", "NNP"], ["cat", "NN"]]),
            [[u"Schrödinger's", "NNP-PERS"], ["cat", "NNP-PERS"]])
        print "pattern.text.Lexicon"
        print "pattern.text.Morphology"
        print "pattern.text.Context"
        print "pattern.text.Entities"

#---------------------------------------------------------------------------------------------------

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_find_tokens(self):
        # Assert the default tokenizer and its optional parameters.
        p = text.Parser()
        v1 = p.find_tokens(u"Schrödinger's cat is alive!", punctuation="", replace={})
        v2 = p.find_tokens(u"Schrödinger's cat is dead!", punctuation="!", replace={"'s": " 's"})
        v3 = p.find_tokens(u"etc.", abbreviations=set())
        v4 = p.find_tokens(u"etc.", abbreviations=set(("etc.",)))
        self.assertEqual(v1[0], u"Schrödinger's cat is alive!")
        self.assertEqual(v2[0], u"Schrödinger 's cat is dead !")
        self.assertEqual(v3[0], "etc .")
        self.assertEqual(v4[0], "etc.")
        print "pattern.text.Parser.find_tokens()"
        
    def test_find_tags(self):
        # Assert the default part-of-speech tagger and its optional parameters.
        p = text.Parser()
        v1 = p.find_tags([u"Schrödinger", "cat", "1.0"], lexicon={}, default=("NN?", "NNP?", "CD?"))
        v2 = p.find_tags([u"Schrödinger", "cat", "1.0"], lexicon={"1.0": "CD?"})
        v3 = p.find_tags([u"Schrödinger", "cat", "1.0"], map=lambda tag: tag+"!")
        v4 = p.find_tags(["observer", "observable"], language="fr")
        v5 = p.find_tags(["observer", "observable"], language="en")
        self.assertEqual(v1, [[u"Schr\xf6dinger", "NNP?"], ["cat", "NN?"], ["1.0", "CD?"]])
        self.assertEqual(v2, [[u"Schr\xf6dinger", "NNP" ], ["cat", "NN" ], ["1.0", "CD?"]])
        self.assertEqual(v3, [[u"Schr\xf6dinger", "NNP!"], ["cat", "NN!"], ["1.0", "CD!"]])
        self.assertEqual(v4, [["observer", "NN"], ["observable", "NN"]])
        self.assertEqual(v5, [["observer", "NN"], ["observable", "JJ"]])
        print "pattern.text.Parser.find_tags()"
        
    def test_find_chunks(self):
        # Assert the default phrase chunker and its optional parameters.
        p = text.Parser()
        v1 = p.find_chunks([["", "DT"], ["", "JJ"], ["", "NN"]], language="en")
        v2 = p.find_chunks([["", "DT"], ["", "JJ"], ["", "NN"]], language="es")
        v3 = p.find_chunks([["", "DT"], ["", "NN"], ["", "JJ"]], language="en")
        v4 = p.find_chunks([["", "DT"], ["", "NN"], ["", "JJ"]], language="es")
        self.assertEqual(v1, [["", "DT", "B-NP", "O"], ["", "JJ", "I-NP", "O"], ["", "NN", "I-NP", "O"]])
        self.assertEqual(v2, [["", "DT", "B-NP", "O"], ["", "JJ", "I-NP", "O"], ["", "NN", "I-NP", "O"]])
        self.assertEqual(v3, [["", "DT", "B-NP", "O"], ["", "NN", "I-NP", "O"], ["", "JJ", "B-ADJP", "O"]])
        self.assertEqual(v4, [["", "DT", "B-NP", "O"], ["", "NN", "I-NP", "O"], ["", "JJ", "I-NP", "O"]])
        print "pattern.text.Parser.find_chunks()"  

#---------------------------------------------------------------------------------------------------

class TestSentiment(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_dict(self):
        # Assert weighted average polarity and subjectivity for dictionary.
        s = text.Sentiment()
        v = {":-(": 3, ":-)": 1}
        self.assertEqual(s(v)[0], -0.5)
        self.assertEqual(s(v)[1], +1.0)
        self.assertEqual(s(v).assessments[0], ([":-("], -1.0, 1.0))
        self.assertEqual(s(v).assessments[1], ([":-)"], +1.0, 1.0))
        
    def test_bag_of_words(self):
        # Assert weighted average polarity and subjectivity for bag-of-words with weighted features.
        from pattern.vector import BagOfWords # Alias for pattern.vector.Document.
        s = text.Sentiment()
        v = BagOfWords({":-(": 3, ":-)": 1})
        self.assertEqual(s(v)[0], -0.5)
        self.assertEqual(s(v)[1], +1.0)
        self.assertEqual(s(v).assessments[0], ([":-("], -1.0, 1.0))
        self.assertEqual(s(v).assessments[1], ([":-)"], +1.0, 1.0))

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestLexicon))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())