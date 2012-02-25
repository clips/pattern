import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import time

from pattern.vector import Document, Corpus, KNN
from pattern.db import Datasheet

# Latent Semantic Analysis (LSA) is a statistical machine learning method 
# based on a matrix calculation called "singular value decomposition" (SVD).
# It discovers semantically related words across documents.
# It groups these into different "concepts" 
# and creates a "concept vector" instead of a word vector for each document.
# This reduces the amount of data to work with (for example when clustering),
# and filters out noise, so that semantically related words come out stronger. 

# We'll use the Pang & Lee corpus of movie reviews, included in the testing suite.
# Take 200 positive reviews and 200 negative reviews:
data = Datasheet.load(os.path.join("..","..","test","corpora","pang&lee-polarity.csv"))
data = data[:200] + data[-200:]

# Build a corpus of review documents.
# Each document consists of the top 30 words in the movie review.
documents = []
for score, review in data:
    document = Document(review, type=int(score) > 0, top=30)
    documents.append(document)
corpus = Corpus(documents)

print "number of documents:", len(corpus)
print "number of words:", len(corpus.vector)
print "number of words (average):", sum(len(d.terms) for d in corpus.documents) / float(len(corpus))
print

# This may be too much words for some clustering algorithms (e.g., hierarchical).
# We'll reduce the documents to vectors of 4 concepts.

# First, let's test how the corpus would perform as a classifier.
# The details of KNN are not that important right now, just observe the numbers.
# Naturally, we want accuracy to stay the same after LSA reduction,
# and hopefully decrease the time needed to run.
t = time.time()
print "accuracy:", KNN.test(corpus, folds=10)[-1]
print "time:", time.time() - t
print

# Reduce the documents to vectors of 4 concepts (= 1/7 of 30 words).
print "LSA reduction..."
print
corpus.reduce(4)

t = time.time()
print "accuracy:", KNN.test(corpus, folds=10)[-1]
print "time:", time.time() - t
print

# Not bad, accuracy is about the same but performance is 3x faster,
# because each document is now a "4-word summary" of the original review.

# Let's take a closer look at the concepts.
# The concept vector for the first document:
print corpus.lsa.vectors[corpus[0].id]
print

# It is a dictionary linking concept id's to a score.
# This is is not very helpful.
# But we can look up the words related to a concept id:
#print corpus.lsa.concepts[0]

# That's a lot of words.
# Actually, all words in the corpus have a score in one of the four concepts. 
# This is a little bit abstract.
# We'll do a new reduction with 100 concepts (or semantic "categories"),
# and examine only the salient words for a concept.

corpus.lsa = None
corpus.reduce(100)

for word, weight in corpus.lsa.concepts[1].items():
    if abs(weight) > 0.1:
        print word
        
# Concept  1 = "truman", "ventura", "ace", "carrey", ... It's obviously about Jim Carrey movies.
# Concept 20 = "ripley", "butcher", "aliens", ... the Alien-franchise?
# Concept 40 = "wars", "lucas", "jedi", "phantom", "star", ...

# You'll notice that not all concepts are equally easy to interpret,
# or that some of them seem to mingle 2 or more core ideas.
# However, it should underpin that (with further massaging)
# LSA can not only be used for faster processing but also to discover synonym sets.
