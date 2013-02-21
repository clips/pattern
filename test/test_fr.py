# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(".."))
import unittest
import subprocess

from pattern import fr

try:
    PATH = os.path.dirname(os.path.abspath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------

class TestInflection(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_predicative(self):
        # Assert the accuracy of the predicative algorithm ("belles" => "beau").
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, tag in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-fr-lexique.csv")):
            if tag == "a":
                if fr.predicative(attr) == pred:
                    i +=1
                n += 1
        self.assertTrue(float(i) / n > 0.95)
        print "pattern.fr.predicative()"

    def test_parse_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        i, n = 0, 0
        for v1, v2 in fr.inflect.VERBS.inflections.items():
            if fr.inflect._parse_lemma(v1) == v2: 
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.80)
        print "pattern.fr.inflect._parse_lemma()"
        
    def test_parse_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in fr.inflect.VERBS.infinitives.items():
            lexeme2 = fr.inflect._parse_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.85)
        print "pattern.fr.inflect._parse_lexeme()"

    def test_lexeme(self):
        # Assert all inflections of "sein".
        v = fr.lexeme(u"être")
        self.assertEqual(v, [
            u"être", u"suis", u"es", u"est", u"sommes", u"êtes", u"sont", u"étant", u"été", 
            u"fus", u"fut", u"fûmes", u"fûtes", u"furent", 
            u"étais", u"était", u"étions", u"étiez", u"étaient", 
            u"serai", u"seras", u"sera", u"serons", u"serez", u"seront", 
            u"serais", u"serait", u"serions", u"seriez", u"seraient", 
            u"sois", u"soyons", u"soyez", u"soit", u"soient", 
            u"fusse", u"fusses", u"fût", u"fussions", u"fussiez", u"fussent"
        ])
        print "pattern.es.inflect.lexeme()"

    def test_tenses(self):
        # Assert tense of "is".
        self.assertTrue((fr.PRESENT, 3, fr.SG) in fr.tenses("est"))
        self.assertTrue("2sg" in fr.tenses("es"))
        print "pattern.fr.tenses()"

#---------------------------------------------------------------------------------------------------

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass
   
    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.fr.parser", "-s", u"Le chat noir.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "Le/DT/B-NP/O/O/le chat/NN/I-NP/O/O/chat noir/JJ/I-NP/O/O/noir ././O/O/O/.")
        print "python -m pattern.fr.parser"

#---------------------------------------------------------------------------------------------------

class TestSentiment(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_sentiment(self):
        # Assert < 0 for negative adjectives and > 0 for positive adjectives.
        self.assertTrue(fr.sentiment("fabuleux")[0] > 0)
        self.assertTrue(fr.sentiment("terrible")[0] < 0)
        # Assert the accuracy of the sentiment analysis.
        # Given are the scores for 1,500 book reviews.
        # The baseline should increase (not decrease) when the algorithm is modified.
        from pattern.db import Datasheet
        from pattern.metrics import test
        reviews = []
        for review, score in Datasheet.load(os.path.join(PATH, "corpora", "polarity-fr-amazon.csv")):
            reviews.append((review, int(score) > 0))
        A, P, R, F = test(lambda review: fr.positive(review), reviews)
        self.assertTrue(A > 0.75)
        self.assertTrue(P > 0.76)
        self.assertTrue(R > 0.73)
        self.assertTrue(F > 0.75)
        print "pattern.fr.sentiment()"

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
