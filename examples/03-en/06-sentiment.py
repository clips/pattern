import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.en import sentiment, polarity, subjectivity, positive

# Sentiment analysis (or opinion mining) attempts to determine if
# a text is objective or subjective, positive or negative.
# The sentiment analysis lexicon bundled in Pattern focuses on adjectives.
# It contains adjectives that occur frequently in customer reviews,
# hand-tagged with values for polarity and subjectivity.

# polarity() measures positive vs. negative, as a number between -1.0 and +1.0.
# subjectivity() measures objective vs. subjective, as a number between 0.0 and 1.0.
# sentiment() returns a tuple of (polarity, subjectivity) for a given string.
for word in ("amazing", "horrible", "public"):
    print word, sentiment(word)

print
print sentiment(
    "The movie attempts to be surreal by incorporating time travel and various time paradoxes,"
    "but it's presented in such a ridiculous way it's seriously boring.") 

# The input string can also be a Synset, or a parsed Sentence, Text, Chunk or Word.

# positive() returns True if the string's polarity >= threshold.
# The threshold can be lowered or raised, 
# but overall for strings with multiple words +0.1 yields the best results.
print
print "good:", positive("good", threshold=0.1)
print " bad:", positive("bad")
print

# You can also do sentiment analysis in Dutch, it works exactly the same:

#from pattern.nl import sentiment as sentiment_nl
#print "In Dutch:"
#print sentiment_nl("Een onwijs spannend goed boek!")

# You can also use Pattern with SentiWordNet.
# You can get SentiWordNet at: http://sentiwordnet.isti.cnr.it/
# Put the file "SentiWordNet*.txt" in pattern/en/wordnet/
# You can then use Synset.weight() and wordnet.sentiwordnet:

#from pattern.en import wordnet, ADJECTIVE
#print wordnet.synsets("horrible", pos=ADJECTIVE)[0].weight # Yields a (polarity, subjectivity)-tuple.
#print wordnet.sentiwordnet["horrible"]
