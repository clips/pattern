import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.vector import Document, Corpus

# Latent Semantic Analysis (LSA) is a statistical machine learning method 
# based on a matrix calculation called "singular value decomposition" (SVD).
# It discovers semantically related words across documents.
# It groups these into different "concepts" 
# and creates a "concept vector" instead of a word vector for each document.
# This reduces the amount of data to work with (for example when clustering),
# and filters out noise, so that semantically related words come out stronger. 

D1 = Document("The dog wags his tail.", threshold=0, name="dog")
D2 = Document("Curiosity killed the cat.", threshold=0, name="cat")
D3 = Document("Cats and dogs make good pets.", threshold=0, name="pet")
D4 = Document("Curiosity drives science.", threshold=0, name="science")

corpus = Corpus([D1,D2,D3,D4])

print corpus.search("curiosity")
print

corpus.reduce()

# A search on the reduced concept space also yields D3 ("pet") as a result,
# since D2 and D2 are slightly similar even though D3 does not explicitly contain "curiosity".
# Note how the results also yield stronger similarity scores (noise was filtered out).
print corpus.search("curiosity")
print

# The concept vector for document D1:
#print corpus.lsa.vectors[D1.id]
#print

# The word scores for each concept:
#print corpus.lsa.concepts