import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.vector import Corpus

# In the previous example we saw that words in a Document have a weight
# based on how many times the word occurs in the document.
# This is called term frequency (TF).

# Another interesting measure is term frequency-inverse document frequency (TF-IDF).
# If "important" is the most important word in a document,
# but it also occurs frequently in many other documents, then it is not important at all.

# The Corpus object groups a number of documents
# so that their words can be compared to calculate TF-IDF.

# You can build a corpus from a folder of text files.
# We supply a naming function that names individual documents based on the file path.
corpus = Corpus.build(os.path.join("corpus", "*.txt"), name=lambda path: os.path.basename(path)[:-4])

d = corpus.document(name="lion") # Filename is now used as document name.

print d.keywords(top=10)
print
print d.tf("food")
print d.tfidf("food") # TF-IDF is less: "food" is also mentioned with the other animals.
print

# This allows us to compare how similar two documents are.
# The corpus can be represented as a matrix with documents as rows
# and words as columns. Each document row is called a "vector",
# containing the TF-IDF scores for word columns.
# We can compare two vectors by calculating their angle,
# this is called "cosine-similarity":
d1 = corpus.document(name="lion")
d2 = corpus.document(name="tiger")
d3 = corpus.document(name="dolphin")
d4 = corpus.document(name="shark")
d5 = corpus.document(name="parakeet")
print "lion-tiger:", corpus.similarity(d1, d2)
print "lion-dolphin:", corpus.similarity(d1, d3)
print "dolphin-shark:", corpus.similarity(d3, d4)
print "dolphin-parakeet:", corpus.similarity(d3, d5)
print

print "Related to tiger:"
print corpus.neighbors(d2, top=3) # Top three most similar.
print

print "Related to a search query ('water'):"
print corpus.search("water", top=10)
