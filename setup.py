from distutils.core import setup
from distutils.dist import DistributionMetadata

# Patch distutils if it can't cope with the "classifiers" keyword (prior to Python 2.3.0).
if not hasattr(DistributionMetadata, 'classifiers'):
    DistributionMetadata.classifiers = None

setup(
            name = "Pattern",
         version = "2.3",
     description = "Web mining module for Python.",
         license = "BSD",
          author = "Tom De Smedt",
    author_email = "tom@organisms.be",
             url = "http://www.clips.ua.ac.be/pages/pattern",
        packages = [
        "pattern",
        "pattern.web", 
        "pattern.web.cache", 
        "pattern.web.feed", 
        "pattern.web.imap", 
        "pattern.web.json", 
        "pattern.web.oauth", 
        "pattern.web.pdf", 
        "pattern.web.soup",
        "pattern.db", 
        "pattern.text",
        "pattern.text.en",
        "pattern.text.en.inflect", 
        "pattern.text.en.parser", 
        "pattern.text.en.wordlist",
        "pattern.text.en.wordnet", 
        "pattern.text.en.wordnet.pywordnet",
        "pattern.text.nl",
        "pattern.text.nl.parser",
        "pattern.text.nl.inflect",
        "pattern.vector",
        "pattern.vector.svm",
        "pattern.graph"
    ],
    package_data = {
        "pattern"                   : ["*.js"],
        "pattern.web.cache"         : ["tmp/*"],
        "pattern.web.feed"          : ["*"],
        "pattern.web.json"          : ["*"],
        "pattern.web.pdf"           : ["*.txt", "cmap/*"],
        "pattern.web.soup"          : ["*"],
        "pattern.text.en.inflect"   : ["*.txt"],
        "pattern.text.en.parser"    : ["*.txt", "*.xml"],
        "pattern.text.en.wordlists" : ["*.txt"],
        "pattern.text.en.wordnet"   : ["*.txt", "dict/*"],
        "pattern.text.en.wordnet.pywordnet" : ["*"],
        "pattern.text.nl.parser"    : ["*", "*.xml"],
        "pattern.text.nl.inflect"   : ["*.txt"],
        "pattern.vector"            : ["*.txt"],
        "pattern.vector.svm"        : ["*"],
        "pattern.graph"             : ["*.js"],
    },
    py_modules = [
        "pattern.metrics",
        "pattern.table", 
        "pattern.text.search"
    ],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: Dutch",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: HTML"
    ]
)