import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.en import article, referenced
from pattern.en import pluralize, singularize
from pattern.en import comparative, superlative
from pattern.en import conjugate, lemma, lexeme, tenses
from pattern.en import NOUN, VERB, ADJECTIVE

# The en module has a range of tools for word inflection:
# guessing the indefinite article of a word (a/an?),
# pluralization and singularization, comparative and superlative adjectives, verb conjugation.

# INDEFINITE ARTICLE
# ------------------
# The article() command returns the indefinite article (a/an) for a given noun.
# The definitive article is always "the". The plural indefinite is "some".
print article("bear"), "bear"
print

# The referenced() command returns a string with article() prepended to the given word.
# The referenced() command is non-trivial, as demonstrated with the exception words below:
for word in ["hour", "one-liner", "European", "university", "owl", "yclept", "year"]:
    print referenced(word)
print
print

# PLURALIZATION
# -------------
# The pluralize() command returns the plural form of a singular noun (or adjective).
# The algorithm is robust and handles about 98% of exceptions correctly:
for word in ["part-of-speech", "child", "dog's", "wolf", "bear", "kitchen knife"]:
    print pluralize(word)
print pluralize("octopus", classical=True)
print pluralize("matrix", classical=True)
print pluralize("matrix", classical=False)
print pluralize("my", pos=ADJECTIVE)
print

# SINGULARIZATION
# ---------------
# The singularize() command returns the singular form of a plural noun (or adjective).
# It is slightly less robust than the pluralize() command.
for word in ["parts-of-speech", "children", "dogs'", "wolves", "bears", "kitchen knives", 
             "octopodes", "matrices", "matrixes"]:
    print singularize(word)
print singularize("our", pos=ADJECTIVE)
print
print

# COMPARATIVE & SUPERLATIVE ADJECTIVES
# ------------------------------------
# The comparative() and superlative() commands give the comparative/superlative form of an adjective.
# Words with three or more syllables are simply preceded by "more" or "most".
for word in ["gentle", "big", "pretty", "hurt", "important", "bad"]:
    print word, "=>", comparative(word), "=>", superlative(word)
print
print

# VERB CONJUGATION
# ----------------
# The lexeme() command returns a list of all possible verb inflections.
# The lemma() command returns the base form (infinitive) of a verb.
print "lexeme:", lexeme("be")
print "lemma:", lemma("was")

# The conjugate() command inflects a verb to another tense.
# The tense can be given as a constant, e.g. 
# INFINITIVE, PRESENT_1ST_PERSON_SINGULAR PRESENT_PLURAL, PAST_PARTICIPLE, ...
# or as an abbreviated alias: inf, 1sg, 2sg, 3sg, pl, part, 1sgp, 2sgp, 3sgp, ppl, ppart.
print conjugate("being", tense="1sg", negated=False)

# Prefer the full constants for code that will be reused/shared.

# The tenses() command returns a list of all tenses for the given verb form.
# For example: tenses("are") => ['present 2nd person singular', 'present plural']
# You can then check if a tense constant is in the list.
# This will also work with aliases, even though they are not explicitly in the list.
from pattern.en import PRESENT_PLURAL
print tenses("are")
print PRESENT_PLURAL in tenses("are")
print "pl" in tenses("are")
