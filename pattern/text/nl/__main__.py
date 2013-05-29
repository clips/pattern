#### PATTERN | NL | PARSER COMMAND-LINE ############################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# In Python 2.7+ modules invoked from the command line  will look for a __main__.py.

from __init__ import commandline, parse
commandline(parse)