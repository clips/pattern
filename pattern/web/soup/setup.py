from distutils.core import setup
import unittest
import warnings
warnings.filterwarnings("ignore", "Unknown distribution option")

import sys
# patch distutils if it can't cope with the "classifiers" keyword
if sys.version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

from BeautifulSoup import __version__

#Make sure all the tests complete.
import BeautifulSoupTests
loader = unittest.TestLoader()
result = unittest.TestResult()
suite = loader.loadTestsFromModule(BeautifulSoupTests)
suite.run(result)
if not result.wasSuccessful():
    print "Unit tests have failed!"
    for l in result.errors, result.failures:
        for case, error in l:
            print "-" * 80
            desc = case.shortDescription()
            if desc:
                print desc
            print error        
    print '''If you see an error like: "'ascii' codec can't encode character...", see\nthe Beautiful Soup documentation:\n http://www.crummy.com/software/BeautifulSoup/documentation.html#Why%20can't%20Beautiful%20Soup%20print%20out%20the%20non-ASCII%20characters%20I%20gave%20it?'''
    print "This might or might not be a problem depending on what you plan to do with\nBeautiful Soup."
    if sys.argv[1] == 'sdist':
        print
        print "I'm not going to make a source distribution since the tests don't pass."
        sys.exit(1)

setup(name="BeautifulSoup",
      version=__version__,
      py_modules=['BeautifulSoup', 'BeautifulSoupTests'],
      description="HTML/XML parser for quick-turnaround applications like screen-scraping.",
      author="Leonard Richardson",
      author_email = "leonardr@segfault.org",
      long_description="""Beautiful Soup parses arbitrarily invalid SGML and provides a variety of methods and Pythonic idioms for iterating and searching the parse tree.""",
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: Python Software Foundation License",
                   "Programming Language :: Python",
                   "Topic :: Text Processing :: Markup :: HTML",
                   "Topic :: Text Processing :: Markup :: XML",
                   "Topic :: Text Processing :: Markup :: SGML",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
      url="http://www.crummy.com/software/BeautifulSoup/",
      license="BSD",
      download_url="http://www.crummy.com/software/BeautifulSoup/download/"
      )
    
    # Send announce to:
    #   python-announce@python.org
    #   python-list@python.org
