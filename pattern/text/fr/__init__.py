#### PATTERN | FR ##################################################################################
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# French linguistical tools using fast regular expressions.

from inflect import \
    predicative, attributive

from parser.sentiment import sentiment, polarity, subjectivity, positive
from parser.sentiment import NOUN, VERB, ADJECTIVE, ADVERB    