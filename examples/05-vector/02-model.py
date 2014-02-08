import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import glob
import codecs

from pattern.vector import Document, Model, TF, TFIDF

# A documents is a bag-of-word representations of a text.
# Each word or feature in the document vector has a weight,
# based on how many times the word occurs in the text.
# This weight is called term frequency (TF).

# Another interesting measure is TF-IDF:
# term frequency-inverse document frequency.
# Suppose that "the" is the most frequent word in the text.
# But it also occurs frequently in many other texts,
# so it is not very specific or "unique" in any one document.
# TF-IDF divided term frequency ("how many times in this text?")
# by the document frequency ("how many times in all texts?")
# to represent this.

# A Model is a collection of documents vectors.
# A Model is a matrix (or vector space) 
# with features as columns and feature weights as rows.
# We can then do calculations on the matrix,
# for example to compute TF-IDF or similarity between documents.

# Load a model from a folder of text documents:
documents = []
for f in glob.glob(os.path.join(os.path.dirname(__file__), "corpus", "*.txt")):
    text = codecs.open(f, encoding="utf-8").read()
    name = os.path.basename(f)[:-4]
    documents.append(Document(text, name=name))
    
m = Model(documents, weight=TFIDF)

# We can retrieve documents by name:
d = m.document(name="lion")

print d.keywords(top=10)
print
print d.tf("food")
print d.tfidf("food") # TF-IDF is less: "food" is also mentioned with the other animals.
print

# We can compare how similar two documents are.
# This is done by calculating the distance between the document vectors
# (i.e., finding those that are near to each other).

# For example, say we have two vectors with features "x" and "y".
# We can calculate the distance between two points (x, y) in 2-D space:
# d = sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2))
# This is the Euclidean distance in 2-D space.
# Similarily, we can calculate the distance in n-D space,
# in other words, for vectors with lots of features.

# For text, a better metric than Euclidean distance
# is called cosine similarity. This is what a Model uses:
d1 = m.document(name="lion")
d2 = m.document(name="tiger")
d3 = m.document(name="dolphin")
d4 = m.document(name="shark")
d5 = m.document(name="parakeet")
print "lion-tiger:", m.similarity(d1, d2)
print "lion-dolphin:", m.similarity(d1, d3)
print "dolphin-shark:", m.similarity(d3, d4)
print "dolphin-parakeet:", m.similarity(d3, d5)
print

print "Related to tiger:"
print m.neighbors(d2, top=3) # Top three most similar.
print

print "Related to a search query ('water'):"
print m.search("water", top=10)

# In summary:

# A Document:
# - takes a string of text,
# - counts the words in the text,
# - constructs a vector of words (features) and normalized word count (weight).

# A Model:
# - groups multiple vectors in a matrix,
# - tweaks the weight with TF-IDF to find "unique" words in each document,
# - computes cosine similarity (= distance between vectors),
# - compares documents using cosine similatity.