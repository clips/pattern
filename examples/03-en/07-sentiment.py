import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.en import sentiment, polarity, subjectivity, positive

# Sentiment analysis (or opinion mining) attempts to determine if
# a text is objective or subjective, positive or negative.
# The sentiment analysis lexicon bundled in Pattern focuses on adjectives.
# It contains adjectives that occur frequently in customer reviews,
# hand-tagged with values for polarity and subjectivity.

# The polarity() function measures positive vs. negative, as a number between -1.0 and +1.0.
# The subjectivity() function measures objective vs. subjective, as a number between 0.0 and 1.0.
# The sentiment() function returns an averaged (polarity, subjectivity)-tuple for a given string.
for word in ("amazing", "horrible", "public"):
    print(word, sentiment(word))

print("")
print(sentiment(
    "The movie attempts to be surreal by incorporating time travel and various time paradoxes,"
    "but it's presented in such a ridiculous way it's seriously boring."))

# The input string can be:
# - a string, 
# - a Synset (see pattern.en.wordnet),
# - a parsed Sentence, Text, Chunk or Word (see pattern.en),
# - a Document (see pattern.vector).

# The positive() function returns True if the string's polarity >= threshold.
# The threshold can be lowered or raised,
# but overall for strings with multiple words +0.1 yields the best results.
print("")
print("good", positive("good", threshold=0.1))
print("bad", positive("bad"))
print("")

# You can also do sentiment analysis in Dutch or French,
# it works exactly the same:

#from pattern.nl import sentiment as sentiment_nl
#print("In Dutch:")
#print(sentiment_nl("Een onwijs spannend goed boek!"))

# You can also use Pattern with SentiWordNet.
# You can get SentiWordNet at: http://sentiwordnet.isti.cnr.it/
# Put the file "SentiWordNet*.txt" in pattern/en/wordnet/
# You can then use Synset.weight() and wordnet.sentiwordnet:

#from pattern.en import wordnet, ADJECTIVE
#print(wordnet.synsets("horrible", pos=ADJECTIVE)[0].weight)  # Yields a (polarity, subjectivity)-tuple.
#print(wordnet.sentiwordnet["horrible"])

# For fine-grained analysis,
# the return value of sentiment() has a special "assessments" property.
# Each assessment is a (chunk, polarity, subjectivity, label)-tuple,
# where chunk is a list of words (e.g., "not very good").

# The label offers additional meta-information.
# For example, its value is MOOD for emoticons:

s = "amazing... :/"
print(sentiment(s))
for chunk, polarity, subjectivity, label in sentiment(s).assessments:
    print(chunk, polarity, subjectivity, label)

# Observe the output.
# The average sentiment is positive because the expression contains "amazing".
# However, the smiley is slightly negative, hinting at the author's bad mood.
# He or she might be using sarcasm.
# We could work this out from the fine-grained analysis.

from pattern.metrics import avg

a = sentiment(s).assessments

score1 = avg([p for chunk, p, s, label in a if label is None])    # average polarity for words
score2 = avg([p for chunk, p, s, label in a if label == "mood"])  # average polarity for emoticons

if score1 > 0 and score2 < 0:
    print("...sarcasm?")
