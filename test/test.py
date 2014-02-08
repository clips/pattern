import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest

import test_metrics
import test_web
import test_db
import test_de
import test_en
import test_es
import test_fr
import test_it
import test_nl
import test_text
import test_search
import test_vector
import test_graph

#---------------------------------------------------------------------------------------------------
# Run all tests.
# pattern.db tests require a valid username and password for MySQL.
# pattern.web tests require a working internet connection 
# and API license keys (see pattern.web.api.py) for Google and Yahoo API's.

def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_metrics.suite())
    suite.addTest(test_web.suite())
    suite.addTest(test_db.suite(host="localhost", port=3306, username="root", password=""))
    suite.addTest(test_de.suite())
    suite.addTest(test_en.suite())
    suite.addTest(test_es.suite())
    suite.addTest(test_fr.suite())
    suite.addTest(test_it.suite())
    suite.addTest(test_nl.suite())
    suite.addTest(test_text.suite())
    suite.addTest(test_search.suite())
    suite.addTest(test_vector.suite())
    suite.addTest(test_graph.suite())
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())