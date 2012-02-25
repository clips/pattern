import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import codecs

from pattern.vector import Document, PORTER, LEMMA

# A Document is a "bag-of-words" that splits a string into words and counts them.
# Word count can then be used to compare documents in various ways.
# Words can be filtered and "stemmed" before counting them.
# The purpose of stemming is to bring variant forms a word together.
# For example, with the Porter2 stemming algorithm
# "conspiracy" and "conspired" are both reduced to "conspir".
# Nowadays, lemmatization is preferred over stemming, e.g.,
# "conspiracies" => "conspiracy", "conspired" => "conspire".

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
# Some stop words like "the", "and", "I", "is" are always ignored.
document = Document(s, threshold=1)
print document.terms
print

# The /corpus folder contains texts mined from Wikipedia.
# Below is the mining script (we already executed it for you):

#import os, codecs
#from pattern.web import Wikipedia
#
#wp = Wikipedia()
#for q in (
#  "badger", "bear", "dog", "dolphin", "lion", "parakeet", 
#  "rabbit", "shark", "sparrow", "tiger", "wolf"):
#    s = wp.search(q, cached=True)
#    s = s.plaintext()
#    f = codecs.open(os.path.join("corpus", q+".txt"), "w", encoding="utf-8")
#    f.write(s)
#    f.close()

# A document can be loaded from a text file path:
f = os.path.join("corpus", "wolf.txt")
document = Document.open(f, encoding="utf-8", name="wolf", stemmer=PORTER)
print document
print document.keywords(top=10)
print

# Same document, but instead of using the Porter2 stemming algorithm
# we lemmatize words (which is slower).
# Observe the difference between the two sets.
document = Document.open(f, name="wolf", stemmer=LEMMA)
print document
print document.keywords(top=10)
print

#print document.vector
