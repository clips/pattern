import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

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
# The article() function returns the indefinite article (a/an) for a given noun.
# The definitive article is always "the". The plural indefinite is "some".
print(article("bear") + " bear")
print("")

# The referenced() function returns a string with article() prepended to the given word.
# The referenced() funtion is non-trivial, as demonstrated with the exception words below:
for word in ["hour", "one-liner", "European", "university", "owl", "yclept", "year"]:
    print(referenced(word))
print("")

# PLURALIZATION
# -------------
# The pluralize() function returns the plural form of a singular noun (or adjective).
# The algorithm is robust and handles about 98% of exceptions correctly:
for word in ["part-of-speech", "child", "dog's", "wolf", "bear", "kitchen knife"]:
    print(pluralize(word))
print(pluralize("octopus", classical=True))
print(pluralize("matrix", classical=True))
print(pluralize("matrix", classical=False))
print(pluralize("my", pos=ADJECTIVE))
print("")

# SINGULARIZATION
# ---------------
# The singularize() function returns the singular form of a plural noun (or adjective).
# It is slightly less robust than the pluralize() function.
for word in ["parts-of-speech", "children", "dogs'", "wolves", "bears", "kitchen knives", 
             "octopodes", "matrices", "matrixes"]:
    print(singularize(word))
print(singularize("our", pos=ADJECTIVE))
print("")

# COMPARATIVE & SUPERLATIVE ADJECTIVES
# ------------------------------------
# The comparative() and superlative() functions give the comparative/superlative form of an adjective.
# Words with three or more syllables are simply preceded by "more" or "most".
for word in ["gentle", "big", "pretty", "hurt", "important", "bad"]:
    print("%s => %s => %s" % (word, comparative(word), superlative(word)))
print("")

# VERB CONJUGATION
# ----------------
# The lexeme() function returns a list of all possible verb inflections.
# The lemma() function returns the base form (infinitive) of a verb.
print("lexeme: %s" % lexeme("be"))
print("lemma: %s" % lemma("was"))
print("")

# The conjugate() function inflects a verb to another tense.
# You can supply: 
# - tense : INFINITIVE, PRESENT, PAST, 
# - person: 1, 2, 3 or None, 
# - number: SINGULAR, PLURAL,
# - mood  : INDICATIVE, IMPERATIVE,
# - aspect: IMPERFECTIVE, PROGRESSIVE.
# The tense can also be given as an abbreviated alias, e.g., 
# inf, 1sg, 2sg, 3sg, pl, part, 1sgp, 2sgp, 3sgp, ppl, ppart.
from pattern.en import PRESENT, SINGULAR
print(conjugate("being", tense=PRESENT, person=1, number=SINGULAR, negated=False))
print(conjugate("being", tense="1sg", negated=False))
print("")

# Prefer the full constants for code that will be reused/shared.

# The tenses() function returns a list of all tenses for the given verb form.
# Each tense is a tuple of (tense, person, number, mood, aspect).
# For example: tenses("are") => [('present', 2, 'plural', 'indicative', 'imperfective'), ...]
# You can then check if a tense constant is in the list.
# This will also work with aliases, even though they are not explicitly in the list.
from pattern.en import PRESENT, PLURAL
print(tenses("are"))
print((PRESENT, 1, PLURAL) in tenses("are"))
print("pl" in tenses("are"))