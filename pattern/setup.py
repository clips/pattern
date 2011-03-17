from distutils.core import setup
from distutils.dist import DistributionMetadata

# Patch distutils if it can't cope with the "classifiers" keyword (prior to Python 2.3.0).
if not hasattr(DistributionMetadata, 'classifiers'):
    DistributionMetadata.classifiers = None

setup(
            name = "Pattern",
         version = "1.6",
     description = "Web mining module for Python.",
         license = "BSD",
          author = "Tom De Smedt",
    author_email = "tom@organisms.be",
             url = "http://www.clips.ua.ac.be/pages/pattern",
     package_dir = {"pattern": "../pattern"},
        packages = [
        "pattern",
        "pattern.web", 
        "pattern.web.cache", 
        "pattern.web.feed", 
        "pattern.web.imap", 
        "pattern.web.json", 
        "pattern.web.soup",
        "pattern.en", 
        "pattern.en.inflect", 
        "pattern.en.parser", 
        "pattern.en.wordnet", 
        "pattern.en.wordnet.pywordnet",
        "pattern.vector",
        "pattern.vector.wordlists",
        "pattern.graph"
    ],
    package_data = {
        "pattern.web.cache"            : ["tmp/*"], 
        "pattern.web.feed"             : ["*"], 
        "pattern.web.json"             : ["*"], 
        "pattern.web.soup"             : ["*"],
        "pattern.en.inflect"           : ["*.txt"], 
        "pattern.en.parser"            : ["*.txt"], 
        "pattern.en.wordnet"           : ["*.txt", "dict/*"], 
        "pattern.en.wordnet.pywordnet" : ["*"],
        "pattern.vector"               : ["*.txt"], 
        "pattern.vector.wordlists"     : ["*.txt"], 
        "pattern.graph"                : ["js/*.js"],
        "pattern" : [
            "*.txt", 
            "examples/*/*.py", 
            "examples/*/*/*.txt"
        ]
    },
    py_modules = [
        "pattern.metrics",
        "pattern.table", 
        "pattern.search"
    ],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: HTML",
        "Natural Language :: English"
    ]
)