import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import random

from codecs         import open
from collections    import defaultdict
from pattern.text   import Model
from pattern.vector import shuffled, SLP
from pattern.en     import lexicon, parsetree
from random         import seed

# This example demonstrates how a Perceptron classifier 
# can be used to construct an English language model 
# (i.e., a classifier that predicts part-of-speech tags),
# by learning from a training set of tagged sentences.

# First we need training data: a corpus of manually annotated (= tagged) sentences.
# Typically, Penn Treebank is used, which contains texts from the Wall Street Journal (WSJ).
# In this example we will use the freely available Open American National Corpus (OANC).

print "load training data..."

def corpus(path, encoding="utf-8"):
    """ Yields sentences of (word, tag)-tuples from the given corpus,
        which is a .txt file with a sentence on each line, 
        with slash-encoded tokens (e.g., the/DT cat/NN).
    """
    for s in open(path, encoding=encoding):
        s = map(lambda w:  w.split("/"), s.strip().split(" "))
        s = map(lambda w: (w[0].replace("&slash;", "/"), w[1]), s)
        yield s

# The corpus is included in the Pattern download zip, in pattern/test/corpora:
path = os.path.join(os.path.dirname(__file__), "..", "..", "test", "corpora", "tagged-en-oanc.txt")
data = list(corpus(path))

# A parser is typically based on a lexicon of known words (aka a tag dictionary),
# that contains frequent words and their most frequent part-of-speech tag.
# This approach is fast. However, some words can have more than one tag,
# depending on their context in the sentence (e.g., "a can" vs. "can I").

# When we train a language model (i.e., a classifier),
# we want to make sure that it captures all ambiguity,
# ignoring ambiguous entries in the lexicon,
# handling them with the classifier instead.

# For example, the lexicon in pattern.en will always tag "about" as IN (preposition),
# even though it can also be used as RB (adverb) in about 25% of the cases.

# We will add "about" to the set of words in the lexicon to ignore
# when using a language model. 

print "load training lexicon..."

f = defaultdict(lambda: defaultdict(int)) # {word1: {tag1: count, tag2: count, ...}}
for s in data:
    for w, tag in s:
        f[w][tag] += 1

known, unknown = set(), set()
for w, tags in f.items():
    n = sum(tags.values()) # total count
    m = sorted(tags, key=tags.__getitem__, reverse=True)[0] # most frequent tag
    if float(tags[m]) / n >= 0.97 and n > 1:
        # Words that are always handled by the lexicon.
        known.add(w)
    if float(tags[m]) / n <  0.92 and w in lexicon:
        # Words in the lexicon that should be ignored and handled by the model.
        unknown.add(w)

# A language model is a classifier (e.g., NB, KNN, SVM, SLP)
# trained on words and their context (= words to the left & right in sentence),
# that predicts the part-of-speech tag of unknown words.

# Take a look at the Model class in pattern/text/__init__.py.
# You'll see an internal Model._v() method
# that creates a training vector from a given word and its context,
# using information such as word suffix, first letter (i.e., for proper nouns), 
# the part-of-speech tags of preceding words, surrounding tags, etc.

# Perceptron (SLP, single-layer averaged perceptron) works well for language models.
# Perceptron is an error-driven classifier.
# When given a training example (e.g., tagged word + surrounding words), 
# it will check if it could correctly predict this example.
# If not, it will adjust its weights.
# So the accuracy of the perceptron can be improved significantly
# by training in multiple iterations, averaging out all weights.

# This will take several minutes.
# If you want it to run faster for experimentation,
# use less iterations or less data in the code below:

print "training model..."

seed(0) # Lock random list shuffling so we can compare.

m = Model(known=known, unknown=unknown, classifier=SLP())
for iteration in range(5):
    for s in shuffled(data[:20000]):
        prev = None
        next = None
        for i, (w, tag) in enumerate(s):
            if i < len(s) - 1:
                next = s[i+1]
            m.train(w, tag, prev, next)
            prev = (w, tag)
            next = None

f = os.path.join(os.path.dirname(__file__), "en-model.slp")
m.save(f, final=True)

# Each parser in Pattern (pattern.en, pattern.es, pattern.it, ...)
# assumes that a lexicon of known words and their most frequent tag is available,
# along with some rules for morphology (suffixes, e.g., -ly = adverb)
# and context (surrounding words) for unknown words.

# If a language model is also available, it overrides these (simpler) rules.
# For English, this can raise accuracy from about 94% up to about 97%,
# and makes the parses about 3x faster.

print "loading model..."

f = os.path.join(os.path.dirname(__file__), "en-model.slp")
lexicon.model = Model.load(lexicon, f)

# To test the accuracy of the language model,
# we can compare a tagged corpus to the predicted tags.
# This corpus must be different from the one used for training.
# Typically, sections 22, 23 and 24 of the WSJ are used.

# Note that the WSJ contains standardized English.
# The accuracy will be lower when tested on, for example, informal tweets.
# A different classifier could be trained for informal language use.

print "testing..."

i, n = 0, 0
for s1 in data[-5000:]:
    s2 = " ".join(w for w, tag in s1)
    s2 = parsetree(s2, tokenize=False)
    s2 = ((w.string, w.tag or "") for w in s2[0])
    for (w1, tag1), (w2, tag2) in zip(s1, s2):
        if tag1 == tag2.split("-")[0]: # NNP-PERS => NNP
            i += 1
        n += 1

print float(i) / n # accuracy