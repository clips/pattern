#### PATTERN | IT | PARSER COMMAND-LINE ############################################################
# In Python 2.7+ modules invoked from the command line  will look for a __main__.py.

from __init__ import parse, commandline
commandline(parse)