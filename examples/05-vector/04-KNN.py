import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Twitter
from pattern.en import Sentence, parse
from pattern.search import search
from pattern.vector import Document, Corpus, KNN

# This example trains a simple classifier with Twitter messages.
# The idea is that if you have a number of texts with a "type" 
# (e.g., positive/negative opinion, language, author, ...),
# you can predict the type of other "unknown" texts.
# The k-nearest neighbor algorithm classifies texts according
# to the types of known texts that are most similar to the given input text.
# Different similarity measures can be used (e.g, how many characters are the same,
# how many words are the same, ...), by default cosine similarity is used (see the docs).

corpus = Corpus()

# First, we mine a corpus of tweets.
# We'll use hashtags as type.
for page in range(1,6):
    for tweet in Twitter().search('#win OR #fail', start=page, count=100, cached=False):
        # If the tweet contains #win hashtag, we'll set its type to 'WIN':
        p = '#win' in tweet.description.lower() and 'WIN' or 'FAIL'
        s = tweet.description.lower()        # tweet in lowercase
        s = Sentence(parse(s))               # parse tree with part-of-speech tags
        s = search('JJ', s)                  # adjectives in the tweet
        s = [match[0].string for match in s] # adjectives as a list of strings
        s = " ".join(s)                      # adjectives as string
        if len(s) > 0:
            corpus.append(Document(s, type=p, threshold=0, stemmer=None))

# Train k-nearest neighbor on the corpus.
# Note that this is a only simple example: to build a robust classifier
# you would need a lot more training data (e.g., tens of thousands of tweets).
# The more training data, the more statistically reliable the classifier becomes.
# The only way to really know if you're classifier is working correctly
# is to test it with testing data, see the documentation for Classifier.test().
classifier = KNN()
for document in corpus:
    classifier.train(document)

# These are the words the classifier has learned:
print classifier.terms
print

# We can ask it to classify texts containing those words.
# Note that you may get different results than the ones indicated below,
# since you will be mining other (more recent) tweets.
# Again, a robust classifier needs lots and lots of training data.
print classifier.classify('sweet')  # yields 'WIN'
print classifier.classify('stupid') # yields 'FAIL'

# "What can I do with it?"
# In the scientific community, classifiers have been used to predict
# the author of medieval poems,
# the opinion (positive/negative) in product reviews on blogs,
# the age of users posting on teen social networks,
# spam e-mail messages,
# search engine query results (e.g., where "jeans" queries also yield "denim" results),
# and so on.