from __future__ import print_function

from ast import parse
import os
from setuptools import setup
from sys import version_info


def version():
    """Return version string from pattern/__init__.py."""
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           'pattern',
                           '__init__.py')) as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return parse(line).body[0].value.s

install_requires = ["beautifulsoup4",
                    "cherrypy",
                    "docx",
                    "feedparser",
                    "pdfminer" if version_info[0] == 2 else "pdfminer3k",
                    "simplejson"]

setup(
    name="pattern",
    version=version(),
    description="Web mining module for Python.",
    license="BSD",
    author="Tom De Smedt",
    author_email="tom@organisms.be",
    url="http://www.clips.ua.ac.be/pages/pattern",
    packages=["pattern",
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
    package_data={"pattern": ["*.js"],
                  "pattern.web.cache": ["tmp/*"],
                  "pattern.web.locale": ["__init__.py"],
                  "pattern.text.de": ["*.txt", "*.xml"],
                  "pattern.text.en": ["*.txt", "*.xml", "*.slp"],
                  "pattern.text.en.wordlist": ["*.txt"],
                  "pattern.text.en.wordnet": ["*.txt", "dict/*"],
                  "pattern.text.en.wordnet.pywordnet": ["*.py"],
                  "pattern.text.es": ["*.txt", "*.xml"],
                  "pattern.text.fr": ["*.txt", "*.xml"],
                  "pattern.text.it": ["*.txt", "*.xml"],
                  "pattern.text.nl": ["*.txt", "*.xml"],
                  "pattern.vector": ["*.txt"],
                  "pattern.vector.svm": ["*.txt", "libsvm-3.11/*", "libsvm-3.17/*", "liblinear-1.93/*"],
                  "pattern.graph": ["*.js", "*.csv"],
                  "pattern.server": ["static/*"],
    },
    py_modules=["pattern.metrics",
                "pattern.text.search",
                "pattern.text.tree"
    ],
    classifiers=[
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
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
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
    zip_safe=True,
    install_requires=install_requires
)
