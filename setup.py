from distutils.core import setup
from distutils.dist import DistributionMetadata

# Patch distutils if it can't cope with the "classifiers" keyword (prior to Python 2.3.0).
if not hasattr(DistributionMetadata, 'classifiers'):
    DistributionMetadata.classifiers = None

setup(
            name = "Pattern",
         version = "2.1",
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
        "pattern.en", 
        "pattern.en.inflect", 
        "pattern.en.parser", 
        "pattern.en.wordlist",
        "pattern.en.wordnet", 
        "pattern.en.wordnet.pywordnet",
        "pattern.nl",
        "pattern.nl.parser",
        "pattern.nl.inflect",
        "pattern.vector",
        "pattern.graph"
    ],
    package_data = {
        "pattern"                      : ["*.js"],
        "pattern.web.cache"            : ["tmp/*"],
        "pattern.web.feed"             : ["*"],
        "pattern.web.json"             : ["*"],
        "pattern.web.pdf"              : ["*.txt", "cmap/*"],
        "pattern.web.soup"             : ["*"],
        "pattern.en.inflect"           : ["*.txt"],
        "pattern.en.parser"            : ["*.txt", "*.xml"],
        "pattern.en.wordlists"         : ["*.txt"],
        "pattern.en.wordnet"           : ["*.txt", "dict/*"],
        "pattern.en.wordnet.pywordnet" : ["*"],
        "pattern.nl.parser"            : ["*", "*.xml"],
        "pattern.nl.inflect"           : ["*.txt"],
        "pattern.vector"               : ["*.txt"],
        "pattern.graph"                : ["js/*.js"],
    },
    py_modules = [
        "pattern.metrics",
        "pattern.table", 
        "pattern.search"
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
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: HTML"
    ]
)