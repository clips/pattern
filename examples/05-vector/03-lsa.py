import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import time

from pattern.vector import Document, Model, KNN
from pattern.db import Datasheet

# Long documents contain lots of words.
# Models with lots of long documents can become slow,
# because calculating cosine similarity then takes a long time.

# Latent Semantic Analysis (LSA) is a statistical machine learning method,
# based on a matrix calculation called "singular value decomposition" (SVD).
# It discovers semantically related words across documents.
# It groups related words into "concepts" .
# It then creates a concept vector for each document.
# This reduces the amount of data to work with (for example when clustering),
# and filters out noise, so that semantically related words come out stronger. 

# We'll use the Pang & Lee corpus of movie reviews, included in the testing suite.
# Take 250 positive reviews and 250 negative reviews:
data = os.path.join(os.path.dirname(__file__), "..","..","test", "corpora", "polarity-en-pang&lee1.csv")
data = Datasheet.load(data)
data = data[:250] + data[-250:]

# Build a model of movie reviews.
# Each document consists of the top 40 words in the movie review.
documents = []
for score, review in data:
    document = Document(review, stopwords=False, top=40, type=int(score) > 0)
    documents.append(document)

m = Model(documents)

print "number of documents:", len(m)
print "number of features:", len(m.vector)
print "number of features (average):", sum(len(d.features) for d in m.documents) / float(len(m))
print

# 6,337 different features may be too slow for some algorithms (e.g., hierarchical clustering).
# We'll reduce the document vectors to 10 concepts.

# Let's test how our model performs as a classifier.
# A document can have a label (or type, or class).
# For example, in the movie reviews corpus,
# there are positive reviews (score > 0) and negative reviews (score < 0).
# A classifier uses a model as "training" data
# to predict the label (type/class) of unlabeled documents.
# In this case, it can predict whether a new movie review is positive or negative.

# The details are not that important right now, just observe the accuracy.
# Naturally, we want accuracy to stay the same after LSA reduction,
# and hopefully decrease the time needed to run.

t = time.time()
print "accuracy:", KNN.test(m, folds=10)[-1]
print "time:", time.time() - t
print

# Reduce the documents to vectors of 10 concepts (= 1/4 of 40 features).
print "LSA reduction..."
print
m.reduce(10)

t = time.time()
print "accuracy:", KNN.test(m, folds=10)[-1]
print "time:", time.time() - t
print

# Accuracy is about the same, but the performance is better: 2x-3x faster,
# because each document is now a "10-word summary" of the original review.

# Let's take a closer look at the concepts.
# The concept vector for the first document:
print m.lsa.vectors[m[0].id]
print

# It is a dictionary of concept id's (instead of features).
# This is is not very helpful.
# But we can look up the features "bundled" in each concept:
print len(m.lsa.concepts[0])

# That's a lot of words.
# In fact, all features in the model have a score for one of the ten concepts.

# To make it clearer, let's generate 100 concepts (i.e., semantic categories),
# and then examine the features with the highest score for a concept:

m.lsa = None
m.reduce(100)

for feature, weight in m.lsa.concepts[15].items(): # concept id=2
    if abs(weight) > 0.1:
        print feature
        
# Concept  2 = "truman", "ventura", "ace", "carrey", ... Obviously about Jim Carrey movies.
# Concept 15 = "sixth", "sense", "child", "dead", "willis" ...

# Not all concepts are equally easy to interpret,
# but the technique can be useful to discover synonym sets.