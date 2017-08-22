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
import math

from types import GeneratorType

from pattern import metrics

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------


class TestProfiling(unittest.TestCase):

    def setUp(self):
        # Test set for accuracy, precision and recall:
        self.documents = (
            (None, True),
            (None, True),
            (None, False)
        )

    def test_duration(self):
        # Assert 0.1 or slightly higher.
        v = metrics.duration(time.sleep, 0.1)
        self.assertTrue(v > 0.1)
        print("pattern.metrics.duration()")

    def test_confustion_matrix(self):
        # Assert 2 true positives (TP) and 1 false positive (FP).
        v = metrics.confusion_matrix(lambda document: True, self.documents)
        self.assertEqual(v, (2, 0, 1, 0))
        # Assert 1 true negative (TN) and 2 false negatives (FN).
        v = metrics.confusion_matrix(lambda document: False, self.documents)
        self.assertEqual(v, (0, 1, 0, 2))
        print("pattern.metrics.confusion_matrix()")

    def test_accuracy(self):
        # Assert 2.0/3.0 (two out of three correct predictions).
        v = metrics.accuracy(lambda document: True, self.documents)
        self.assertEqual(v, 2.0 / 3.0)
        print("pattern.metrics.accuracy()")

    def test_precision(self):
        # Assert 2.0/3.0 (2 TP, 1 FP).
        v = metrics.precision(lambda document: True, self.documents)
        self.assertEqual(v, 2.0 / 3.0)
        # Assert 0.0 (no TP).
        v = metrics.precision(lambda document: False, self.documents)
        self.assertEqual(v, 0.0)
        print("pattern.metrics.precision()")

    def test_recall(self):
        # Assert 1.0 (no FN).
        v = metrics.recall(lambda document: True, self.documents)
        self.assertEqual(v, 1.0)
        # Assert 0.0 (no TP).
        v = metrics.recall(lambda document: False, self.documents)
        self.assertEqual(v, 0.0)
        print("pattern.metrics.recall()")

    def test_F1(self):
        # Assert 0.8 (F1 for precision=2/3 and recall=1).
        v = metrics.F1(lambda document: True, self.documents)
        self.assertEqual(v, 0.8)
        self.assertEqual(v, metrics.F(lambda document: True, self.documents, beta=1))
        print("pattern.metrics.F1()")

    def test_agreement(self):
        # Assert 0.210 (example from http://en.wikipedia.org/wiki/Fleiss'_kappa).
        m = [[0, 0, 0, 0, 14],
              [0, 2, 6, 4, 2 ],
              [0, 0, 3, 5, 6 ],
              [0, 3, 9, 2, 0 ],
              [2, 2, 8, 1, 1 ],
              [7, 7, 0, 0, 0 ],
              [3, 2, 6, 3, 0 ],
              [2, 5, 3, 2, 2 ],
              [6, 5, 2, 1, 0 ],
              [0, 2, 2, 3, 7 ]]
        v = metrics.agreement(m)
        self.assertAlmostEqual(v, 0.210, places=3)
        print("pattern.metrics.agreement()")


class TestTextMetrics(unittest.TestCase):

    def setUp(self):
        pass

    def test_levenshtein(self):
        # Assert 0 (identical strings).
        v = metrics.levenshtein("gallahad", "gallahad")
        self.assertEqual(v, 0)
        # Assert 3 (1 insert, 1 delete, 1 replace).
        v = metrics.levenshtein("gallahad", "_g_llaha")
        self.assertEqual(v, 3)
        print("pattern.metrics.levenshtein()")

    def test_levenshtein_similarity(self):
        # Assert 1.0 (identical strings).
        v = metrics.levenshtein_similarity("gallahad", "gallahad")
        self.assertEqual(v, 1.0)
        # Assert 0.75 (2 out of 8 characters differ).
        v = metrics.levenshtein_similarity("gallahad", "g_ll_had")
        self.assertEqual(v, 0.75)
        print("pattern.metrics.levenshtein_similarity()")

    def test_dice_coefficient(self):
        # Assert 1.0 (identical strings).
        v = metrics.dice_coefficient("gallahad", "gallahad")
        self.assertEqual(v, 1.0)
        # Assert 0.25 (example from http://en.wikipedia.org/wiki/Dice_coefficient).
        v = metrics.dice_coefficient("night", "nacht")
        self.assertEqual(v, 0.25)
        print("pattern.metrics.dice_coefficient()")

    def test_similarity(self):
        self.assertEqual(
            metrics.levenshtein_similarity("night", "nacht"),
            metrics.similarity("night", "nacht", metrics.LEVENSHTEIN))
        self.assertEqual(
            metrics.dice_coefficient("night", "nacht"),
            metrics.similarity("night", "nacht", metrics.DICE))
        print("pattern.metrics.similarity()")

    def test_readability(self):
        # Assert that technical jargon is in the "difficult" range (< 0.30).
        s = "The Australian platypus is seemingly a hybrid of a mammal and reptilian creature."
        v = metrics.readability(s)
        self.assertTrue(v < 0.30)
        # Assert that Dr. Seuss is in the "easy" range (> 0.70).
        s = "'I know some good games we could play,' said the cat. " + \
            "'I know some new tricks,' said the cat in the hat. " + \
            "'A lot of good tricks. I will show them to you.' " + \
            "'Your mother will not mind at all if I do.'"
        v = metrics.readability(s)
        self.assertTrue(v > 0.70)
        print("pattern.metrics.readability()")

    def test_intertextuality(self):
        # Evaluate accuracy for plagiarism detection.
        from pattern.db import Datasheet
        data = Datasheet.load(os.path.join(PATH, "corpora", "plagiarism-clough&stevenson.csv"))
        data = [((txt, src), int(plagiarism) > 0) for txt, src, plagiarism in data]

        def plagiarism(txt, src):
            return metrics.intertextuality([txt, src], n=3)[0, 1] > 0.05
        A, P, R, F = metrics.test(lambda x: plagiarism(*x), data)
        self.assertTrue(P > 0.96)
        self.assertTrue(R > 0.94)
        print("pattern.metrics.intertextuality()")

    def test_ttr(self):
        # Assert type-token ratio: words = 7, unique words = 6.
        s = "The black cat \n sat on the mat."
        v = metrics.ttr(s)
        self.assertAlmostEqual(v, 0.86, places=2)
        print("pattern.metrics.ttr()")

    def test_suffixes(self):
        # Assert base => inflected and reversed inflected => base suffixes.
        s = [("beau", "beaux"), ("jeune", "jeunes"), ("hautain", "hautaines")]
        v = metrics.suffixes(s, n=3)
        self.assertEqual(v, [
            (2, "nes", [("ne", 0.5), ("n", 0.5)]),
            (1, "aux", [("au", 1.0)])])
        v = metrics.suffixes(s, n=2, reverse=False)
        self.assertEqual(v, [
            (1, "ne", [("nes", 1.0)]),
            (1, "in", [("ines", 1.0)]),
            (1, "au", [("aux", 1.0)])])
        print("pattern.metrics.suffixes()")

    def test_isplit(self):
        # Assert string.split() iterator.
        v = metrics.isplit("test\nisplit")
        self.assertTrue(isinstance(v, GeneratorType))
        self.assertEqual(list(v), ["test", "isplit"])
        print("pattern.metrics.isplit()")

    def test_cooccurrence(self):
        s = "The black cat sat on the mat."
        v = metrics.cooccurrence(s, window=(-1, 1),
                term1 = lambda w: w in ("cat",),
            normalize = lambda w: w.lower().strip(".:;,!?()[]'\""))
        self.assertEqual(sorted(v.keys()), ["cat"])
        self.assertEqual(sorted(v["cat"].keys()), ["black", "cat", "sat"])
        self.assertEqual(sorted(v["cat"].values()), [1, 1, 1])
        s = [("The", "DT"), ("black", "JJ"), ("cat", "NN"), ("sat", "VB"), ("on", "IN"), ("the", "DT"), ("mat", "NN")]
        v = metrics.co_occurrence(s, window=(-2, -1),
             term1 = lambda token: token[1].startswith("NN"),
             term2 = lambda token: token[1].startswith("JJ"))
        self.assertEqual(v, {("cat", "NN"): {("black", "JJ"): 1}})
        print("pattern.metrics.cooccurrence()")


class TestInterpolation(unittest.TestCase):

    def setUp(self):
        pass

    def test_lerp(self):
        # Assert linear interpolation.
        v = metrics.lerp(100, 200, 0.5)
        self.assertEqual(v, 150.0)
        print("pattern.metrics.lerp()")

    def test_smoothstep(self):
        # Assert cubic interpolation.
        v1 = metrics.smoothstep(0.0, 1.0, 0.5)
        v2 = metrics.smoothstep(0.0, 1.0, 0.9)
        v3 = metrics.smoothstep(0.0, 1.0, 0.1)
        self.assertEqual(v1, 0.5)
        self.assertTrue(v2 > 0.9)
        self.assertTrue(v3 < 0.1)
        print("pattern.metrics.smoothstep()")

    def test_smoothrange(self):
        # Assert nice ranges for line charts.
        v = list(metrics.smoothrange(0.0, 1.0))
        [self.assertAlmostEqual(x, y, places=1) for x, y in zip(v,
            [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])]
        v = list(metrics.smoothrange(-2, 2))
        [self.assertAlmostEqual(x, y, places=1) for x, y in zip(v,
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0])]
        v = list(metrics.smoothrange(1, 13))
        [self.assertAlmostEqual(x, y, places=1) for x, y in zip(v,
            [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0])]
        print("pattern.metrics.smoothrange()")


class TestStatistics(unittest.TestCase):

    def setUp(self):
        pass

    def test_mean(self):
        # Assert (1+2+3+4) / 4 = 2.5.
        v = metrics.mean([1, 2, 3, 4])
        self.assertEqual(v, 2.5)
        print("pattern.metrics.mean()")

    def test_median(self):
        # Assert 2.5 (between 2 and 3).
        v = metrics.median([1, 2, 3, 4])
        self.assertEqual(v, 2.5)
        # Assert 3 (middle of list).
        v = metrics.median([1, 2, 3, 4, 5])
        self.assertEqual(v, 3)
        # Assert that empty list raises ValueError.
        self.assertRaises(ValueError, metrics.median, [])
        print("pattern.metrics.median()")

    def test_variance(self):
        # Assert 2.5.
        v = metrics.variance([1, 2, 3, 4, 5], sample=True)
        self.assertEqual(v, 2.5)
        # Assert 2.0 (population variance).
        v = metrics.variance([1, 2, 3, 4, 5], sample=False)
        self.assertEqual(v, 2.0)
        print("pattern.metrics.variance()")

    def test_standard_deviation(self):
        # Assert 2.429 (sample).
        v = metrics.standard_deviation([1, 5, 6, 7, 6, 8], sample=True)
        self.assertAlmostEqual(v, 2.429, places=3)
        # Assert 2.217 (population).
        v = metrics.standard_deviation([1, 5, 6, 7, 6, 8], sample=False)
        self.assertAlmostEqual(v, 2.217, places=3)
        print("pattern.metrics.standard_deviation()")

    def test_histogram(self):
        # Assert 1 bin.
        v = metrics.histogram([1, 2, 3, 4], k=0)
        self.assertTrue(len(v) == 1)
        # Assert 4 bins, each with one value, each with midpoint == value.
        v = metrics.histogram([1, 2, 3, 4], k=4, range=(0.5, 4.5))
        for i, ((start, stop), v) in enumerate(sorted(v.items())):
            self.assertTrue(i + 1 == v[0])
            self.assertAlmostEqual(start + (stop - start) / 2, i + 1, places=3)
        # Assert 2 bins, one with all the low numbers, one with the high number.
        v = metrics.histogram([1, 2, 3, 4, 100], k=2)
        v = sorted(v.values(), key=lambda item: len(item))
        self.assertTrue(v[0] == [100])
        self.assertTrue(v[1] == [1, 2, 3, 4])
        print("pattern.metrics.histogram()")

    def test_moment(self):
        # Assert 0.0 (1st central moment = 0.0).
        v = metrics.moment([1, 2, 3, 4, 5], n=1)
        self.assertEqual(v, 0.0)
        # Assert 2.0 (2nd central moment = population variance).
        v = metrics.moment([1, 2, 3, 4, 5], n=2)
        self.assertEqual(v, 2.0)
        print("pattern.metrics.moment()")

    def test_skewness(self):
        # Assert < 0.0 (few low values).
        v = metrics.skewness([1, 100, 101, 102, 103])
        self.assertTrue(v < 0.0)
        # Assert > 0.0 (few high values).
        v = metrics.skewness([1, 2, 3, 4, 100])
        self.assertTrue(v > 0.0)
        # Assert 0.0 (evenly distributed).
        v = metrics.skewness([1, 2, 3, 4])
        self.assertTrue(v == 0.0)
        print("pattern.metrics.skewness()")

    def test_kurtosis(self):
        # Assert -1.2 for the uniform distribution.
        a = 1
        b = 1000
        v = metrics.kurtosis([float(i - a) / (b - a) for i in range(a, b)])
        self.assertAlmostEqual(v, -1.2, places=3)
        print("pattern.metrics.kurtosis()")

    def test_quantile(self):
        # Assert 2.5 (quantile with p=0.5 == median).
        v = metrics.quantile([1, 2, 3, 4], p=0.5, a=1, b=-1, c=0, d=1)
        self.assertEqual(v, 2.5)
        # Assert 3.0 (discontinuous sample).
        v = metrics.quantile([1, 2, 3, 4], p=0.5, a=0.5, b=0, c=1, d=0)
        self.assertEqual(v, 3.0)
        return "pattern.metrics.quantile()"

    def test_boxplot(self):
        # Different a,b,c,d quantile parameters produce different results.
        # By approximation, assert (53, 79.5, 84.5, 92, 98).
        a = [79, 53, 82, 91, 87, 98, 80, 93]
        v = metrics.boxplot(a)
        self.assertEqual(v[0], min(a))
        self.assertTrue(abs(v[1] - 79.5) <= 0.5)
        self.assertTrue(abs(v[2] - metrics.median(a)) <= 0.5)
        self.assertTrue(abs(v[3] - 92.0) <= 0.5)
        self.assertEqual(v[4], max(a))
        print("pattern.metrics.boxplot()")


class TestStatisticalTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_fisher_test(self):
        # Assert Fisher exact test significance.
        v = metrics.fisher_exact_test(a=1, b=9, c=11, d=3)
        self.assertAlmostEqual(v, 0.0028, places=4)
        v = metrics.fisher_exact_test(a=45, b=15, c=75, d=45)
        self.assertAlmostEqual(v, 0.1307, places=4)
        print("pattern.metrics.fisher_test()")

    def test_chi_squared(self):
        # Assert chi-squared test (upper tail).
        o1, e1 = [[44, 56]], [[50, 50]]
        o2, e2 = [[22, 21, 22, 27, 22, 36]], []
        o3, e3 = [[48, 35, 15, 3]], [[58, 34.5, 7, 0.5]]
        o4, e4 = [[36, 14], [30, 25]], []
        o5, e5 = [[46, 71], [37, 83]], [[40.97, 76.02], [42.03, 77.97]]
        v1 = metrics.chi2(o1, e1)
        v2 = metrics.chi2(o2, e2)
        v3 = metrics.chi2(o3, e3)
        v4 = metrics.chi2(o4, e4)
        v5 = metrics.chi2(o5, e5)
        self.assertAlmostEqual(v1[0], 1.4400, places=4)
        self.assertAlmostEqual(v1[1], 0.2301, places=4)
        self.assertAlmostEqual(v2[0], 6.7200, places=4)
        self.assertAlmostEqual(v2[1], 0.2423, places=4)
        self.assertAlmostEqual(v3[0], 23.3742, places=4)
        self.assertAlmostEqual(v4[0], 3.4177, places=4)
        self.assertAlmostEqual(v5[0], 1.8755, places=4)
        print("pattern.metrics.chi2()")

    def test_chi_squared_p(self):
        # Assert chi-squared P-value (upper tail).
        for df, X2 in [
          (1, (3.85, 5.05, 6.65, 7.90)),
          (2, (6.00, 7.40, 9.25, 10.65)),
          (3, (7.85, 9.40, 11.35, 12.85)),
          (4, (9.50, 11.15, 13.30, 14.90)),
          (5, (11.10, 12.85, 15.10, 16.80))]:
            for i, x2 in enumerate(X2):
                v = metrics.chi2p(x2, df, tail=metrics.UPPER)
                self.assertTrue(v < (0.05, 0.025, 0.01, 0.005)[i])
        print("pattern.metrics.chi2p()")

    def test_kolmogorov_smirnov(self):
        v = metrics.ks2([1, 2, 3], [1, 2, 4])
        self.assertAlmostEqual(v[0], 0.3333, places=4)
        self.assertAlmostEqual(v[1], 0.9762, places=4)
        print("pattern.metrics.ks2()")


class TestSpecialFunctions(unittest.TestCase):

    def setUp(self):
        pass

    def test_gamma(self):
        # Assert complete gamma function.
        v = metrics.gamma(0.5)
        self.assertAlmostEqual(v, math.sqrt(math.pi), places=4)
        print("pattern.metrics.gamma()")

    def test_gammai(self):
        # Assert incomplete gamma function.
        v = metrics.gammai(a=1, x=2)
        self.assertAlmostEqual(v, 0.1353, places=4)
        print("pattern.metrics.gammai()")

    def test_erfc(self):
        # Assert complementary error function.
        for x, y in [
          (-3.00, 2.000),
          (-2.00, 1.995),
          (-1.00, 1.843),
          (-0.50, 1.520),
          (-0.25, 1.276),
          ( 0.00, 1.000),
          ( 0.25, 0.724),
          ( 0.50, 0.480),
          ( 1.00, 0.157),
          ( 2.00, 0.005),
          ( 3.00, 0.000)]:
            self.assertAlmostEqual(metrics.erfc(x), y, places=3)
        print("pattern.metrics.erfc()")

    def test_kolmogorov(self):
        # Assert Kolmogorov limit distribution.
        self.assertAlmostEqual(metrics.kolmogorov(0.0), 1.0000, places=4)
        self.assertAlmostEqual(metrics.kolmogorov(0.5), 0.9639, places=4)
        self.assertAlmostEqual(metrics.kolmogorov(1.0), 0.2700, places=4)
        self.assertAlmostEqual(metrics.kolmogorov(2.0), 0.0007, places=4)
        self.assertAlmostEqual(metrics.kolmogorov(4.0), 0.0000, places=4)
        print("pattern.metrics.kolmogorov()")

#---------------------------------------------------------------------------------------------------


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProfiling))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestTextMetrics))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInterpolation))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestStatistics))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestStatisticalTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSpecialFunctions))
    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
