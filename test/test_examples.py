"""This creates a TestExamples test class and adds a method for each python
file in the examples directory.

examples/01-web/01-google.py -> TestExamples.test_01web_01google

The test itself calls this python file, and asserts that it exits with exit
code 0 (i.e. it was successful). If it wasn't it raises an AssertionError
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
        # todo capture output
        p = Popen([PYTHON, example_py], stderr=PIPE, stdout=PIPE)
        out, err = p.communicate()

        # TODO remove this, currently a couple of examples give HTTPErrors:
        # test_01web_02googletranslate HTTP401Authentication
        # test_01web_14flickr HTTP403Forbidden
        if p.returncode != 0 and ("raise HTTP" in err or "raise URLTimeout" in err):
            raise unittest.SkipTest("Test skipped due to an HTTPError or URLTimeout")

        if p.returncode != 0 and "translate API is a paid service" in err:
            raise unittest.SkipTest("Test skipped as translate API costs")

        if p.returncode != 0 and "NotImplementedError" in err and "2.6" in err:
            raise unittest.SkipTest("Example is not python 2.6 compatible")

        assert (p.returncode == 0), "%s exited with bad status %s\n\n%s" % (
            example_py, p.returncode, err)
    _test.__name__ = test_name

    setattr(TestExamples, test_name, _test)
    del _test

if __name__ == '__main__':
    unittest.main()
