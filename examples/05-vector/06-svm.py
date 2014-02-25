import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import random

from pattern.db     import Datasheet
from pattern.nl     import tag, predicative
from pattern.vector import SVM, KNN, NB, count, shuffled

# This example demonstrates a Support Vector Machine (SVM).
# SVM is a robust classifier that uses "kernel" functions.
# See: http://www.clips.ua.ac.be/pages/pattern-vector#svm
#
# As a metaphor, imagine the following game:
# - The ground is scattered with red and blue marbles.
# - It is your task to separate them using a single, straight line.
#
# The separation is going to be a rough approximation, obviously.
#
# Now imagine the following game:
# - The room is filled with static, floating red and blue marbles.
# - It is your task to separate them by inserting a glass panel between them.
#
# The 3-D space gives a lot more options. Adding more dimensions add even more options.
# This is roughly what a SVM does, using kernel functions to push the separation
# to a higher dimension.

# Pattern includes precompiled C binaries of libsvm.
# If these do not work on your system you have to compile libsvm manually.
# You can also change the "SVM()" statement below with "KNN()",
# so you can still follow the rest of the example.

classifier = SVM()

# We'll build a classifier to predict sentiment in Dutch movie reviews.
# For example, "geweldige film!" (great movie) indicates a positive sentiment.
# The CSV file at pattern/test/corpora/polarity-nl-bol.com.csv
# contains 1,500 positive and 1,500 negative reviews.

# The pattern.vector module has a shuffled() function
# which we use to randomly arrange the reviews in the list:

print "loading data..."
data = os.path.join(os.path.dirname(__file__), "..", "..", "test", "corpora", "polarity-nl-bol.com.csv")
data = Datasheet.load(data)
data = shuffled(data)

# We do not necessarily need Document objects as in the previous examples.
# We can train any classifier on simple Python dictionaries too.
# This is sometimes easier if you want full control over the data.
# The instance() function below returns a train/test instance for a given review:
# 1) parse the review for part-of-speech tags,
# 2) keep adjectives, adverbs and exclamation marks (these mainly carry sentiment),
# 3) lemmatize the Dutch adjectives, e.g., "goede" => "goed" (good).
# 4) count the distinct words in the list, map it to a dictionary.

def instance(review):                     # "Great book!"
    v = tag(review)                       # [("Great", "JJ"), ("book", "NN"), ("!", "!")]
    v = [word for (word, pos) in v if pos in ("JJ", "RB") or word in ("!")]
    v = [predicative(word) for word in v] # ["great", "!", "!"]
    v = count(v)                          # {"great": 1, "!": 1}
    return v

# We can add any kind of features to a custom instance dict.
# For example, in a deception detection experiment
# we may want to populate the dict with PRP (pronouns), punctuation marks, 
# average sentence length, a score for word diversity, etc.

# Use 1,000 random instances as training material.

print "training..."
for score, review in data[:1000]:
    classifier.train(instance(review), type=int(score) > 0)
#classifier.save("sentiment-nl-svm.p")
#classifier = SVM.load("sentiment-nl-svm.p")

# Use 500 random instances as test.

print "testing..."
i = n = 0
for score, review in data[1000:1500]:
    if classifier.classify(instance(review)) == (int(score) > 0):
        i += 1
    n += 1

# The overall accuracy is around 82%.
# A Naieve Bayes classifier has about 78% accuracy.
# A KNN classifier has about 80% accuracy.
# Careful: to get a reliable score you need to calculate precision and recall,
# study the documentation at:
# http://www.clips.ua.ac.be/pages/pattern-metrics#accuracy

print float(i) / n

# The work is not done here.
# Low accuracy is disappointing, but high accuracy is often suspicious.
# Things to look out for:
# - distinction between train and test set,
# - overfitting: http://en.wikipedia.org/wiki/Overfitting