#### PATTERN | EN | RULE-BASED SHALLOW PARSER ########################################################
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

from math      import log
from itertools import izip

try:
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

try: from pattern.en.inflect import singularize, conjugate
except:
    try: 
        import sys; sys.path.append(os.path.join(MODULE, ".."))
        from en.inflect import singularize, conjugate
    except:
        singularize = lambda w: w
        conjugate = lambda w,t: w
        
#-----------------------------------------------------------------------------------------------------
    
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

# Read-only dictionary, used for Document.terms and Corpus.document.
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

#### DOCUMENT ########################################################################################

#--- FREQUENCY+TERM LIST -----------------------------------------------------------------------------

# List of (frequency, term)-items that prints frequency with a rounded precision.
# This is used for the output of Document.keywords() and Corpus.related() (=easier to read).
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

PUNCTUATION = "[]():;,.!?\n\r\t\f "

def words(string, filter=lambda w: w.isalpha() and len(w)>1, punctuation=PUNCTUATION, **kwargs):
    """ Returns a list of words from the given string.
        Common punctuation marks are stripped from words.
    """
    if isinstance(string, unicode):
        string = string.replace(u"’", u"'")    
    words = string.replace("\n", "\n ")
    words = (w.strip(punctuation) for w in words.split(" "))
    words = [w for w in words if filter(w) is True]
    return words

PORTER, LEMMA = "porter", "lemma"
def stem(word, stemmer=PORTER, **kwargs):
    """ Returns the base form of the word when counting words in count().
        With stemmer=PORTER, the Porter2 stemming algorithm is used.
        With stemmer=LEMMA, either uses Word.lemma or inflect.singularize().
    """
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
    return word

def count(words=[], top=None, threshold=0, stemmer=PORTER, exclude=[], stopwords=False, **kwargs):
    """ Returns a dictionary of (word, count)-items.
        Words in the exclude list and stop words are not counted.
        Words whose count falls below (or equals) the given threshold are excluded.
        Words that are not in the given top most counted are excluded.
    """
    count = {}
    for word in words:
        if word.__class__.__name__ == "Word":
            w = word.string.lower()
        else:
            w = word.lower()
        if (stopwords or not w in _stopwords) and not w in exclude:
            if stemmer is not None:
                w = stem(word, stemmer, **kwargs)
            count[w] = (w in count) and count[w]+1 or 1
    for k in count.keys():
        if count[k] <= threshold: 
            del count[k]
    if top is not None:
        count = [(k,v) for v,k in sorted(((v,k) for k,v in count.iteritems()), reverse=True)]
        count = dict(count[:top])
    return count

#--- DOCUMENT ----------------------------------------------------------------------------------------
# Document is a bag of words in which each word is a feature.
# Document is represented as a vector of weighted (TF-IDF) features.

__UID = 0
def _uid():
    global __UID; __UID+=1; return __UID

TF, TFIDF = "tf", "tf-idf"

class Document(object):
    
    # Document(string="", filter, punctuation, top, threshold, stemmer, exclude, stopwords, name, type)
    def __init__(self, string="", **kwargs):
        """ A dictionary of (word, count)-items parsed from the string.
            Punctuation marks are stripped from the words.
            Stop words in the exclude list are excluded from the document.
            Only words whose count exceeds the threshold and who are in the top are included in the document.
        """
        kwargs.setdefault("threshold", 1)
        if isinstance(string, basestring):
            w = words(string, **kwargs)
        elif string.__class__.__name__ == "Sentence":
            w = string.words
        elif string.__class__.__name__ == "Text":
            w = []; [w.extend(sentence.words) for sentence in string]
        else:
            raise TypeError, "document string is not str, unicode, Sentence or Text."
        self._id     = _uid()               # Read-only Document.id, used as dictionary key.
        self._name   = kwargs.get("name")   # Name that describes the document content.
        self.type    = kwargs.get("type")   # Type that describes the category or class of the document.
        self.terms   = count(w, **kwargs)   # Dictionary of (word, count)-items.
        self._count  = None                 # Total number of words (minus stop words).
        self._vector = None                 # Cached tf-idf vector.
        self._corpus = None                 # Corpus this document belongs to.

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
        s = [[w]*n for w, n in self.terms.items()]
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
    def words(self):
        return self.terms
    
    @property
    def count(self):
        return self.__len__()

    def __len__(self):
        # Yields the number of words (excluding stop words) in the document.
        # Cache the word count so we can reuse it when calculating tf.
        if not self._count: self._count = sum(self.terms.values())
        return self._count
    def __iter__(self):
        return iter(self.terms)
    def __contains__(self, word):
        return word in self.terms
    def __getitem__(self, word):
        return self.terms[word]
    def get(self, word, default=None):
        return self.terms.get(word, default)
    
    def term_frequency(self, word):
        """ Returns the term frequency of a word in the document.
            tf = number of occurences of the word / number of words in document.
            The more occurences of the word, the higher its tf weight.
        """
        return float(self.terms.get(word, 0)) / (len(self) or 1)
        
    tf = term_frequency
    
    def relevancy(self, word, weight=TFIDF):
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
        
    tf_idf = tfidf = relevancy
    
    @property
    def vector(self):
        """ Yields a dictionary of (word, relevancy)-items from the document, based on tf-idf.
        """
        # See the Vector class below. It's just a dict with some extra functionality (copy, norm, etc.)
        if not self._vector: self._vector = Vector(((w, self.tfidf(w)) for w in self.terms))
        return self._vector
        
    def keywords(self, top=10, normalized=True):
        """ Returns a sorted list of (relevancy, word)-tuples that are top keywords in the document.
            With normalized=True, weights are normalized between 0.0 and 1.0 (their sum will be 1.0).
        """
        n = normalized and sum(self.vector.itervalues()) or 1.0
        v = ((f/n, w) for w, f in self.vector.iteritems())
        v = heapq.nsmallest(top, v, key=lambda v: (-v[0],v[1]))
        return ftlist(v)
    
    def similarity(self, document):
        """ Returns the similarity between the two documents as a number between 0.0-1.0.
            If both documents are in the same corpus the calculations are cached for reuse.
        """
        if self._corpus: 
            return self._corpus.similarity(self, document)
        elif document._corpus:
            return document._corpus.similarity(self, document)
        else:
            f = Corpus((self, document)).similarity(self, document)
            # Unlink both documents from the ad-hoc corpus:
            self._corpus = document._corpus = None
            return f
    
    def copy(self):
        d = Document(name=self.name); d.terms.update(self); return d
    
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

class Vector(dict):
    
    def __init__(self, *args, **kwargs):
        """ Vector is a dictionary of (word, weight)-items based on the terms in a Document.
        """
        self.weight = kwargs.pop("weight", TFIDF) # Vector weights based on tf or tf-idf?
        self._norm  = None
        dict.__init__(self, *args, **kwargs)
        
    @property
    def frobenius_norm(self):
        """ Yields the Frobenius matrix norm.
            n = the square root of the sum of the absolute squares of the values.
            The matrix norm is used when calculating cosine similarity between documents.
        """
        if not self._norm: self._norm = sum(x**2 for x in self.itervalues())**0.5
        return self._norm
        
    norm = l2_norm = frobenius_norm
    
    def copy(self):
        return Vector(self)

    def __call__(self, vector={}):
        if isinstance(vector, (Document, Corpus)):
            vector = vector.vector
        if isinstance(vector, Vector) and self.weight != vector.weight:
            raise WeightError, "mixing %s vector with %s vector" % (self.weight, vector.weight)
        # Return a copy of the vector, updated with values from the other vector.
        # Only keys that appear in this vector will be updated (i.e. no new keys are added).
        V = self.copy(); V.update((k,v) for k,v in vector.iteritems() if k in V); return V

#### CORPUS ##########################################################################################

#--- CORPUS ------------------------------------------------------------------------------------------

NORM, TOP300 = "norm", "top300"

class Corpus(object):
    
    def __init__(self, documents=[]):
        """ A corpus is a collection of documents,
            where each document is a bag of (word, count)-items.
            Documents can be compared for similarity.
        """
        self.documents   = readonlydict() # Document.id => Document
        self._index      = {}             # Document.name => Document
        self._df         = {}             # Cache of document frequency per word.
        self._similarity = {}             # Cache of ((D1.id,D2.id), weight)-items (cosine similarity).
        self._vector     = None           # Cache of corpus vector with all the words in the corpus.
        self._update()
        self.extend(documents)
    
    @classmethod
    def build(Corpus, path, *args, **kwargs):
        """ Builds the corpus from a folder of text documents (e.g. path="folder/*.txt").
            Each file is split into words and the words are counted.
        """
        documents = []
        for f in glob.glob(path):
            kwargs["name"] = name=filename(f)
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
            for d1 in self.documents.values():
                for d2 in self.documents.values():
                    self.cosine_similarity(d1, d2) # Update the entire cache before saving.
        cPickle.dump(self, open(path, "w"))
    
    def _update(self):
        # Ensures that all document relevancy vectors are recalculated
        # when a document is added or deleted in the corpus (= new words or less words).
        self._vector = None
        self._df = {}
        self._similarity = {}
        for document in self.documents.values():
            document._vector = None
    
    def __len__(self):
        return len(self.documents)
    def __iter__(self):
        return iter(self.documents.values())
    def __getitem__(self, id):
        return self.documents[id]
    def __delitem__(self, id):
        if not id in self.documents:
            return
        d = dict.pop(self.documents, id)
        d._corpus = None
        self._index.pop(d.name, None)
        self._update()
    def clear(self):
        dict.clear(self.documents)
        self._update()

    def append(self, document):
        """ Appends the given Document to the corpus, setting the corpus as its parent.
            The corpus is updated, meaning that the cache of vectors and similarities is cleared
            (relevancy and similarity weights will be different now that there is a new document).
        """
        document._corpus = self
        if document.name is not None:
            self._index[document.name] = document
        dict.__setitem__(self.documents, document.id, document)
        self._update()
        
    def extend(self, documents):
        for document in documents:
            document._corpus = self
            if document.name is not None:
                self._index[document.name] = document
            dict.__setitem__(self.documents, document.id, document)
        self._update()
        
    def remove(self, document):
        self.__delitem__(document.id)
        
    def document(self, name):
        # This assumes document names are unique.
        if name in self._index:
            return self._index[name]
        if isinstance(name, int):
            return self.documents.get(name)
        
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
            for d in self.documents.itervalues():
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
            [[self._vector.setdefault(word, 0) for word in d] for d in self.documents.values()]
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
        v1 = self.vector(document1)
        v2 = self.vector(document2)
        dot = sum(a*b for a,b in izip(v1.itervalues(), v2.itervalues()))
        # It makes no difference if we use v1.norm or document1.vector.norm,
        # so we opt for the second choice because it is cached.
        s = float(dot) / (document1.vector.norm * document2.vector.norm)
        # Cache the similarity weight for reuse.
        self._similarity[(id1,id2)] = s
        return s
        
    similarity = cosine_similarity
    
    def related(self, document, top=10):
        """ Returns a list of (weight, document)-tuples in the corpus, 
            sorted by similarity to the given document.
        """
        v = ((self.similarity(document, d), d) for d in self.documents.itervalues())
        # Filter the input document from the matches.
        # Filter documents that scored 0.0 and return the top.
        v = [(w, d) for w, d in v if w > 0 and d.id != document.id]
        v = heapq.nsmallest(top, v, key=lambda v: (-v[0],v[1]))
        return ftlist(v)
        
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
        return self.related(words, top)
        
    search = vector_space_search
        
    def latent_semantic_analysis(self, threshold=0, filter=NORM):
        """ Returns a Vectorspace matrix with document rows and word columns, containing relevancy values.
            Latent Semantic Analysis is a statistical machine learning method,
            based on singular value decomposition (SVD).
            The idea is to group document vectors (containing the relevancy of each word in the document) 
            in a matrix, and then to reduce the size of the matrix, filtering out "noise".
            The result is an approximation that brings together words with a similar co-currence pattern
            across documents. This results in "topic" vectors with words that are semantically related.
        """
        # Based on: Joseph Wilk, Latent Semantic Analysis in Python, 2007
        # http://blog.josephwilk.net/projects/latent-semantic-analysis-in-python.html
        import numpy
        #def diagsvd(array, m, n):
        #    # For array [1, 2, 3], m=4, n=5, returns an array with 4 rows and 5 columns:
        #    # [[1, 0, 0, 0, 0],
        #    #  [0, 2, 0, 0, 0],
        #    #  [0, 0, 3, 0, 0],
        #    #  [0, 0, 0, 0, 0]]
        #    a = []
        #    for i in range(m):
        #        a.append([0]*n)
        #        if i < len(array): 
        #            a[-1][i] = array[i]
        #    return a
        # The vector search space: a matrix with one row for each document, 
        # in which the word tf-idf weights are in the same order for each row.
        O = self.vector.keys()
        D = self.documents.values()
        sorted = lambda v, o: [v[k] for k in o]
        matrix = [sorted(self.vector(d), O) for d in D]
        matrix = numpy.array(matrix)
        # Filter words (columns) that have a low relevancy in all documents from the matrix.
        v = Vectorspace(self, matrix, documents=D, words=O)
        v.filter(threshold)
        # Singular value decomposition, where u * sigma * vt = svd(matrix).
        # Sigma is a diagonal matrix in decreasing order, of the same dimensions as the search space.
        # NumPy returns it as a flat list of just the diagonal values, which we pass to diagsvd().
        if len(v.matrix) > 0 and len(v.matrix[0]) > 0:
            u, sigma, vt = numpy.linalg.svd(v.matrix, full_matrices=False)
            # Delete the smallest coefficients in diagonal matrix (e.g. at the end of list sigma).
            # The reduction will combine some dimensions so they are on more than one term.
            # The real difficulty and weakness of LSA is knowing how many dimensions to remove.
            # Generally L2-norm or Frobenius norm are used:
            if filter == NORM:
                filter = int(round(numpy.linalg.norm(sigma)))
            if filter == TOP300:
                filter = len(sigma)-300
            if type(filter).__name__ == "function":
                filter = int(filter(sigma))
            for i in xrange(max(0,len(sigma)-filter), len(sigma)):
                sigma[i] = 0
            # Recalculate the matrix from the reduced sigma.
            # Return it as a Vectorspace (just some handy extra methods on top of the matrix).
            v.matrix = numpy.dot(u, numpy.dot(numpy.diag(sigma), vt))
        return v
        
    reduce = lsa = latent_semantic_analysis

#--- VECTOR SPACE ------------------------------------------------------------------------------------
# A facade for the output of Corpus.latent_semantic_analysis().

class Vectorspace:
    
    def __init__(self, corpus, matrix, documents, words):
        """ A Vectorspace is a thin wrapper around a NumPy array with easy access methods.
            Each row in the matrix has the word relevancy values for a document.
            Each column has the relevancy values for a word in each of the documents.
        """
        self.corpus    = corpus
        self.matrix    = matrix
        self.words     = list(words)
        self.documents = list(documents)
        self._index1   = dict(((d.id, (i,d)) for i,d in enumerate(documents)))
        self._index2   = dict(((w,i) for i,w in enumerate(words)))
            
    def keywords(self, id, top=10):
        """ Returns a list of (relevancy, word)-tuples for the given document (by id).
        """
        if isinstance(id, Document):
            id = id.id
        if id not in self._index1:
            return []
        v = self.matrix[self._index1[id][0]]
        v = izip(v, self.words)
        v = heapq.nsmallest(top, v, key=lambda v: (-v[0],v[1]))
        return ftlist(v)
        
    def search(self, word, top=10, stemmer=PORTER):
        """ Returns a list of (relevancy, document)-tuples for the given word.
        """
        w = stem(word, stemmer)
        if w not in self._index2:
            return []
        v = self.matrix[:,self._index2[w]]
        v = izip(v, self.documents)
        v = heapq.nsmallest(top, v, key=lambda v: (-v[0],v[1]))
        return ftlist(v)

    def filter(self, threshold=0):
        """ Removes columns (words) whose relevancy is less than or equal the threshold in all documents.
        """
        import numpy
        noise = numpy.max(self.matrix, axis=0) # Maximum value for each column.
        noise = [i for i,v in enumerate(noise) if v<=threshold] # Indices where max <= threshold.
        self.matrix = numpy.delete(self.matrix, noise, axis=1)
        for i in reversed(noise):
            del self._index2[self.words[i]]
            del self.words[i]
            
    def save(self, path):
        cPickle.dump(self, open(path, "w"))
    
    @classmethod
    def load(self, path):
        return cPickle.load(open(path))

#### CLASSIFIER ######################################################################################

#--- CLASSIFIER BASE CLASS ---------------------------------------------------------------------------

class Classifier:
    
    def train(self, document, type):
        pass
        
    def classify(self, document):
        return None

    @classmethod
    def load(self, path):
        return cPickle.load(open(path))

    def save(self, path):
        cPickle.dump(self, open(path, "w"))

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

    def train(self, document, type=None, weight=TF):
        """ Trains the classifier with the given document of the given type (i.e., class).
            A document can be a Document object or a list of words.
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
    
    @classmethod
    def test(self, corpus=[], d=0.65, aligned=False):
        """ Returns the accuracy of the Naive Bayes classifier for the given corpus.
            The corpus is a list of documents or (wordlist, type)-tuples.
            2/3 of the data will be used as training material and tested against the other 1/3.
        """
        corpus = [isinstance(x, Document) and (x, x.type) or x for x in corpus]
        d = int(d * len(corpus))
        train, test = corpus[:d], corpus[d:]
        classifier = NaiveBayes(aligned)
        n = 0
        for document, type in train:
            classifier.train(document, type)
        for document, type in test:
            n += classifier.classify(document) == type
        return n / float(len(test))
