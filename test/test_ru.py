# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
import random
import subprocess

from pattern import text
from pattern import ru

from io import open

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------


class TestSpelling(unittest.TestCase):

    def test_spelling(self):
        i = j = 0.0
        from pattern.db import Datasheet
        for correct, wrong in Datasheet.load(os.path.join(PATH, "corpora", "spelling-ru.csv")):
            for w in wrong.split(" "):
                suggested = ru.suggest(w)
                if suggested[0][0] == correct:
                    i += 1
                else:
                    j += 1
        self.assertTrue(i / (i + j) > 0.65)
        print("pattern.ru.suggest()")

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSpelling))
    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
