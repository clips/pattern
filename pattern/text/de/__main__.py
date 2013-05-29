#### PATTERN | DE | RULE-BASED SHALLOW PARSER ######################################################
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# In Python 2.7+ modules invoked from the command line  will look for a __main__.py.

from __init__ import parse, commandline
commandline(parse)