import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.vector import Document, Corpus, Bayes
from pattern.db import Datasheet

# Naive Bayes is one of the oldest classifiers,
# but is is still popular because it is fast for corpora 
# that have many documents and many words.
# It is outperformed by KNN and SVM, but useful for running tests.

# We'll test it with a corpus of spam e-mail messages
# included in the test suite, stored as a CSV-file.
# The corpus contains mostly technical e-mail from developer mailing lists.
data = Datasheet.load(os.path.join("..","..","test","corpora","apache-spam.csv"))

documents = []
for score, message in data:
    document = Document(message, type=int(score) > 0)
    documents.append(document)
corpus = Corpus(documents)

print "number of documents:", len(corpus)
print "number of words:", len(corpus.vector)
print "number of words (average):", sum(len(d.terms) for d in corpus.documents) / float(len(corpus))
print

# Train Naive Bayes on all documents.
# Each document has a type: True for real e-mail, False for spam.
# This results in a "binary" classifier that either answers True or False
# for unknown documents.
classifier = Bayes()
for document in corpus:
    classifier.train(document)

# We can now ask it questions about unknown e-mails:

print classifier.classify("win money") # False: most likely spam.
print classifier.classify("fix bug")   # True: most likely a real message.
print

print classifier.classify("customer")  # False: people don't talk like this on developer lists...
print classifier.classify("guys")      # True: because most likely everyone knows everyone.
print

# To test the accuracy of a classifier,
# we typically use 10-fold cross validation.
# This means that 10 individual tests are performed, 
# each with 90% of the corpus as training data and 10% as testing data.
print Bayes.test(corpus, folds=10)

# This yields 4 scores: Accuracy, Precision, Recall and F-score.
# Accuracy in itself is not very useful, 
# since some spam may have been regarded as real messages (false positives),
# and some real messages may have been regarded as spam (false negatives).
# Precision = how accurate false positives are discarded,
# Recall = how accurate false negatives are discarded.
