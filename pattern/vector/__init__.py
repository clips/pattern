#### PATTERN | VECTOR ##############################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Vector space model, based on cosine similarity using tf-idf.
# Documents (e.g., a sentence or a text) are represented as bag-of-words:
# the unordered words in the document and their (relative frequency).
# The dictionary of word => frequency items is called the document vector.
# The frequency weight is either TF or TF-IDF (term frequency-inverse document frequency, i.e.,
# the relevance of a word in a document offset by the frequency of the word in all documents).
# Documents can be grouped in a Model to calculate TF-IDF and cosine similarity, 
# which measures similarity (0.0-1.0) between documents based on the cosine distance metric.
# A document cay have a type (or label). A model of labeled documents can be used to train
# a classifier. A classifier can be used to predict the label of unlabeled documents.
# This is called supervised machine learning (since we provide labeled training examples).
# Unsupervised machine learning or clustering can be used to group unlabeled documents
# into subsets based on their similarity.

import sys
import os
import re
import glob
import heapq
import codecs
import cPickle; BINARY=1
import stemmer; _stemmer=stemmer

from math        import log, exp, sqrt
from time        import time
from random      import random, choice
from itertools   import izip, chain
from bisect      import insort
from operator    import itemgetter
from StringIO    import StringIO
from codecs      import open
from collections import defaultdict

try:
    MODULE = os.path.dirname(os.path.abspath(__file__))
except:
    MODULE = ""

try: from pattern.text import singularize, predicative, conjugate
except:
    try: 
        import sys; sys.path.insert(0, os.path.join(MODULE, ".."))
        from text import singularize, predicative, conjugate
    except:
        singularize = lambda w, **k: w
        predicative = lambda w, **k: w
        conjugate   = lambda w, t, **k: w

#--- STRING FUNCTIONS ------------------------------------------------------------------------------
# Latin-1 (ISO-8859-1) encoding is identical to Windows-1252 except for the code points 128-159:
# Latin-1 assigns control codes in this range, Windows-1252 has characters, punctuation, symbols
# assigned to these code points.

def decode_string(v, encoding="utf-8"):
    """ Returns the given value as a Unicode string (if possible).
    """
    if isinstance(encoding, basestring):
        encoding = ((encoding,),) + (("windows-1252",), ("utf-8", "ignore"))
    if isinstance(v, str):
        for e in encoding:
            try: return v.decode(*e)
            except:
                pass
        return v
    return unicode(v)

def encode_string(v, encoding="utf-8"):
    """ Returns the given value as a Python byte string (if possible).
    """
    if isinstance(encoding, basestring):
        encoding = ((encoding,),) + (("windows-1252",), ("utf-8", "ignore"))
    if isinstance(v, unicode):
        for e in encoding:
            try: return v.encode(*e)
            except:
                pass
        return v
    return str(v)

decode_utf8 = decode_string
encode_utf8 = encode_string
    
def shi(i, base="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"):
    """ Returns a short string hash for a given int.
    """
    s = []
    while i > 0:
        i, r = divmod(i, len(base))
        s.append(base[r])
    return "".join(reversed(s))

#--- LIST FUNCTIONS --------------------------------------------------------------------------------

def shuffled(list):
    """ Yields a copy of the given list with the items in random order.
    """
    return sorted(list, key=lambda x: random())

def chunk(list, n):
    """ Yields n successive equal-sized chunks from the given list.
    """
    i = 0
    for m in xrange(n):
        j = i + len(list[m::n]) 
        yield list[i:j]
        i = j

def pimap(iterable, function, *args, **kwargs):
    """ Returns an iterator of function(x, *args, **kwargs) for the iterable (x1, x2, x3, ...).
        The function is applied in parallel over available CPU cores.
    """
    from multiprocessing import Pool
    global worker
    def worker(x):
        return function(x, *args, **kwargs)
    return Pool(processes=None).imap(worker, iterable)

#--- READ-ONLY DICTIONARY --------------------------------------------------------------------------

class ReadOnlyError(Exception):
    pass

# Read-only dictionary, used for Document.terms and Document.vector
# (updating these directly invalidates the Document and Model cache).
class readonlydict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    @classmethod
    def fromkeys(cls, k, default=None):
        return readonlydict((k, default) for k in k)
    def copy(self):
        return readonlydict(self)
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

# Read-only list, used for Model.documents.
class readonlylist(list):
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
    def __setitem__(self, i, v):
        raise ReadOnlyError
    def __delitem__(self, i):
        raise ReadOnlyError
    def append(self, v):
        raise ReadOnlyError
    def extend(self, v):
        raise ReadOnlyError
    def insert(self, i, v):
        raise ReadOnlyError
    def remove(self, v):
        raise ReadOnlyError
    def pop(self, i):
        raise ReadOnlyError

#### DOCUMENT ######################################################################################

#--- STOP WORDS ------------------------------------------------------------------------------------
# A dictionary of (language, words)-items of function words, for example: {"en": {"the": True}}.
# - de: 950+, Marco Götze & Steffen Geyer
# - en: 550+, Martin Porter (http://snowball.tartarus.org)
# - es: 300+, Martin Porter
# - fr: 550+, Martin Porter, Audrey Baneyx
# - nl: 100+, Martin Porter, Damien van Holten

stopwords = _stopwords = {}
for f in glob.glob(os.path.join(MODULE, "stopwords-*.txt")):
    language = os.path.basename(f)[-6:-4] # stopwords-[en].txt
    w = codecs.open(f, encoding="utf-8")
    w = (w.strip() for w in w.read().split(","))
    stopwords[language] = dict.fromkeys(w, True)

# The following English words could also be meaningful nouns:
#for w in ["mine", "us", "will", "can", "may", "might"]:
#    stopwords["en"].pop(w)

#--- WORD COUNT ------------------------------------------------------------------------------------
# Simple bag-of-word models are often made up of word frequencies or character trigram frequencies.

PUNCTUATION = ".,;:!?()[]{}`''\"@#$^&*+-|=~_"

def words(string, filter=lambda w: w.lstrip("'").isalnum(), punctuation=PUNCTUATION, **kwargs):
    """ Returns a list of words (alphanumeric character sequences) from the given string.
        Common punctuation marks are stripped from words.
    """
    string = decode_utf8(string)
    string = re.sub(r"([a-z|A-Z])'(m|s|ve|re|ll|d)", u"\\1 `'\\2", string)
    words = (w.strip(punctuation).replace(u"`'", "'", 1) for w in string.split())
    words = (w for w in words if filter is None or filter(w) is not False)
    words = [w for w in words if w]
    return words

PORTER, LEMMA = "porter", "lemma"
def stem(word, stemmer=PORTER, **kwargs):
    """ Returns the base form of the word when counting words in count().
        With stemmer=PORTER, the Porter2 stemming algorithm is used.
        With stemmer=LEMMA, either uses Word.lemma or inflect.singularize().
        (with optional parameter language="en", pattern.en.inflect is used).
    """
    if isinstance(word, basestring):
        word = decode_utf8(word.lower())
    if stemmer is None:
        return word.lower()
    if stemmer == PORTER:
        return _stemmer.stem(word, **kwargs)
    if stemmer == LEMMA:
        if word.__class__.__name__ == "Word":
            w = word.string.lower()
            if word.lemma is not None:
                return word.lemma
            if word.pos == "NNS":
                return singularize(w)
            if word.pos.startswith(("VB", "MD")):
                return conjugate(w, "infinitive") or w
            if word.pos.startswith(("JJ",)):
                return predicative(w)
            if word.pos.startswith(("DT", "PR", "WP")):
                return singularize(w, pos=pos)
        return singularize(word, pos=kwargs.get("pos", "noun"))
    if hasattr(stemmer, "__call__"):
        return decode_utf8(stemmer(word))
    return word.lower()

def count(words=[], top=None, threshold=0, stemmer=None, exclude=[], stopwords=False, language=None, **kwargs):
    """ Returns a dictionary of (word, count)-items, in lowercase.
        Words in the exclude list and stop words (by default, English) are not counted.
        Words whose count falls below (or equals) the given threshold are excluded.
        Words that are not in the given top most counted are excluded.
    """
    # An optional dict-parameter can be used to specify a subclass of dict, 
    # e.g., count(words, dict=readonlydict) as used in Document.
    count = kwargs.get("dict", dict)()
    for w in words:
        if w.__class__.__name__ == "Word":
            w = w.string.lower()
        if isinstance(w, basestring):
            w = w.lower()
        if (stopwords or not w in _stopwords.get(language or "en", ())) and not w in exclude:
            if stemmer is not None:
                w = stem(w, stemmer, **kwargs)
            dict.__setitem__(count, w, (w in count) and count[w]+1 or 1)
    for k in count.keys():
        if count[k] <= threshold:
            dict.__delitem__(count, k)
    if top is not None:
        count = count.__class__(heapq.nsmallest(top, count.iteritems(), key=lambda (k,v): (-v,k)))
    return count

def character_ngrams(string="", n=3, top=None, threshold=0, exclude=[], **kwargs):
    """ Returns a dictionary of (character n-gram, count)-items, in lowercase.
        N-grams in the exclude list are not counted.
        N-grams whose count falls below (or equals) the given threshold are excluded.
        N-grams that are not in the given top most counted are excluded.
    """
    # An optional dict-parameter can be used to specify a subclass of dict, 
    # e.g., count(words, dict=readonlydict) as used in Document.
    count = kwargs.get("dict", dict)()
    for w in re.findall(r"(?=(" + "."*n + "))", string.lower()):
        if w not in exclude:
            dict.__setitem__(count, w, (w in count) and count[w]+1 or 1)
    for k in count.keys():
        if count[k] <= threshold:
            dict.__delitem__(count, k)
    if top is not None:
        count = count.__class__(heapq.nsmallest(top, count.iteritems(), key=lambda (k,v): (-v,k)))
    return count
    
chngrams = character_ngrams

def trigrams(*args, **kwargs):
    kwargs["n"]=3; return character_ngrams(*args, **kwargs)

#--- DOCUMENT --------------------------------------------------------------------------------------
# A Document is a bag of words in which each word is a feature.
# A Document is represented as a vector of weighted (TF-IDF) features.
# A Document can be part of a training model used for learning (i.e., clustering or classification).

_UID = 0
_SESSION = shi(int(time() * 1000)) # Avoid collision with pickled documents.
def _uid():
    """ Returns a string id, for example: "NPIJYaS-1", "NPIJYaS-2", ...
        The string part is based on the current time, the number suffix is auto-incremental.
    """
    global _UID; _UID+=1; return _SESSION+"-"+str(_UID)

# Term relevance weight:
TF, TFIDF, TF_IDF, WEIGHT_BINARY, WEIGHT_ORIGINAL = "tf", "tf-idf", "tf-idf", "binary", "original"

class Document(object):
    # Document(string = "", 
    #          filter = lambda w: w.lstrip("'").isalnum(),
    #     punctuation = PUNCTUATION,
    #             top = None,
    #       threshold = 0, 
    #         stemmer = None, 
    #         exclude = [], 
    #       stopwords = False, 
    #        language = None,
    #            name = None, 
    #            type = None
    # )
    def __init__(self, string="", **kwargs):
        """ An unordered bag-of-words representation of the given string, list, dict or Sentence.
            Lists can contain tuples (of), strings or numbers.
            Dicts can contain tuples (of), strings or numbers as keys, and floats as values.
            Document.terms stores a dict of (word, count)-items.
            Document.vector stores a dict of (word, weight)-items, 
            where weight is the term frequency normalized (0.0-1.0) to remove document length bias.
            Punctuation marks are stripped from the words.
            Stop words in the exclude list are excluded from the document.
            Only top words whose count exceeds the threshold are included in the document.        
        """
        kwargs.setdefault("filter", lambda w: w.lstrip("'").isalnum())
        kwargs.setdefault("threshold", 0)
        kwargs.setdefault("dict", readonlydict)
        # A string of words: map to read-only dict of (word, count)-items.
        if string is None:
            w = kwargs["dict"]()
            v = None
        elif isinstance(string, basestring):
            w = words(string, **kwargs)
            w = count(w, **kwargs)
            v = None
        # A list of words: map to read-only dict of (word, count)-items.
        elif isinstance(string, (list, tuple)) and not string.__class__.__name__ == "Text":
            w = string
            w = count(w, **kwargs)
            v = None
        # A Vector of (word, TF weight)-items: copy as document vector.
        elif isinstance(string, Vector) and string.weight == TF:
            w = string
            w = kwargs["dict"](w)
            v = Vector(w)
        # A Vector of (word, TF-IDF weight)-items: copy as document vector.
        elif isinstance(string, Vector) and string.weight == TF_IDF:
            w = string
            w = kwargs["dict"](w) # XXX term count is lost.
            v = Vector(w)
        # A dict of (word, count)-items: make read-only.
        elif isinstance(string, dict):
            w = string
            w = kwargs["dict"](w)
            v = None
        # pattern.en.Sentence with Word objects: can use stemmer=LEMMA.
        elif string.__class__.__name__ == "Sentence":
            w = string.words
            w = [w for w in w if kwargs["filter"](w.string)]
            w = count(w, **kwargs)
            v = None
        # pattern.en.Text with Sentence objects, can use stemmer=LEMMA.
        elif string.__class__.__name__ == "Text":
            w = []; [w.extend(sentence.words) for sentence in string]
            w = [w for w in w if kwargs["filter"](w.string)]
            w = count(w, **kwargs)
            v = None
        else:
            raise TypeError, "document string is not str, unicode, list, dict, Vector, Sentence or Text."
        self._id          = _uid()             # Document ID, used when comparing objects.
        self._name        = kwargs.get("name") # Name that describes the document content.
        self._type        = kwargs.get("type", # Type that describes the category or class of the document.
                            kwargs.get("label"))
        self._language    = kwargs.get("language")
        self._description = kwargs.get("description", "")
        self._terms       = w                  # Dictionary of (word, count)-items.
        self._vector      = v                  # Cached tf-idf vector.
        self._count       = None               # Total number of words (minus stop words).
        self._model       = None               # Parent Model.

    @classmethod
    def load(cls, path):
        """ Returns a new Document from the given text file path.
            The given text file must be generated with Document.save().
        """
        # Open unicode file.
        s = open(path, "rb").read()
        s = s.lstrip(codecs.BOM_UTF8)
        s = decode_utf8(s)
        a = {}
        v = {}
        # Parse document name and type.
        # Parse document terms and frequency.
        for s in s.splitlines():
            if s.startswith("#"): # comment
                a["description"] = a.get("description", "") + s.lstrip("#").strip() + "\n"
            elif s.startswith("@name:"):
                a["name"] = s[len("@name:")+1:].replace("\\n", "\n")
            elif s.startswith("@type:"):
                a["type"] = s[len("@type:")+1:].replace("\\n", "\n")
            elif s.startswith("@language:"):
                a["lang"] = s[len("@lang:")+1:].replace("\\n", "\n")
            else:
                s = s.split(" ")
                w, f = " ".join(s[:-1]), s[-1]
                if f.isdigit():
                    v[w] = int(f)
                else:
                    v[w] = float(f)
        return cls(v, name = a.get("name"), 
                      type = a.get("type"), 
                  language = a.get("lang"),
               description = a.get("description").rstrip("\n"))
    
    def save(self, path):
        """ Saves the document as a text file at the given path.
            The file content has the following format:
            # Cat document.
            @name: cat
            @type: animal
            a 3
            cat 2
            catch 1
            claw 1
            ...
        """
        s = []
        # Parse document description.
        for x in self.description.split("\n"):
            s.append("# %s" % x)
        # Parse document name, type and language.
        for k, v in (("@name:", self.name), ("@type:", self.type), ("@lang:", self.language)):
            if v is not None:
                s.append("%s %s" % (k, v.replace("\n", "\\n")))
        # Parse document terms and frequency.
        for w, f in sorted(self.terms.items()):
            if isinstance(f, int):
                s.append("%s %i" % (w, f))
            if isinstance(f, float):
                s.append("%s %.3f" % (w, f))
        s = "\n".join(s)
        s = encode_utf8(s)
        # Save unicode file.
        f = open(path, "wb")
        f.write(codecs.BOM_UTF8)
        f.write(s)
        f.close()

    def _get_model(self):
        return self._model
    def _set_model(self, model):
        self._vector = None
        self._model and self._model._update()
        self._model = model
        self._model and self._model._update()
        
    model = corpus = property(_get_model, _set_model)

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
    def label(self):
        return self._type
        
    @property
    def language(self):
        return self._language
        
    @property
    def description(self):
        return self._description
    
    @property
    def terms(self):
        return self._terms
    
    @property
    def words(self):
        return self._terms
    
    @property
    def features(self):
        return self._terms.keys()
    
    @property
    def count(self):
        # Yields the number of words in the document representation.
        # Cache the word count so we can reuse it when calculating tf.
        if not self._count: self._count = sum(self.terms.values())
        return self._count

    def __len__(self):
        return len(self.terms)
    def __iter__(self):
        return iter(self.terms)
    def __contains__(self, word):
        return word in self.terms
    def __getitem__(self, word):
        return self.terms.__getitem__(word)
    def get(self, word, default=None):
        return self.terms.get(word, default)
    
    def term_frequency(self, word):
        """ Returns the term frequency of a given word in the document (0.0-1.0).
            tf = number of occurences of the word / number of words in document.
            The more occurences of the word, the higher its relative tf weight.
        """
        return float(self.terms.get(word, 0)) / (self.count or 1)
        
    tf = term_frequency
    
    def term_frequency_inverse_document_frequency(self, word, weight=TFIDF):
        """ Returns the word relevance as tf * idf (0.0-1.0).
            The relevance is a measure of how frequent the word occurs in the document,
            compared to its frequency in other documents in the model.
            If the document is not incorporated in a model, simply returns tf weight.
        """
        w = self.tf(word)
        if weight == TFIDF and self.model:
            # Use tf if no model, or idf==None (happens when the word is not in the model).
            idf = self.model.idf(word)
            idf = idf is None and 1 or idf
            w *= idf
        return w
        
    tf_idf = tfidf = term_frequency_inverse_document_frequency
    
    @property
    def vector(self):
        """ Yields the document vector, a dictionary of (word, relevance)-items from the document.
            The relevance is tf, or tf * idf if the document is part of a Model.
            The document vector is used to calculate similarity between two documents,
            for example in a clustering or classification algorithm.
        """
        if not self._vector:
            # See the Vector class below = a dict with extra functionality (copy, norm).
            # Model.weight (TFIDF or TF) determines how the weights will be calculated.
            # When a document is added/deleted from a model, the cached vector is deleted.
            if getattr(self.model, "weight", TF) == TFIDF:
                w, f = TFIDF, self.tf_idf
            elif getattr(self.model, "weight", TF) == WEIGHT_ORIGINAL:
                w, f = WEIGHT_ORIGINAL, (lambda word: float(self.terms.get(word, 0)))
            elif getattr(self.model, "weight", TF) == WEIGHT_BINARY:
                w, f = WEIGHT_BINARY, (lambda word: 1 if float(self.terms.get(word, 0)) > 0 else 0)
            else:
                w, f = TF, self.tf
            self._vector = Vector(((w, f(w)) for w in self.terms), weight=w)
        return self._vector

    def keywords(self, top=10, normalized=True):
        """ Returns a sorted list of (relevance, word)-tuples that are top keywords in the document.
            With normalized=True, weights are normalized between 0.0 and 1.0 (their sum will be 1.0).
        """
        n = normalized and sum(self.vector.itervalues()) or 1.0
        v = ((f/n, w) for w, f in self.vector.iteritems())
        v = heapq.nsmallest(top, v, key=lambda v: (-v[0], v[1]))
        return v
    
    def cosine_similarity(self, document):
        """ Returns the similarity between the two documents as a number between 0.0-1.0.
            If both documents are part of the same model the calculations are cached for reuse.
        """
        if self.model: 
            return self.model.cosine_similarity(self, document)
        if document.model:
            return document.model.cosine_similarity(self, document)
        return cosine_similarity(self.vector, document.vector)
            
    similarity = cosine_similarity
    
    def copy(self):
        d = Document(None, name=self.name, type=self.type, description=self.description)
        dict.update(d.terms, self.terms)
        return d
    
    def __eq__(self, document):
        return isinstance(document, Document) and self.id == document.id
    def __ne__(self, document):
        return not self.__eq__(document)
    
    def __repr__(self):
        return "Document(id=%s%s)" % (
            repr(self._id), self.name and ", name=%s" % repr(self.name) or "")

#--- VECTOR ----------------------------------------------------------------------------------------
# A Vector represents document terms (called features) and their tf or tf * idf relevance weight.
# A Vector is a sparse represenation: i.e., a dictionary with only those features > 0.
# This is fast, usually also faster than LSA which creates a full vector space with non-zero values.
# Document vectors can be used to calculate similarity between documents,
# for example in a clustering or classification algorithm.

# To find the average feature length in a model: 
# sum(len(d.vector) for d in model.documents) / float(len(model))

class Vector(readonlydict):
    
    id = 1
    
    def __init__(self, *args, **kwargs):
        """ A dictionary of (feature, weight)-items of the features (terms, words) in a Document.
            A vector can be used to compare the document to another document with a distance metric.
            For example, vectors with 2 features (x, y) can be compared using 2D Euclidean distance.
            Vectors that represent text documents can be compared using cosine similarity.
        """
        self.id     = Vector.id; Vector.id+=1  # Unique ID.
        self.weight = kwargs.pop("weight", TF) # Vector weights based on tf or tf-idf?
        self._norm  = None
        readonlydict.__init__(self, *args, **kwargs)
    
    @property
    def features(self):
        return self.keys()
    
    @property
    def l2_norm(self):
        """ Yields the Frobenius matrix norm (cached).
            n = the square root of the sum of the absolute squares of the values.
            The matrix norm is used to normalize (0.0-1.0) cosine similarity between documents.
        """
        if self._norm is None: 
            self._norm = sum(w * w for w in self.itervalues()) ** 0.5
        return self._norm
        
    norm = l2 = L2 = L2norm = l2norm = L2_norm = l2_norm
    
    def copy(self):
        return Vector(self, weight=self.weight)

    def __call__(self, vector={}):
        """ Vector(vector) returns a new vector updated with values from the given vector.
            No new features are added. For example: Vector({1:1, 2:2})({1:0, 3:3}) => {1:0, 2:2}.
        """
        if isinstance(vector, (Document, Model)):
            vector = vector.vector
        v = self.copy()
        s = dict.__setitem__
        for f, w in vector.iteritems():
            if f in v:
                s(v, f, w)
        return v

#--- VECTOR DISTANCE -------------------------------------------------------------------------------
# The "distance" between two vectors can be calculated using different metrics.
# For vectors that represent text, cosine similarity is a good metric.
# For more information, see Domain Similarity Measures (Vincent Van Asch, 2012).

# The following functions can be used if you work with Vectors or plain dictionaries, 
# instead of Documents and Models (which use caching for cosine similarity).

def features(vectors=[]):
    """ Returns the set of unique features for all given vectors.
    """
    return set(f for f in chain(*vectors))

_features = features

def relative(v):
    """ Returns the vector with feature weights normalized so that their sum is 1.0 (in-place).
    """
    n = float(sum(v.itervalues())) or 1.0
    s = dict.__setitem__
    for f in v: # Modified in-place.
        s(v, f, v[f] / n)
    return v
    
rel = relative

def l2_norm(v):
    """ Returns the L2-norm of the given vector.
    """
    if isinstance(v, Vector):
        return v.l2_norm
    return sum(w * w for w in v.itervalues()) ** 0.5
    
norm = l2 = L2 = L2norm = l2norm = L2_norm = l2_norm

def cosine_similarity(v1, v2):
    """ Returns the cosine similarity of the given vectors.
    """
    s = sum(v1.get(f, 0) * w for f, w in v2.iteritems())
    s = float(s) / (l2_norm(v1) * l2_norm(v2) or 1)
    return s
    
cos = cosine_similarity

def tf_idf(vectors=[], base=2.71828): # e
    """ Calculates tf * idf on the vector feature weights (in-place).
    """
    df = {}
    for v in vectors:
        for f in v:
            if v[f] != 0:
                df[f] = df[f] + 1 if f in df else 1.0
    n = len(vectors)
    s = dict.__setitem__
    for v in vectors: 
        for f in v: # Modified in-place.
            s(v, f, v[f] * (log(n / df[f], base)))
    return vectors

tfidf = tf_idf

COSINE, EUCLIDEAN, MANHATTAN, HAMMING = \
    "cosine", "euclidean", "manhattan", "hamming"
    
def distance(v1, v2, method=COSINE):
    """ Returns the distance between two vectors.
    """
    if method == COSINE:
        return 1 - cosine_similarity(v1, v2)
    if method == EUCLIDEAN: # Squared Euclidean distance is used (1.5x faster).
        return sum((v1.get(w, 0) - v2.get(w, 0)) ** 2 for w in set(chain(v1, v2)))
    if method == MANHATTAN:
        return sum(abs(v1.get(w, 0) - v2.get(w, 0)) for w in set(chain(v1, v2)))
    if method == HAMMING:
        d = sum(not (w in v1 and w in v2 and v1[w] == v2[w]) for w in set(chain(v1, v2))) 
        d = d / float(max(len(v1), len(v2)) or 1)
        return d
    if isinstance(method, type(distance)):
        # Given method is a function of the form: distance(v1, v2) => float.
        return method(v1, v2)

_distance  = distance

def entropy(p=[]):
    """ Returns the Shannon entropy for the given list of probabilities.
    """
    s = float(sum(p)) or 1
    return -sum(x / s * log(x / s, len(p)) for x in p if x != 0) 

#### MODEL #########################################################################################

#--- MODEL -----------------------------------------------------------------------------------------
# A Model is a representation of a collection of documents as bag-of-words.
# A Model is a matrix (or vector space) with features as columns and feature weights as rows,
# where each document is a vector of features (e.g., words) and feature weights (e.g., frequency).
# The matrix is used to calculate adjusted weights (e.g., tf * idf), document similarity and LSA.

# Export formats:
ORANGE, WEKA = "orange", "weka"

# LSA reduction methods:
NORM, L1, L2, TOP300 = "norm", "L1", "L2", "top300"

# Feature selection methods:
IG = INFOGAIN = "infogain"

# Clustering methods:
KMEANS, HIERARCHICAL, ALL = "k-means", "hierarchical", "all"

class Model(object):
    
    def __init__(self, documents=[], weight=TFIDF):
        """ A model is a bag-of-word representation of a corpus of documents, 
            where each document vector is a bag of (word, relevance)-items.
            Vectors can then be compared for similarity using a distance metric.
        """
        self.description = ""             # Description of the dataset: author e-mail, etc.
        self._documents  = readonlylist() # List of documents (read-only).
        self._index      = {}             # Document.name => Document
        self._df         = {}             # Cache of document frequency per word.
        self._cos        = {}             # Cache of ((d1.id, d2.id), relevance)-items (cosine similarity).
        self._ig         = {}             # Cache of (word, information gain)-items.
        self._vector     = None           # Cache of model vector with all the features in the model.
        self._lsa        = None           # LSA matrix with reduced dimensionality.
        self._weight     = weight         # Weight used in Document.vector (TFIDF or TF).
        self._update()
        self.extend(documents)
    
    @property
    def documents(self):
        return self._documents

    @property
    def terms(self):
        return self.vector.keys()
        
    features = words = terms
    
    @property
    def classes(self):
        return list(set(d.type for d in self.documents))
        
    labels = classes

    def _get_lsa(self):
        return self._lsa
    def _set_lsa(self, v=None):
        self._lsa = v
        self._update()
        
    lsa = property(_get_lsa, _set_lsa)

    def _get_weight(self):
        return self._weight
    def _set_weight(self, w):
        self._weight = w
        self._update() # Clear the cache.
        
    weight = property(_get_weight, _set_weight)

    @classmethod
    def load(cls, path):
        """ Loads the model from a pickle file created with Model.save().
        """
        return cPickle.load(open(path))
        
    def save(self, path, update=False):
        """ Saves the model as a pickle file at the given path.
            The advantage is that cached vectors and cosine similarity are stored.
        """
        if update:
            # Update the entire cache before saving.
            for d1 in self.documents:
                for d2 in self.documents:
                    self.cosine_similarity(d1, d2)
        m = dict.fromkeys((d.id for d in self.documents), True)
        for id1, id2 in self._cos.keys():
            # Remove Model.search() query cache.
            if id1 not in m \
            or id2 not in m:
                self._cos.pop((id1, id2))
        cPickle.dump(self, open(path, "wb"), BINARY)
        
    def export(self, path, format=ORANGE, **kwargs):
        """ Exports the model as a file for other machine learning applications,
            e.g., Orange or Weka.
        """
        # The Document.vector space is exported without cache or LSA concept space.
        keys = sorted(self.vector.keys())
        s = []
        # Orange tab format:
        if format == ORANGE:
            s.append("\t".join(keys + ["m#name", "c#type"]))
            for document in self.documents:
                v = document.vector
                v = [v.get(k, 0) for k in keys]
                v = "\t".join(x==0 and "0" or "%.4f" % x for x in v)
                v = "%s\t%s\t%s" % (v, document.name or "", document.type or "")
                s.append(v)
        # Weka ARFF format:
        if format == WEKA:
            s.append("@RELATION %s" % kwargs.get("name", hash(self)))
            s.append("\n".join("@ATTRIBUTE %s NUMERIC" % k for k in keys))
            s.append("@ATTRIBUTE class {%s}" % ",".join(set(d.type or "" for d in self.documents)))
            s.append("@DATA")
            for document in self.documents:
                v = document.vector
                v = [v.get(k, 0) for k in keys]
                v = ",".join(x==0 and "0" or "%.4f" % x for x in v)
                v = "%s,%s" % (v, document.type or "")
                s.append(v)
        s = "\n".join(s)
        f = open(path, "w", encoding="utf-8")
        f.write(decode_utf8(s))
        f.close()
    
    def _update(self):
        # Ensures that all document vectors are recalculated
        # when a document is added or deleted (= new features).
        self._df  = {}
        self._cos = {}
        self._ig  = {}
        self._vector = None
        self._lsa = None
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
        d._model = None
        self._index.pop(d.name, None)
        self._update()
    def clear(self):
        self._documents = readonlylist()
        self._update()

    def append(self, document):
        """ Appends the given Document to the model.
            If Model.weight != TF, the cache of vectors and cosine similarity is cleared
            (feature weights will be different now that there is a new document).
        """
        if not isinstance(document, Document):
            raise TypeError, "Model.append() expects a Document."
        document._model = self
        if document.name is not None:
            self._index[document.name] = document
        if self._weight != TF:
            self._update()
        list.append(self.documents, document)
        
    def extend(self, documents):
        """ Extends the model with the given list of documents.
        """
        for document in documents:
            if not isinstance(document, Document):
                raise TypeError, "Model.extend() expects a list of Documents."
            document._model = self
            if document.name is not None:
                self._index[document.name] = document
        if self._weight != TF:
            self._update()
        list.extend(self.documents, documents)
        
    def remove(self, document):
        """ Removes the given Document from the model, and sets Document.model=None.
        """
        self.__delitem__(self.documents.index(document))
        
    def document(self, name):
        """ Returns the Document with the given name (assuming document names are unique).
        """
        if name in self._index:
            return self._index[name]
        
    def document_frequency(self, word):
        """ Returns the document frequency for the given word or feature.
            Returns 0 if there are no documents in the model (e.g. no word frequency).
            df = number of documents containing the word / number of documents.
            The more occurences of the word across the model, the higher its df weight.
        """
        if len(self.documents) == 0:
            return 0.0     
        if len(self._df) == 0:
            # Caching document frequency for each word gives a 300x performance boost
            # (i.e., calculated all at once). Drawback is if you need it for just one word.
            for d in self.documents:
                for w in d.terms:
                    if d.terms[w] != 0:
                        self._df[w] = (w in self._df) and self._df[w] + 1 or 1.0
            for w in self._df:
                self._df[w] /= float(len(self.documents))
        return self._df.get(word, 0.0)
        
    df = document_frequency
    
    def inverse_document_frequency(self, word, base=2.71828):
        """ Returns the inverse document frequency for the given word or feature.
            Returns None if the word is not in the model, or if there are no documents in the model.
            Using the natural logarithm:
            idf = log(1/df)
            The more occurences of the word, the lower its idf weight (log() makes it grow slowly).
        """
        df = self.df(word)
        if df == 0.0: 
            return None
        if df == 1.0: 
            return 0.0
        return log(1.0 / df, base)
        
    idf = inverse_document_frequency

    @property
    def vector(self):
        """ Returns a Vector dict of (word, 0.0)-items from the vector space model.
            It includes all words from all documents (i.e. it is the dimension of the vector space).
            Model.vector(document) yields a vector with the feature weights of the given document.
        """
        # Notes: 
        # 1) Model.vector is the dictionary of all (word, 0.0)-items.
        # 2) Model.vector(document) returns a copy with the document's word frequencies.
        #    This is the full vector, as opposed to the sparse Document.vector.
        #    Words in a document that are not in the model are ignored,
        #    i.e., the document was not in the model, this can be the case in Model.search().
        # See: Vector.__call__().
        if not self._vector: 
            self._vector = Vector((w, 0.0) for w in chain(*(d.terms for d in self.documents)))
        return self._vector

    @property
    def vectors(self):
        """ Yields a list of all document vectors.
        """
        return [d.vector for d in self.documents]

    @property
    def density(self):
        """ Yields the overall word coverage as a number between 0.0-1.0.
        """
        return float(sum(len(d.vector) for d in self.documents)) / len(self.vector) ** 2

    # Following methods rely on Document.vector:
    # frequent sets, cosine similarity, nearest neighbors, search, clustering, 
    # information gain, latent semantic analysis.
    
    def frequent_concept_sets(self, threshold=0.5):
        """ Returns a dictionary of (set(feature), frequency) 
            of feature combinations with a frequency above the given threshold.
        """
        return apriori([d.terms for d in self.documents], support=threshold)
        
    sets = frequent = frequent_concept_sets
    
    def cosine_similarity(self, document1, document2):
        """ Returns the similarity between two documents in the model as a number between 0.0-1.0,
            based on the document feature weight (e.g., tf * idf of words in the text).
            cos = dot(v1, v2) / (norm(v1) * norm(v2))
        """
        # If we already calculated similarity between two given documents,
        # it is available in cache for reuse.
        id1 = document1.id
        id2 = document2.id
        if (id1, id2) in self._cos: return self._cos[(id1, id2)]
        if (id2, id1) in self._cos: return self._cos[(id2, id1)]
        # Calculate the matrix multiplication of the document vectors.
        if not getattr(self, "lsa", None):
            v1 = document1.vector
            v2 = document2.vector
            s = cosine_similarity(v1, v2)
        else:
            # Using LSA concept space:
            v1 = id1 in self.lsa and self.lsa[id1] or self._lsa.transform(document1)
            v2 = id2 in self.lsa and self.lsa[id2] or self._lsa.transform(document2)
            s = sum(a * b for a, b in izip(v1.itervalues(), v2.itervalues())) / (v1.norm * v2.norm or 1)
        # Cache the similarity weight for reuse.
        self._cos[(id1, id2)] = s
        return s
        
    similarity = cosine_similarity
    
    def nearest_neighbors(self, document, top=10):
        """ Returns a list of (similarity, document)-tuples in the model, 
            sorted by cosine similarity to the given document.
        """
        v = ((self.cosine_similarity(document, d), d) for d in self.documents)
        # Filter the input document from the matches.
        # Filter documents that score zero, and return the top.
        v = [(w, d) for w, d in v if w > 0 and d.id != document.id]
        v = heapq.nsmallest(top, v, key=lambda v: (-v[0],v[1]))
        return v
        
    similar = related = neighbors = nn = nearest_neighbors
        
    def vector_space_search(self, words=[], **kwargs):
        """ Returns related documents from the model as a list of (similarity, document)-tuples.
            The given words can be a string (one word), a list or tuple of words, or a Document.
        """
        top = kwargs.pop("top", 10)
        if not isinstance(words, (list, tuple, Document)):
            words = [words]
        if not isinstance(words, Document):
            kwargs.setdefault("threshold", 0) # Same stemmer as other documents should be given.
            words = Document(" ".join(words), **kwargs)
        words._model = self # So we can calculate tf-idf.
        # Documents that are not in the model,
        # consisting only of words that are not in the model,
        # have no related documents in the model:
        if len([True for w in words if w in self.vector]) == 0:
            return []
        return self.nearest_neighbors(words, top)
        
    search = vector_space_search
    
    def distance(self, document1, document2, *args, **kwargs):
        """ Returns the distance (COSINE, EUCLIDEAN, ...) between two document vectors (0.0-1.0).
        """
        return distance(document1.vector, document2.vector, *args, **kwargs)
    
#   def cluster(self, documents=ALL, method=KMEANS, k=10, iterations=10)
#   def cluster(self, documents=ALL, method=HIERARCHICAL, k=1, iterations=1000)
    def cluster(self, documents=ALL, method=KMEANS, **kwargs):
        """ Clustering is an unsupervised machine learning method for grouping similar documents.
            - k-means clustering returns a list of k clusters (each is a list of documents).
            - hierarchical clustering returns a list of documents and Cluster objects,
              where a Cluster is a list of documents and other clusters (see Cluster.flatten()).
        """
        if documents == ALL:
            documents = self.documents
        if not getattr(self, "lsa", None):
            # Using document vectors:
            vectors, features = [d.vector for d in documents], self.vector.keys()
        else:
            # Using LSA concept space:
            vectors, features = [self.lsa[d.id] for d in documents], range(len(self.lsa))
        # Create a dictionary of vector.id => Document.
        # We need it to map the clustered vectors back to the actual documents.
        map = dict((v.id, documents[i]) for i, v in enumerate(vectors))
        if method in (KMEANS, "kmeans"):
            clusters = k_means(vectors, 
                             k = kwargs.pop("k", 10),
                    iterations = kwargs.pop("iterations", 10),
                      features = features, **kwargs)
        if method == HIERARCHICAL:
            clusters = hierarchical(vectors, 
                             k = kwargs.pop("k", 1),
                    iterations = kwargs.pop("iterations", 1000),
                      features = features, **kwargs)
        if method in (KMEANS, "kmeans"):
            clusters = [[map[v.id] for v in cluster] for cluster in clusters]
        if method == HIERARCHICAL:
            clusters.traverse(visit=lambda cluster: \
                [cluster.__setitem__(i, map[v.id]) 
                    for i, v in enumerate(cluster) if not isinstance(v, Cluster)])
        return clusters

    def latent_semantic_analysis(self, dimensions=NORM):
        """ Creates LSA concept vectors by reducing the vector space's dimensionality.
            Each concept vector has the given number of features (concepts).
            The concept vectors are consequently used in Model.cosine_similarity(), Model.cluster()
            and classification. This can be faster for high-dimensional vectors (i.e., many features).
            The reduction can be undone by setting Model.lsa=False.
        """
        self._lsa = LSA(self, k=dimensions)
        self._cos = {}
        
    reduce = latent_semantic_analysis
    
    def information_gain(self, word):
        """ Returns the information gain (IG) for the given feature, 
            by examining how much it contributes to each document type (class).
            High IG means low entropy (or predictability) = interesting for feature selection.
        """
        if not self._ig:
            # Based on Vincent Van Asch, http://www.clips.ua.ac.be/~vincent/scripts/textgain.py
            # For classes {xi...xn} and features {yi...yn}:
            # IG(X,Y)  = H(X) - H(X|Y)
            # H(X)     = -sum(p(x) * log2(x) for x in X)
            # H(X|Y)   =  sum(p(y) * H(X|Y=y) for y in Y)
            # H(X|Y=y) = -sum(p(x) * log2(x) for x in X if y in x)
            # H is the entropy for a list of probabilities.
            # Lower entropy indicates predictability, i.e., some values are more probable.
            # H([0.50,0.50]) = 1.00
            # H([0.75,0.25]) = 0.81
            H = entropy
            # X = document type (class) distribution.
            # "How many documents have class xi?"
            X = dict.fromkeys(self.classes, 0)
            for d in self.documents:
                X[d.type] += 1
            # Y = document feature distribution.
            # "How many documents have feature yi?"
            Y = dict.fromkeys(self.features, 0)
            for d in self.documents:
                for y, v in d.vector.items():
                    if v > 0:
                        Y[y] += 1 # Discrete: feature is present (1) or not (0).
            Y = dict((y, Y[y] / float(len(self.documents))) for y in Y)
            # XY = features by class distribution.
            # "How many documents of class xi have feature yi?"
            XY = dict.fromkeys(self.features, {})
            for d in self.documents:
                for y, v in d.vector.items():
                    if v != 0:
                        XY[y][d.type] = XY[y].get(d.type, 0) + 1
            # IG.
            for y in self.features:
                self._ig[y] = H(X.values()) - Y[y] * H(XY[y].values())
        return self._ig[word]
            
    IG = ig = infogain = gain = information_gain
    
    def feature_selection(self, top=100, method=INFOGAIN, verbose=False):
        """ Returns the top unpredictable (or original) features (terms), using information gain.
            This is a subset of Model.features that can be used to build a Classifier
            that is faster (less features = less matrix columns) but still efficient.
        """
        if method == IG:
            subset = ((self.information_gain(w), w) for w in self.terms)
            subset = sorted(subset, key=itemgetter(1))
            subset = sorted(subset, key=itemgetter(0), reverse=True)
            subset = [w for ig, w in subset[:top]]
            return subset
        
    def filter(self, features=[]):
        """ Returns a new Model with documents only containing the given list of features,
            for example a subset returned from Model.feature_selection().
        """
        features = dict.fromkeys(features, True)
        model = Model(weight=self.weight)
        model.extend([
            Document(dict((w, f) for w, f in d.terms.iteritems() if w in features),
                name = d.name,
                type = d.type) for d in self.documents])
        return model

# Backwards compatibility.
Corpus = Model

#### FREQUENT CONCEPT SETS #########################################################################
# Agrawal R. & Srikant R. (1994), Fast algorithms for mining association rules in large databases.
# Based on: https://gist.github.com/1423287

class Apriori:
    
    def __init__(self):
        self._candidates = []
        self._support = {}
    
    def C1(self, sets):
        """ Returns the unique features from all sets as a list of (hashable) frozensets.
        """
        return [frozenset([v]) for v in set(chain(*sets))]

    def Ck(self, sets):
        """ For the given sets of length k, returns combined candidate sets of length k+1.
        """
        Ck = []
        for i, s1 in enumerate(sets):
            for j, s2 in enumerate(sets[i+1:]):
                if set(list(s1)[:-1]) == set(list(s2)[:-1]):
                    Ck.append(s1 | s2)
        return Ck
        
    def Lk(self, sets, candidates, support=0.0):
        """ Prunes candidate sets whose frequency < support threshold.
            Returns a dictionary of (candidate set, frequency)-items.
        """
        Lk, x = {}, 1.0 / (len(sets) or 1) # relative count
        for s1 in candidates:
            for s2 in sets:
                if s1.issubset(s2):
                    Lk[s1] = s1 in Lk and Lk[s1]+x or x
        return dict((s, f) for s, f in Lk.items() if f >= support)

    def __call__(self, sets, support=0.5):
        """ Returns a dictionary of (set(features), frequency)-items.
            The given support (0.0-1.0) is the relative amount of documents
            in which a combination of feature must appear.
        """
        C1 = self.C1(sets)
        L1 = self.Lk(sets, C1, support)
        self._candidates = [L1.keys()]
        self._support = L1
        while True:
            # Terminate when no further extensions are found.
            if len(self._candidates[-1]) == 0:
                break
            # Extend frequent subsets one item at a time.
            Ck = self.Ck(self._candidates[-1])
            Lk = self.Lk(sets, Ck, support)
            self._candidates.append(Lk.keys())
            self._support.update(Lk)
        return self._support
        
apriori = Apriori()

#### LATENT SEMANTIC ANALYSIS ######################################################################
# Based on:
# http://en.wikipedia.org/wiki/Latent_semantic_analysis
# http://blog.josephwilk.net/projects/latent-semantic-analysis-in-python.html

class LSA:
    
    def __init__(self, model, k=NORM):
        """ Latent Semantic Analysis is a statistical machine learning method based on 
            singular value decomposition (SVD), and related to principal component analysis (PCA).
            Closely related features (words) in the model are combined into "concepts".
            Documents then get a concept vector that is an approximation of the original vector,
            but with reduced dimensionality so that cosine similarity and clustering run faster.
        """
        import numpy
        # Calling Model.vector() in a loop is quite slow, we should refactor this:
        matrix = [model.vector(d).values() for d in model.documents]
        matrix = numpy.array(matrix)
        # Singular value decomposition, where u * sigma * vt = svd(matrix).
        # Sigma is the diagonal matrix of singular values,
        # u has document rows and concept columns, vt has concept rows and term columns.
        u, sigma, vt = numpy.linalg.svd(matrix, full_matrices=False)
        # Delete the smallest coefficients in the diagonal matrix (i.e., at the end of the list).
        # The difficulty and weakness of LSA is knowing how many dimensions to reduce
        # (generally L2-norm is used).
        if k == L1:
            k = int(round(numpy.linalg.norm(sigma, 1)))
        if k == L2 or k == NORM:
            k = int(round(numpy.linalg.norm(sigma, 2)))
        if k == TOP300:
            k = max(0, len(sigma) - 300)
        if isinstance(k, int):
            k = max(0, len(sigma) - k)
        if type(k).__name__ == "function":
            k = max(0, int(k(sigma)))
        #print numpy.dot(u, numpy.dot(numpy.diag(sigma), vt))
        # Apply dimension reduction.
        # The maximum length of a concept vector = the number of documents.
        assert k < len(model.documents), \
            "can't create more dimensions than there are documents"
        tail = lambda list, i: range(len(list)-i, len(list))
        u, sigma, vt = (
            numpy.delete(u, tail(u[0], k), axis=1),
            numpy.delete(sigma, tail(sigma, k), axis=0),
            numpy.delete(vt, tail(vt, k), axis=0)
        )
        # Store as Python dict and lists so we can pickle it.
        self.model = model
        self._terms = dict(enumerate(model.vector().keys())) # Vt-index => word.
        self.u, self.sigma, self.vt = (
            dict((d.id, Vector((i, float(x)) for i, x in enumerate(v))) for d, v in izip(model, u)),
            list(sigma),
            [[float(x) for x in v] for v in vt]
        )
    
    @property
    def terms(self):
        """ Yields a list of all terms, identical to LSA.model.vector.keys().
        """
        return self._terms.values()
        
    features = words = terms

    @property
    def concepts(self):
        """ Yields a list of all concepts, each a dictionary of (word, weight)-items.
        """
        # Round the weight so 9.0649330400000009e-17 becomes a more meaningful 0.0.
        return [dict((self._terms[i], round(w, 15)) for i, w in enumerate(concept)) for concept in self.vt]
    
    @property
    def vectors(self):
        """ Yields a dictionary of (Document.id, concepts),
            where each concept is a dictionary of (concept_index, weight)-items.
            for document in lsa.model:
                for concept in lsa.vectors(document.id):
                    print document, concept
        """
        return self.u

    def __getitem__(self, id):
        return self.u[id]
    def __contains__(self, id):
        return id in self.u
    def __iter__(self):
        return iter(self.u)
    def __len__(self):
        return len(self.u)
        
    def transform(self, document):
        """ Given a document not in the model, returns a vector in LSA concept space.
            This happes automatically in Model.cosine_similarity(),
            but it must be done explicitly for Classifier.classify() input.
        """
        if document.id in self.u:
            return self.u[document.id]
        if document.id in _lsa_transform_cache:
            return _lsa_transform_cache[document.id]
        import numpy
        v = self.model.vector(document)
        v = [v[self._terms[i]] for i in range(len(v))]
        v = numpy.dot(numpy.dot(numpy.linalg.inv(numpy.diag(self.sigma)), self.vt), v)
        v = _lsa_transform_cache[document.id] = Vector(enumerate(v))
        return v
        
# LSA cache for Model.vector_space_search() shouldn't be stored with Model.save()
# (so it is a global instead of a property of the LSA class).
_lsa_transform_cache = {}

#def iter2array(iterator, typecode):
#    a = numpy.array([iterator.next()], typecode)
#    shape0 = a.shape[1:]
#    for (i, item) in enumerate(iterator):
#        a.resize((i+2,) + shape0)
#        a[i+1] = item
#    return a

#def filter(matrix, min=0):
#    columns = numpy.max(matrix, axis=0)
#    columns = [i for i, v in enumerate(columns) if v <= min] # Indices of removed columns.
#    matrix = numpy.delete(matrix, columns, axis=1)
#    return matrix, columns

#### CLUSTERING ####################################################################################
# Clustering can be used to categorize a set of unlabeled documents.
# Clustering is an unsupervised machine learning method that partitions a set of vectors into
# subsets, using a distance metric to determine how similar two vectors are.
# For example, for (x, y)-points in 2D space we can use Euclidean distance ("as the crow flies").
# The k_means() and hierarchical() functions work with Vector objects or dictionaries.

def mean(iterable, length=None):
    """ Returns the arithmetic mean of the values in the given iterable or iterator.
    """
    if length is None:
        if not hasattr(iterable, "__len__"):
            iterable = list(iterable)
        length = len(iterable)
    return sum(iterable) / float(length or 1)

def centroid(vectors=[], features=[]):
    """ Returns the center of the given list of vectors.
        For example: if each vector has two features, (x, y)-coordinates in 2D space,
        the centroid is the geometric center of the coordinates forming a polygon.
        Since vectors are sparse (i.e., features with weight 0 are omitted), 
        the list of all features (= Model.vector) must be given.
    """
    c = []
    for v in vectors:
        if isinstance(v, Cluster):
            c.extend(v.flatten())
        elif isinstance(v, Document):
            c.append(v.vector)
        else:
            c.append(v)
    if not features:
        features = _features(c)
    c = [(f, mean((v.get(f, 0) for v in c), len(c))) for f in features]
    c = Vector((f, w) for f, w in c if w != 0)
    return c

class DistanceMap:
    
    def __init__(self, method=COSINE):
        """ A lazy map of cached distances between Vector objects.
        """
        self.method = method
        self._cache = {}
        
    def __call__(self, v1, v2):
        return self.distance(v1, v2)
        
    def distance(self, v1, v2):
        """ Returns the cached distance between two vectors.
        """
        try:
            # Two Vector objects for which the distance was already calculated.
            d = self._cache[(v1.id, v2.id)]
        except KeyError:
            # Two Vector objects for which the distance has not been calculated.
            d = self._cache[(v1.id, v2.id)] = distance(v1, v2, method=self.method)
        except AttributeError:
            # No "id" property, so not a Vector but a plain dict.
            d = distance(v1, v2, method=self.method)
        return d

def cluster(method=KMEANS, vectors=[], **kwargs):
    """ Clusters the given list of vectors using the k-means or hierarchical algorithm.
    """
    if method == KMEANS:
        return k_means(vectors, **kwargs)
    if method == HIERARCHICAL:
        return hierarchical(vectors, **kwargs)

#--- K-MEANS ---------------------------------------------------------------------------------------
# k-means is fast but no optimal solution is guaranteed (random initialization).

# Initialization methods:
RANDOM, KMPP = "random", "kmeans++"

def k_means(vectors, k=None, iterations=10, distance=COSINE, seed=RANDOM, **kwargs):
    """ Returns a list of k clusters, where each cluster is a list of vectors (Lloyd's algorithm).
        Vectors are assigned to k random centers using a distance metric (EUCLIDEAN, COSINE, ...).
        Since the initial centers are chosen randomly (by default, seed=RANDOM),
        there is no guarantee of convergence or of finding an optimal solution.
        A more efficient way is to use seed=KMPP (k-means++ initialization algorithm).
    """
    features = kwargs.get("features") or _features(vectors)
    if k is None:
        k = sqrt(len(vectors) / 2)
    if k < 2: 
        return [[v for v in vectors]]
    if seed == KMPP:
        clusters = kmpp(vectors, k, distance)
    else:
        clusters = [[] for i in xrange(int(k))]
        for i, v in enumerate(sorted(vectors, key=lambda x: random())):
            # Randomly partition the vectors across k clusters.
            clusters[i % int(k)].append(v)
    # Cache the distance calculations between vectors (up to 4x faster).
    map = DistanceMap(method=distance); distance = map.distance
    converged = False
    while not converged and iterations > 0 and k > 0:
        # Calculate the center of each cluster.
        centroids = [centroid(cluster, features) for cluster in clusters]
        # Triangle inequality: one side is shorter than the sum of the two other sides.
        # We can exploit this to avoid costly distance() calls (up to 3x faster).
        p = 0.5 * kwargs.get("p", 0.8) # "Relaxed" triangle inequality (cosine distance is a semimetric) 0.25-0.5.
        D = {}
        for i in range(len(centroids)):
            for j in range(i, len(centroids)): # center1–center2 < center1–vector + vector–center2 ?
                D[(i,j)] = D[(j,i)] = p * distance(centroids[i], centroids[j])
        # For every vector in every cluster,
        # check if it is nearer to the center of another cluster.
        # If so, assign it. When visualized, this produces a Voronoi diagram.
        converged = True
        for i in xrange(len(clusters)):
            for v in clusters[i]:
                nearest, d1 = i, distance(v, centroids[i])
                for j in xrange(len(clusters)):
                    if D[(i,j)] < d1: # Triangle inequality (Elkan, 2003).
                        d2 = distance(v, centroids[j])
                        if d2 < d1:
                            nearest = j
                if nearest != i: # Other cluster is nearer.
                    clusters[nearest].append(clusters[i].pop(clusters[i].index(v)))
                    converged = False
        iterations -= 1; #print iterations
    return clusters
    
kmeans = k_means

def kmpp(vectors, k, distance=COSINE):
    """ The k-means++ initialization algorithm returns a set of initial clusers, 
        with the advantage that:
        - it generates better clusters than k-means(seed=RANDOM) on most data sets,
        - it runs faster than standard k-means,
        - it has a theoretical approximation guarantee.
    """
    # Cache the distance calculations between vectors (up to 4x faster).
    map = DistanceMap(method=distance); distance = map.distance
    # David Arthur, 2006, http://theory.stanford.edu/~sergei/slides/BATS-Means.pdf
    # Based on:
    # http://www.stanford.edu/~darthur/kmpp.zip
    # http://yongsun.me/2008/10/k-means-and-k-means-with-python
    # Choose one center at random.
    # Calculate the distance between each vector and the nearest center.
    centroids = [choice(vectors)]
    d = [distance(v, centroids[0]) for v in vectors]
    s = sum(d)
    for _ in range(int(k) - 1):
        # Choose a random number y between 0 and d1 + d2 + ... + dn.
        # Find vector i so that: d1 + d2 + ... + di >= y > d1 + d2 + ... + dj.
        # Perform a number of local tries so that y yields a small distance sum.
        i = 0
        for _ in range(int(2 + log(k))):
            y = random() * s
            for i1, v1 in enumerate(vectors):
                if y <= d[i1]: 
                    break
                y -= d[i1]
            s1 = sum(min(d[j], distance(v1, v2)) for j, v2 in enumerate(vectors))
            if s1 < s:
                s, i = s1, i1
        # Add vector i as a new center.
        # Repeat until we have chosen k centers.
        centroids.append(vectors[i])
        d = [min(d[i], distance(v, centroids[-1])) for i, v in enumerate(vectors)]
        s = sum(d)
    # Assign points to the nearest center.
    clusters = [[] for i in xrange(int(k))]
    for v1 in vectors:
        d = [distance(v1, v2) for v2 in centroids]
        clusters[d.index(min(d))].append(v1)
    return clusters

#--- HIERARCHICAL ----------------------------------------------------------------------------------
# Hierarchical clustering is slow but the optimal solution guaranteed in O(len(vectors) ** 3).

class Cluster(list):
    
    def __init__(self, *args, **kwargs):
        """ A nested list of Cluster and Vector objects, 
            returned from hierarchical() clustering.
        """
        list.__init__(self, *args, **kwargs)
    
    @property
    def depth(self):
        """ Yields the maximum depth of nested clusters.
            Cluster((1, Cluster((2, Cluster((3, 4)))))).depth => 2.
        """
        return max([0] + [1 + n.depth for n in self if isinstance(n, Cluster)])
    
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
        """ Calls the given visit() function on this cluster and each nested cluster, breadth-first.
        """
        visit(self)
        for item in self:
            if isinstance(item, Cluster): 
                item.traverse(visit)

    def __repr__(self):
        return "Cluster(%s)" % list.__repr__(self)[1:-1]

def sequence(i=0, f=lambda i: i+1):
    """ Yields an infinite sequence, for example:
        sequence() => 0, 1, 2, 3, ...
        sequence(1.0, lambda i: i/2) => 1, 0.5, 0.25, 0.125, ...
    """
    # Used to generate unique vector id's in hierarchical().
    # We cannot use Vector.id, since the given vectors might be plain dicts.
    # We cannot use id(vector), since id() is only unique for the lifespan of the object.
    while True: 
        yield i; i=f(i)

def hierarchical(vectors, k=1, iterations=1000, distance=COSINE, **kwargs):
    """ Returns a Cluster containing k items (vectors or clusters with nested items).
        With k=1, the top-level cluster contains a single cluster.
    """
    id = sequence()
    features  = kwargs.get("features", _features(vectors))
    clusters  = Cluster((v for v in shuffled(vectors)))
    centroids = [(id.next(), v) for v in clusters]
    map = {}
    for _ in range(iterations):
        if len(clusters) <= max(k, 1): 
            break
        nearest, d0 = None, None
        for i, (id1, v1) in enumerate(centroids):
            for j, (id2, v2) in enumerate(centroids[i+1:]):
                # Cache the distance calculations between vectors.
                # This is identical to DistanceMap.distance(),
                # but it is faster in the inner loop to use it directly.
                try:
                    d = map[(id1, id2)]
                except KeyError:
                    d = map[(id1, id2)] = _distance(v1, v2, method=distance)
                if d0 is None or d < d0:
                    nearest, d0 = (i, j+i+1), d
        # Pairs of nearest clusters are merged as we move up the hierarchy:
        i, j = nearest
        merged = Cluster((clusters[i], clusters[j]))
        clusters.pop(j)
        clusters.pop(i)
        clusters.append(merged)
        # Cache the center of the new cluster.
        v = centroid(merged.flatten(), features)
        centroids.pop(j)
        centroids.pop(i)
        centroids.append((id.next(), v))
    return clusters

#v1 = Vector(wings=0, beak=0, claws=1, paws=1, fur=1) # cat
#v2 = Vector(wings=0, beak=0, claws=0, paws=1, fur=1) # dog
#v3 = Vector(wings=1, beak=1, claws=1, paws=0, fur=0) # bird
#print hierarchical([v1, v2, v3])

#### CLASSIFIER ####################################################################################
# Classification can be used to predict the label of an unlabeled document.
# Classification is a supervised machine learning method that uses labeled documents
# (i.e., Document objects with a type) as training examples to statistically predict
# the label (type, class) of new documents, based on their similarity to the training examples 
# using a distance metric (e.g., cosine similarity).

#--- CLASSIFIER BASE CLASS -------------------------------------------------------------------------

# The default baseline (i.e., the default predicted class) is the most frequent class:
FREQUENCY = "frequency"

class Classifier:

    def __init__(self, train=[], baseline=FREQUENCY, **kwargs):
        """ A base class for Naive Bayes, k-NN and SVM.
            Trains a classifier on the given list of Documents or (document, type)-tuples,
            where document can be a Document, Vector, dict or string
            (dicts and strings are implicitly converted to vectors).
        """
        self._vectors  = []       # List of trained (type, vector)-tuples.
        self._classes  = {}       # Dict of (class, frequency)-items.
        self._baseline = baseline # Default predicted class.
        # Train on the list of Document objects or (document, type)-tuples:
        for d in (isinstance(d, Document) and (d, d.type) or d for d in train):
            self.train(*d)
        # In Pattern 2.5-, Classifier.test() is a classmethod.
        # In Pattern 2.6+, it is replaced with Classifier._test() once instantiated:
        self.test = self._test

    @property
    def features(self):
        """ Yields a list of trained features.
        """
        return list(features(v for type, v in self._vectors))

    @property
    def classes(self):
        """ Yields a list of trained classes.
        """
        return self._classes.keys()
    
    terms, types = features, classes

    @property
    def binary(self):
        """ Yields True if the classifier predicts either True (0) or False (1).
        """
        return sorted(self.classes) in ([False, True], [0, 1])
        
    @property
    def distribution(self):
        """ Yields a dictionary of trained (class, frequency)-items.
        """
        return self._classes.copy()
        
    @property
    def majority(self):
        """ Yields the majority class (= most frequent class).
        """
        d = sorted((v, k) for k, v in self._classes.iteritems())
        return d and d[-1][1] or None
    
    @property
    def minority(self):
        """ Yields the minority class (= least frequent class).
        """
        d = sorted((v, k) for k, v in self._classes.iteritems())
        return d and d[0][1] or None
        
    @property
    def baseline(self):
        """ Yields the most frequent class in the training data,
            or a user-defined class if Classifier(baseline != FREQUENCY).
        """
        if self._baseline != FREQUENCY:
            return self._baseline
        return ([(0, None)] + sorted([(v, k) for k, v in self._classes.iteritems()]))[-1][1]
        
    @property
    def skewness(self):
        """ Yields 0.0 if the trained classes are evenly distributed.
            Yields > +1.0 or < -1.0 if the training data is highly skewed.
        """
        def moment(a, m, k=1):
            return sum([(x-m)**k for x in a]) / (len(a) or 1)
        # List each training instance by an int that represents its class:
        a = list(chain(*([i] * v for i, (k, v) in enumerate(self._classes.iteritems()))))
        m = float(sum(a)) / len(a) # mean
        return moment(a, m, 3) / (moment(a, m, 2) ** 1.5 or 1)

    def train(self, document, type=None):
        """ Trains the classifier with the given document of the given type (i.e., class).
            A document can be a Document, Vector, dict, list or string.
            If no type is given, Document.type will be used instead.
        """
        type, vector = self._vector(document, type)
        self._vectors.append((type, vector))
        self._classes[type] = self._classes.get(type, 0) + 1
        
    def classify(self, document, discrete=True):
        """ Returns the type with the highest probability for the given document.
            Returns a dict of (class, probability)-items if discrete=False.
        """
        # This method must be implemented in subclass.
        if not discrete:
            return defaultdict(float)
        return self.baseline

    def _vector(self, document, type=None):
        """ Returns a (type, Vector)-tuple for the given document.
            If the document is part of a LSA-reduced model, returns the LSA concept vector.
            If the given type is None, returns document.type (if a Document is given).
        """
        if isinstance(document, Document):
            if type is None:
                type = document.type
            if document.model and document.model.lsa:
                return type, document.model.lsa[document.id] # LSA concept vector.
            return type, document.vector
        if isinstance(document, Vector):
            return type, document
        if isinstance(document, dict):
            return type, Vector(document)
        if isinstance(document, (list, tuple)):
            return type, Document(document, filter=None, stopwords=True).vector
        if isinstance(document, basestring):
            return type, Document(document, filter=None, stopwords=True).vector

    @classmethod
    def k_fold_cross_validation(cls, corpus=[], k=10, **kwargs):
        # Backwards compatibility.
        return K_fold_cross_validation(cls, documents=corpus, folds=k, **kwargs)
    
    crossvalidate = cross_validate = cv = k_fold_cross_validation
    
    @classmethod
    def test(cls, corpus=[], d=0.65, folds=1, **kwargs):
        # Backwards compatibility.
        # In Pattern 2.5-, Classifier.test() is a classmethod.
        # In Pattern 2.6+, it is replaced with Classifier._test() once instantiated.
        if folds > 1:
            return K_fold_cross_validation(cls, documents=corpus, folds=folds, **kwargs)
        i = int(round(max(0.0, min(1.0, d)) * len(corpus)))
        d = shuffled(corpus)
        return cls(train=d[:i]).test(d[i:])
    
    def _test(self, documents=[], target=None, **kwargs):
        """ Returns an (accuracy, precision, recall, F1-score)-tuple for the given documents,
            with values between 0.0 and 1.0 (0-100%).
            Accuracy is the percentage of correct predictions for the given test set,
            but this metric can be misleading (e.g., classifier *always* predicts True).
            Precision is the percentage of predictions that were correct.
            Recall is the percentage of documents that were correctly labeled.
            F1-score is the harmonic mean of precision and recall.
        """
        A = [] # Accuracy.
        P = [] # Precision.
        R = [] # Recall.
        for type, TP, TN, FP, FN in self.confusion_matrix(documents).split():
            if type == target or target is None:
                # Calculate precision & recall per class.
                A.append(float(TP + TN) / ((TP + TN + FP + FN)))
                P.append(float(TP) / ((TP + FP) or 1))
                R.append(float(TP) / ((TP + FN) or 1))
        # Macro-averaged:
        A = sum(A) / (len(A) or 1)
        P = sum(P) / (len(P) or 1)
        R = sum(R) / (len(R) or 1)
        F = 2.0 * P * R / ((P + R) or 1)
        return A, P, R, F

    def confusion_matrix(self, documents=[]):
        """ Returns the confusion matrix for the given test data,
            which is a list of Documents or (document, type)-tuples.
        """
        documents = [isinstance(d, Document) and (d, d.type) or d for d in documents]
        return ConfusionMatrix(self.classify, documents)

    def auc(self, documents=[], k=10):
        """ Returns the area under the ROC-curve.
            Returns the probability (0.0-1.0) that a classifier will rank 
            a random positive document (True) higher than a random negative one (False).
        """
        roc = [(0.0, 0.0), (1.0, 1.0)]
        for type, TP, TN, FP, FN in self.confusion_matrix(documents).split():
            x = FPR = float(FP) / ((FP + TN) or 1) # false positive rate
            y = TPR = float(TP) / ((TP + FN) or 1) #  true positive rate
            roc.append((x, y))
            #print "%s\t%s %s %s %s\t %s %s" % (TP, TN, FP, FN, FPR, TPR)
        roc = sorted(roc)
        # Trapzoidal rule: area = (a + b) * h / 2, where a=y0, b=y1 and h=x1-x0.
        return sum(0.5 * (x1 - x0) * (y1 + y0) for (x0, y0), (x1, y1) in sorted(izip(roc, roc[1:])))

    def save(self, path):
        self.test = None # Can't pickle instancemethods.
        cPickle.dump(self, open(path, "wb"), BINARY)

    @classmethod
    def load(cls, path):
        self = cPickle.load(open(path))
        self.test = self._test
        return self

#--- CLASSIFIER EVALUATION -------------------------------------------------------------------------

class ConfusionMatrix(defaultdict):
    
    def __init__(self, classify=lambda document: True, documents=[]):
        """ Returns the matrix of classes x predicted classes as a dictionary.
        """
        defaultdict.__init__(self, lambda: defaultdict(int))
        for document, type1 in documents:
            type2 = classify(document)
            self[type1][type2] += 1

    def split(self):
        """ Returns an iterator over one-vs-all (type, TP, TN, FP, FN)-tuples.
        """
        return iter((type,) + self(type) for type in self)

    def __call__(self, type):
        """ Returns a (TP, TN, FP, FN)-tuple for the given class (one-vs-all).
        """
        TP = 0 # True positives.
        TN = 0 # True negatives.
        FP = 0 # False positives (type I error).
        FN = 0 # False negatives (type II error).
        for t1 in self:
            for t2, n in self[t1].iteritems():
                if type == t1 == t2: 
                    TP += n
                if type != t1 == t2: 
                    TN += n
                if type == t1 != t2: 
                    FN += n
                if type == t2 != t1: 
                    FP += n
        return (TP, TN, FP, FN)
    
    @property
    def table(self, padding=1):
        k = sorted(self)
        n = max(map(lambda x: len(decode_utf8(x)), k))
        n = max(n, *(len(str(self[k1][k2])) for k1 in k for k2 in k)) + padding
        s = "".ljust(n)
        for t1 in k:
            s += decode_utf8(t1).ljust(n)
        for t1 in k:
            s += "\n"
            s += decode_utf8(t1).ljust(n)
            for t2 in k: 
                s += str(self[t1][t2]).ljust(n)
        return s

def K_fold_cross_validation(Classifier, documents=[], folds=10, **kwargs):
    """ For 10-fold cross-validation, performs 10 separate tests of the classifier,
        each with a different 9/10 training and 1/10 testing documents.
        The given classifier is a class (Bayes, KNN, SVM)
        which is initialized with the given optional parameters.
    """
    K = kwargs.pop("K", folds)
    d = [isinstance(d, Document) and (d, d.type) or d for d in documents]
    d = shuffled(d) # Avoid a list sorted by type (because we take successive folds).
    m = [0.0, 0.0, 0.0, 0.0] # Macro-average accuracy, precision, recall & F1-score.
    for i in range(K):
        n = len(d) / float(K)     # Test fold size.
        x = int(round(i * n))     # Test fold start index.
        y = int(round(i * n + n)) # Test fold stop index.
        classifier = Classifier(train=d[:x]+d[y:], **kwargs)
        A, P, R, F = classifier.test(d[x:y], **kwargs)
        m[0] += A
        m[1] += P
        m[2] += R
        m[3] += F
    return tuple([v / (K or 1) for v in m])
    
kfoldcv = K_fold_cv = k_fold_cv = k_fold_cross_validation = K_fold_cross_validation

def gridsearch(Classifier, documents=[], folds=10, **kwargs):
    """ Returns the test results for every combination of optional parameters,
        using K-fold cross-validation for the given classifier (Bayes, KNN, SVM).
        For example:
        for (A, P, R, F), p in gridsearch(SVM, data, c=[0.1, 1, 10]):
            print (A, P, R, F), p
        > (0.919, 0.921, 0.919, 0.920), {"c": 10}
        > (0.874, 0.884, 0.865, 0.874), {"c": 1}
        > (0.535, 0.424, 0.551, 0.454), {"c": 0.1}
    """
    def product(*args):
        # Yields the cartesian product of given iterables:
        # list(product([1, 2], [3, 4])) => [(1, 3), (1, 4), (2, 3), (2, 4)]
        p = [[]]
        for iterable in args:
            p = [x + [y] for x in p for y in iterable]
        for p in p:
            yield tuple(p)
    s = [] # [((A, P, R, F), parameters), ...]
    p = [] # [[("c", 0.1), ("c", 10), ...], 
           #  [("gamma", 0.1), ("gamma", 0.2), ...], ...]
    for k, v in kwargs.items():
        p.append([(k, v) for v in v])
    for p in product(*p):
        p = dict(p)
        s.append((K_fold_cross_validation(Classifier, documents, folds, **p), p))
    return sorted(s, reverse=True)

#--- NAIVE BAYES CLASSIFIER ------------------------------------------------------------------------

MULTINOMIAL = "multinomial" # Feature weighting.
BERNOUILLI  = "bernouilli"  # Feature occurs in class (1) or not (0).

class NaiveBayes(Classifier):
    
    def __init__(self, train=[], baseline=FREQUENCY, method=MULTINOMIAL, alpha=0.0001):
        """ Naive Bayes is a simple supervised learning method for text classification.
            Documents are classified based on the probability that a feature occurs in a class,
            (independent of other features).
        """
        self._classes    = {}     # {class: frequency}
        self._features   = {}     # {feature: frequency}
        self._likelihood = {}     # {class: {feature: frequency}}
        self._method     = method # MULTINOMIAL or BERNOUILLI.
        self._alpha      = alpha  # Smoothing.
        Classifier.__init__(self, train, baseline)

    @property
    def method(self):
        return self._method

    @property
    def features(self):
        return self._features.keys()

    def train(self, document, type=None):
        """ Trains the classifier with the given document of the given type (i.e., class).
            A document can be a Document, Vector, dict, list or string.
            If no type is given, Document.type will be used instead.
        """
        # Calculate the probability of a class.
        # Calculate the probability of a feature.
        # Calculate the probability of a feature occuring in a class (= conditional probability).
        type, vector = self._vector(document, type=type)
        self._classes[type] = self._classes.get(type, 0) + 1
        self._likelihood.setdefault(type, {})
        for f, w in vector.iteritems():
            if self.method == BERNOUILLI:
                w = 1
            self._features[f] = self._features.get(f, 0) + 1
            self._likelihood[type][f] = self._likelihood[type].get(f, 0) + w

    def classify(self, document, discrete=True):
        """ Returns the type with the highest probability for the given document.
            If the classifier has been trained on LSA concept vectors
            you need to supply LSA.transform(document).
        """
        # Given red & round, what is the likelihood that it is an apple?
        # p = p(red|apple) * p(round|apple) * p(apple) / (p(red) * p(round))
        # The multiplication can cause underflow so we use log() instead.
        # For unknown features, we smoothen with an alpha value.
        v = self._vector(document)[1]
        n = float(sum(self._classes.itervalues()))
        p = defaultdict(float)
        for type in self._classes:
            if self._method == MULTINOMIAL:
                d = float(sum(self._likelihood[type].itervalues()))
            if self._method == BERNOUILLI:
                d = float(self._classes[type])
            g = 0
            for f in v:
                # Conditional probabilities:
                g += log(self._likelihood[type].get(f, self._alpha) / d)
            g = exp(g) * self._classes[type] / n # prior
            p[type] = g
        # Normalize probability estimates.
        s = sum(p.itervalues()) or 1
        for type in p:
            p[type] /= s
        if not discrete:
            return p
        try:
            # Ties are broken in favor of the majority class
            # (random winner for majority ties).
            m = max(p.itervalues())
            p = sorted((self._classes[type], type) for type, g in p.iteritems() if g == m > 0)
            p = [type for frequency, type in p if frequency == p[0][0]]
            return choice(p)
        except:
            return self.baseline

Bayes = NB = NaiveBayes

#--- K-NEAREST NEIGHBOR CLASSIFIER -----------------------------------------------------------------

class KNN(Classifier):
    
    def __init__(self, k=10, distance=COSINE, train=[], baseline=FREQUENCY):
        """ k-nearest neighbor (kNN) is a simple supervised learning method for text classification.
            Documents are classified by a majority vote of nearest neighbors (cosine distance)
            in the training data.
        """
        self.k = k               # Number of nearest neighbors to observe.
        self.distance = distance # COSINE, EUCLIDEAN, ...
        Classifier.__init__(self, train, baseline)
        
    def train(self, document, type=None):
        """ Trains the classifier with the given document of the given type (i.e., class).
            A document can be a Document, Vector, dict, list or string.
            If no type is given, Document.type will be used instead.
        """
        Classifier.train(self, document, type)
    
    def classify(self, document, discrete=True):
        """ Returns the type with the highest probability for the given document.
            If the classifier has been trained on LSA concept vectors
            you need to supply LSA.transform(document).
        """
        # Distance is calculated between the document vector and all training instances.
        # This will make KNN.test() slow in higher dimensions.
        classes = {}
        v1 = self._vector(document)[1]
        D = ((distance(v1, v2, method=self.distance), type) for type, v2 in self._vectors)
        D = ((d, type) for d, type in D if d < 1) # Nothing in common if distance=1.0.
        D = heapq.nsmallest(self.k, D)            # k-least distant.
        # Normalize probability estimates.
        s = sum(1 - d for d, type in D) or 1
        p = defaultdict(float)
        for d, type in D:
            p[type] += (1 - d) / s
        if not discrete:
            return p
        try:
            # Ties are broken in favor of the majority class
            # (random winner for majority ties).
            m = max(p.itervalues())
            p = sorted((self._classes[type], type) for type, w in p.iteritems() if w == m > 0)
            p = [type for frequency, type in p if frequency == p[0][0]]
            return choice(p)
        except:
            return self.baseline

NearestNeighbor = kNN = KNN

#d1 = Document("cats have stripes, purr and drink milk", type="cat", threshold=0, stemmer=None)
#d2 = Document("cows are black and white, they moo and give milk", type="cow", threshold=0, stemmer=None)
#d3 = Document("birds have wings and can fly", type="bird", threshold=0, stemmer=None)
#knn = kNN()
#for d in (d1, d2, d3):
#    knn.train(d)
#print knn.binary
#print knn.classes
#print knn.classify(Document("something that can fly", threshold=0, stemmer=None))
#print KNN.test((d1, d2, d3), folds=2)

#--- SUPPORT VECTOR MACHINE ------------------------------------------------------------------------
# Pattern comes bundled with LIBSVM 3.17:
# http://www.csie.ntu.edu.tw/~cjlin/libsvm/
#
# Compiled binaries for 32-bit and 64-bit Windows, Mac OS X and Ubuntu are included.
# If no binary works, SVM() raises an ImportError,
# and you will need to download and compile LIBSVM from source.
# If Mac OS X complains during compilation, rename -soname" to "-install_name" in libsvm/Makefile.
# If the binary is named "libsvm.so.2", strip the ".2".
# Put the binary (i.e., "libsvm.dll" or "libsvm.so") in pattern/vector/svm/.
# Windows binaries can be downloaded from:
# http://www.lfd.uci.edu/~gohlke/pythonlibs/#libsvm

# SVM extensions:
LIBSVM, LIBLINEAR = \
    "libsvm", "liblinear"

# SVM type:
SVC = CLASSIFICATION = 0
SVR = REGRESSION     = 3
SVO = DETECTION      = 2 # One-class SVM: X belongs to the class or not?

# SVM kernels:
LINEAR       = 0 # Straight line: u' * v
POLYNOMIAL   = 1 # Curved line: (gamma * u' * v + coef0) ** degree
RADIAL = RBF = 2 # Curved path: exp(-gamma * |u-v| ** 2)

# The simplest way to divide two clusters is a straight line.
# If the clusters are separated by a curved line,
# separation may be easier in higher dimensions (using a kernel).

class SVM(Classifier):
    
    def __init__(self, *args, **kwargs):
        """ Support Vector Machine (SVM) is a supervised learning method 
            where training documents are represented as points in n-dimensional space.
            The SVM constructs a number of hyperplanes that subdivide the space.
            Optional parameters:
            -      type = CLASSIFICATION, 
            -    kernel = LINEAR, 
            -    degree = 3, 
            -     gamma = 1/len(SVM.features), 
            -    coeff0 = 0,
            -      cost = 1, 
            -   epsilon = 0.01, 
            -     cache = 100, 
            - shrinking = True
        """
        import svm
        self._svm = svm
        # Cached LIBSVM or LIBLINEAR model:
        self._model = None
        # SVM.extensions is a tuple of extension modules that can be used.
        # By default, LIBLINEAR will be used for linear SVC (it is faster).
        # If you do not want to use LIBLINEAR, use SVM(extension=LIBSVM).
        self._extensions = \
            kwargs.get("extensions", 
            kwargs.get("extension", (LIBSVM, LIBLINEAR)))
        # Optional parameters are read-only:
        if len(args) > 0: 
            kwargs.setdefault(  "type", args[0])
        if len(args) > 1: 
            kwargs.setdefault("kernel", args[1])
        if len(args) > 2: 
            kwargs.setdefault("degree", args[2])
        for k1, k2, v in (
            (       "type", "s", CLASSIFICATION),
            (     "kernel", "t", LINEAR),
            (     "degree", "d", 3),   # For POLYNOMIAL.
            (      "gamma", "g", 0),   # For POLYNOMIAL + RADIAL.
            (     "coeff0", "r", 0),   # For POLYNOMIAL.
            (       "cost", "c", 1),   # Can be optimized with gridsearch().
            (    "epsilon", "p", 0.1),
            (         "nu", "n", 0.5),
            (      "cache", "m", 100), # MB
            (  "shrinking", "h", True)):
                v = kwargs.get(k2, kwargs.get(k1, v))
                setattr(self, "_"+k1, v)
        Classifier.__init__(self, train=kwargs.get("train", []), baseline=FREQUENCY)
    
    @property
    def extension(self):
        """ Yields the extension module used (LIBSVM or LIBLINEAR).
        """
        if LIBLINEAR in self._extensions and \
          self._svm.LIBLINEAR and \
          self._type == CLASSIFICATION and \
          self._kernel == LINEAR:
            return LIBLINEAR
        return LIBSVM
    
    @property
    def _extension(self):
        """ Yields the extension module object,
            e.g., pattern/vector/svm/3.17/libsvm-mac64.so.
        """
        if self.extension == LIBLINEAR:
            return self._svm.liblinear.liblinear
        return self._svm.libsvm.libsvm

    @property
    def type(self):
        return self._type
    @property
    def kernel(self):
        return self._kernel
    @property
    def degree(self):
        return self._degree
    @property
    def gamma(self):
        return self._gamma
    @property
    def coeff0(self):
        return self._coeff0
    @property
    def cost(self):
        return self._cost
    @property
    def epsilon(self):
        return self._epsilon
    @property
    def nu(self):
        return self._nu
    @property
    def cache(self):
        return self._cache
    @property
    def shrinking(self):
        return self._shrinking
        
    s, t, d, g, r, c, p, n, m, h = (
        type, kernel, degree, gamma, coeff0, cost, epsilon, nu, cache, shrinking
    )

    @property
    def support_vectors(self):
        """ Yields the support vectors.
        """
        if self._model is None:
            self._train()
        if self.extension == LIBLINEAR:
            return []
        return self._model[0].get_SV()
        
    sv = support_vectors

    def _train(self):
        """ Calls libsvm.svm_train() to create a model.
            Vector classes and features are mapped to integers.
        """
        # Note: LIBLINEAR feature indices start from 1 (not 0).
        M  = [v for type, v in self._vectors]                    # List of vectors.
        H1 = dict((w, i+1) for i, w in enumerate(self.features)) # Feature => integer hash.
        H2 = dict((w, i+1) for i, w in enumerate(self.classes))  # Class => integer hash.
        H3 = dict((i+1, w) for i, w in enumerate(self.classes))  # Class reversed hash.
        x  = [dict((H1[k], v) for k, v in v.items()) for v in M] # Hashed vectors.
        y  = [H2[type] for type, v in self._vectors]             # Hashed classes.
        # For linear SVC, use LIBLINEAR which is faster.
        # For kernel SVC, use LIBSVM.
        if self.extension == LIBLINEAR:
            f = self._svm.liblinearutil.train
            o = "-s 1 -c %s -p %s -q" % (
                self._cost,       # -c
                self._epsilon     # -p
            )
        else:
            f = self._svm.libsvmutil.svm_train
            o = "-s %s -t %s -d %s -g %s -r %s -c %s -p %s -n %s -m %s -h %s -b %s -q" % (
                self._type,       # -s
                self._kernel,     # -t
                self._degree,     # -d
                self._gamma,      # -g
                self._coeff0,     # -r
                self._cost,       # -c
                self._epsilon,    # -p
                self._nu,         # -n
                self._cache,      # -m
            int(self._shrinking), # -h
                1,               # -b
            )
        # Cache the model and the feature hash.
        # SVM.train() will remove the cached model (since it needs to be retrained).
        self._model = (f(y, x, o), H1, H2, H3)
  
    def _classify(self, document, probability=False):
        """ Calls libsvm.svm_predict() with the cached model.
            For CLASSIFICATION, returns the predicted class.
            For CLASSIFICATION with probability=True, returns a list of (weight, class)-tuples.
            For REGRESSION, returns a float.
        """
        if self._model is None:
            return None
        M  = self._model[0]
        H1 = self._model[1]
        H2 = self._model[2]
        H3 = self._model[3]
        v  = self._vector(document)[1]
        v  = dict((H1.get(k, len(H1)+i+1), v) for i, (k, v) in enumerate(v.items()))
        # For linear SVC, use LIBLINEAR which is 10x faster.
        # For kernel SVC, use LIBSVM.
        if self.extension == LIBLINEAR:
            f = self._svm.liblinearutil.predict
            o = "-b 0 -q"
        else:
            f = self._svm.libsvmutil.svm_predict
            o = "-b %s -q" % int(probability)
        p = f([0], [v], M, o)
        # Note: LIBLINEAR does not currently support probabilities for classification.
        if self._type == CLASSIFICATION and probability is True and self.extension == LIBLINEAR:
            return {}
        if self._type == CLASSIFICATION and probability is True:
            return defaultdict(float, ((H3[i], w) for i, w in enumerate(p[2][0])))
        if self._type == CLASSIFICATION:
            return H3.get(int(p[0][0]))
        if self._type == REGRESSION:
            return p[0][0]
        if self._type == DETECTION:
            return p[0][0] > 0 # -1 = outlier => return False
        return p[0][0]
    
    def train(self, document, type=None):
        """ Trains the classifier with the given document of the given type (i.e., class).
            A document can be a Document, Vector, dict, list or string.
            If no type is given, Document.type will be used instead.
        """
        Classifier.train(self, document, type)
        self._model = None
            
    def classify(self, document, discrete=True):
        """ Returns the type with the highest probability for the given document.
            If the classifier has been trained on LSA concept vectors
            you need to supply LSA.transform(document).
        """
        if self._model is None:
            self._train()
        return self._classify(document, probability=not discrete)
            
    def save(self, path):
        svm, model = self._svm, self._model
        if model is not None:
            # Convert the SVM model to a string, save the string:
            _save = self.extension == LIBLINEAR and \
                svm.liblinearutil.save_model or \
                svm.libsvmutil.svm_save_model
            _save(path, model[0])
        self._svm = None
        self._model = ((open(path).read(),) + model[1:]) if model else None
        Classifier.save(self, path)
        self._svm = svm
        self._model = model
        
    @classmethod
    def load(cls, path):
        import svm
        classifier = Classifier.load(path)
        classifier._svm = svm
        if classifier._model is not None:
            # Convert the SVM model string to a tmp file, load the file:
            f = open(path + ".tmp", "w")
            f.write(classifier._model[0])
            f.close()
            _load = classifier.extension == LIBLINEAR and \
                svm.liblinearutil.load_model or \
                svm.libsvmutil.svm_load_model
            classifier._model = (_load(path + ".tmp"),) + classifier._model[1:]
            os.remove(f.name)
        return classifier

#---------------------------------------------------------------------------------------------------
# "Nothing beats SVM + character n-grams."
# Character n-grams seem to capture all information: morphology, context, frequency, ...
# SVM will discover the most informative features.
# Each row in the CSV is a score (positive = +1, negative = –1) and a Dutch book review.
# Can we learn from this dataset to predict sentiment? Yes we can!
# The following script demonstrates sentiment analysis for Dutch book reviews,
# with 90% accuracy, in 10 lines of Python code:

#from pattern.db import CSV
#from pattern.vector import SVM, chngrams, kfoldcv
#
#def v(s):
#    return chngrams(s, n=4)
#
#data = CSV.load(os.path.join("..", "..", "test", "corpora", "polarity-nl-bol.com.csv"))
#data = map(lambda (p, review): (v(review), int(p) > 0), data)
#
#print kfoldcv(SVM, data, folds=3)

#---------------------------------------------------------------------------------------------------
# I hate to spoil your party..." by Lars Buitinck.
# As pointed out by Lars Buitinck, words + word-level bigrams with TF-IDF can beat the 90% boundary:

#from pattern.db import CSV
#from pattern.en import ngrams
#from pattern.vector import Model, SVM, gridsearch
#
#def v(s):
#    return count(words(s) + ngrams(s, n=2))
#    
#data = CSV.load(os.path.join("..", "..", "test", "corpora", "polarity-nl-bol.com.csv"))
#data = map(lambda (p, review): Document(v(review), type=int(p) > 0), data)
#data = Model(data, weight="tf-idf")
#
#for p in gridsearch(SVM, data, c=[0.1, 1, 10], folds=3):
#    print p

# This reports 92% accuracy for the best run (c=10).
# Of course, it's optimizing for the same cross-validation 
# that it's testing on, so this is easy to overfit.
# In scikit-learn it will run faster (4 seconds <=> 22 seconds), see: http://goo.gl/YqlRa

#### GENETIC ALGORITHM #############################################################################

class GeneticAlgorithm:
    
    def __init__(self, candidates=[], **kwargs):
        """ A genetic algorithm is a stochastic search method  based on natural selection.
            Each generation, the fittest candidates are selected and recombined into a new generation. 
            With each new generation the system converges towards an optimal fitness.
        """
        self.population = candidates
        self.generation = 0
        self._avg = None # Average fitness for this generation.
        # GeneticAlgorithm.fitness(), crossover(), mutate() can be given as functions:
        for f in ("fitness", "crossover", "mutate"):
            if f in kwargs: 
                setattr(self, f, kwargs[f])
    
    def fitness(self, candidate):
        """ Must be implemented in a subclass, returns 0.0-1.0.
        """
        return 1.0
    
    def crossover(self, candidate1, candidate2, d=0.5):
        """ Must be implemented in a subclass, returns a new candidate.
        """
        return None
        
    def mutate(self, candidate, d=0.1):
        """ Must be implemented in a subclass, returns a new candidate.
        """
        return None or candidate
        
    def update(self, top=0.7, crossover=0.5, mutation=0.1, d=0.9):
        """ Updates the population by selecting the top fittest candidates,
            and recombining them into a new generation.
        """
        # 1) Selection.
        p = sorted((self.fitness(x), x) for x in self.population) # Weakest-first.
        a = self._avg = float(sum(f for f, x in p)) / len(p)
        x = min(f for f, x in p)
        y = max(f for f, x in p)
        i = 0
        while len(p) > len(self.population) * top:
            # Weaker candidates have a higher chance of being removed,
            # chance being equal to (1-fitness), starting with the weakest.
            if x + (y - x) * random() >= p[i][0]:
                p.pop(i)
            else:
                i = (i + 1) % len(p)
        # 2) Reproduction.
        g = []
        while len(g) < len(self.population):
            # Choose randomly between recombination of parents or mutation.
            # Mutation avoids local optima by maintaining genetic diversity.
            if random() < d:
                i = int(round(random() * (len(p)-1)))
                j = choice(range(0, i) + range(i + 1, len(p)))
                g.append(self.crossover(p[i][1], p[j][1], d=crossover))
            else:
                g.append(self.mutate(choice(p)[1], d=mutation))
        self.population = g
        self.generation += 1
        
    @property
    def avg(self):
        # Average fitness is supposed to increase each generation.
        if not self._avg: self._avg = float(sum(map(self.fitness, self.population))) / len(self.population)
        return self._avg
    
    average_fitness = avg

GA = GeneticAlgorithm

# GA for floats between 0.0-1.0 that prefers higher numbers:
#class HighFloatGA(GeneticAlgorithm):
#    def fitness(self, x):
#        return x
#    def crossover(self, x, y, d=0.5):
#        return (x + y) / 2
#    def mutate(self, x, d=0.1):
#        return min(1, max(0, x + random() * 0.2 - 0.1))
#
#ga = HighFloatGA([random() for i in range(100)])
#for i in range(100):
#    ga.update()
#    print ga.average_fitness
#print ga.population
