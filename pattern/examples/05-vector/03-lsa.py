import os, sys; sys.path.insert(0, os.path.join("..", "..", ".."))

from pattern.vector import Document, Corpus, Vectorspace

# Latent Semantic Analysis (LSA) is a statistical machine learning method 
# based on singular value decomposition (SVD).
# It discovers semantically related words across documents. 
# The idea is to group the document vectors in a matrix 
# (each document is a row, each word in the corpus is a column), 
# and then to reduce the number of dimensions, filtering out "noise".

D1 = Document("The dog wags his tail.", threshold=0, name="dog")
D2 = Document("Curiosity killed the cat.", threshold=0, name="cat")
D3 = Document("Cats and dogs make good pets.", threshold=0, name="pet")
D4 = Document("Curiosity drives science.", threshold=0, name="science")

corpus = Corpus([D1,D2,D3,D4])

lsa = corpus.lsa()

print lsa.keywords(D4)
print
print lsa.search("curiosity")

# Document D4 now yields kill as a keyword, although this word was not D4's description. 
# However, document D2 and D4 share curiosity as a keyword, 
# so D4 inherits some of the keywords from D2. 
# Performing a search on curiosity now also yields document D3 as a result.
