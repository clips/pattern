import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.en import wordnet
from pattern.en import NOUN, VERB

# WordNet is a lexical database for the English language. 
# It groups English words into sets of synonyms called synsets, provides short, general definitions, 
# and records the various semantic relations between these synonym sets.

# For a given word, WordNet yields a list of synsets that
# represent different "senses" in which the word can be understood.
for synset in wordnet.synsets("train", pos=NOUN):
    print("Description: %s" % synset.gloss)       # Definition string.
    print("   Synonyms: %s" % synset.senses)      # List of synonyms in this sense.
    print("   Hypernym: %s" % synset.hypernym)    # Synset one step higher in the semantic network.
    print("   Hyponyms: %s" % synset.hyponyms())  # List of synsets that are more specific.
    print("   Holonyms: %s" % synset.holonyms())  # List of synsets of which this synset is part/member.
    print("   Meronyms: %s" % synset.meronyms())  # List of synsets that are part/member of this synset.
    print("")

# What is the common ancestor (hypernym) of "cat" and "dog"?
a = wordnet.synsets("cat")[0]
b = wordnet.synsets("dog")[0]
print("Common ancestor: %s" % wordnet.ancestor(a, b))
print("")

# Synset.hypernyms(recursive=True) returns all parents of the synset,
# Synset.hyponyms(recursive=True) returns all children,
# optionally up to a given depth.
# What kind of animal nouns are also verbs?
synset = wordnet.synsets("animal")[0]
for s in synset.hyponyms(recursive=True, depth=2):
    for word in s.senses:
        if word in wordnet.VERBS:
            print("%s => %s" % (word, wordnet.synsets(word, pos=VERB)))

# Synset.similarity() returns an estimate of the semantic similarity to another synset,
# based on Lin's semantic distance measure and Resnik Information Content.
# Lower values indicate higher similarity.
a = wordnet.synsets("cat")[0]  # river, bicycle
s = []
for word in ["poodle", "cat", "boat", "carrot", "rocket",
             "spaghetti", "idea", "grass", "education",
             "lake", "school", "balloon", "lion"]:
    b = wordnet.synsets(word)[0]
    s.append((a.similarity(b), word))
print("")
print("Similarity to %s: %s" % (a.senses[0], sorted(s)))
print("")
