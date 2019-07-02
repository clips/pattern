#### PATTERN #######################################################################################

from __future__ import print_function

import sys
import os

from io import open

from setuptools import setup

from pattern import __version__

#---------------------------------------------------------------------------------------------------
# "python setup.py zip" will create the zipped distribution and checksum.

if sys.argv[-1] == "zip":

    import zipfile
    import hashlib
    import re

    n = "pattern-%s.zip" % __version__
    p = os.path.join(os.path.dirname(os.path.realpath(__file__)))
    z = zipfile.ZipFile(os.path.join(p, "..", n), "w", zipfile.ZIP_DEFLATED)
    for root, folders, files in os.walk(p):
        for f in files:
            f = os.path.join(root, f)
            # Exclude private settings.
            if f.endswith(os.path.join("web", "api.py")):
                d = "#--- PRIVATE"
                s = open(f, "r", encoding="utf-8").read().split(d)
                x = open(f, "w", encoding="utf-8")
                x.write(s[0])
                x.close()
            # Exclude revision history (.git).
            # Exclude development files (.dev).
            if not re.search(r"\.DS|\.git[^i]|\.pyc|\.dev|tmp", f):
                z.write(f, os.path.join("pattern-" + __version__, os.path.relpath(f, p)))
            if f.endswith(os.path.join("web", "api.py")):
                x = open(f, "w", encoding="utf-8")
                x.write(d.join(s))
                x.close()
    z.close()
    print(n)
    print(hashlib.sha256(open(z.filename).read()).hexdigest())
    sys.exit(0)

#---------------------------------------------------------------------------------------------------
# "python setup.py install" will install /pattern in /site-packages.

setup(
            name = "Pattern",
         version = "3.6",
     description = "Web mining module for Python.",
         license = "BSD",
          author = "Tom De Smedt",
    author_email = "tom@organisms.be",
             url = "http://www.clips.ua.ac.be/pages/pattern",
        packages = [
        "pattern",
        "pattern.web",
        "pattern.web.cache",
        "pattern.web.imap",
        "pattern.web.locale",
        "pattern.web.oauth",
        "pattern.db",
        "pattern.text",
        "pattern.text.de",
        "pattern.text.en",
        "pattern.text.en.wordlist",
        "pattern.text.en.wordnet",
        "pattern.text.ru",
        "pattern.text.ru.wordlist",
        "pattern.text.es",
        "pattern.text.fr",
        "pattern.text.it",
        "pattern.text.nl",
        "pattern.vector",
        "pattern.vector.svm",
        "pattern.graph",
        "pattern.server"
    ],
    package_data = {
        "pattern"                 : ["*.js"],
        "pattern.web.cache"       : ["tmp/*"],
        "pattern.web.locale"      : ["*"],
        "pattern.text.de"         : ["*.txt", "*.xml"],
        "pattern.text.en"         : ["*.txt", "*.xml", "*.slp"],
        "pattern.text.en.wordlist": ["*.txt"],
        "pattern.text.en.wordnet" : ["*.txt", "dict/*"],
        "pattern.text.ru": ["*.txt", "*.xml", "*.slp"],
        "pattern.text.ru.wordlist": ["*.txt"],
        "pattern.text.es"         : ["*.txt", "*.xml"],
        "pattern.text.fr"         : ["*.txt", "*.xml"],
        "pattern.text.it"         : ["*.txt", "*.xml"],
        "pattern.text.nl"         : ["*.txt", "*.xml"],
        "pattern.vector"          : ["*.txt"],
        "pattern.vector.svm"      : ["*.txt"],
        "pattern.graph"           : ["*.js", "*.csv"],
        "pattern.server"          : ["static/*"],
    },
    py_modules = [
        "pattern.metrics",
        "pattern.helpers",
        "pattern.text.search",
        "pattern.text.tree"
    ],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: Dutch",
        "Natural Language :: English",
        "Natural Language :: French",
        "Natural Language :: German",
        "Natural Language :: Italian",
        "Natural Language :: Spanish",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: HTML"
    ],
    install_requires = [
        "future",
        "backports.csv",
        "beautifulsoup4",
        "lxml",
        "feedparser",
        "pdfminer" if sys.version < "3" else "pdfminer.six",
        "numpy",
        "scipy",
        "nltk",
        "python-docx",
        "cherrypy",
        "requests"
    ],
    zip_safe = False
)
