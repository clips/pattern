#### PATTERN | FR | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# A set of rule-based tools for French word inflection:
# - comparative and superlative of adjectives.

import re
import os

try:
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"

# Accuracy (measured on CELEX English morphology word forms):
# 95% pluralize()
# 96% singularize()
# 95% _parse_lemma()
# 96% _parse_lexeme()

#### ATTRIBUTIVE & PREDICATIVE #####################################################################

def attributive(adjective):
    return adjective

def predicative(adjective):
    return adjective
