# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import time
import random
import codecs
import unittest

from random import seed; seed(0)

from pattern import vector

from pattern.en import Text, Sentence, Word, parse
from pattern.db import Datasheet

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

def model(top=None):
    """ Returns a Model of e-mail messages.
        Document type=True => HAM, False => SPAM.
        Documents are mostly of a technical nature (developer forum posts).
    """
    documents = []
    for score, message in Datasheet.load(os.path.join(PATH, "corpora", "spam-apache.csv")):
        document = vector.Document(message, stemmer="porter", top=top, type=int(score) > 0)
        documents.append(document)
    return vector.Model(documents)

#---------------------------------------------------------------------------------------------------

class TestUnicode(unittest.TestCase):
    
    def setUp(self):
        # Test data with different (or wrong) encodings.
        self.strings = (
            u"ünîcøde",
            u"ünîcøde".encode("utf-16"),
            u"ünîcøde".encode("latin-1"),
            u"ünîcøde".encode("windows-1252"),
             "ünîcøde",
            u"אוניקאָד"
        )
        
    def test_decode_utf8(self):
        # Assert unicode.
        for s in self.strings:
            self.assertTrue(isinstance(vector.decode_utf8(s), unicode))
        print("pattern.vector.decode_utf8()")

    def test_encode_utf8(self):
        # Assert Python bytestring.
        for s in self.strings:
            self.assertTrue(isinstance(vector.encode_utf8(s), str))
        print("pattern.vector.encode_utf8()")

#---------------------------------------------------------------------------------------------------

class TestUtilityFunctions(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_shi(self):
        # Assert integer hashing algorithm.
        for a, b in (
          (   100, "1c"), 
          (  1000, "G8"), 
          ( 10000, "2bI"), 
          (100000, "Q0u")):
            self.assertEqual(vector.shi(a), b)
        print("pattern.vector.shi()")
            
    def test_shuffled(self):
        # Assert shuffled() <=> sorted().
        v1 = [1,2,3,4,5,6,7,8,9,10]
        v2 = vector.shuffled(v1)
        self.assertTrue(v1 != v2 and v1 == sorted(v2))
        print("pattern.vector.shuffled()")
        
    def test_chunk(self):
        # Assert list chunk (near-)equal size.
        for a, n, b in (
          ([1,2,3,4,5], 0, []),
          ([1,2,3,4,5], 1, [[1,2,3,4,5]]),
          ([1,2,3,4,5], 2, [[1,2,3], [4,5]]),
          ([1,2,3,4,5], 3, [[1,2], [3,4], [5]]),
          ([1,2,3,4,5], 4, [[1,2], [3], [4], [5]]),
          ([1,2,3,4,5], 5, [[1], [2], [3], [4], [5]]),
          ([1,2,3,4,5], 6, [[1], [2], [3], [4], [5], []])):
            self.assertEqual(list(vector.chunk(a, n)), b)
        print("pattern.vector.chunk()")
        
    def test_readonlydict(self):
        # Assert read-only dict.
        v = vector.readonlydict({"a":1})
        self.assertTrue(isinstance(v, dict))
        self.assertRaises(vector.ReadOnlyError, v.__setitem__, "a", 2)
        self.assertRaises(vector.ReadOnlyError, v.__delitem__, "a")
        self.assertRaises(vector.ReadOnlyError, v.pop, "a")
        self.assertRaises(vector.ReadOnlyError, v.popitem, ("a", 2))
        self.assertRaises(vector.ReadOnlyError, v.clear)
        self.assertRaises(vector.ReadOnlyError, v.update, {"b": 2})
        self.assertRaises(vector.ReadOnlyError, v.setdefault, "b", 2)
        print("pattern.vector.readonlydict")
        
    def test_readonlylist(self):
        # Assert read-only list.
        v = vector.readonlylist([1,2])
        self.assertTrue(isinstance(v, list))
        self.assertRaises(vector.ReadOnlyError, v.__setitem__, 0, 0)
        self.assertRaises(vector.ReadOnlyError, v.__delitem__, 0)
        self.assertRaises(vector.ReadOnlyError, v.append, 3)
        self.assertRaises(vector.ReadOnlyError, v.insert, 2, 3)
        self.assertRaises(vector.ReadOnlyError, v.extend, [3, 4])
        self.assertRaises(vector.ReadOnlyError, v.remove, 1)
        self.assertRaises(vector.ReadOnlyError, v.pop, 0)
        print("pattern.vector.readonlylist")

#---------------------------------------------------------------------------------------------------

class TestStemmer(unittest.TestCase):

    def setUp(self):
        # Test data from http://snowball.tartarus.org/algorithms/english/stemmer.html
        self.input = [
            'consign', 'consigned', 'consigning', 'consignment', 'consist', 'consisted', 'consistency', 
            'consistent', 'consistently', 'consisting', 'consists', 'consolation', 'consolations', 
            'consolatory', 'console', 'consoled', 'consoles', 'consolidate', 'consolidated', 'consolidating', 
            'consoling', 'consolingly', 'consols', 'consonant', 'consort', 'consorted', 'consorting', 
            'conspicuous', 'conspicuously', 'conspiracy', 'conspirator', 'conspirators', 'conspire', 
            'conspired', 'conspiring', 'constable', 'constables', 'constance', 'constancy', 'constant',
            'generate', 'generates', 'generated', 'generating', 'general', 'generally', 'generic', 
            'generically', 'generous', 'generously', 'knack', 'knackeries', 'knacks', 'knag', 'knave', 
            'knaves', 'knavish', 'kneaded', 'kneading', 'knee', 'kneel', 'kneeled', 'kneeling', 'kneels', 
            'knees', 'knell', 'knelt', 'knew', 'knick', 'knif', 'knife', 'knight', 'knightly', 'knights', 
            'knit', 'knits', 'knitted', 'knitting', 'knives', 'knob', 'knobs', 'knock', 'knocked', 'knocker', 
            'knockers', 'knocking', 'knocks', 'knopp', 'knot', 'knots', 'skies', 'spy'
        ]
        self.output = [
            'consign', 'consign', 'consign', 'consign', 'consist', 'consist', 'consist', 'consist', 'consist', 
            'consist', 'consist', 'consol', 'consol', 'consolatori', 'consol', 'consol', 'consol', 'consolid', 
            'consolid', 'consolid', 'consol', 'consol', 'consol', 'conson', 'consort', 'consort', 'consort', 
            'conspicu', 'conspicu', 'conspiraci', 'conspir', 'conspir', 'conspir', 'conspir', 'conspir', 
            'constabl', 'constabl', 'constanc', 'constanc', 'constant', 'generat', 'generat', 'generat', 
            'generat', 'general', 'general', 'generic', 'generic', 'generous', 'generous', 'knack', 'knackeri', 
            'knack', 'knag', 'knave', 'knave', 'knavish', 'knead', 'knead', 'knee', 'kneel', 'kneel', 'kneel', 
            'kneel', 'knee', 'knell', 'knelt', 'knew', 'knick', 'knif', 'knife', 'knight', 'knight', 'knight', 
            'knit', 'knit', 'knit', 'knit', 'knive', 'knob', 'knob', 'knock', 'knock', 'knocker', 'knocker', 
            'knock', 'knock', 'knopp', 'knot', 'knot', 'sky', 'spi'
        ]
        
    def test_stem(self):
        # Assert the accuracy of the stemmer.
        i = 0
        n = len(self.input)
        for a, b in zip(self.input, self.output):
            if vector.stemmer.stem(a, cached=True) == b:
                i += 1
        self.assertEqual(float(i) / n, 1.0)
        print("pattern.vector.stemmer.stem()")
    
    def test_stem_case_sensitive(self):
        # Assert stemmer case-sensitivity.
        for a, b in (
          ("Ponies", "Poni"),
          ("pONIES", "pONI"),
          ( "SKiES", "SKy"),
          ("cosmos", "cosmos")):
            self.assertEqual(vector.stemmer.stem(a), b)
        print("pattern.vector.stemmer.case_sensitive()")

#---------------------------------------------------------------------------------------------------

class TestDocument(unittest.TestCase):
    
    def setUp(self):
        # Test file for loading and saving documents.
        self.path = "test_document2.txt"
        
    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)
    
    def test_stopwords(self):
        # Assert common stop words.
        for w in ("a", "am", "an", "and", "i", "the", "therefore", "they", "what", "while"):
            self.assertTrue(w in vector.stopwords["en"])
        print("pattern.vector.stopwords")
        
    def test_words(self):
        # Assert word split algorithm (default treats lines as spaces and ignores numbers).
        s = "The cat sat on the\nmat. 1 11."
        v = vector.words(s, filter=lambda w: w.isalpha())
        self.assertEqual(v, ["The", "cat", "sat", "on", "the", "mat"])
        # Assert custom word filter.
        v = vector.words(s, filter=lambda w: True)
        self.assertEqual(v, ["The", "cat", "sat", "on", "the", "mat", "1", "11"])
        print("pattern.vector.words()")
        
    def test_stem(self):
        # Assert stem with PORTER, LEMMA and pattern.en.Word.
        s = "WOLVES"
        v1 = vector.stem(s, stemmer=None)
        v2 = vector.stem(s, stemmer=vector.PORTER)
        v3 = vector.stem(s, stemmer=vector.LEMMA)
        v4 = vector.stem(s, stemmer=lambda w: "wolf*")
        v5 = vector.stem(Word(None, s, lemma=u"wolf*"), stemmer=vector.LEMMA)
        v6 = vector.stem(Word(None, s, type="NNS"), stemmer=vector.LEMMA)
        self.assertEqual(v1, "wolves")
        self.assertEqual(v2, "wolv")
        self.assertEqual(v3, "wolf")
        self.assertEqual(v4, "wolf*")
        self.assertEqual(v5, "wolf*")
        self.assertEqual(v6, "wolf")
        # Assert unicode output.
        self.assertTrue(isinstance(v1, unicode))
        self.assertTrue(isinstance(v2, unicode))
        self.assertTrue(isinstance(v3, unicode))
        self.assertTrue(isinstance(v4, unicode))
        self.assertTrue(isinstance(v5, unicode))
        self.assertTrue(isinstance(v6, unicode))
        print("pattern.vector.stem()")
        
    def test_count(self):
        # Assert wordcount with stemming, stopwords and pruning.
        w = ["The", "cats", "sat", "on", "the", "mat", "."]
        v1 = vector.count(w)
        v2 = vector.count(w, stemmer=vector.LEMMA)
        v3 = vector.count(w, exclude=["."])
        v4 = vector.count(w, stopwords=True)
        v5 = vector.count(w, stopwords=True, top=3)
        v6 = vector.count(w, stopwords=True, top=3, threshold=1)
        v7 = vector.count(w, dict=vector.readonlydict, cached=False)
        self.assertEqual(v1, {"cats":1, "sat":1, "mat":1, ".":1})
        self.assertEqual(v2, {"cat":1, "sat":1, "mat":1, ".":1})
        self.assertEqual(v3, {"cats":1, "sat":1, "mat":1})
        self.assertEqual(v4, {"the":2, "cats":1, "sat":1, "on":1, "mat":1, ".":1})
        self.assertEqual(v5, {"the":2, "cats":1, ".":1})
        self.assertEqual(v6, {"the":2})
        # Assert custom dict class.
        self.assertTrue(isinstance(v7, vector.readonlydict))
        print("pattern.vector.count()")

    def test_document(self):
        # Assert Document properties.
        # Test with different input types.
        for constructor, w in (
          (vector.Document, "The cats sit on the mat."),
          (vector.Document, ["The", "cats", "sit", "on", "the", "mat"]),
          (vector.Document, {"cat":1, "mat":1, "sit":1}),
          (vector.Document, Text(parse("The cats sat on the mat."))),
          (vector.Document, Sentence(parse("The cats sat on the mat.")))):
            # Test copy.
            v = constructor(w, stemmer=vector.LEMMA, stopwords=False, name="Cat", type="CAT")
            v = v.copy()
            # Test properties.
            self.assertEqual(v.name, "Cat")
            self.assertEqual(v.type, "CAT")
            self.assertEqual(v.count, 3)
            self.assertEqual(v.terms, {"cat":1, "mat":1, "sit":1})
            # Test iterator decoration.
            self.assertEqual(sorted(v.features), ["cat", "mat", "sit"])
            self.assertEqual(sorted(v), ["cat", "mat", "sit"])
            self.assertEqual(len(v), 3)
            self.assertEqual(v["cat"], 1)
            self.assertEqual("cat" in v, True)
        print("pattern.vector.Document")
    
    def test_document_load(self):
        # Assert save + load document integrity.
        v1 = "The cats are purring on the mat."
        v1 = vector.Document(v1, stemmer=vector.PORTER, stopwords=True, name="Cat", type="CAT")
        v1.save(self.path)
        v2 = vector.Document.load(self.path)
        self.assertEqual(v1.name,   v2.name)
        self.assertEqual(v1.type,   v2.type)
        self.assertEqual(v1.vector, v2.vector)
        print("pattern.vector.Document.save()")
        print("pattern.vector.Document.load()")
    
    def test_document_vector(self):
        # Assert Vector properties.
        # Test copy.
        v = vector.Document("the cat sat on the mat").vector
        v = v.copy()
        # Test properties.
        self.assertTrue(isinstance(v, dict))
        self.assertTrue(isinstance(v, vector.Vector))
        self.assertTrue(isinstance(v.id, int))
        self.assertEqual(sorted(v.features), ["cat", "mat", "sat"])
        self.assertEqual(v.weight, vector.TF)
        self.assertAlmostEqual(v.norm,   0.58, places=2)
        self.assertAlmostEqual(v["cat"], 0.33, places=2)
        self.assertAlmostEqual(v["sat"], 0.33, places=2)
        self.assertAlmostEqual(v["mat"], 0.33, places=2)
        # Test copy + update.
        v = v({"cat":1, "sat":1, "mat":1})
        self.assertEqual(sorted(v.features), ["cat", "mat", "sat"])
        self.assertAlmostEqual(v["cat"], 1.00, places=2)
        self.assertAlmostEqual(v["sat"], 1.00, places=2)
        self.assertAlmostEqual(v["mat"], 1.00, places=2)
        print("pattern.vector.Document.vector")

    def test_document_keywords(self):
        # Assert Document.keywords() based on term frequency.
        v = vector.Document(["cat", "cat", "cat", "sat", "sat", "mat"]).keywords(top=2)
        self.assertEqual(len(v), 2)
        self.assertEqual(v[0][1], "cat")
        self.assertEqual(v[1][1], "sat")
        self.assertAlmostEqual(v[0][0], 0.50, places=2)
        self.assertAlmostEqual(v[1][0], 0.33, places=2)
        print("pattern.vector.Document.keywords()")
    
    def test_tf(self):
        # Assert Document.term_frequency() (= weights used in Vector for orphaned documents).
        v = vector.Document("the cat sat on the mat")
        for feature, weight in v.vector.items():
            self.assertEqual(v.term_frequency(feature), weight)
            self.assertAlmostEqual(v.term_frequency(feature), 0.33, places=2)
        print("pattern.vector.Document.tf()")
        
    def test_tfidf(self):
        # Assert tf-idf for documents not in a model.
        v = [[0.0, 0.4, 0.6], [0.6, 0.4, 0.0]]
        v = [dict(enumerate(v)) for v in v]
        m = vector.Model([vector.Document(x) for x in v], weight=vector.TFIDF)
        v = [vector.sparse(v) for v in vector.tf_idf(v)]
        self.assertEqual(sorted(m[0].vector.items()), sorted(v[0].items()))
        self.assertAlmostEqual(v[0][2], 0.42, places=2)
        self.assertAlmostEqual(v[1][0], 0.42, places=2)
        print("pattern.vector.tf_idf()")

    def test_cosine_similarity(self):
        # Test cosine similarity for documents not in a model.
        v1 = vector.Document("the cat sat on the mat")
        v2 = vector.Document("a cat with a hat")
        self.assertAlmostEqual(v1.cosine_similarity(v2), 0.41, places=2)
        print("pattern.vector.Document.similarity()")
        print("pattern.vector.cosine_similarity()")
        print("pattern.vector.l2_norm()")

#---------------------------------------------------------------------------------------------------

class TestModel(unittest.TestCase):
    
    def setUp(self):
        # Test model.
        self.model = vector.Model(documents=(
            vector.Document("cats purr", name="cat1", type=u"cåt"),
            vector.Document("cats meow", name="cat2", type=u"cåt"),
            vector.Document("dogs howl", name="dog1", type=u"døg"),
            vector.Document("dogs bark", name="dog2", type=u"døg")
        ))
        
    def test_model(self):
        # Assert Model properties.
        v = self.model
        self.assertEqual(list(v), v.documents)
        self.assertEqual(len(v), 4)
        self.assertEqual(sorted(v.terms), ["bark", "cats", "dogs", "howl", "meow", "purr"])
        self.assertEqual(sorted(v.terms), sorted(v.vector.keys()))
        self.assertEqual(v.weight, vector.TFIDF)
        self.assertEqual(v.lsa, None)
        self.assertEqual(v.vectors, [d.vector for d in v.documents])
        self.assertAlmostEqual(v.density, 0.22, places=2)
        print("pattern.vector.Model")
        
    def test_model_append(self):
        # Assert Model.append().
        self.assertRaises(vector.ReadOnlyError, self.model.documents.append, None)
        self.model.append(vector.Document("birds chirp", name="bird"))
        self.assertEqual(self.model[0]._vector, None)
        self.assertEqual(len(self.model), 5)
        self.model.remove(self.model.document("bird"))
        print("pattern.vector.Model.append()")
        
    def test_model_save(self):
        # Assert Model save & load.
        self.model.save("test_model.pickle", update=True)
        self.model._update()
        model = vector.Model.load("test_model.pickle")
        # Assert that the precious cache is saved and reloaded.
        self.assertTrue(len(model._df) > 0)
        self.assertTrue(len(model._cos) > 0)
        self.assertTrue(len(model.vectors) > 0)
        os.remove("test_model.pickle")
        print("pattern.vector.Model.save()")
        print("pattern.vector.Model.load()")
    
    def test_model_export(self):
        # Assert Orange and Weka ARFF export formats.
        for format, src in (
            (vector.ORANGE, 
                u"bark\tcats\tdogs\thowl\tmeow\tpurr\tm#name\tc#type\n"
                u"0\t0.3466\t0\t0\t0\t0.6931\tcat1\tcåt\n"
                u"0\t0.3466\t0\t0\t0.6931\t0\tcat2\tcåt\n"
                u"0\t0\t0.3466\t0.6931\t0\t0\tdog1\tdøg\n"
                u"0.6931\t0\t0.3466\t0\t0\t0\tdog2\tdøg"),
            (vector.WEKA,
                u"@RELATION 5885744\n"
                u"@ATTRIBUTE bark NUMERIC\n"
                u"@ATTRIBUTE cats NUMERIC\n"
                u"@ATTRIBUTE dogs NUMERIC\n"
                u"@ATTRIBUTE howl NUMERIC\n"
                u"@ATTRIBUTE meow NUMERIC\n"
                u"@ATTRIBUTE purr NUMERIC\n"
                u"@ATTRIBUTE class {døg,cåt}\n"
                u"@DATA\n0,0.3466,0,0,0,0.6931,cåt\n"
                u"0,0.3466,0,0,0.6931,0,cåt\n"
                u"0,0,0.3466,0.6931,0,0,døg\n"
                u"0.6931,0,0.3466,0,0,0,døg")):
            self.model.export("test_%s.txt" % format, format=format)
            v = codecs.open("test_%s.txt" % format, encoding="utf-8").read()
            v = v.replace("\r\n", "\n")
            for line in src.split("\n"):
                self.assertTrue(line in src)
            os.remove("test_%s.txt" % format)
        print("pattern.vector.Model.export()")
        
    def test_df(self):
        # Assert document frequency: "cats" appears in 1/2 documents,"purr" in 1/4.
        self.assertEqual(self.model.df("cats"), 0.50)
        self.assertEqual(self.model.df("purr"), 0.25)
        self.assertEqual(self.model.df("????"), 0.00)
        print("pattern.vector.Model.df()")
    
    def test_idf(self):
        # Assert inverse document frequency: log(1/df).
        self.assertAlmostEqual(self.model.idf("cats"), 0.69, places=2)
        self.assertAlmostEqual(self.model.idf("purr"), 1.39, places=2)
        self.assertEqual(      self.model.idf("????"), None)
        print("pattern.vector.Model.idf()")
        
    def test_tfidf(self):
        # Assert term frequency - inverse document frequency: tf * idf.
        self.assertAlmostEqual(self.model[0].tfidf("cats"), 0.35, places=2) # 0.50 * 0.69
        self.assertAlmostEqual(self.model[0].tfidf("purr"), 0.69, places=2) # 0.50 * 1.39
        self.assertAlmostEqual(self.model[0].tfidf("????"), 0.00, places=2)
        print("pattern.vector.Document.tfidf()")
        
    def test_frequent_concept_sets(self):
        # Assert Apriori algorithm.
        v = self.model.frequent(threshold=0.5)
        self.assertEqual(sorted(v.keys()), [frozenset(["dogs"]), frozenset(["cats"])])
        print("pattern.vector.Model.frequent()")
        
    def test_cosine_similarity(self):
        # Assert document cosine similarity.
        v1 = self.model.similarity(self.model[0], self.model[1])
        v2 = self.model.similarity(self.model[0], self.model[2])
        v3 = self.model.similarity(self.model[0], vector.Document("cats cats"))
        self.assertAlmostEqual(v1, 0.20, places=2)
        self.assertAlmostEqual(v2, 0.00, places=2)
        self.assertAlmostEqual(v3, 0.45, places=2)
        # Assert that Model.similarity() is aware of LSA reduction.
        try:
            import numpy
            self.model.reduce(2)
            v1 = self.model.similarity(self.model[0], self.model[1])
            v2 = self.model.similarity(self.model[0], self.model[2])
            self.assertAlmostEqual(v1, 1.00, places=2)
            self.assertAlmostEqual(v2, 0.00, places=2)
            self.model.lsa = None
        except ImportError, e:
            pass
        print("pattern.vector.Model.similarity()")
        
    def test_nearest_neighbors(self):
        # Assert document nearest-neighbor search.
        v1 = self.model.neighbors(self.model[0])
        v2 = self.model.neighbors(vector.Document("cats meow"))
        v3 = self.model.neighbors(vector.Document("????"))
        self.assertEqual(v1[0][1], self.model[1])
        self.assertEqual(v2[0][1], self.model[1])
        self.assertEqual(v2[1][1], self.model[0])
        self.assertAlmostEqual(v1[0][0], 0.20, places=2)
        self.assertAlmostEqual(v2[0][0], 0.95, places=2)
        self.assertAlmostEqual(v2[1][0], 0.32, places=2)
        self.assertTrue(len(v3) == 0)
        print("pattern.vector.Model.neighbors()")
        
    def test_search(self):
        # Assert document vector space search.
        v1 = self.model.search(self.model[0])
        v2 = self.model.search(vector.Document("cats meow"))
        v3 = self.model.search(vector.Document("????"))
        v4 = self.model.search("meow")
        v5 = self.model.search(["cats", "meow"])
        self.assertEqual(v1, self.model.neighbors(self.model[0]))
        self.assertEqual(v2[0][1], self.model[1])
        self.assertEqual(v3, [])
        self.assertEqual(v4[0][1], self.model[1])
        self.assertEqual(v5[0][1], self.model[1])
        self.assertAlmostEqual(v4[0][0], 0.89, places=2)
        self.assertAlmostEqual(v5[0][0], 1.00, places=2)
        print("pattern.vector.Model.search()")
    
    def test_distance(self):
        # Assert Model document distance.
        v1 = self.model.distance(self.model[0], self.model[1], method=vector.COSINE)
        v2 = self.model.distance(self.model[0], self.model[2], method=vector.COSINE)
        v3 = self.model.distance(self.model[0], self.model[2], method=vector.EUCLIDEAN)
        self.assertAlmostEqual(v1, 0.8, places=1)
        self.assertAlmostEqual(v2, 1.0, places=1)
        self.assertAlmostEqual(v3, 1.2, places=1)
        print("pattern.vector.Model.distance()")
    
    def test_cluster(self):
        # Assert Model document clustering.
        v1 = self.model.cluster(method=vector.KMEANS, k=10)
        v2 = self.model.cluster(method=vector.HIERARCHICAL, k=1)
        self.assertTrue(isinstance(v1, list) and len(v1) == 10)
        self.assertTrue(isinstance(v2, vector.Cluster))
        def _test_clustered_documents(cluster):
            if self.model[0] in cluster:
                self.assertTrue(self.model[1] in cluster \
                        and not self.model[2] in cluster)
            if self.model[2] in cluster:
                self.assertTrue(self.model[3] in cluster \
                        and not self.model[1] in cluster)
        v2.traverse(_test_clustered_documents)
        print("pattern.vector.Model.cluster()")
    
    def test_centroid(self):
        # Assert centroid of recursive Cluster.
        v = vector.Cluster(({"a": 1}, vector.Cluster(({"a": 2}, {"a": 4}))))
        self.assertAlmostEqual(vector.centroid(v)["a"], 2.33, places=2)
        print("pattern.vector.centroid()")
    
    def test_lsa(self):
        # Assert Model.reduce() LSA reduction.
        try:
            import numpy
        except ImportError, e:
            return
        self.model.reduce(2)
        self.assertTrue(isinstance(self.model.lsa, vector.LSA))
        self.model.lsa = None
        print("pattern.vector.Model.reduce()")
    
    def test_feature_selection(self):
        # Assert information gain feature selection.
        m = vector.Model((
            vector.Document("the cat sat on the mat", type="cat", stopwords=True),
            vector.Document("the dog howled at the moon", type="dog", stopwords=True)
        ))
        v = m.feature_selection(top=3, method=vector.IG, threshold=0.0)
        self.assertEqual(v, ["at", "cat", "dog"])
        # Assert Model.filter().
        v = m.filter(v)
        self.assertTrue("at"  in v.terms)
        self.assertTrue("cat" in v.terms)
        self.assertTrue("dog" in v.terms)
        self.assertTrue("the" not in v.terms)
        self.assertTrue("mat" not in v.terms)
        print("pattern.vector.Model.feature_selection()")
        print("pattern.vector.Model.filter()")
        
    def test_information_gain(self):
        # Assert information gain weights.
        # Example from http://www.comp.lancs.ac.uk/~kc/Lecturing/csc355/DecisionTrees_given.pdf
        m = vector.Model([
            vector.Document({"wind":1}, type=False),
            vector.Document({"wind":0}, type=True),
            vector.Document({"wind":0}, type=True),
            vector.Document({"wind":0}, type=True),
            vector.Document({"wind":1}, type=True),
            vector.Document({"wind":1}, type=False),
            vector.Document({"wind":1}, type=False)], weight=None
        )
        self.assertAlmostEqual(m.information_gain("wind"), 0.52, places=2)
        # Example from http://rutcor.rutgers.edu/~amai/aimath02/PAPERS/14.pdf
        m = vector.Model([
            vector.Document({"3":1}, type=True),
            vector.Document({"3":5}, type=True),
            vector.Document({"3":1}, type=False),
            vector.Document({"3":7}, type=True),
            vector.Document({"3":2}, type=False),
            vector.Document({"3":2}, type=True),
            vector.Document({"3":6}, type=False),
            vector.Document({"3":4}, type=True),
            vector.Document({"3":0}, type=False),
            vector.Document({"3":9}, type=True)], weight=None
        )
        self.assertAlmostEqual(m.ig("3"), 0.571, places=3)
        self.assertAlmostEqual(m.gr("3"), 0.195, places=3)
        print("patten.vector.Model.information_gain()")
        print("patten.vector.Model.gain_ratio()")
        
    def test_entropy(self):
        # Assert Shannon entropy calculcation.
        self.assertAlmostEqual(vector.entropy([1, 1]), 1.00, places=2)
        self.assertAlmostEqual(vector.entropy([2, 1]), 0.92, places=2)
        self.assertAlmostEqual(vector.entropy([0.5, 0.5]), 1.00, places=2)
        self.assertAlmostEqual(vector.entropy([0.6]), 0.44, places=2)
        print("pattern.vector.entropy()")
        
    def test_condensed_nearest_neighbor(self):
        # Assert CNN for data reduction.
        v = vector.Model((
            vector.Document("woof", type="dog"),
            vector.Document("meow", type="cat"),  # redundant
            vector.Document("meow meow", type="cat")
        ))
        self.assertTrue(len(v.cnn()) < len(v))
        print("pattern.vector.Model.condensed_nearest_neighbor()")
        
    def test_classifier(self):
        # Assert that the model classifier is correctly saved and loaded.
        p = "test.model.tmp"
        v = vector.Model([vector.Document("chirp", type="bird")])
        v.train(vector.SVM)
        v.save(p)
        v = vector.Model.load(p)
        self.assertTrue(isinstance(v.classifier, vector.SVM))
        os.unlink(p)
        print("pattern.vector.Model.classifier")
        print("pattern.vector.Model.train()")

#---------------------------------------------------------------------------------------------------

class TestApriori(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_apriori(self):
        # Assert frequent sets frequency.
        v = vector.apriori((
            [1, 2, 4],
            [1, 2, 5],
            [1, 3, 6],
            [1, 3, 7]
        ), support=0.5)
        self.assertTrue(len(v), 3)
        self.assertEqual(v[frozenset((1, ))], 1.0)
        self.assertEqual(v[frozenset((1,2))], 0.5)
        self.assertEqual(v[frozenset((2, ))], 0.5)
        self.assertEqual(v[frozenset((3, ))], 0.5)

#---------------------------------------------------------------------------------------------------

class TestLSA(unittest.TestCase):
    
    model = None
    
    def setUp(self):
        # Test spam model for reduction.
        if self.__class__.model is None:
            self.__class__.model = model(top=250)
        self.model = self.__class__.model
        random.seed(0)
        
    def tearDown(self):
        random.seed()
    
    def test_lsa(self):
        try:
            import numpy
        except ImportError, e:
            print(e)
            return
        # Assert LSA properties.
        k = 100
        lsa = vector.LSA(self.model, k)
        self.assertEqual(lsa.model, self.model)
        self.assertEqual(lsa.vectors, lsa.u)
        self.assertEqual(set(lsa.terms), set(self.model.vector.keys()))
        self.assertTrue(isinstance(lsa.u,     dict))
        self.assertTrue(isinstance(lsa.sigma, list))
        self.assertTrue(isinstance(lsa.vt,    list))
        self.assertTrue(len(lsa.u),     len(self.model))
        self.assertTrue(len(lsa.sigma), len(self.model)-k)
        self.assertTrue(len(lsa.vt),    len(self.model)-k)
        for document in self.model:
            v = lsa.vectors[document.id]
            self.assertTrue(isinstance(v, vector.Vector))
            self.assertTrue(len(v) <= k)
        print("pattern.vector.LSA")
        
    def test_lsa_concepts(self):
        try:
            import numpy
        except ImportError:
            return
        # Assert LSA concept space.
        model = vector.Model((
            vector.Document("cats purr"),
            vector.Document("cats meow"),
            vector.Document("dogs howl"),
            vector.Document("dogs bark")
        ))
        model.reduce(2)
        # Intuitively, we'd expect two concepts:
        # 1) with cats + purr + meow grouped together,
        # 2) with dogs + howl + bark grouped together.
        i1, i2 = 0, 0
        for i, concept in enumerate(model.lsa.concepts):
            self.assertTrue(isinstance(concept, dict))
            if concept["cats"] > 0.5:
                self.assertTrue(concept["purr"] >  0.5)
                self.assertTrue(concept["meow"] >  0.5)
                self.assertTrue(concept["howl"] == 0.0)
                self.assertTrue(concept["bark"] == 0.0)
                i1 = i
            if concept["dogs"] > 0.5:
                self.assertTrue(concept["howl"] >  0.5)
                self.assertTrue(concept["bark"] >  0.5)
                self.assertTrue(concept["purr"] == 0.0)
                self.assertTrue(concept["meow"] == 0.0)
                i2 = i
        # We'd expect the "cat" documents to score high on the "cat" concept vector.
        # We'd expect the "dog" documents to score high on the "dog" concept vector.
        v1 = model.lsa[model.documents[0].id]
        v2 = model.lsa[model.documents[2].id]
        self.assertTrue(v1.get(i1, 0)  > 0.7)
        self.assertTrue(v1.get(i2, 0) == 0.0)
        self.assertTrue(v2.get(i1, 0) == 0.0)
        self.assertTrue(v2.get(i2, 0)  > 0.7)
        # Assert LSA.transform() for unknown documents.
        v = model.lsa.transform(vector.Document("cats dogs"))
        self.assertAlmostEqual(v[0], 0.34, places=2)
        self.assertAlmostEqual(v[1], 0.34, places=2)
        print("pattern.vector.LSA.concepts")
        print("pattern.vector.LSA.transform()")
    
    def test_model_reduce(self):
        try:
            import numpy
        except ImportError:
            return
        # Test time and accuracy of model with sparse vectors of maximum 250 features.
        t1 = time.time()
        A1, P1, R1, F1, stdev = vector.KNN.test(self.model, folds=10)
        t1 = time.time() - t1
        # Test time and accuracy of model with reduced vectors of 20 features.
        self.model.reduce(dimensions=20)
        t2 = time.time()
        A2, P2, R2, F2, stdev = vector.KNN.test(self.model, folds=10)
        t2 = time.time() - t2
        self.assertTrue(len(self.model.lsa[self.model.documents[0].id]) == 20)
        self.assertTrue(t2 * 2 < t1)       # KNN over 2x faster.
        self.assertTrue(abs(F1-F2) < 0.06) # Difference in F-score = 1-6%.
        self.model.lsa = None
        print("pattern.vector.Model.reduce()")
          
#---------------------------------------------------------------------------------------------------

class TestClustering(unittest.TestCase):
    
    model = None
    
    def setUp(self):
        # Test spam model for clustering.
        if self.__class__.model is None:
            self.__class__.model = model(top=10)
        self.model = self.__class__.model
        random.seed(0)
        
    def tearDown(self):
        random.seed()
        
    def test_features(self):
        # Assert unique list of vector keys.
        v = vector.features(vectors=[{"cat":1}, {"dog":1}])
        self.assertEqual(sorted(v), ["cat", "dog"])
        print("pattern.vector.features()")
    
    def test_mean(self):
        # Assert iterator mean.
        self.assertEqual(vector.mean([], 0), 0)
        self.assertEqual(vector.mean([1,1.5,2], 3), 1.5)
        self.assertEqual(vector.mean(xrange(4), 4), 1.5)
        print("pattern.vector.mean()")
        
    def test_centroid(self):
        # Assert center of list of vectors.
        v = vector.centroid([{"cat":1}, {"cat":0.5, "dog":1}], features=["cat", "dog"])
        self.assertEqual(v, {"cat":0.75, "dog":0.5})
        print("pattern.vector.centroid()")
        
    def test_distance(self):
        # Assert distance metrics.
        v1 = vector.Vector({"cat":1})
        v2 = vector.Vector({"cat":0.5, "dog":1})
        for d, method in (
          (0.55, vector.COSINE),    # 1 - ((1*0.5 + 0*1) / (sqrt(1**2 + 0**2) * sqrt(0.5**2 + 1**2)))
          (1.25, vector.EUCLIDEAN), # (1-0.5)**2 + (0-1)**2
          (1.50, vector.MANHATTAN), # abs(1-0.5) + abs(0-1)
          (1.00, vector.HAMMING),   # (True + True) / 2
          (1.11, lambda v1, v2: 1.11)):
            self.assertAlmostEqual(vector.distance(v1, v2, method), d, places=2)
        print("pattern.vector.distance()")
        
    def test_distancemap(self):
        # Assert distance caching mechanism.
        v1 = vector.Vector({"cat":1})
        v2 = vector.Vector({"cat":0.5, "dog":1})
        m  = vector.DistanceMap(method=vector.COSINE)
        for i in range(100):
            self.assertAlmostEqual(m.distance(v1, v2), 0.55, places=2)
            self.assertAlmostEqual(m._cache[(v1.id, v2.id)], 0.55, places=2)
        print("pattern.vector.DistanceMap")
        
    def _test_k_means(self, seed):
        # Assert k-means clustering accuracy.
        A = []
        n = 100
        m = dict((d.vector.id, d.type) for d in self.model[:n])
        for i in range(30):
            # Create two clusters of vectors.
            k = vector.kmeans([d.vector for d in self.model[:n]], k=2, seed=seed)
            # Measure the number of spam in each clusters.
            # Ideally, we have a cluster without spam and one with only spam.
            i = len([1 for v in k[0] if m[v.id] == False])
            j = len([1 for v in k[1] if m[v.id] == False])
            A.append(max(i,j) * 2.0 / n)
        # Return average accuracy after 10 tests.
        return sum(A) / 30.0
    
    def test_k_means_random(self):
        # Assert k-means with random initialization.
        v = self._test_k_means(seed=vector.RANDOM)
        self.assertTrue(v >= 0.6)
        print("pattern.vector.kmeans(seed=RANDOM)")
        
    def test_k_means_kmpp(self):
        # Assert k-means with k-means++ initialization.
        # Note: vectors contain the top 10 features - see setUp().
        # If you include more features (more noise?) accuracy and performance will drop.
        v = self._test_k_means(seed=vector.KMPP)
        self.assertTrue(v >= 0.8)
        print("pattern.vector.kmeans(seed=KMPP)")
    
    def test_hierarchical(self):
        # Assert cluster contains nested clusters and/or vectors.
        def _test_cluster(cluster):
            for nested in cluster:
                if isinstance(nested, vector.Cluster):
                    v1 = set((v.id for v in nested.flatten()))
                    v2 = set((v.id for v in cluster.flatten()))
                    self.assertTrue(nested.depth < cluster.depth)
                    self.assertTrue(v1.issubset(v2))
                else:
                    self.assertTrue(isinstance(nested, vector.Vector))
            self.assertTrue(isinstance(cluster, list))
            self.assertTrue(isinstance(cluster.depth, int))
            self.assertTrue(isinstance(cluster.flatten(), list))
        n = 50
        m = dict((d.vector.id, d.type) for d in self.model[:n])
        h = vector.hierarchical([d.vector for d in self.model[:n]], k=2)
        h.traverse(_test_cluster)
        # Assert the accuracy of hierarchical clustering (shallow test).
        # Assert that cats are separated from dogs.
        v = (
            vector.Vector({"feline":1, " lion":1,   "mane":1}),
            vector.Vector({"feline":1, "tiger":1, "stripe":1}),
            vector.Vector({"canine":1,  "wolf":1,   "howl":1}),
            vector.Vector({"canine":1,   "dog":1,   "bark":1})
        )
        h = vector.hierarchical(v)
        self.assertTrue(len(h[0][0]) == 2)
        self.assertTrue(len(h[0][1]) == 2)
        self.assertTrue(v[0] in h[0][0] and v[1] in h[0][0] or v[0] in h[0][1] and v[1] in h[0][1])
        self.assertTrue(v[2] in h[0][0] and v[3] in h[0][0] or v[2] in h[0][1] and v[3] in h[0][1])
        print("pattern.vector.Cluster()")
        print("pattern.vector.hierarchical()"        )
    
#---------------------------------------------------------------------------------------------------

class TestClassifier(unittest.TestCase):
    
    model = None
    
    def setUp(self):
        # Test model for training classifiers.
        if self.__class__.model is None:
            self.__class__.model = model()
        self.model = self.__class__.model

    def _test_classifier(self, Classifier, **kwargs):
        # Assert classifier training + prediction for trivial cases.
        v = Classifier(**kwargs)
        for document in self.model:
            v.train(document)
        for type, message in (
          (False, "win money"),
          ( True, "fix bug")):
            self.assertEqual(v.classify(message), type)
        # Assert classifier properties.
        self.assertEqual(v.binary, True)
        self.assertEqual(sorted(v.classes), [False, True])
        self.assertTrue(isinstance(v.features, list))
        self.assertTrue("ftp" in v.features)
        # Assert saving + loading.
        v.save(Classifier.__name__)
        v = Classifier.load(Classifier.__name__)
        self.assertEqual(v.classify("win money"), False)
        self.assertEqual(v.classify("fix bug"),   True)
        os.remove(Classifier.__name__)
        # Assert untrained classifier returns None.
        v = Classifier(**kwargs)
        self.assertEqual(v.classify("herring"), None)
        print("pattern.vector.%s.train()"    % Classifier.__name__)
        print("pattern.vector.%s.classify()" % Classifier.__name__)
        print("pattern.vector.%s.save()"     % Classifier.__name__)
    
    def test_classifier_vector(self):
        # Assert Classifier._vector() (translates input from train() and classify() to a Vector).
        v = vector.Classifier()._vector
        self.assertEqual(("cat", {"cat":0.5, "purs":0.5}), v(vector.Document("the cat purs", type="cat")))
        self.assertEqual(("cat", {"cat":0.5, "purs":0.5}), v({"cat":0.5, "purs":0.5}, type="cat"))
        self.assertEqual(("cat", {"cat":0.5, "purs":0.5}), v(["cat", "purs"], type="cat"))
        self.assertEqual(("cat", {"cat":0.5, "purs":0.5}), v("cat purs", type="cat"))
        print("pattern.vector.Classifier._vector()")
    
    def test_nb(self):
        # Assert Bayesian probability classification.
        self._test_classifier(vector.NB)
        # Assert the accuracy of the classifier.
        A, P, R, F, o = vector.NB.test(self.model, folds=10, method=vector.BERNOUILLI)
        #print(A, P, R, F, o)
        self.assertTrue(P >= 0.89)
        self.assertTrue(R >= 0.89)
        self.assertTrue(F >= 0.89)
        
    def test_igtree(self):
        # Assert information gain tree classification.
        self._test_classifier(vector.IGTREE, method=vector.GAINRATIO)
        # Assert the accuracy of the classifier.
        A, P, R, F, o = vector.IGTREE.test(self.model, folds=10, method=vector.GAINRATIO)
        #print(A, P, R, F, o)
        self.assertTrue(P >= 0.90)
        self.assertTrue(R >= 0.89)
        self.assertTrue(F >= 0.89)
        
    def test_knn(self):
        # Assert nearest-neighbor classification.
        self._test_classifier(vector.KNN, k=10, distance=vector.COSINE)
        # Assert the accuracy of the classifier.
        A, P, R, F, o = vector.KNN.test(self.model, folds=10, k=2, distance=vector.COSINE)
        #print(A, P, R, F, o)
        self.assertTrue(P >= 0.92)
        self.assertTrue(R >= 0.92)
        self.assertTrue(F >= 0.92)

    def test_slp(self):
        random.seed(1)
        # Assert single-layer averaged perceptron classification.
        self._test_classifier(vector.SLP)
        # Assert the accuracy of the classifier.
        A, P, R, F, o = vector.SLP.test(self.model, folds=10, iterations=3)
        #print(A, P, R, F, o)
        self.assertTrue(P >= 0.92)
        self.assertTrue(R >= 0.92)
        self.assertTrue(F >= 0.92)
        
    def test_svm(self):
        try:
            from pattern.vector import svm
        except ImportError, e:
            print(e)
            return
        # Assert support vector classification.
        self._test_classifier(vector.SVM, type=vector.SVC, kernel=vector.LINEAR)
        # Assert the accuracy of the classifier.
        A, P, R, F, o = vector.SVM.test(self.model, folds=10, type=vector.SVC, kernel=vector.LINEAR)
        #print(A, P, R, F, o)
        self.assertTrue(P >= 0.93)
        self.assertTrue(R >= 0.93)
        self.assertTrue(F >= 0.93)
        
    def test_liblinear(self):
        # If LIBLINEAR can be loaded, 
        # assert that it is used for linear SVC (= 10x faster).
        try:
            from pattern.vector import svm
        except ImportError, e:
            print(e)
            return
        if svm.LIBLINEAR:
            classifier1 = vector.SVM(
                      type =  vector.CLASSIFICATION, 
                    kernel =  vector.LINEAR,
                extensions = (vector.LIBSVM, vector.LIBLINEAR))
            classifier2 = vector.SVM(
                      type =  vector.CLASSIFICATION, 
                    kernel =  vector.RBF,
                extensions = (vector.LIBSVM, vector.LIBLINEAR))
            classifier3 = vector.SVM(
                      type =  vector.CLASSIFICATION, 
                    kernel =  vector.LINEAR,
                extensions = (vector.LIBSVM,))
            self.assertEqual(classifier1.extension, vector.LIBLINEAR)
            self.assertEqual(classifier2.extension, vector.LIBSVM)
            self.assertEqual(classifier3.extension, vector.LIBSVM)
        print("pattern.vector.svm.LIBSVM")
        print("pattern.vector.svm.LIBLINEAR")

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUnicode))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestStemmer))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDocument))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestModel))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestApriori))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestLSA))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestClustering))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestClassifier))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
