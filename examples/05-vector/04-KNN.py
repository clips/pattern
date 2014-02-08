import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Twitter
from pattern.en import Sentence, parse
from pattern.search import search
from pattern.vector import Document, Model, KNN

# Classification is a supervised machine learning method,
# where labeled documents are used as training material
# to learn how to label unlabeled documents.

# This example trains a simple classifier with Twitter messages.
# The idea is that, if you have a number of texts with a "type"
# (mail/spam, positive/negative, language, author's age, ...),
# you can predict the type of other "unknown" texts.
# The k-Nearest Neighbor algorithm classifies texts according
# to the k documents that are most similar (cosine similarity) to the given input document.

m = Model()
t = Twitter()

# First, we mine a model of a 1000 tweets.
# We'll use hashtags as type.
for page in range(1, 10):
    for tweet in t.search('#win OR #fail', start=page, count=100, cached=True):
        # If the tweet contains #win hashtag, we'll set its type to 'WIN':
        s = tweet.text.lower()               # tweet in lowercase
        p = '#win' in s and 'WIN' or 'FAIL'  # document labels      
        s = Sentence(parse(s))               # parse tree with part-of-speech tags
        s = search('JJ', s)                  # adjectives in the tweet
        s = [match[0].string for match in s] # adjectives as a list of strings
        s = " ".join(s)                      # adjectives as string
        if len(s) > 0:
            m.append(Document(s, type=p, stemmer=None))

# Train k-Nearest Neighbor on the model.
# Note that this is a only simple example: to build a robust classifier
# you would need a lot more training data (e.g., tens of thousands of tweets).
# The more training data, the more statistically reliable the classifier becomes.
# The only way to really know if you're classifier is working correctly
# is to test it with testing data, see the documentation for Classifier.test().
classifier = KNN(baseline=None) # By default, baseline=MAJORITY
for document in m:              # (classify unknown documents with the most frequent type).
    classifier.train(document)

# These are the adjectives the classifier has learned:
print sorted(classifier.features)
print

# We can now ask it to classify documents containing these words.
# Note that you may get different results than the ones below,
# since you will be mining other (more recent) tweets.
# Again, a robust classifier needs lots and lots of training data.
# If None is returned, the word was not recognized,
# and the classifier returned the default value (see above).
print classifier.classify('sweet potato burger') # yields 'WIN'
print classifier.classify('stupid autocorrect')  # yields 'FAIL'

# "What can I do with it?"
# In the scientific community, classifiers have been used to predict:
# - the opinion (positive/negative) in product reviews on blogs,
# - the age of users posting on social networks,
# - the author of medieval poems,
# - spam in  e-mail messages,
# - lies & deception in text,
# - doubt & uncertainty in text,
# and to:
# - improve search engine query results (e.g., where "jeans" queries also yield "denim" results),
# - win at Jeopardy!,
# - win at rock-paper-scissors,
# and so on...