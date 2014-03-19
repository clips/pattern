#### PATTERN #######################################################################################

import sys
import os

from setuptools import setup

from pattern import __version__

#---------------------------------------------------------------------------------------------------
# "python setup.py zip" will create the zipped distribution and checksum.

if sys.argv[-1] == "zip":
    import zipfile
    import hashlib
    import codecs
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
                s = codecs.open(f, "r", encoding="utf-8").read().split(d)
                x = codecs.open(f, "w", encoding="utf-8")
                x.write(s[0])
                x.close()
            # Exclude revision history (.git).
            # Exclude development files (.dev).
            if not re.search(r"\.DS|\.git[^i]|\.pyc|\.dev|tmp", f):
                z.write(f, os.path.join("pattern-" + __version__, os.path.relpath(f, p)))
            if f.endswith(os.path.join("web", "api.py")):
                x = codecs.open(f, "w", encoding="utf-8")
                x.write(d.join(s))
                x.close()
    z.close()
    print n
    print hashlib.sha256(open(z.filename).read()).hexdigest()
    sys.exit(0)

#---------------------------------------------------------------------------------------------------
# "python setup.py install" will install /pattern in /site-packages.

setup(
            name = "Pattern",
         version = "2.6",
     description = "Web mining module for Python.",
         license = "BSD",
          author = "Tom De Smedt",
    author_email = "tom@organisms.be",
             url = "http://www.clips.ua.ac.be/pages/pattern",
        packages = [
        "pattern",
        "pattern.web",
        "pattern.web.cache",
        "pattern.web.docx",
        "pattern.web.feed",
        "pattern.web.imap",
        "pattern.web.json",
        "pattern.web.locale",
        "pattern.web.oauth",
        "pattern.web.pdf",
        "pattern.web.soup",
        "pattern.db",
        "pattern.text",
        "pattern.text.de",
        "pattern.text.en",
        "pattern.text.en.wordlist",
        "pattern.text.en.wordnet",
        "pattern.text.en.wordnet.pywordnet",
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
        "pattern.web.docx"        : ["*"],
        "pattern.web.feed"        : ["*"],
        "pattern.web.json"        : ["*"],
        "pattern.web.locale"      : ["*"],
        "pattern.web.pdf"         : ["*.txt", "cmap/*"],
        "pattern.web.soup"        : ["*"],
        "pattern.text.de"         : ["*.txt", "*.xml"],
        "pattern.text.en"         : ["*.txt", "*.xml", "*.slp"],
        "pattern.text.en.wordlist": ["*.txt"],
        "pattern.text.en.wordnet" : ["*.txt", "dict/*"],
        "pattern.text.en.wordnet.pywordnet": ["*"],
        "pattern.text.es"         : ["*.txt", "*.xml"],
        "pattern.text.fr"         : ["*.txt", "*.xml"],
        "pattern.text.it"         : ["*.txt", "*.xml"],
        "pattern.text.nl"         : ["*.txt", "*.xml"],
        "pattern.vector"          : ["*.txt"],
        "pattern.vector.svm"      : ["*.txt", "libsvm-3.11/*", "libsvm-3.17/*", "liblinear-1.93/*"],
        "pattern.graph"           : ["*.js", "*.csv"],
        "pattern.server"          : ["static/*", "cherrypy/cherrypy/*.*", 
                                                 "cherrypy/cherrypy/*/*", 
                                                 "cherrypy/cherrypy/cherryd"],
    },
    py_modules = [
        "pattern.metrics",
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
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: HTML"
    ],
    zip_safe = False
)
