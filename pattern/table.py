#### PATTERN | EN | TABLE ##########################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

# This module is deprecated.
# Since version 2.1, Table is renamed to Datasheet as part of pattern.db.

from db import Datasheet, ALL, uid, pprint
from db import Date, date, time, NOW
from db import decode_utf8, encode_utf8, order, avg, variance, stdev

class Table(Datasheet):
    pass

def flip(table):
    return table.copy(rows=table.columns)

def index(list):
    n = len(list)
    return dict((v, n-i-1) for i, v in enumerate(reversed([x for x in list])))