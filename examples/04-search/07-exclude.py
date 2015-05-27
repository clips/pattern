import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.search import match
from pattern.en     import Sentence, parse

# This example demonstrates how to exclude certain words or tags from a constraint.
# It also demonstrates the use of "^",
# for a constraint that can only match the first word.

# We'll use a naive imperative() function as a demonstration.
# Sentences can have different moods: indicative, conditional, imperative, subjunctive.
# The imperative mood is used to give orders, instructions, warnings:
# - "Do your homework!",
# - "You will eat your dinner!".
# It is marked by an infinitive verb, without a "to" preceding it.
# It does not use modal verbs such as "could" and "would":
# "You could eat your dinner!" is not a command but a bubbly suggestion.

# We can create a pattern that scans for infinitive verbs (VB),
# and use "!" to exclude certain words:
# "!could|!would|!should|!to+ VB" = infinitive not preceded by modal or "to".
# This works fine except in one case: if the sentence starts with a verb.
# So we need a second rule "^VB" to catch this.
# Note that the example below contains a third rule: "^do|VB*".
# This catches all sentences that start with a "do" verb regardless if it is infinitive,
# because the parses sometimes tags infinitive "do" incorrectly.

def imperative(sentence):
    for p in ("!could|!would|!should|!to+ VB", "^VB", "^do|VB*"):
        m = match(p, sentence)
        if match(p, sentence) and sentence.string.endswith((".","!")):  # Exclude questions.
            return True
    return False

for s in (
  "Just stop it!",
  "Look out!",
  "Do your homework!",
  "You should do your homework.",
  "Could you stop it.",
  "To be, or not to be."):
    s = parse(s)
    s = Sentence(s)
    print(s)
    print(imperative(s))
    print("")

