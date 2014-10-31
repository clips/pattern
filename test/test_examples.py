"""This creates a TestExamples test class and adds methods for each python
file in the examples directory.

examples/01-web/01-google.py -> TestExamples.test_01web_01google

The test itself calls this python file, and asserts that it exits with exits
status 0 (i.e. it was successful). If it wasn't it raises an AssertionError
which includes stacktrace (from the stderr).

"""

import glob
import os
from subprocess import PIPE, Popen
import sys

from util import unittest, StringIO

PACKAGE_DIR = os.path.realpath(os.path.split(os.path.split(__file__)[0])[0])
PYTHON = sys.executable

examples = os.path.join(PACKAGE_DIR, "examples", "*", "*.py")

class TestExamples(unittest.TestCase):
    pass


for example_py in glob.glob(examples):
    dir_, name = os.path.split(example_py)
    _, section = os.path.split(dir_)

    test_name = ("test_%s_%s" % (section, name)).replace("-", "")[:-3]

    def _test(self, example_py=example_py, test_name=test_name):
        p = Popen([PYTHON, example_py], stderr=PIPE, stdout=PIPE) # todo capture output
        out, err = p.communicate()
        assert (p.returncode == 0), "%s exited with bad status %s\n\n%s" % (example_py, p.returncode, err)
    _test.__name__ = test_name

    setattr(TestExamples, test_name, _test)
    del _test

if __name__ == '__main__':
    unittest.main()
