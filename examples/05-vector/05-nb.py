import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.vector import Document, Model, NB
from pattern.db import Datasheet

# Naive Bayes is one of the oldest classifiers,
# but is is still popular because it is fast for models
# that have many documents and many features.
# It is outperformed by KNN and SVM, but useful as a baseline for tests.

# We'll test it with a corpus of spam e-mail messages,
# included in the test suite, stored as a CSV-file.
# The corpus contains mostly technical e-mail from developer mailing lists.
data = os.path.join(os.path.dirname(__file__), "..","..","test","corpora","spam-apache.csv")
data = Datasheet.load(data)

documents = []
for score, message in data:
    document = Document(message, type=int(score) > 0)
    documents.append(document)
m = Model(documents)

print "number of documents:", len(m)
print "number of words:", len(m.vector)
print "number of words (average):", sum(len(d.features) for d in m.documents) / float(len(m))
print

# Train Naive Bayes on all documents.
# Each document has a type: True for actual e-mail, False for spam.
# This results in a "binary" classifier that either answers True or False
# for unknown documents.
classifier = NB()
for document in m:
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
from pattern.vector import k_fold_cv
print k_fold_cv(NB, documents=m, folds=10)

# This yields 5 scores: (Accuracy, Precision, Recall, F-score, standard deviation).
# Accuracy in itself is not very useful, 
# since some spam may have been regarded as real messages (false positives),
# and some real messages may have been regarded as spam (false negatives).
# Precision = how accurately false positives are discarded,
#    Recall = how accurately false negatives are discarded.
#   F-score = harmonic mean of precision and recall.
#     stdev = folds' variation from average F-score.