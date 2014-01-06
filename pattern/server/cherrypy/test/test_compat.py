import unittest

import nose

from cherrypy import _cpcompat as compat

class StringTester(unittest.TestCase):
    def test_ntob_non_native(self):
        """
        ntob should raise an Exception on unicode.
        (Python 2 only)

        See #1132 for discussion.
        """
        if compat.py3k:
            raise nose.SkipTest("Only useful on Python 2")
        self.assertRaises(Exception, compat.ntob, unicode('fight'))
