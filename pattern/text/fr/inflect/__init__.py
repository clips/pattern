#### PATTERN | FR | INFLECT ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2012 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################
# A set of rule-based tools for French word inflection:
# - predicative and attributive of adjectives.

import re
import os

try:
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

VERB, NOUN, ADJECTIVE, ADVERB = "VB", "NN", "JJ", "RB"

# Accuracy (measured on Lexique French morphology word forms):
# 95% predicative()

#### ATTRIBUTIVE & PREDICATIVE #####################################################################

def attributive(adjective):
    return adjective

def predicative(adjective): 
    """ Returns the predicative adjective (lowercase): belles => beau.
    """
    w = adjective.lower()
    if w.endswith(("ais", "ois")):
        return w
    if w.endswith((u"és", u"ée", u"ées")):
        return w.rstrip("es")
    if w.endswith(("que", "ques")):
        return w.rstrip("s")
    if w.endswith(("nts", "nte", "ntes")):
        return w.rstrip("es")
    if w.endswith("eaux"):
        return w.rstrip("x")
    if w.endswith(("aux", "ale", "ales")):
        return w.rstrip("uxles") + "l"
    if w.endswith(("rteuse", "rteuses", "ailleuse")):
        return w.rstrip("es") + "r"
    if w.endswith(("euse", "euses")):
        return w.rstrip("es") + "x"
    if w.endswith(("els", "elle", "elles")):
        return w.rstrip("les") + "el"
    if w.endswith(("ifs", "ive", "ives")):
        return w.rstrip("es")[:-2] + "if"
    if w.endswith(("is", "ie", "ies")):
        return w.rstrip("es")
    if w.endswith(("enne", "ennes")):
        return w.rstrip("nes") + "en"
    if w.endswith(("onne", "onnes")):
        return w.rstrip("nes") + "n"
    if w.endswith(("igne", "ignes", "ingue", "ingues")):
        return w.rstrip("s")
    if w.endswith((u"ène", u"ènes")):
        return w.rstrip("s")
    if w.endswith(("ns", "ne", "nes")):
        return w.rstrip("es")
    if w.endswith(("ite", "ites")):
        return w.rstrip("es")
    if w.endswith(("is", "ise", "ises")):
        return w.rstrip("es") + "s"
    if w.endswith(("rice", "rices")):
        return w.rstrip("rices") + "eur"
    if w.endswith(("iers", u"ière", u"ières")):
        return w.rstrip("es")[:-3] + "ier"
    if w.endswith(("ette", "ettes")):
        return w.rstrip("tes") + "et"
    if w.endswith(("rds", "rde", "rdes")):
        return w.rstrip("es")
    if w.endswith(("nds", "nde", "ndes")):
        return w.rstrip("es")
    if w.endswith(("us", "ue", "ues")):
        return w.rstrip("es")
    return w.rstrip("s")