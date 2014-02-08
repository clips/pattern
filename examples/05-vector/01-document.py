import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import codecs

from pattern.vector import Document, PORTER, LEMMA

# A Document is a "bag-of-words" that splits a string into words and counts them.
# A list of words or dictionary of (word, count)-items can also be given.

# Words (or more generally "features") and their word count ("feature weights")
# can be used to compare documents. The word count in a document is normalized
# between 0.0-1.0 so that shorted documents can be compared to longer documents.

# Words can be stemmed or lemmatized before counting them.
# The purpose of stemming is to bring variant forms a word together.
# For example, "conspiracy" and "conspired" are both stemmed to "conspir".
# Nowadays, lemmatization is usually preferred over stemming, 
# e.g., "conspiracies" => "conspiracy", "conspired" => "conspire".

s = """
The shuttle Discovery, already delayed three times by technical problems and bad weather, 
was grounded again Friday, this time by a potentially dangerous gaseous hydrogen leak 
in a vent line attached to the ship's external tank.
The Discovery was initially scheduled to make its 39th and final flight last Monday, 
bearing fresh supplies and an intelligent robot for the International Space Station. 
But complications delayed the flight from Monday to Friday, 
when the hydrogen leak led NASA to conclude that the shuttle would not be ready to launch 
before its flight window closed this Monday.
"""

# With threshold=1, only words that occur more than once are counted.
# With stopwords=False, words like "the", "and", "I", "is" are ignored.
document = Document(s, threshold=1, stopwords=False)
print document.words
print

# The /corpus folder contains texts mined from Wikipedia.
# Below is the mining script (we already executed it for you):

#import os, codecs
#from pattern.web import Wikipedia
#
#w = Wikipedia()
#for q in (
#  "badger", "bear", "dog", "dolphin", "lion", "parakeet", 
#  "rabbit", "shark", "sparrow", "tiger", "wolf"):
#    s = w.search(q, cached=True)
#    s = s.plaintext()
#    print os.path.join("corpus2", q+".txt")
#    f = codecs.open(os.path.join("corpus2", q+".txt"), "w", encoding="utf-8")
#    f.write(s)
#    f.close()

# Loading a document from a text file:
f = os.path.join(os.path.dirname(__file__), "corpus", "wolf.txt")
s = codecs.open(f, encoding="utf-8").read()
document = Document(s, name="wolf", stemmer=PORTER)
print document
print document.keywords(top=10) # (weight, feature)-items.
print

# Same document, using lemmatization instead of stemming (slower):
document = Document(s, name="wolf", stemmer=LEMMA)
print document
print document.keywords(top=10)
print

# In summary, a document is a bag-of-words representation of a text.
# Bag-of-words means that the word order is discarded.
# The dictionary of words (features) and their normalized word count (weights)
# is also called the document vector:
document = Document("a black cat and a white cat", stopwords=True)
print document.words
print document.vector.features
for feature, weight in document.vector.items():
    print feature, weight

# Document vectors can be bundled into a Model (next example).