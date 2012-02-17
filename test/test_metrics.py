import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest
import time

from pattern import metrics

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
        print "pattern.metrics.duration()"

    def test_confustion_matrix(self):
        # Assert 2 true positives (TP) and 1 false positive (FP).
        v = metrics.confusion_matrix(lambda document: True, self.documents)
        self.assertEqual(v, (2,0,1,0))  
        # Assert 1 true negative (TN) and 2 false negatives (FN).
        v = metrics.confusion_matrix(lambda document: False, self.documents)
        self.assertEqual(v, (0,1,0,2))  
        print "pattern.metrics.confusion_matrix()"      
    
    def test_accuracy(self):
        # Assert 2.0/3.0 (two out of three correct predictions).
        v = metrics.accuracy(lambda document: True, self.documents)
        self.assertEqual(v, 2.0/3.0)
        print "pattern.metrics.accuracy()"

    def test_precision(self):
        # Assert 2.0/3.0 (2 TP, 1 FP).
        v = metrics.precision(lambda document: True, self.documents)
        self.assertEqual(v, 2.0/3.0)
        # Assert 0.0 (no TP).
        v = metrics.precision(lambda document: False, self.documents)
        self.assertEqual(v, 0.0)
        print "pattern.metrics.precision()"

    def test_recall(self):
        # Assert 1.0 (no FN).
        v = metrics.recall(lambda document: True, self.documents)
        self.assertEqual(v, 1.0)
        # Assert 0.0 (no TP).
        v = metrics.recall(lambda document: False, self.documents)
        self.assertEqual(v, 0.0)
        print "pattern.metrics.recall()"
        
    def test_F1(self):
        # Assert 0.8 (F1 for precision=2/3 and recall=1).
        v = metrics.F1(lambda document: True, self.documents)
        self.assertEqual(v, 0.8)
        self.assertEqual(v, metrics.F(lambda document: True, self.documents, beta=1))
        print "pattern.metrics.F1()"
        
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
        print "pattern.metrics.agreement()"

class TestStringFunctions(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_levenshtein(self):
        # Assert 0 (identical strings).
        v = metrics.levenshtein("gallahad", "gallahad")
        self.assertEqual(v, 0)
        # Assert 3 (1 insert, 1 delete, 1 replace).
        v = metrics.levenshtein("gallahad", "_g_llaha")
        self.assertEqual(v, 3)
        print "pattern.metrics.levenshtein()"

    def test_levenshtein_similarity(self):
        # Assert 1.0 (identical strings).
        v = metrics.levenshtein_similarity("gallahad", "gallahad")
        self.assertEqual(v, 1.0)
        # Assert 0.75 (2 out of 8 characters differ).
        v = metrics.levenshtein_similarity("gallahad", "g_ll_had")
        self.assertEqual(v, 0.75)
        print "pattern.metrics.levenshtein_similarity()"
        
    def test_dice_coefficient(self):
        # Assert 1.0 (identical strings).
        v = metrics.dice_coefficient("gallahad", "gallahad")
        self.assertEqual(v, 1.0)
        # Assert 0.25 (example from http://en.wikipedia.org/wiki/Dice_coefficient).
        v = metrics.dice_coefficient("night", "nacht")
        self.assertEqual(v, 0.25)
        print "pattern.metrics.dice_coefficient()"
        
    def test_similarity(self):
        self.assertEqual(
            metrics.levenshtein_similarity("night", "nacht"), 
            metrics.similarity("night", "nacht", metrics.LEVENSHTEIN))
        self.assertEqual(
            metrics.dice_coefficient("night", "nacht"), 
            metrics.similarity("night", "nacht", metrics.DICE))
        print "pattern.metrics.similarity()"
            
    def test_readability(self):
        # Assert technical jargon in the "difficult" range (< 0.30).
        s = "The Australian platypus is seemingly a hybrid of a mammal and reptilian creature"
        v = metrics.readability(s)
        self.assertTrue(v < 0.30)        
        # Assert that Dr. Seuss isin the "easy" range (> 0.70).
        s = "'I know some good games we could play,' said the cat." + \
            "'I know some new tricks,' said the cat in the hat." + \
            "'A lot of good tricks. I will show them to you.'" + \
            "'Your mother will not mind at all if I do.'"
        v = metrics.readability(s)
        self.assertTrue(v > 0.70)
        print "pattern.metrics.readability()"

class TestStatistics(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_mean(self):
        # Assert (1+2+3+4) / 4 = 2.5.
        v = metrics.mean([1,2,3,4])
        self.assertEqual(v, 2.5)
        print "pattern.metrics.mean()"
        
    def test_median(self):
        # Assert 2.5 (between 2 and 3).
        v = metrics.median([1,2,3,4])
        self.assertEqual(v, 2.5)
        # Assert 3 (middle of list).
        v = metrics.median([1,2,3,4,5])
        self.assertEqual(v, 3)
        # Assert that empty list raises ValueError.
        self.assertRaises(ValueError, metrics.median, [])
        print "pattern.metrics.median()"
        
    def test_variance(self):
        # Assert 2.5.
        v = metrics.variance([1,2,3,4,5], sample=True)
        self.assertEqual(v, 2.5)
        # Assert 2.0 (population variance).
        v = metrics.variance([1,2,3,4,5], sample=False)
        self.assertEqual(v, 2.0)
        print "pattern.metrics.variance()"
        
    def test_standard_deviation(self):
        # Assert 2.429 (sample).
        v = metrics.standard_deviation([1,5,6,7,6,8], sample=True)
        self.assertAlmostEqual(v, 2.429, places=3)
        # Assert 2.217 (population).
        v = metrics.standard_deviation([1,5,6,7,6,8], sample=False)
        self.assertAlmostEqual(v, 2.217, places=3)
        print "pattern.metrics.standard_deviation()"
    
    def test_histogram(self):
        # Assert 1 bin.
        v = metrics.histogram([1,2,3,4], k=0)
        self.assertTrue(len(v) == 1)
        # Assert 4 bins, each with one value, each with midpoint == value.
        v = metrics.histogram([1,2,3,4], k=4, range=(0.5,4.5))
        for i, ((start, stop), v) in enumerate(sorted(v.items())):
            self.assertTrue(i+1 == v[0])
            self.assertAlmostEqual(start + (stop-start)/2, i+1, places=3)
        # Assert 2 bins, one with all the low numbers, one with the high number.
        v = metrics.histogram([1,2,3,4,100], k=2)
        v = sorted(v.values(), key=lambda item: len(item))
        self.assertTrue(v[0] == [100])
        self.assertTrue(v[1] == [1,2,3,4])
        print "pattern.metrics.histogram()"
    
    def test_moment(self):
        # Assert 0.0 (1st central moment = 0.0).
        v = metrics.moment([1,2,3,4,5], k=1)
        self.assertEqual(v, 0.0)
        # Assert 2.0 (2nd central moment = population variance).
        v = metrics.moment([1,2,3,4,5], k=2)
        self.assertEqual(v, 2.0)
        print "pattern.metrics.moment()"
    
    def test_skewness(self):
        # Assert < 0.0 (few low values).
        v = metrics.skewness([1,100,101,102,103])
        self.assertTrue(v < 0.0)
        # Assert > 0.0 (few high values).
        v = metrics.skewness([1,2,3,4,100])
        self.assertTrue(v > 0.0)
        # Assert 0.0 (evenly distributed).
        v = metrics.skewness([1,2,3,4])
        self.assertTrue(v == 0.0)
        print "pattern.metrics.skewness()"
        
    def test_kurtosis(self):
        # Assert -1.2 for the uniform distribution.
        a = 1
        b = 1000
        v = metrics.kurtosis([float(i-a)/(b-a) for i in range(a,b)])
        self.assertAlmostEqual(v, -1.2, places=3)
        print "pattern.metrics.kurtosis()"
        
    def test_quantile(self):
        # Assert 2.5 (quantile with p=0.5 == median).
        v = metrics.quantile([1,2,3,4], p=0.5, a=1, b=-1, c=0, d=1)
        self.assertEqual(v, 2.5)
        # Assert 3.0 (discontinuous sample).
        v = metrics.quantile([1,2,3,4], p=0.5, a=0.5, b=0, c=1, d=0)
        self.assertEqual(v, 3.0)
        return "pattern.metrics.quantile()"
    
    def test_boxplot(self):
        # Different a,b,c,d quantile parameters produce different results.
        # By approximation, assert (53, 79.5, 84.5, 92, 98).
        a = [79,53,82,91,87,98,80,93]
        v = metrics.boxplot(a)
        self.assertEqual(v[0], min(a))
        self.assertTrue(abs(v[1] - 79.5) <= 0.5)
        self.assertTrue(abs(v[2] - metrics.median(a)) <= 0.5)
        self.assertTrue(abs(v[3] - 92.0) <= 0.5)
        self.assertEqual(v[4], max(a))
        print "pattern.metrics.boxplot()"

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProfiling))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestStringFunctions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestStatistics))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())