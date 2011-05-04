PATTERN
=======

Pattern is a web mining module for the Python programming language. It bundles tools for data retrieval (Google + Twitter + Wikipedia API, web spider, HTML DOM parser), text analysis (rule-based shallow parser, WordNet interface, syntactical + semantical n-gram search algorithm, tf-idf + cosine similarity + LSA metrics) and data visualization (graph networks). The module is bundled with 30+ example scripts.

VERSION
=======

1.7

LICENSE
=======

BSD, see LICENSE.txt for further details.

INSTALLATION
============

Pattern is written for Python 2.4+ (no support for Python 3 yet). The module has no external dependencies except when using LSA in the vector module, which requires NumPy (installed by default on Mac OS X). To install it so that the module is available in all your scripts, open a terminal and do:
> cd pattern
> python setup.py install

If for any reason this does not work, you can make Python aware of the module in three ways:
- Put the pattern folder in the same folder as your script.
- Put the pattern folder in the standard location for modules so it is available to all scripts:
  c:\python25\Lib\site-packages\ (Windows),
  /Library/Python/2.5/site-packages/ (Mac OS X),   /usr/lib/python2.5/site-packages/ (Unix).
- Add the location of the module to sys.path in your script, before importing it:
  >>> MODULE = '/users/tom/desktop/pattern'
  >>> import sys; if MODULE not in sys.path: sys.path.append(MODULE)
  >>> from pattern.en import parse, Sentence

DOCUMENTATION
=============

http://www.clips.ua.ac.be/pages/pattern

ACKNOWLEDGEMENTS
================

Authors: 
- Tom De Smedt (tom@organisms.be)
- Walter Daelemans

Contributing authors:
- Frederik De Bleser
- Thomas Crombez