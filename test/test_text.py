# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
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
        print("pattern.text.lazydict")

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
        print("pattern.text.lazylist")
        
    def test_lexicon(self):
        # Assert lexicon from file (or file-like string).
        f1 = u";;; Comments. \n schrödinger NNP \n cat NN"
        f2 = StringIO.StringIO(u";;; Comments. \n schrödinger NNP \n cat NN")
        v1 = text.Lexicon(path=f1)
        v2 = text.Lexicon(path=f2)
        self.assertEqual(v1[u"schrödinger"], "NNP")
        self.assertEqual(v2[u"schrödinger"], "NNP")
        print("pattern.text.Lexicon")

#---------------------------------------------------------------------------------------------------

class TestFrequency(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_frequency(self):
        # Assert word frequency from file (or file-like string).
        f1 = u";;; Comments. \n the 1.0000 \n of 0.5040"
        f2 = StringIO.StringIO(u";;; Comments. \n the 1.0000 \n of 0.5040")
        v1 = text.Frequency(path=f1)
        v2 = text.Frequency(path=f2)
        self.assertEqual(v1[u"of"], 0.504)
        self.assertEqual(v2[u"of"], 0.504)
        print("pattern.text.Frequency")

#---------------------------------------------------------------------------------------------------

class TestModel(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_model(self):
        # Assert SLP language model.
        v = text.Model()
        for i in range(2):
            v.train("black", "JJ", previous=("the", "DT"), next=("cat", "NN"))
            v.train("on", "IN", previous=("sat", "VBD"), next=("the", "DT"))
        self.assertEqual("JJ", v.classify("slack"))
        self.assertEqual("JJ", v.classify("white", previous=("a", "DT"), next=("cat", "NN")))
        self.assertEqual("IN", v.classify("on", previous=("sat", "VBD")))
        self.assertEqual("IN", v.classify("on", next=("the", "")))
        self.assertEqual(["white", "JJ"], v.apply(("white", ""), next=("cat", "")))
        print("pattern.text.Model")

#---------------------------------------------------------------------------------------------------

class TestMorphology(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_morphology(self):
        # Assert morphological tagging rules.
        f = StringIO.StringIO(u"NN s fhassuf 1 NNS x")
        v = text.Morphology(f)
        self.assertEqual(v.apply(
            ["cats", "NN"]), 
            ["cats", "NNS"])
        print("pattern.text.Morphology")

#---------------------------------------------------------------------------------------------------

class TestContext(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_context(self):
        # Assert contextual tagging rules.
        f = StringIO.StringIO(u"VBD VB PREVTAG TO")
        v = text.Context(path=f)
        self.assertEqual(v.apply(
            [["to", "TO"], ["be", "VBD"]]), 
            [["to", "TO"], ["be", "VB"]])
        print("pattern.text.Context")

#---------------------------------------------------------------------------------------------------

class TestEntities(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_entities(self):
        # Assert named entity recognizer.
        f = StringIO.StringIO(u"Schrödinger's cat PERS")
        v = text.Entities(path=f)
        self.assertEqual(v.apply(
            [[u"Schrödinger's", "NNP"], ["cat", "NN"]]),
            [[u"Schrödinger's", "NNP-PERS"], ["cat", "NNP-PERS"]])
        print("pattern.text.Entities")

#---------------------------------------------------------------------------------------------------

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_stringio(self):
        # Assert loading data from file-like strings.
        p = text.Parser(
               lexicon = {"to": "TO", "saw": "VBD"},
            morphology = StringIO.StringIO(u"NN s fhassuf 1 NNS x"),
               context = StringIO.StringIO(u"VBD VB PREVTAG TO"))
        self.assertEqual(p.parse("cats"), "cats/NNS/B-NP/O")
        self.assertEqual(p.parse("to saw"), "to/TO/B-VP/O saw/VB/I-VP/O")
        
    def test_find_keywords(self):
        # Assert the intrinsic keyword extraction algorithm.
        p = text.Parser()
        p.lexicon["the"] = "DT"
        p.lexicon["cat"] = "NN"
        p.lexicon["dog"] = "NN"
        v1 = p.find_keywords("the cat")
        v2 = p.find_keywords("cat. cat. dog.")
        v3 = p.find_keywords("cat. dog. dog.")
        v4 = p.find_keywords("the. cat. dog.", frequency={"cat": 1.0, "dog": 0.0})
        self.assertEqual(v1, ["cat"])
        self.assertEqual(v2, ["cat", "dog"])
        self.assertEqual(v3, ["dog", "cat"])
        self.assertEqual(v3, ["dog", "cat"])
        print("pattern.text.Parser.find_keywords()")
        
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
        print("pattern.text.Parser.find_tokens()")
        
    def test_find_tags(self):
        # Assert the default part-of-speech tagger and its optional parameters.
        p = text.Parser()
        v1 = p.find_tags([u"Schrödinger", "cat", "1.0"], lexicon={}, default=("NN?", "NNP?", "CD?"))
        v2 = p.find_tags([u"Schrödinger", "cat", "1.0"], lexicon={"1.0": "CD?"})
        v3 = p.find_tags([u"Schrödinger", "cat", "1.0"], map=lambda token, tag: (token, tag+"!"))
        v4 = p.find_tags(["observer", "observable"], language="fr")
        v5 = p.find_tags(["observer", "observable"], language="en")
        self.assertEqual(v1, [[u"Schr\xf6dinger", "NNP?"], ["cat", "NN?"], ["1.0", "CD?"]])
        self.assertEqual(v2, [[u"Schr\xf6dinger", "NNP" ], ["cat", "NN" ], ["1.0", "CD?"]])
        self.assertEqual(v3, [[u"Schr\xf6dinger", "NNP!"], ["cat", "NN!"], ["1.0", "CD!"]])
        self.assertEqual(v4, [["observer", "NN"], ["observable", "NN"]])
        self.assertEqual(v5, [["observer", "NN"], ["observable", "JJ"]])
        print("pattern.text.Parser.find_tags()")
        
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
        print("pattern.text.Parser.find_chunks()"  )

#---------------------------------------------------------------------------------------------------

class TestSentiment(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_dict(self):
        # Assert weighted average polarity and subjectivity for dictionary.
        s = text.Sentiment()
        v = {":-(": 4, ":-)": 1}
        self.assertEqual(s(v)[0], -0.5)
        self.assertEqual(s(v)[1], +1.0)
        self.assertEqual(s(v).assessments[0], ([":-("], -0.75, 1.0, "mood"))
        self.assertEqual(s(v).assessments[1], ([":-)"], +0.50, 1.0, "mood"))
        print "pattern.text.Sentiment.assessments"
        
    def test_bag_of_words(self):
        # Assert weighted average polarity and subjectivity for bag-of-words with weighted features.
        from pattern.vector import BagOfWords # Alias for pattern.vector.Document.
        s = text.Sentiment()
        v = BagOfWords({":-(": 4, ":-)": 1})
        self.assertEqual(s(v)[0], -0.5)
        self.assertEqual(s(v)[1], +1.0)
        self.assertEqual(s(v).assessments[0], ([":-("], -0.75, 1.0, "mood"))
        self.assertEqual(s(v).assessments[1], ([":-)"], +0.50, 1.0, "mood"))
        
    def test_annotate(self):
        # Assert custom annotations.
        s = text.Sentiment()
        s.annotate("inconceivable", polarity=0.9, subjectivity=0.9)
        v = "inconceivable"
        self.assertEqual(s(v)[0], +0.9)
        self.assertEqual(s(v)[1], +0.9)

#---------------------------------------------------------------------------------------------------

class TestMultilingual(unittest.TestCase):

    def setUp(self):
        pass

    def test_language(self):
        # Assert language recognition.
        self.assertEqual(text.language(u"the cat sat on the mat")[0], "en")
        self.assertEqual(text.language(u"de kat zat op de mat")[0], "nl")
        self.assertEqual(text.language(u"le chat s'était assis sur le tapis")[0], "fr")
        print("pattern.text.language()")
        
    def test_deflood(self):
        # Assert flooding removal.
        self.assertEqual(text.deflood("NIIICE!!!", n=1), "NICE!")
        self.assertEqual(text.deflood("NIIICE!!!", n=2), "NIICE!!")
        print("pattern.text.deflood()")

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestLexicon))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestFrequency))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestModel))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMorphology))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestContext))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEntities))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMultilingual))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())