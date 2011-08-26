import os, sys; sys.path.insert(0, os.path.join("..", ".."))

import os
import glob
from pattern.vector import Document, Corpus, Bayes, KNN, features, distance, Vector, _distance, COSINE, kdtree


#from pattern.web import PDF
##pdf = PDF(open("/users/tom/downloads/10-1.1.1.61.7217.pdf", "rb").read())
#pdf = PDF(open("/users/tom/downloads/10-1.1.1.14.8422.pdf", "rb").read())
#print Document(unicode(pdf), threshold=1).keywords(30)
#print xxx

corpus = Corpus()
for product in glob.glob(os.path.join("reviews", "*")):
    for review in glob.glob(os.path.join(product, "*.txt")):
        polarity = "yes" in review
        s = open(review).read()
        corpus.append(Document(s, type=polarity, top=50, threshold=2))

#print "testtree"
#V = lambda x: Vector(dict(enumerate(x)))
#v = [(2,3), (5,4), (9,6), (4,7), (8,1), (7,2)]
#v = [V(x) for x in v]
#t = kdtree(v)
#print t.nn(V((9,5)))
#print xxx

n = 10
x = 0
t1 = 0
t2 = 0

for j in range(n):
    k = 40
    d1 = corpus.documents[j]
    from time import time
    t = time()
    nn1 = corpus.nn(d1, k)
    t1 += time()-t
    nn2 = kdtree(corpus).nn(d1, k)
    t = time()
    nn2 = [(w,d) for w,d in nn2 if w < 1.0]
    t2 += time()-t
    m = min(len(nn1), len(nn2))
    #print
    #print j
    print len(nn1), len(nn2)
    #for i in range(m):
    #    print nn1[i][1] == nn2[i][1], nn1[i][1].id, nn2[i][1].id
    if m > 0:
        x += len([nn1[i][1] == nn2[i][1] for i in range(m)]) / float(m)
    else:
        x += 1

print "ERROR"
print x / n
print t1
print t2

#print xxx


print len(corpus)
print len(corpus.features)
print len(corpus.documents[0].vector)
from time import time
t = time()
print KNN.test(corpus, folds=10)
print time()-t

print "filter..."

from time import time
t = time()
f = corpus.feature_selection(150, verbose=False)
print f
print time()-t
corpus = corpus.filter(f)

#corpus.reduce(300)
#print len(corpus.lsa.vectors[corpus.documents[0].id])
#print corpus.lsa.vectors[corpus.documents[0].id]
#print len(corpus)
#print len(corpus.lsa.terms)

#print corpus.feature_selection(top=100, verbose=True)

from time import time
t = time()
print KNN.test(corpus, folds=10)
print time()-t