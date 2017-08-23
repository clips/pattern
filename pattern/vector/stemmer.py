##### PATTERN | VECTOR | PORTER STEMMER ############################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# The Porter2 stemming algorithm (or "Porter stemmer") is a process for removing the commoner
# morphological and inflexional endings from words in English.
# Its main use is as part of a term normalisation process that is usually done
# when setting up Information Retrieval systems.

# Reference:
# C.J. van Rijsbergen, S.E. Robertson and M.F. Porter, 1980.
# "New models in probabilistic information retrieval."
# London: British Library. (British Library Research and Development Report, no. 5587).
#
# http://tartarus.org/~martin/PorterStemmer/

# Comments throughout the source code were taken from:
# http://snowball.tartarus.org/algorithms/english/stemmer.html

from __future__ import unicode_literals
from __future__ import division

import re

from builtins import str, bytes, dict, int
from builtins import object, range

#---------------------------------------------------------------------------------------------------
# Note: this module is optimized for performance.
# There is little gain in using more regular expressions.

VOWELS = ["a", "e", "i", "o", "u", "y"]
DOUBLE = ["bb", "dd", "ff", "gg", "mm", "nn", "pp", "rr", "tt"]
VALID_LI = ["b", "c", "d", "e", "g", "h", "k", "m", "n", "r", "t"]


def is_vowel(s):
    return s in VOWELS


def is_consonant(s):
    return s not in VOWELS


def is_double_consonant(s):
    return s in DOUBLE


def is_short_syllable(w, before=None):
    """ A short syllable in a word is either:
        - a vowel followed by a non-vowel other than w, x or Y and preceded by a non-vowel
        - a vowel at the beginning of the word followed by a non-vowel. 
        Checks the three characters before the given index in the word (or entire word if None).
    """
    if before is not None:
        i = before < 0 and len(w) + before or before
        return is_short_syllable(w[max(0, i - 3):i])
    if len(w) == 3 and is_consonant(w[0]) and is_vowel(w[1]) and is_consonant(w[2]) and w[2] not in "wxY":
        return True
    if len(w) == 2 and is_vowel(w[0]) and is_consonant(w[1]):
        return True
    return False


def is_short(w):
    """ A word is called short if it consists of a short syllable preceded by zero or more consonants. 
    """
    return is_short_syllable(w[-3:]) and len([ch for ch in w[:-3] if ch in VOWELS]) == 0

# A point made at least twice in the literature is that words beginning with gener-
# are overstemmed by the Porter stemmer:
# generate => gener, generically => gener
# Moving the region one vowel-consonant pair to the right fixes this:
# generate => generat, generically => generic
overstemmed = ("gener", "commun", "arsen")

RE_R1 = re.compile(r"[aeiouy][^aeiouy]")


def R1(w):
    """ R1 is the region after the first non-vowel following a vowel, 
        or the end of the word if there is no such non-vowel. 
    """
    m = RE_R1.search(w)
    if m:
        return w[m.end():]
    return ""


def R2(w):
    """ R2 is the region after the first non-vowel following a vowel in R1, 
        or the end of the word if there is no such non-vowel.
    """
    if w.startswith(tuple(overstemmed)):
        return R1(R1(R1(w)))
    return R1(R1(w))


def find_vowel(w):
    """ Returns the index of the first vowel in the word.
        When no vowel is found, returns len(word).
    """
    for i, ch in enumerate(w):
        if ch in VOWELS:
            return i
    return len(w)


def has_vowel(w):
    """ Returns True if there is a vowel in the given string.
    """
    for ch in w:
        if ch in VOWELS:
            return True
    return False


def vowel_consonant_pairs(w, max=None):
    """ Returns the number of consecutive vowel-consonant pairs in the word.
    """
    m = 0
    for i, ch in enumerate(w):
        if is_vowel(ch) and i < len(w) - 1 and is_consonant(w[i + 1]):
            m += 1
            # An optimisation to stop searching once we reach the amount of <vc> pairs we need.
            if m == max:
                break
    return m

#--- REPLACEMENT RULES -----------------------------------------------------------------------------


def step_1a(w):
    """ Step 1a handles -s suffixes.
    """
    if w.endswith("s"):
        if w.endswith("sses"):
            return w[:-2]
        if w.endswith("ies"):
            # Replace by -ie if preceded by just one letter,
            # otherwise by -i (so ties => tie, cries => cri).
            return len(w) == 4 and w[:-1] or w[:-2]
        if w.endswith(("us", "ss")):
            return w
        if find_vowel(w) < len(w) - 2:
            # Delete -s if the preceding part contains a vowel not immediately before the -s
            # (so gas and this retain the -s, gaps and kiwis lose it).
            return w[:-1]
    return w


def step_1b(w):
    """ Step 1b handles -ed and -ing suffixes (or -edly and -ingly).
        Removes double consonants at the end of the stem and adds -e to some words.
    """
    if w.endswith("y") and w.endswith(("edly", "ingly")):
        w = w[:-2] # Strip -ly for next step.
    if w.endswith(("ed", "ing")):
        if w.endswith("ied"):
            # See -ies in step 1a.
            return len(w) == 4 and w[:-1] or w[:-2]
        if w.endswith("eed"):
            # Replace by -ee if preceded by at least one vowel-consonant pair.
            return R1(w).endswith("eed") and w[:-1] or w
        for suffix in ("ed", "ing"):
            # Delete if the preceding word part contains a vowel.
            # - If the word ends -at, -bl or -iz add -e (luxuriat => luxuriate).
            # - If the word ends with a double remove the last letter (hopp => hop).
            # - If the word is short, add e (hop => hope).
            if w.endswith(suffix) and has_vowel(w[:-len(suffix)]):
                w = w[:-len(suffix)]
                if w.endswith(("at", "bl", "iz")):
                    return w + "e"
                if is_double_consonant(w[-2:]):
                    return w[:-1]
                if is_short(w):
                    return w + "e"
    return w


def step_1c(w):
    """ Step 1c replaces suffix -y or -Y by -i if preceded by a non-vowel 
        which is not the first letter of the word (cry => cri, by => by, say => say).
    """
    if len(w) > 2 and w.endswith(("y", "Y")) and is_consonant(w[-2]):
        return w[:-1] + "i"
    return w

suffixes2 = [
    ("al", (("ational", "ate"), ("tional", "tion"))),
    ("ci", (("enci", "ence"), ("anci", "ance"))),
    ("er", (("izer", "ize"),)),
    ("li", (("bli", "ble"), ("alli", "al"), ("entli", "ent"), ("eli", "e"), ("ousli", "ous"))),
    ("on", (("ization", "ize"), ("isation", "ize"), ("ation", "ate"))),
    ("or", (("ator", "ate"),)),
    ("ss", (("iveness", "ive"), ("fulness", "ful"), ("ousness", "ous"))),
    ("sm", (("alism", "al"),)),
    ("ti", (("aliti", "al"), ("iviti", "ive"), ("biliti", "ble"))),
    ("gi", (("logi", "log"),))
]


def step_2(w):
    """ Step 2 replaces double suffixes (singularization => singularize).
        This only happens if there is at least one vowel-consonant pair before the suffix.
    """
    for suffix, rules in suffixes2:
        if w.endswith(suffix):
            for A, B in rules:
                if w.endswith(A):
                    return R1(w).endswith(A) and w[:-len(A)] + B or w
    if w.endswith("li") and R1(w)[-3:-2] in VALID_LI:
        # Delete -li if preceded by a valid li-ending.
        return w[:-2]
    return w

suffixes3 = [
    ("e", (("icate", "ic"), ("ative", ""), ("alize", "al"))),
    ("i", (("iciti", "ic"),)),
    ("l", (("ical", "ic"), ("ful", ""))),
    ("s", (("ness", ""),))
]


def step_3(w):
    """ Step 3 replaces -ic, -ful, -ness etc. suffixes.
        This only happens if there is at least one vowel-consonant pair before the suffix.
    """
    for suffix, rules in suffixes3:
        if w.endswith(suffix):
            for A, B in rules:
                if w.endswith(A):
                    return R1(w).endswith(A) and w[:-len(A)] + B or w
    return w

suffixes4 = [
    ("al", ("al",)),
    ("ce", ("ance", "ence")),
    ("er", ("er",)),
    ("ic", ("ic",)),
    ("le", ("able", "ible")),
    ("nt", ("ant", "ement", "ment", "ent")),
    ("e",  ("ate", "ive", "ize")),
    (("m", "i", "s"), ("ism", "iti", "ous"))
]


def step_4(w):
    """ Step 4 strips -ant, -ent etc. suffixes.
        This only happens if there is more than one vowel-consonant pair before the suffix.
    """
    for suffix, rules in suffixes4:
        if w.endswith(suffix):
            for A in rules:
                if w.endswith(A):
                    return R2(w).endswith(A) and w[:-len(A)] or w
    if R2(w).endswith("ion") and w[:-3].endswith(("s", "t")):
        # Delete -ion if preceded by s or t.
        return w[:-3]
    return w


def step_5a(w):
    """ Step 5a strips suffix -e if preceded by multiple vowel-consonant pairs,
        or one vowel-consonant pair that is not a short syllable.
    """
    if w.endswith("e"):
        if R2(w).endswith("e") or R1(w).endswith("e") and not is_short_syllable(w, before=-1):
            return w[:-1]
    return w


def step_5b(w):
    """ Step 5b strips suffix -l if preceded by l and multiple vowel-consonant pairs,
        bell => bell, rebell => rebel.
    """
    if w.endswith("ll") and R2(w).endswith("l"):
        return w[:-1]
    return w

#--- EXCEPTIONS ------------------------------------------------------------------------------------

# Exceptions:
# - in, out and can stems could be seen as stop words later on.
# - Special -ly cases.
exceptions = {
    "skis": "ski",
    "skies": "sky",
    "dying": "die",
    "lying": "lie",
    "tying": "tie",
    "innings": "inning",
    "outings": "outing",
    "cannings": "canning",
    "idly": "idl",
    "gently": "gentl",
    "ugly": "ugli",
    "early": "earli",
    "only": "onli",
    "singly": "singl"
}

# Words that are never stemmed:
uninflected = dict.fromkeys([
    "sky",
    "news",
    "howe",
    "inning", "outing", "canning",
    "proceed", "exceed", "succeed",
    "atlas", "cosmos", "bias", "andes" # not plural forms
], True)

#--- STEMMER ---------------------------------------------------------------------------------------


def case_sensitive(stem, word):
    """ Applies the letter case of the word to the stem:
        Ponies => Poni
    """
    ch = []
    for i in range(len(stem)):
        if word[i] == word[i].upper():
            ch.append(stem[i].upper())
        else:
            ch.append(stem[i])
    return "".join(ch)


def upper_consonant_y(w):
    """ Sets the initial y, or y after a vowel, to Y.
        Of course, y is interpreted as a vowel and Y as a consonant.
    """
    a = []
    p = None
    for ch in w:
        if ch == "y" and (p is None or p in VOWELS):
            a.append("Y")
        else:
            a.append(ch)
        p = ch
    return "".join(a)

# If we stemmed a word once, we can cache the result and reuse it.
# By default, keep a history of a 10000 entries (<500KB).
cache = {}


def stem(word, cached=True, history=10000, **kwargs):
    """ Returns the stem of the given word: ponies => poni.
        Note: it is often taken to be a crude error 
        that a stemming algorithm does not leave a real word after removing the stem. 
        But the purpose of stemming is to bring variant forms of a word together, 
        not to map a word onto its "paradigm" form. 
    """
    stem = word.lower()
    if cached and stem in cache:
        return case_sensitive(cache[stem], word)
    if cached and len(cache) > history: # Empty cache every now and then.
        cache.clear()
    if len(stem) <= 2:
        # If the word has two letters or less, leave it as it is.
        return case_sensitive(stem, word)
    if stem in exceptions:
        return case_sensitive(exceptions[stem], word)
    if stem in uninflected:
        return case_sensitive(stem, word)
    # Mark y treated as a consonant as Y.
    stem = upper_consonant_y(stem)
    for f in (step_1a, step_1b, step_1c, step_2, step_3, step_4, step_5a, step_5b):
        stem = f(stem)
    # Turn any remaining Y letters in the stem back into lower case.
    # Apply the case of the original word to the stem.
    stem = stem.lower()
    stem = case_sensitive(stem, word)
    if cached:
        cache[word.lower()] = stem.lower()
    return stem
