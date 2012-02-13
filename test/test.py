import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest

import test_db
import test_en
import test_metrics
import test_nl
import test_search
import test_vector
import test_web

#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_db.suite())
    suite.addTest(test_en.suite())
    suite.addTest(test_metrics.suite())
    suite.addTest(test_nl.suite())
    suite.addTest(test_search.suite())
    suite.addTest(test_vector.suite())
    suite.addTest(test_web.suite())
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())