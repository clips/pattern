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

class TestSentiment(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_sentiment(self):
        # Assert < 0 for negative adjectives and > 0 for positive adjectives.
        self.assertTrue(fr.sentiment("fabuleux")[0] > 0)
        self.assertTrue(fr.sentiment("terrible")[0] < 0)
        # Assert the accuracy of the sentiment analysis.
        # Given are the scores for 3,000 book reviews.
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
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
