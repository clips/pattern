# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest

from pattern import vector
from pattern.en import Text, Sentence, Word, parse

#-----------------------------------------------------------------------------------------------------

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
        print "pattern.web.decode_utf8()"

    def test_encode_utf8(self):
        # Assert Python bytestring.
        for s in self.strings:
            self.assertTrue(isinstance(vector.encode_utf8(s), str))
        print "pattern.web.encode_utf8()"

#-----------------------------------------------------------------------------------------------------

class TestUtilityFunctions(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_lreplace(self):
        # Assert left replace "1" => "2".
        v = vector.lreplace("1", "2", "123")
        self.assertEqual(v, "223")
        print "pattern.vector.lreplace()"
        
    def test_rreplace(self):
        # Assert right replace "3" => "2".
        v = vector.rreplace("3", "2", "123")
        self.assertEqual(v, "122")
        print "pattern.vector.rreplace()"
        
    def test_filename(self):
        # Assert "/path/path/file_name.txt" => "file name".
        v = vector.filename("/path/path/file_name.txt", map={"_":" "})
        self.assertEqual(v, "file name")
        print "pattern.vector.filename()"
        
    def test_shi(self):
        # Assert integer hashing algorithm.
        for a, b in (
          (   100, "1c"), 
          (  1000, "G8"), 
          ( 10000, "2bI"), 
          (100000, "Q0u")):
            self.assertEqual(vector.shi(a), b)
        print "pattern.vector.shi()"
            
    def test_shuffled(self):
        # Assert shuffled() <=> sorted().
        v1 = [1,2,3,4,5,6,7,8,9,10]
        v2 = vector.shuffled(v1)
        self.assertTrue(v1 != v2 and v1 == sorted(v2))
        print "pattern.vector.shuffled()"
        
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
        print "pattern.vector.chunk()"
        
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
        print "pattern.vector.readonlydict"
        
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
        print "pattern.vector.readonlylist"

#-----------------------------------------------------------------------------------------------------

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
        print "pattern.vector.stemmer.stem()"
    
    def test_stem_case_sensitive(self):
        # Assert stemmer case-sensitivity.
        for a, b in (
          ("Ponies", "Poni"),
          ("pONIES", "pONI"),
          ( "SKiES", "SKy"),
          ("cosmos", "cosmos")):
            self.assertEqual(vector.stemmer.stem(a), b)
        print "pattern.vector.stemmer.case_sensitive()"

#-----------------------------------------------------------------------------------------------------

class TestDocument(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_stopwords(self):
        # Assert common stop words.
        for w in ("a", "am", "an", "and", "i", "the", "therefore", "they", "what", "while"):
            self.assertTrue(w in vector.stopwords)
        print "pattern.vector.stopwords"
        
    def test_words(self):
        # Assert word split algorithm (default treats lines as spaces and ignores numbers).
        s = "The cat sat on the\nmat. 1 11."
        v = vector.words(s)
        self.assertEqual(v, ["The", "cat", "sat", "on", "the", "mat"])
        # Assert custom word filter.
        v = vector.words(s, filter=lambda w: True)
        self.assertEqual(v, ["The", "cat", "sat", "on", "the", "mat", "1", "11"])
        print "pattern.vector.words()"
        
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
        print "pattern.vector.stem()"
        
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
        print "pattern.vector.count()"

    def test_document(self):
        for w in (
          "The cats sat on the mat.",
          ["The", "cats", "sat", "on", "the", "mat", "."],
          {"the":2, "cats":1, "sat":1, "on":1, "mat":1, ".":1},
          Text(parse("The cats sat on the mat.")),
          Sentence(parse("The cats sat on the mat."))):
            v = vector.Document(w, stemmer=vector.LEMMA, stopwords=False, name="cat", type="cat")
            v = v.copy()
            self.assertEqual(v.name, "cat")
            self.assertEqual(v.type, "cat")
            print v.terms

#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUnicode))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestStemmer))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDocument))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
