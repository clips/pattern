#### PATTERN | VECTOR ################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

######################################################################################################
# Vector space search, based on cosine similarity using tf-idf.
# Term frequency – inverse document frequency is a statistical measure used to evaluate 
# how important a word is to a document in a collection or corpus. 
# The importance increases proportionally to the number of times a word appears in the document 
# but is offset by the frequency of the word in the corpus. 
# Variations of the tf–idf weighting scheme are often used by search engines 
# as a central tool in scoring and ranking a document's relevance given a user query.

import os
import glob
import heapq
import codecs
import cPickle
import stemmer; _stemmer=stemmer

from math      import pow, log
from random    import random
from itertools import izip

try:
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

try: from pattern.en.inflect import singularize, conjugate
except:
    try: 
        import sys; sys.path.insert(0, os.path.join(MODULE, ".."))
        from en.inflect import singularize, conjugate
    except:
        singularize = lambda w: w
        conjugate = lambda w,t: w

#--- STRING FUNCTIONS --------------------------------------------------------------------------------
            
def decode_utf8(string):
    """ Returns the given string as a unicode string (if possible).
    """
    if isinstance(string, str):
        try: 
            return string.decode("utf-8")
        except:
            return string
    return unicode(string)
    
def encode_utf8(string):
    """ Returns the given string as a Python byte string (if possible).
    """
    if isinstance(string, unicode):
        try: 
            return string.encode("utf-8")
        except:
            return string
    return str(string)
    
def lreplace(a, b, string):
    """ Replaces the head of the string.
    """
    if string.startswith(a): 
        return b + string[len(a):]
    return string
       
def rreplace(a, b, string):
    """ Replaces the tail of the string.
    """
    if string.endswith(a): 
        return string[:len(string)-len(a)] + b
    return string
    
def filename(path, map={"_":" "}):
    """ Returns the basename of the file at the given path, without the extension.
        For example: /users/tom/desktop/corpus/aesthetics.txt => aesthetics.
    """
    f = os.path.splitext(os.path.basename(path))[0]
    for k in map: 
        f = f.replace(k, map[k])
    return f

#--- READ-ONLY DICTIONARY ----------------------------------------------------------------------------

class ReadOnlyError(Exception):
    pass

# Read-only dictionary, used for Document.terms and Document.vector.
# These can't be updated because it invalidates the cache.
class readonlydict(dict):
    def __setitem__(self, k, v):
        raise ReadOnlyError
    def __delitem__(self, k):
        raise ReadOnlyError
    def pop(self, k, default=None):
        raise ReadOnlyError
    def popitem(self, kv):
        raise ReadOnlyError
    def clear(self):
        raise ReadOnlyError
    def update(self, kv):
        raise ReadOnlyError
    def setdefault(self, k, default=None):
        if k in self: 
            return self[k]
        raise ReadOnlyError

# Read-only list, used for Corpus.documents.
class readonlylist(list):
    def __setitem__(self, i, v):
        raise ReadOnlyError
    def __delitem__(self, i):
        raise ReadOnlyError
    def append(self, v):
        raise ReadOnlyError
    def insert(self, i, v):
        raise ReadOnlyError
    def extend(self, v):
        raise ReadOnlyError
    def remove(self, v):
        raise ReadOnlyError
    def pop(self, i):
        raise ReadOnlyError

#### DOCUMENT ########################################################################################

#--- FREQUENCY+TERM LIST -----------------------------------------------------------------------------

# List of (frequency, term)-items that prints frequency with a rounded precision.
# This is used for the output of Document.keywords() and Corpus.similar() (=easier to read).
class ftlist(list):
    def __repr__(self):
        return repr([("%.3f"%f, t) for f, t in self])

#--- STOP WORDS --------------------------------------------------------------------------------------

stopwords = _stopwords = dict.fromkeys(
    open(os.path.join(MODULE, "stopwords.txt")).read().split(", "), True)

# The following words could also be meaningful nouns:
#for w in ["mine", "us", "will", "can", "may", "might"]:
#    stopwords.pop(w)

#--- WORD COUNT --------------------------------------------------------------------------------------

PUNCTUATION = "#[]():;,.!?\n\r\t\f "

def words(string, filter=lambda w: w.isalpha() and len(w)>1, punctuation=PUNCTUATION, **kwargs):
    """ Returns a list of words from the given string.
        Common punctuation marks are stripped from words.
    """
    if isinstance(string, unicode):
        string = string.replace(u"’", u"'")
    words = string.replace("\n", "\n ")
    words = (rreplace("'s", "", w.strip(punctuation)) for w in words.split(" "))
    words = [w for w in words if filter(w) is True]
    return words

PORTER, LEMMA = "porter", "lemma"
def stem(word, stemmer=PORTER, **kwargs):
    """ Returns the base form of the word when counting words in count().
        With stemmer=PORTER, the Porter2 stemming algorithm is used.
        With stemmer=LEMMA, either uses Word.lemma or inflect.singularize().
    """
    if stemmer is None:
        return word
    if stemmer == PORTER:
        return _stemmer.stem(decode_utf8(word).lower(), **kwargs)
    if stemmer == LEMMA:
        if word.__class__.__name__ == "Word":
            if word.lemma is not None:
                return word.lemma
            if word.pos == "NNS":
                return singularize(word.string.lower())
            if word.pos.startswith("VB"):
                return conjugate(word.string.lower(), "infinitive") or word
        return singularize(word)
    if type(stemmer).__name__ == "function":
        return stemmer(word)
    return word

def count(words=[], top=None, threshold=0, stemmer=PORTER, exclude=[], stopwords=False, **kwargs):
    """ Returns a dictionary of (word, count)-items, in lowercase.
        Words in the exclude list and stop words are not counted.
        Words whose count falls below (or equals) the given threshold are excluded.
        Words that are not in the given top most counted are excluded.
    """
    # An optional dict-parameter can be used to specify a subclass of dict, 
    # e.g., count(words, dict=readonlydict) as used in Document.
    count = kwargs.get("dict", dict)()
    for word in words:
        if word.__class__.__name__ == "Word":
            w = word.string.lower()
        else:
            w = word.lower()
        if (stopwords or not w in _stopwords) and not w in exclude:
            if stemmer is not None:
                w = stem(w, stemmer, **kwargs)
            dict.__setitem__(count, w, (w in count) and count[w]+1 or 1)
    for k in count.keys():
        if count[k] <= threshold:
            dict.__delitem__(count, k)
    if top is not None:
        count = count.__class__(heapq.nlargest(top, count.iteritems(), key=lambda (k,v): v))
    return count

#--- DOCUMENT ----------------------------------------------------------------------------------------
# Document is a bag of words in which each word is a feature.
# Document is represented as a vector of weighted (TF-IDF) features.

__UID = 0
def _uid():
    global __UID; __UID+=1; return __UID

# Term relevancy weight:
TF, TFIDF, TF_IDF = "tf", "tf-idf", "tf-idf"

class Document(object):
    
    # Document(string="", filter, punctuation, top, threshold, stemmer, exclude, stopwords, name, type)
    def __init__(self, string="", **kwargs):
        """ A dictionary of (word, count)-items parsed from the string.
            Punctuation marks are stripped from the words.
            Stop words in the exclude list are excluded from the document.
            Only words whose count exceeds the threshold and who are in the top are included in the document.
        """
        kwargs.setdefault("threshold", 1)
        kwargs.setdefault("dict", readonlydict)
        if isinstance(string, basestring):
            w = words(string, **kwargs)
        elif isinstance(string, (list, tuple)):
            w = string
        elif string.__class__.__name__ == "Sentence":
            w = string.words
        elif string.__class__.__name__ == "Text":
            w = []; [w.extend(sentence.words) for sentence in string]
        else:
            raise TypeError, "document string is not str, unicode, list, Sentence or Text."
        self._id       = _uid()             # Document ID, used when comparing objects.
        self._name     = kwargs.get("name") # Name that describes the document content.
        self._type     = kwargs.get("type") # Type that describes the category or class of the document.
        self._terms    = count(w, **kwargs) # Dictionary of (word, count)-items.
        self._count    = None               # Total number of words (minus stop words).
        self._vector   = None               # Cached tf-idf vector.
        self._corpus   = None               # Corpus this document belongs to.

    @classmethod
    def open(Document, path, *args, **kwargs):
        """ Creates and returns a new document from the given text file path.
        """
        s = codecs.open(path, encoding=kwargs.get("encoding", "utf-8")).read()
        return Document(s, *args, **kwargs)
        
    @classmethod
    def load(Document, path):
        """ Returns a new Document from the given text file path.
            The text file assumed to be generated with Document.save(), 
            so no filtering and stemming will be carried out (=faster).
        """
        s = open(path, "rb").read()
        s = s.lstrip(codecs.BOM_UTF8)
        return Document(s, name=filename(path), stemmer=None, punctuation="", filter=lambda w:True, threshold=0)
    
    def save(self, path):
        """ Saves the terms in the document as a space-separated text file at the given path.
            The advantage is that terms no longer need to be filtered or stemmed in Document.load().
        """
        s = [[w]*n for w, n in self._terms.items()]
        s = [" ".join(w) for w in s]
        s = encode_utf8(" ".join(s))
        f = open(path, "wb")
        f.write(codecs.BOM_UTF8)
        f.write(s)
        f.close()

    def _get_corpus(self):
        return self._corpus
    def _set_corpus(self, corpus):
        self._vector = None
        self._corpus and self._corpus._update()
        self._corpus = corpus
        self._corpus and self._corpus._update()
        
    corpus = property(_get_corpus, _set_corpus)

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name
        
    @property
    def type(self):
        return self._type
    
    @property
    def terms(self):
        return self._terms
    words = terms
    
    @property
    def count(self):
        return self.__len__()

    def __len__(self):
        # Yields the number of words (excluding stop words) in the document.
        # Cache the word count so we can reuse it when calculating tf.
        if not self._count: self._count = sum(self._terms.values())
        return self._count
    def __iter__(self):
        return iter(self._terms)
    def __contains__(self, word):
        return word in self._terms
    def __getitem__(self, word):
        return self._terms.__getitem__(word)
    def get(self, word, default=None):
        return self._terms.get(word, default)
    
    def term_frequency(self, word):
        """ Returns the term frequency of a word in the document.
            tf = number of occurences of the word / number of words in document.
            The more occurences of the word, the higher its tf weight.
        """
        return float(self._terms.get(word, 0)) / (len(self) or 1)
        
    tf = term_frequency
    
    def term_frequency_inverse_document_frequency(self, word, weight=TFIDF):
        """ Returns the word relevancy as tf*idf.
            The relevancy is a measure of how frequent the word occurs in the document,
            compared to its frequency in other documents in the corpus.
            If the document is not part of a corpus, returns tf weight.
        """
        w = self.tf(word)
        if weight == TFIDF:
            # Use tf if no corpus, or idf==None (happens when the word is not in the corpus).
            w *= self._corpus and self._corpus.idf(word) or 1
        return w
        
    tf_idf = tfidf = term_frequency_inverse_document_frequency
    
    @property
    def vector(self):
        """ Yields a dictionary of (word, relevancy)-items from the document, based on tf-idf.
        """
        # See the Vector class below. It's just a dict with some extra functionality (copy, norm, etc.)
        if not self._vector: self._vector = Vector(((w, self.tf_idf(w)) for w in self._terms))
        return self._vector
        
    def keywords(self, top=10, normalized=True):
        """ Returns a sorted list of (relevancy, word)-tuples that are top keywords in the document.
            With normalized=True, weights are normalized between 0.0 and 1.0 (their sum will be 1.0).
        """
        n = normalized and sum(self.vector.itervalues()) or 1.0
        v = ((f/n, w) for w, f in self.vector.iteritems())
        v = heapq.nsmallest(top, v, key=lambda v: (-v[0],v[1]))
        return ftlist(v)
    
    def cosine_similarity(self, document):
        """ Returns the similarity between the two documents as a number between 0.0-1.0.
            If both documents are in the same corpus the calculations are cached for reuse.
        """
        if self._corpus: 
            return self._corpus.cosine_similarity(self, document)
        if document._corpus:
            return document._corpus.cosine_similarity(self, document)
        # Use dict copies to ensure that the values are in the same order:
        return cosine_similarity(self.vector(self).values(), self.vector(document).values())
            
    similarity = cosine_similarity
    
    def copy(self):
        d = Document(name=self.name); dict.update(d._terms, self._terms); return d
    
    def __eq__(self, document):
        return isinstance(document, Document) and self._id == document._id
    def __ne__(self, document):
        return not self.__eq__(document)
    
    def __repr__(self):
        return "Document(id=%s, %scount=%s)" % (
            self._id,
            self.name and "name=%s, " % repr(self.name) or "", 
            self.count)

#--- VECTOR ------------------------------------------------------------------------------------------

class WeightError(Exception):
    pass

class Vector(readonlydict):
    
    def __init__(self, *args, **kwargs):
        """ Vector is a dictionary of (word, weight)-items based on the terms in a Document.
        """
        self.weight = kwargs.pop("weight", TFIDF) # Vector weights based on tf or tf-idf?
        self._norm  = None
        readonlydict.__init__(self, *args, **kwargs)
        
    @property
    def frobenius_norm(self):
        """ Yields the Frobenius matrix norm.
            n = the square root of the sum of the absolute squares of the values.
            The matrix norm is used when calculating cosine similarity between documents.
        """
        if not self._norm: self._norm = l2_norm(self.itervalues())
        return self._norm
        
    norm = l2_norm = frobenius_norm
    
    def copy(self):
        return Vector(self, weight=self.weight)

    def __call__(self, vector={}):
        if isinstance(vector, (Document, Corpus)):
            vector = vector.vector
        if isinstance(vector, Vector) and self.weight != vector.weight:
            raise WeightError, "mixing %s vector with %s vector" % (self.weight, vector.weight)
        # Return a copy of the vector, updated with values from the other vector.
        # Only keys that appear in this vector will be updated (i.e. no new keys are added).
        V = self.copy(); dict.update(V, ((k,v) for k,v in vector.iteritems() if k in V)); return V

# These functions are useful if you work with a bare matrix instead of Document and Corpus.
# Given vectors must be lists of values (not iterators).
# See also k_means() and hierarchical.
def l2_norm(vector):
    return sum(x**2 for x in vector) ** 0.5

def cosine_similarity(vector1, vector2):
    return sum(a*b for a,b in izip(vector1, vector2)) / (l2_norm(vector1) * l2_norm(vector2) or 1)
    
def tf_idf(vectors):
    for i in range(len(vectors[0])):
        idf.append(sum(1.0 for v in vectors if v[i] > 0))
        idf[-1] = log(len(vectors) / (idf[-1] or 1))
    return [[v[i] * idf[i] for i in range(len(v))] for v in vectors]

#### CORPUS ##########################################################################################

#--- CORPUS ------------------------------------------------------------------------------------------

# LSA reduction methods:
NORM, TOP300 = "norm", "top300"

# Clustering methods:
KMEANS, HIERARCHICAL = "k-means", "hierarchical"

class Corpus(object):
    
    def __init__(self, documents=[]):
        """ A corpus is a collection of documents,
            where each document is a bag of (word, count)-items.
            Documents can be compared for similarity.
        """
        self._documents  = readonlylist() # List of documents (read-only).
        self._index      = {}             # Document.name => Document
        self._df         = {}             # Cache of document frequency per word.
        self._similarity = {}             # Cache of ((D1.id,D2.id), weight)-items (cosine similarity).
        self._vector     = None           # Cache of corpus vector with all the words in the corpus.
        self._reduced    = False          # True when LSA is applied to the vector space.
        self._update()
        self.extend(documents)
    
    @property
    def documents(self):
        return self._documents

    @property
    def reduced(self):
        return self._reduced
    
    @classmethod
    def build(Corpus, path, *args, **kwargs):
        """ Builds the corpus from a folder of text documents (e.g. path="folder/*.txt").
            Each file is split into words and the words are counted.
        """
        documents = []
        for f in glob.glob(path):
            kwargs["name"] = filename(f)
            documents.append(Document.open(f, *args, **kwargs))
        return Corpus(documents)
    
    @classmethod
    def load(Corpus, path):
        """ Loads the corpus from a pickle file created with Corpus.save().
        """
        return cPickle.load(open(path))
        
    def save(self, path, update=False):
        """ Saves the corpus as a pickle file at the given path.
            It can be loaded with Corpus.load().
            This is faster because the words in the documents do not need to be stemmed again,
            and cached vectors and similarities are stored
        """
        if update:
            for d1 in self.documents:
                for d2 in self.documents:
                    self.cosine_similarity(d1, d2) # Update the entire cache before saving.
        cPickle.dump(self, open(path, "w"))
    
    def _update(self):
        # Ensures that all document relevancy vectors are recalculated
        # when a document is added or deleted in the corpus (= new words or less words).
        self._vector = None
        self._df = {}
        self._similarity = {}
        for document in self.documents:
            document._vector = None
    
    def __len__(self):
        return len(self.documents)
    def __iter__(self):
        return iter(self.documents)
    def __getitem__(self, i):
        return self.documents.__getitem__(i)
    def __delitem__(self, i):
        d = list.pop(self.documents, i)
        d._corpus = None
        self._index.pop(d.name, None)
        self._update()
    def clear(self):
        self._documents = readonlylist()
        self._update()

    def append(self, document):
        """ Appends the given Document to the corpus, setting the corpus as its parent.
            The corpus is updated, meaning that the cache of vectors and similarities is cleared
            (relevancy and similarity weights will be different now that there is a new document).
        """
        document._corpus = self
        if document.name is not None:
            self._index[document.name] = document
        list.append(self.documents, document)
        self._update()
        
    def extend(self, documents):
        for document in documents:
            document._corpus = self
            if document.name is not None:
                self._index[document.name] = document
        list.extend(self.documents, documents)
        self._update()
        
    def remove(self, document):
        self.__delitem__(self.documents.index(document))
        
    def document(self, name):
        # This assumes document names are unique.
        if name in self._index:
            return self._index[name]
        if isinstance(name, int):
            return self.documents[name]
        
    def document_frequency(self, word):
        """ Returns the document frequency of a word.
            Returns 0 if there are no documents in the corpus (e.g. no word frequency).
            df = number of documents containing the word / number of documents.
            The more occurences of the word across the corpus, the higher its df weight.
        """
        if len(self.documents) == 0:
            return 0        
        if len(self._df) == 0:
            # Caching document frequency for each word gives a whopping 300x performance boost
            # (calculate all of them once). Drawback: if you need TF-IDF for just one document.
            for d in self.documents:
                for w in d.terms:
                    self._df[w] = (w in self._df) and self._df[w]+1 or 1
            for w, f in self._df.iteritems():
                self._df[w] /= float(len(self.documents))
        return self._df[word]
        
    df = document_frequency
    
    def inverse_document_frequency(self, word):
        """ Returns the inverse document frequency of a word.
            Returns None if the word is not in the corpus, or if there are no documents in the corpus.
            idf = log(1/df)
            The more occurences of the word, the lower its idf weight (log() makes it grow slowly).
        """
        df = self.df(word)
        return df != 0 and log(1.0/df) or None
        
    idf = inverse_document_frequency

    @property
    def vector(self):
        """ Returns a dictionary of (word, 0)-items from the corpus.
            It includes all words from all documents (i.e. it is the dimension of the vector space).
            If a document is given, sets the document word relevancy values in the vector.
        """
        if not self._vector: 
            self._vector = Vector();
            for d in self.documents:
                for word in d.terms: 
                    dict.setdefault(self._vector, word, 0)
        return self._vector
        # Note: 
        # - Corpus.vector is the dictionary of (word, 0)-items.
        # - Corpus.vector(document) returns a copy with the document's word relevancy values in it.
        # Words in a document that are not in the corpus vector are ignored
        # (e.g. the document was not in the corpus, this can be the case in Corpus.search() for example).
        # See Vector.__call__() why this is possible.
        
    def cosine_similarity(self, document1, document2):
        """ Returns the similarity between two documents in the corpus as a number between 0.0-1.0.
            The weight is based on the document relevancy vectors (i.e. tf-idf of words in the text).
            cos = dot(v1,v2) / (norm(v1) * norm(v2))
        """
        # If we already calculated the similarity between the given documents,
        # it is available in cache for reuse.
        id1 = document1.id
        id2 = document2.id
        if (id1,id2) in self._similarity: return self._similarity[(id1,id2)]
        if (id2,id1) in self._similarity: return self._similarity[(id2,id1)]
        # Calculate the matrix multiplication of the document vectors.
        #v1 = self.vector(document1)
        #v2 = self.vector(document2)
        #dot = cosine_similarity(v1.itervalues(), v2.itervalues())
        # This is exponentially faster (0.25 seconds vs. 8 seconds):
        dot = sum(document1.vector.get(w,0) * f for w, f in document2.vector.iteritems())
        # It makes no difference if we use v1.norm or document1.vector.norm,
        # so we opt for the second choice because it is cached.
        s = float(dot) / (document1.vector.norm * document2.vector.norm or 1)
        # Cache the similarity weight for reuse.
        self._similarity[(id1,id2)] = s
        return s
        
    similarity = cosine_similarity
    
    def nearest_neighbors(self, document, top=10):
        """ Returns a list of (weight, document)-tuples in the corpus, 
            sorted by similarity to the given document.
        """
        v = ((self.cosine_similarity(document, d), d) for d in self.documents)
        # Filter the input document from the matches.
        # Filter documents that scored 0.0 and return the top.
        v = [(w, d) for w, d in v if w > 0 and d.id != document.id]
        v = heapq.nsmallest(top, v, key=lambda v: (-v[0],v[1]))
        return ftlist(v)
        
    similar = related = nn = nearest_neighbors
        
    def vector_space_search(self, words=[], **kwargs):
        """ Returns related documents from the corpus, as a list of (weight, document)-tuples.
            The given words can be a string (one word), a list or tuple of words, or a Document.
        """
        top = kwargs.pop("top", 10)
        if not isinstance(words, (list, tuple)):
            words = [words]
        if not isinstance(words, Document):
            kwargs.setdefault("threshold", 0) # Same stemmer as other documents should be given.
            words = Document(" ".join(words), **kwargs)
        # Documents that are not in the corpus consisting only of words that are not in the corpus
        # have no related documents in the corpus.
        if len([w for w in words if w in self.vector]) == 0:
            return []
        return self.nearest_neighbors(words, top)
        
    search = vector_space_search
    
    def cluster(self, method=KMEANS, **kwargs):
        """ Clustering is an unsupervised machine learning method for grouping similar documents.
            For k-means clustering, returns a list of k clusters (each is a list of documents).
            For hierarchical clustering, returns a list of documents and Cluster objects.
            A Cluster is a list of documents and other clusters, with a Cluster.flatten() method.
        """
        # Create vectors as lists of tf-idf values, and a dictionary of vector => Document.
        # We need the dict to map the clustered vectors back to the actual documents.
        vectors = [with_id(self.vector(document).itervalues()) for document in self]
        map = dict((v.id, self.documents[i]) for i, v in enumerate(vectors))
        kw = kwargs.get
        if method == KMEANS:
            # def cluster(self, method=KMEANS, k=10, iterations=10, distance=COSINE)
            clusters = k_means(vectors, kw("k", 10), kw("iterations", 10), kw("distance", "cosine"))
            clusters = [[map[v.id] for v in cluster] for cluster in clusters]
        if method == HIERARCHICAL:
            # def cluster(self, method=HIERARCHICAL, k=1, iterations=1000, distance=COSINE)
            clusters = hierarchical(vectors, kw("k", 1), kw("iterations", 1000), kw("distance", "cosine"))
            clusters.traverse(visit=lambda cluster: \
                [cluster.__setitem__(i, map[v.id]) for i, v in enumerate(cluster) if not isinstance(v, Cluster)])
        return clusters

    def latent_semantic_analysis(self, dimensions=NORM, threshold=0):
        """ Latent Semantic Analysis is a statistical machine learning method 
            based on singular value decomposition (SVD).
            Document vectors (with the relevancy of each word in the document) are grouped in a matrix.
            The dimensionality of the matrix is then reduced to filter out noise,
            bringing words that are semantically related closer together.
            For each document, Document.vector is updated with the new values
            (this results in different cosine similarity).
        """
        # Based on: Joseph Wilk, Latent Semantic Analysis in Python, 2007
        # http://blog.josephwilk.net/projects/latent-semantic-analysis-in-python.html
        import numpy
        # The vector search space: a matrix with one row (vector) for each document.
        matrix = numpy.array([self.vector(d).values() for d in self.documents])
        # Singular value decomposition, where u * sigma * vt = svd(matrix).
        # Sigma is a diagonal matrix in decreasing order, of the same dimensions as the search space.
        # NumPy returns it as a flat list of just the diagonal values.
        if len(matrix) > 0 and len(matrix[0]) > 0:
            u, sigma, vt = numpy.linalg.svd(matrix, full_matrices=False)
            # Delete the smallest coefficients in diagonal matrix (e.g. at the end of list sigma).
            # The reduction will combine some dimensions so they are on more than one term.
            # The real difficulty and weakness of LSA is knowing how many dimensions to reduce.
            # Generally L2-norm or Frobenius norm is used:
            if dimensions == TOP300:
                dimensions = len(sigma)-300
            if dimensions == NORM:
                dimensions = int(round(numpy.linalg.norm(sigma)))
            if type(dimensions).__name__ == "function":
                dimensions = int(dimensions(sigma))
            for i in xrange(max(0,len(sigma)-dimensions), len(sigma)):
                sigma[i] = 0
            # Recalculate the matrix from the reduced sigma.
            matrix = numpy.dot(u, numpy.dot(numpy.diag(sigma), vt))
        # Map the new values to Document.vector.
        column = dict((k, i) for i, k in enumerate(self.vector.keys()))
        for i, document in enumerate(self.documents):
            document._vector = Vector((k, matrix[i][column[k]]) for k in document.vector)
        self._similarity = {}
        self._reduced = True
        
    reduce = lsa = latent_semantic_analysis

#def iter2array(iterator, typecode):
#    a = numpy.array([iterator.next()], typecode)
#    shape0 = a.shape[1:]
#    for (i, item) in enumerate(iterator):
#        a.resize((i+2,) + shape0)
#        a[i+1] = item
#    return a

#### CLUSTERING ######################################################################################
# Clustering assigns vectors to subsets based on a distance measure, 
# which determines how "similar" two vectors are.
# For example, for (x,y) coordinates in 2D we could use Euclidean distance ("as the crow flies");
# for document vectors we could use cosine similarity.

COSINE, EUCLIDEAN, MANHATTAN, HAMMING, CHEBYSHEV = \
    "cosine", "euclidean", "manhattan", "hamming", "chebyshev"

def distance(vector1, vector2, method=EUCLIDEAN):
    """ Returns Manhattan distance, squared Euclidean distance or cosine similarity.
    """
    if method == COSINE:
        return 1 - cosine_similarity(vector1, vector2)
    if method == EUCLIDEAN: # Squared distance is 1.5x faster.
        return sum((a-b)**2 for a, b in izip(vector1, vector2))
    if method == MANHATTAN:
        return sum(abs(a-b) for a, b in izip(vector1, vector2))
    if method == HAMMING:
        return sum( a != b  for a, b in izip(vector1, vector2))
    if method == CHEBYSHEV:
        return max(abs(a-b) for a, b in izip(vector1, vector2))

_distance = distance

def mean(vector):
    """ Returns the arithmetic mean of the given list of numbers.
    """
    m, i = 0, 0 # If a generator is given, len() won't work, use i instead.
    for i, v in enumerate(vector): 
        m += v
    return m / float(i+1)

def centroid(vectors):
    """ Returns the central vector from the given list of vectors.
        For example: for a list of (x,y) points forming a polygon, returns the geometric center.
    """
    return [mean(v[i] for v in vectors) for i in xrange(len(vectors[0]))]

class with_id(list):
    """ Returns a list copy with a unique list.id property.
        This is useful to cache centroids in the hierarchical clustering algorithm.
    """
    UID = 0
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.id = with_id.UID; with_id.UID+=1

#--- K-MEANS ----------------------------------------------------------------------------------------

def k_means(vectors, k, iterations=10, distance=EUCLIDEAN):
    """ Returns a list of k clusters, where each cluster is a list of related vectors.
        A vector is a list of numeric values, and all vectors must be of equal length.
    """
    # Custom distance function must be of the form: distance(vector1, vector2, **kwargs).
    distance, method = type(distance).__name__=="function" and (distance, None) or (_distance, distance)
    # Randomly partition the vectors across k clusters.
    if k < 2: 
        return [[v for v in vectors]]
    clusters = [[] for i in xrange(k)]
    for i, v in enumerate(sorted(vectors, key=lambda x: random())): # shuffled
        clusters[i%k].append(v)
    converged = False
    while not converged and iterations > 0 and k > 0:
        # Calculate the center of each cluster.
        centroids = [centroid(cluster) for cluster in clusters]
        converged = True
        iterations -= 1
        # For every vector in every cluster,
        # check if it is nearer to the center of another cluster (if so, assign it).
        # When visualized, this produces a Voronoi diagram.
        for i in xrange(len(clusters)):
            for v in clusters[i]:
                nearest = i
                for j in xrange(len(clusters)):
                    if distance(v, centroids[j], method=method) < \
                       distance(v, centroids[nearest], method=method):
                        nearest = j
                if nearest != i: # Other cluster is nearer.
                    clusters[nearest].append(clusters[i].pop(clusters[i].index(v)))
                    converged = False
    return clusters
    
kmeans = k_means

#--- HIERARCHICAL -----------------------------------------------------------------------------------
#  100 vectors with 6 features: 0.2 seconds.
# 1000 vectors with 6 features: 2 minutes.
# 3000 vectors with 6 features: 30 minutes.

class Cluster(list):
    
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
    
    @property
    def depth(self):
        """ Yields the maximum depth of nested clusters.
            Cluster((1, Cluster((2, Cluster((3, 4)))))).depth => 2.
        """
        return max([0] + [1+n.depth for n in self if isinstance(n, Cluster)])
    
    def flatten(self, depth=1000):
        """ Flattens nested clusters to a list, down to the given depth.
            Cluster((1, Cluster((2, Cluster((3, 4)))))).flatten(1) => [1, 2, Cluster(3, 4)].
        """
        a = []
        for item in self:
            if isinstance(item, Cluster) and depth > 0:
                a.extend(item.flatten(depth-1))
            else:
                a.append(item)
        return a
    
    def traverse(self, visit=lambda cluster: None):
        """ Calls the visit() function on this and each nested cluster.
        """
        visit(self)
        for item in self:
            if isinstance(item, Cluster): 
                item.traverse(visit)

    def __repr__(self):
        return "Cluster(%s)" % list.__repr__(self)[1:-1]

def hierarchical(vectors, k=1, iterations=1000, distance=EUCLIDEAN):
    """ Returns a Cluster containing k items (vectors or clusters with nested items).
    """
    # Custom distance function must be of the form: distance(vector1, vector2, **kwargs).
    distance, method = type(distance).__name__=="function" and (distance, None) or (_distance, distance)
    clusters = Cluster((v for v in sorted(vectors, key=lambda x: random())))
    centroids = [with_id(cluster) for cluster in clusters]
    D = {}
    for _ in range(iterations):
        if len(clusters) <= max(k,1): 
            break
        nearest, d0 = None, None
        for i, v1 in enumerate(centroids):
            for j, v2 in enumerate(centroids[i+1:]):
                v12 = (v1.id, v2.id)
                if v12 not in D: # Cache distance calculations for reuse.
                    D[v12] = distance(v1, v2, method=method)
                d = D[v12]
                if d0 is None or d < d0:
                    nearest, d0 = (i, j+i+1), d
        # Pairs of nearest clusters are merged as we move up the hierarchy:
        i, j = nearest
        merged = Cluster((clusters[i], clusters[j]))
        clusters.pop(j); centroids.pop(j)
        clusters.pop(i); centroids.pop(i)
        clusters.append(merged)
        centroids.append(with_id(centroid(merged.flatten())))
    del D
    return clusters

#k = hierarchical([(1,2),(3,4),(5,6),(7,8)], k=2)
#print k
#print k.depth

#### CLASSIFIER ######################################################################################

#--- CLASSIFIER BASE CLASS ---------------------------------------------------------------------------

class Classifier:

    @property
    def classes(self):
        return []
    types = classes
    
    @property
    def binary(self):
        return sorted(self.classes) in ([False,True], [0,1])
    
    def train(self, document, type):
        pass
        
    def classify(self, document):
        return None
    
    def save(self, path):
        cPickle.dump(self, open(path, "w"))

    @classmethod
    def load(self, path):
        return cPickle.load(open(path))
        
    @classmethod
    def test(self, corpus=[], d=0.65, folds=1, **kwargs):
        """ Returns an (accuracy, precision, recall, F-score)-tuple for the given corpus.
            The corpus is a list of documents or (wordlist, type)-tuples.
            2/3 of the data will be used as training material and tested against the other 1/3.
            With folds > 1, K-fold cross-validation is performed.
            For example: in 10-fold cross-validation ten tests are performed,
            each using a different 1/10 of the corpus as testing data.
            For non-binary classifiers, precision, recall and F-score are None.
        """
        corpus  = [isinstance(x, Document) and (x, x.type) or x for x in corpus]
        classes = set(type for document, type in corpus)
        binary  = len(classes) == 2 and sorted(classes) in ([False,True], [0,1])
        m = [0,0,0,0] # accuracy | precision | recall | F1-score.
        K = max(folds, 1)
        for k in range(K):
            classifier = self(**kwargs)
            t = len(corpus) / float(K) # Documents per fold.
            i = int(round(k * t))      # Corpus start index.
            j = int(round(k * t + t))  # Corpus stop index.
            if K == 1:
                i = int(len(corpus) * d)
                j = int(len(corpus))
            for document, type in corpus[:i] + corpus[j:]:
                # Train with 9/10 of the corpus, using 1/10 fold for testing.
                classifier.train(document, type)
            TP = TN = FP = FN = 0
            if not binary:
                # If the classifier predicts classes other than True/False,
                # we can only measure accuracy.
                for document, type in corpus[i:j]:
                    if classifier.classify(document) == type:
                        TP += 1
                m[0] += TP / float(j-i)
            else:
                # For binary classifiers, calculate the confusion matrix
                # to measure precision and recall.
                for document, b1 in corpus[i:j]:
                     b2 = classifier.classify(document)
                     if b1 and b2:
                         TP += 1 # true positive
                     elif not b1 and not b2:
                         TN += 1 # true negative
                     elif not b1 and b2:
                         FP += 1 # false positive (type I error)
                     elif b1 and not b2:
                         FN += 1 # false negative (type II error)
                m[0] += float(TP+TN) / ((TP+TN+FP+FN) or 1)
                m[1] += float(TP) / ((TP+FP) or 1)
                m[2] += float(TP) / ((TP+FN) or 1)
        m = [v/K for v in m]
        m[3] = binary and 2 * m[1] * m[2] / ((m[1] + m[2]) or 1) or 0 # F1-score.
        return binary and tuple(m) or (m[0], None, None, None)

#--- NAIVE BAYES CLASSIFIER --------------------------------------------------------------------------
# Based on: Magnus Lie Hetland, http://hetland.org/coding/python/nbayes.py

# We can't include these in the NaiveBayes class description,
# because you can't pickle functions:
# NBid1: store word index, used with aligned=True
# NBid1: ignore word index, used with aligned=False.
NBid1 = lambda type, v, i: (type, v, i)
NBid2 = lambda type, v, i: (type, v, 1)

class NaiveBayes(Classifier):
    
    def __init__(self, aligned=False):
        """ Naive Bayes is a simple supervised learning method for text classification.
            For example: if we have a set of documents of movie reviews (training data),
            and we know the star rating of each document, 
            we can predict the star rating for other movie review documents.
            With aligned=True, the word index is taken into account
            when training on lists of words.
        """
        self.fc = {}   # Frequency of each class (or type).
        self.ff = {}   # Frequency of each feature, as (type, feature, value)-tuples.
        self.count = 0 # Number of training instances.
        self._aligned = aligned

    @property
    def features(self):
        # Yields a dictionary of (word, frequency)-items.
        d = {}
        for (t,v,i), f in self.ff.iteritems():
            d[v] = (v in d) and d[v]+f or f
        return d
    
    @property
    def classes(self):
        return self.fc.keys()
    types = classes

    def train(self, document, type=None, weight=TF):
        """ Trains the classifier with the given document of the given type (i.e., class).
            A document can be a Document object or a list of words (or other hashable items).
            If no type is given, Document.type will be used instead.
        """
        id = self._aligned and NBid1 or NBid2
        if isinstance(document, Document):
            type = type is not None and type or document.type
            document = weight==TF and document.terms or document.vector
        if isinstance(document, (list, tuple)):
            document = dict.fromkeys(document, 1)
        self.fc[type] = self.fc.get(type, 0) + 1
        for i, (v,f) in enumerate(document.iteritems()):
            self.ff[id(type,v,i)] = self.ff.get(id(type,v,i), 0) + f
        self.count += 1

    def classify(self, document):
        """ Returns the type with the highest probability for the given document
            (a Document object or a list of words).
        """
        id = self._aligned and NBid1 or NBid2
        def d(document, type):
            # Bayesian discriminant, proportional to posterior probability.
            f = 1.0 * self.fc[type] / self.count
            for i, v in enumerate(document):
                f *= self.ff.get(id(type,v,i), 0) 
                f /= self.fc[type]
            return f
        try:
            return max((d(document, type), type) for type in self.fc)[1]
        except ValueError: # max() arg is an empty sequence
            return None
