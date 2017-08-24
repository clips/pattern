# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
import random
import subprocess

from pattern import text
from pattern import en

from io import open

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------


class TestInflection(unittest.TestCase):

    def setUp(self):
        pass

    def test_indefinite_article(self):
        # Assert "a" or "an".
        for article, word in (
         ("an", "hour"),
         ("an", "FBI"),
          ("a", "bear"),
          ("a", "one-liner"),
          ("a", "European"),
          ("a", "university"),
          ("a", "uterus"),
         ("an", "owl"),
         ("an", "yclept"),
          ("a", "year")):
            self.assertEqual(en.article(word, function=en.INDEFINITE), article)
        self.assertEqual(en.inflect.article("heir", function=en.DEFINITE), "the")
        self.assertEqual(en.inflect.referenced("ewe"), "a ewe")
        print("pattern.en.inflect.article()")

    def test_pluralize(self):
        # Assert "octopodes" for classical plural of "octopus".
        # Assert "octopuses" for modern plural.
        self.assertEqual("octopodes", en.inflect.pluralize("octopus", classical=True))
        self.assertEqual("octopuses", en.inflect.pluralize("octopus", classical=False))
        # Assert the accuracy of the pluralization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-en-celex.csv")):
            if en.inflect.pluralize(sg) == pl:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.95)
        print("pattern.en.inflect.pluralize()")

    def test_singularize(self):
        # Assert the accuracy of the singularization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-en-celex.csv")):
            if en.inflect.singularize(pl) == sg:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.95)
        print("pattern.en.inflect.singularize()")

    def test_find_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        # Note: the accuracy is higher (95%) when measured on CELEX word forms
        # (probably because en.verbs has high percentage irregular verbs).
        i, n = 0, 0
        for v1, v2 in en.inflect.verbs.inflections.items():
            if en.inflect.verbs.find_lemma(v1) == v2:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.90)
        print("pattern.en.inflect.verbs.find_lemma()")

    def test_find_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in en.inflect.verbs.infinitives.items():
            lexeme2 = en.inflect.verbs.find_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == lexeme2[j] or \
                   lexeme1[j] == "" and \
                   lexeme1[j > 5 and 10 or 0] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.90)
        print("pattern.en.inflect.verbs.find_lexeme()")

    def test_conjugate(self):
        # Assert different tenses with different conjugations.
        for (v1, v2, tense) in (
          ("be",   "be",       en.INFINITIVE),
          ("be",   "am",      (en.PRESENT, 1, en.SINGULAR)),
          ("be",   "are",     (en.PRESENT, 2, en.SINGULAR)),
          ("be",   "is",      (en.PRESENT, 3, en.SINGULAR)),
          ("be",   "are",     (en.PRESENT, 0, en.PLURAL)),
          ("be",   "being",   (en.PRESENT + en.PARTICIPLE,)),
          ("be",   "was",     (en.PAST, 1, en.SINGULAR)),
          ("be",   "were",    (en.PAST, 2, en.SINGULAR)),
          ("be",   "was",     (en.PAST, 3, en.SINGULAR)),
          ("be",   "were",    (en.PAST, 0, en.PLURAL)),
          ("be",   "were",    (en.PAST, 0, None)),
          ("be",   "been",    (en.PAST + en.PARTICIPLE,)),
          ("be",   "am",      "1sg"),
          ("be",   "are",     "2sg"),
          ("be",   "is",      "3sg"),
          ("be",   "are",     "1pl"),
          ("be",   "are",     "2pl"),
          ("be",   "are",     "3pl"),
          ("be",   "are",     "pl"),
          ("be",   "being",   "part"),
          ("be",   "was",     "1sgp"),
          ("be",   "were",    "2sgp"),
          ("be",   "was",     "3sgp"),
          ("be",   "were",    "1ppl"),
          ("be",   "were",    "2ppl"),
          ("be",   "were",    "3ppl"),
          ("be",   "were",    "p"),
          ("be",   "were",    "ppl"),
          ("be",   "been",    "ppart"),
          ("be",   "am not",  "1sg-"),
          ("be",   "aren't",  "2sg-"),
          ("be",   "isn't",   "3sg-"),
          ("be",   "aren't",  "1pl-"),
          ("be",   "aren't",  "2pl-"),
          ("be",   "aren't",  "3pl-"),
          ("be",   "aren't",  "pl-"),
          ("be",   "wasn't",  "1sgp-"),
          ("be",   "weren't", "2sgp-"),
          ("be",   "wasn't",  "3sgp-"),
          ("be",   "weren't", "1ppl-"),
          ("be",   "weren't", "2ppl-"),
          ("be",   "weren't", "3ppl-"),
          ("be",   "weren't", "ppl-"),
          ("had",  "have",    "inf"),
          ("had",  "have",    "1sg"),
          ("had",  "have",    "2sg"),
          ("had",  "has",     "3sg"),
          ("had",  "have",    "pl"),
          ("had",  "having",  "part"),
          ("has",  "had",     "1sgp"),
          ("has",  "had",     "2sgp"),
          ("has",  "had",     "3sgp"),
          ("has",  "had",     "ppl"),
          ("has",  "had",     "p"),
          ("has",  "had",     "ppart"),
          ("will", "will",    "1sg"),
          ("will", "will",    "2sg"),
          ("will", "will",    "3sg"),
          ("will", "will",    "1pl"),
          ("imaginerify", "imaginerifying", "part"),
          ("imaginerify", "imaginerified", "3sgp"),
          ("imaginerify", None, "1sg-")):
            self.assertEqual(en.inflect.conjugate(v1, tense), v2)
        print("pattern.en.inflect.conjugate()")

    def test_lemma(self):
        # Assert the infinitive of "weren't".
        v = en.inflect.lemma("weren't")
        self.assertEqual(v, "be")
        print("pattern.en.inflect.lemma()")

    def test_lexeme(self):
        # Assert all inflections of "be".
        v = en.inflect.lexeme("be")
        self.assertEqual(v, [
            "be", "am", "are", "is", "being",
            "was", "were", "been",
            "am not", "aren't", "isn't", "wasn't", "weren't"
        ])
        v = en.inflect.lexeme("imaginerify")
        self.assertEqual(v, [
            "imaginerify", "imaginerifies", "imaginerifying", "imaginerified"
        ])
        print("pattern.en.inflect.lexeme()")

    def test_tenses(self):
        # Assert tense recognition.
        self.assertTrue((en.inflect.PRESENT, 1, en.inflect.SINGULAR) in en.inflect.tenses("am"))
        self.assertTrue("1sg" in en.inflect.tenses("am"))
        self.assertTrue("1sg" in en.inflect.tenses("will"))
        self.assertTrue("2sg-" in en.inflect.tenses("won't"))
        self.assertTrue("part" in en.inflect.tenses("imaginarifying"))
        print("pattern.en.inflect.tenses()")

    def test_comparative(self):
        # Assert "nice" => "nicer".
        self.assertEqual(en.inflect.comparative("nice"), "nicer")
        print("pattern.en.inflect.comparative()")

    def test_superlative(self):
        # Assert "nice" => "nicest"
        self.assertEqual(en.inflect.superlative("nice"), "nicest")
        # Assert "important" => "most important"
        self.assertEqual(en.inflect.superlative("important"), "most important")
        print("pattern.en.inflect.superlative()")

#---------------------------------------------------------------------------------------------------


class TestQuantification(unittest.TestCase):

    def setUp(self):
        pass

    def test_extract_leading_zeros(self):
        # Assert "zero zero one" => ("one", 2).
        from pattern.text.en.inflect_quantify import zshift
        v = zshift("zero zero one")
        self.assertEqual(v, ("one", 2))
        v = zshift("0 0 one")
        self.assertEqual(v, ("one", 2))
        print("pattern.en.quantify._extract_leading_zeros()")

    def test_numerals(self):
        # Assert number to numerals.
        for x, s in (
          (    1.5, "one point five"),
          (     15, "fifteen"),
          (    150, "one hundred and fifty"),
          (    151, "one hundred and fifty-one"),
          (   1510, "one thousand five hundred and ten"),
          (  15101, "fifteen thousand one hundred and one"),
          ( 150101, "one hundred and fifty thousand one hundred and one"),
          (1500101, "one million, five hundred thousand one hundred and one")):
            self.assertEqual(en.numerals(x), s)
        print("pattern.en.numerals()")

    def test_number(self):
        # Assert numeric string = actual number (after rounding).
        for i in range(100):
            x = random.random()
            y = en.number(en.numerals(x, round=10))
            self.assertAlmostEqual(x, y, places=10)
        print("pattern.en.number()")

    def test_quantify(self):
        # Assert quantification algorithm.
        for a, s in (
          (   2 * ["carrot"], "a pair of carrots"),
          (   4 * ["carrot"], "several carrots"),
          (   9 * ["carrot"], "a number of carrots"),
          (  19 * ["carrot"], "a score of carrots"),
          (  23 * ["carrot"], "dozens of carrots"),
          ( 201 * ["carrot"], "hundreds of carrots"),
          (1001 * ["carrot"], "thousands of carrots"),
          ({"carrot": 4, "parrot": 2}, "several carrots and a pair of parrots")):
            self.assertEqual(en.quantify(a), s)
        print("pattern.en.quantify()")

    def test_reflect(self):
        self.assertEqual(en.reflect(""), "a string")
        self.assertEqual(en.reflect(["", "", ""]), "several strings")
        self.assertEqual(en.reflect(en.reflect), "a function")
        print("pattern.en.reflect()")

#---------------------------------------------------------------------------------------------------


class TestSpelling(unittest.TestCase):

    def test_spelling(self):
        # Assert case-sensitivity + numbers.
        for a, b in (
          (   ".", "."   ),
          (   "?", "?"   ),
          (   "!", "!"   ),
          (   "I", "I"   ),
          (   "a", "a"   ),
          (  "42", "42"  ),
          ("3.14", "3.14"),
          ( "The", "The" ),
          ( "the", "the" )):
            self.assertEqual(en.suggest(a)[0][0], b)
        # Assert spelling suggestion accuracy.
        # Note: simply training on more text will not improve accuracy.
        i = j = 0.0
        from pattern.db import Datasheet
        for correct, wrong in Datasheet.load(os.path.join(PATH, "corpora", "spelling-birkbeck.csv")):
            for w in wrong.split(" "):
                if en.suggest(w)[0][0] == correct:
                    i += 1
                else:
                    j += 1
        self.assertTrue(i / (i + j) > 0.70)
        print("pattern.en.suggest()")

#---------------------------------------------------------------------------------------------------


class TestParser(unittest.TestCase):

    def setUp(self):
        pass

    def test_tokenize(self):
        # Assert list with two sentences.
        # The tokenizer should at least handle common abbreviations and punctuation.
        v = en.tokenize("The cat is eating (e.g., a fish). Yum!")
        self.assertEqual(v, ["The cat is eating ( e.g. , a fish ) .", "Yum !"])
        print("pattern.en.tokenize()")

    def _test_morphological_rules(self, function=en.parser.morphology.apply):
        """ For each word in WordNet that is not in Brill's lexicon,
            test if the given tagger((word, "NN")) yields an improved (word, tag).
            Returns the relative scores for nouns, verbs, adjectives and adverbs.
        """
        scores = []
        for tag, lexicon in (
          ("NN", en.wordnet.NOUNS),
          ("VB", en.wordnet.VERBS),
          ("JJ", en.wordnet.ADJECTIVES),
          ("RB", en.wordnet.ADVERBS)):
            i, n = 0, 0
            for word in lexicon():
                word = word.replace("_", " ")
                if word not in en.lexicon:
                    if function([word, "NN"])[1].startswith(tag):
                        i += 1
                    n += 1
            scores.append(float(i) / n)
        return scores

    def test_default_suffix_rules(self):
        # Assert part-of-speech tag for unknown tokens.
        for a, b in (
          (["eating",  "NN"], ["eating",  "VBG"]),
          (["tigers",  "NN"], ["tigers",  "NNS"]),
          (["really",  "NN"], ["really",  "RB"]),
          (["foolish", "NN"], ["foolish", "JJ"])):
            self.assertEqual(text._suffix_rules(a), b)
        # Test with words in WordNet that are not in Brill's lexicon.
        # Given are the scores for detection of nouns, verbs, adjectives and adverbs.
        # The baseline should increase (not decrease) when the algorithm is modified.
        v = self._test_morphological_rules(function=text._suffix_rules)
        self.assertTrue(v[0] > 0.91) # NN
        self.assertTrue(v[1] > 0.23) # VB
        self.assertTrue(v[2] > 0.38) # JJ
        self.assertTrue(v[3] > 0.60) # RB
        print("pattern.text._suffix_rules()")

    def test_apply_morphological_rules(self):
        # Assert part-of-speech tag for unknown tokens (Brill's lexical rules).
        v = self._test_morphological_rules(function=en.parser.morphology.apply)
        self.assertTrue(v[0] > 0.85) # NN
        self.assertTrue(v[1] > 0.19) # VB
        self.assertTrue(v[2] > 0.65) # JJ
        self.assertTrue(v[3] > 0.59) # RB
        print("pattern.en.parser.morphology.apply()")

    def test_apply_context_rules(self):
        # Assert part-of-speech tags based on word context.
        for a, b in (                                                                 # Rule:
          ([["", "JJ"], ["", "JJ"], ["", ","]], [["", "JJ"], ["", "NN"], ["", ","]]), # SURROUNDTAG
          ([["", "NNP"], ["", "RB"]],           [["", "NNP"], ["", "NNP"]]),          # PREVTAG
          ([["", "NN"], ["", "PRP$"]],          [["", "VB"], ["", "PRP$"]]),          # NEXTTAG
          ([["phone", ""], ["", "VBZ"]],        [["phone", ""], ["", "NNS"]]),        # PREVWD
          ([["", "VB"], ["countries", ""]],     [["", "JJ"], ["countries", ""]]),     # NEXTWD
          ([["close", "VB"], ["to", ""]],       [["close", "RB"], ["to", ""]]),       # RBIGRAM
          ([["very", ""], ["much", "JJ"]],      [["very", ""], ["much", "RB"]]),      # LBIGRAM
          ([["such", "JJ"], ["as", "DT"]],      [["such", "JJ"], ["as", "IN"]]),      # WDNEXTWD
          ([["be", "VB"]],                      [["be", "VB"]])):                     # CURWD
            self.assertEqual(en.parser.context.apply(a), b)
        print("pattern.en.parser.context.apply()")

    def test_find_tags(self):
        # Assert part-of-speech-tag annotation.
        v = en.parser.find_tags(["black", "cat"])
        self.assertEqual(v, [["black", "JJ"], ["cat", "NN"]])
        self.assertEqual(en.parser.find_tags(["felix"])[0][1], "NN")
        self.assertEqual(en.parser.find_tags(["Felix"])[0][1], "NNP")
        print("pattern.en.parser.find_tags()")

    def test_find_chunks(self):
        # Assert chunk tag annotation.
        v = en.parser.find_chunks([["black", "JJ"], ["cat", "NN"]])
        self.assertEqual(v, [["black", "JJ", "B-NP", "O"], ["cat", "NN", "I-NP", "O"]])
        # Assert the accuracy of the chunker.
        # For example, in "The very black cat must be really meowing really loud in the yard.":
        # - "The very black" (NP)
        # - "must be really meowing" (VP)
        # - "really loud" (ADJP)
        # - "in" (PP)
        # - "the yard" (NP)
        v = en.parser.find_chunks([
            ["", "DT"], ["", "RB"], ["", "JJ"], ["", "NN"],
            ["", "MD"], ["", "RB"], ["", "VBZ"], ["", "VBG"],
            ["", "RB"], ["", "JJ"],
            ["", "IN"],
            ["", "CD"], ["", "NNS"]
        ])
        self.assertEqual(v, [
            ["", "DT", "B-NP", "O"], ["", "RB", "I-NP", "O"], ["", "JJ", "I-NP", "O"], ["", "NN", "I-NP", "O"],
            ["", "MD", "B-VP", "O"], ["", "RB", "I-VP", "O"], ["", "VBZ", "I-VP", "O"], ["", "VBG", "I-VP", "O"],
            ["", "RB", "B-ADJP", "O"], ["", "JJ", "I-ADJP", "O"],
            ["", "IN", "B-PP", "B-PNP"],
            ["", "CD", "B-NP", "I-PNP"], ["", "NNS", "I-NP", "I-PNP"]])
        # Assert commas inside chunks.
        # - "the big, black cat"
        v = en.parser.find_chunks([
            ["", "DT"], ["", "JJ"], ["", ","], ["", "JJ"], ["", "NN"]
        ])
        self.assertEqual(v, [
            ["", "DT", "B-NP", "O"],
            ["", "JJ", "I-NP", "O"],
            ["", ",", "I-NP", "O"],
            ["", "JJ", "I-NP", "O"],
            ["", "NN", "I-NP", "O"]
        ])
        # - "big, black and furry"
        v = en.parser.find_chunks([
            ["", "JJ"], ["", ","], ["", "JJ"], ["", "CC"], ["", "JJ"]
        ])
        self.assertEqual(v, [
            ["", "JJ", "B-ADJP", "O"],
            ["", ",", "I-ADJP", "O"],
            ["", "JJ", "I-ADJP", "O"],
            ["", "CC", "I-ADJP", "O"],
            ["", "JJ", "I-ADJP", "O"]
        ])
        # - big, and very black (= two chunks "big" and "very black")
        v = en.parser.find_chunks([
            ["", "JJ"], ["", ","], ["", "CC"], ["", "RB"], ["", "JJ"]
        ])
        self.assertEqual(v, [
            ["", "JJ", "B-ADJP", "O"],
            ["", ",", "O", "O"],
            ["", "CC", "O", "O"],
            ["", "RB", "B-ADJP", "O"],
            ["", "JJ", "I-ADJP", "O"]
        ])
        # Assert cases for which we have written special rules.
        # - "perhaps you" (ADVP + NP)
        v = en.parser.find_chunks([["", "RB"], ["", "PRP"]])
        self.assertEqual(v, [["", "RB", "B-ADVP", "O"], ["", "PRP", "B-NP", "O"]])
        # - "very nice cats" (NP)
        v = en.parser.find_chunks([["", "RB"], ["", "JJ"], ["", "PRP"]])
        self.assertEqual(v, [["", "RB", "B-NP", "O"], ["", "JJ", "I-NP", "O"], ["", "PRP", "I-NP", "O"]])
        print("pattern.en.parser.find_chunks()")

    def test_find_labels(self):
        # Assert relation tag annotation (SBJ/OBJ).
        v = en.parser.find_labels([
            ["", "", "NP"], ["", "", "NP"],
            ["", "", "VP"], ["", "", "VP"],
            ["", "", "NP"]])
        self.assertEqual(v, [
            ["", "", "NP", "NP-SBJ-1"], ["", "", "NP", "NP-SBJ-1"],
            ["", "", "VP", "VP-1"], ["", "", "VP", "VP-1"],
            ["", "", "NP", "NP-OBJ-1"]])
        print("pattern.en.parser.find_labels()")

    def test_find_prepositions(self):
        # Assert preposition tag annotation (PP + NP).
        v = en.parser.find_prepositions([
            ["", "", "NP"],
            ["", "", "VP"],
            ["", "", "PP"],
            ["", "", "NP"],
            ["", "", "NP"], ])
        self.assertEqual(v, [
            ["", "", "NP", "O"],
            ["", "", "VP", "O"],
            ["", "", "PP", "B-PNP"],
            ["", "", "NP", "I-PNP"],
            ["", "", "NP", "I-PNP"]])
        # Assert PNP's with consecutive PP's.
        v = en.parse("The cat was looking at me from up on the roof with interest.", prepositions=True)
        self.assertEqual(v,
            "The/DT/B-NP/O cat/NN/I-NP/O " \
            "was/VBD/B-VP/O looking/VBG/I-VP/O " \
            "at/IN/B-PP/B-PNP me/PRP/B-NP/I-PNP " \
            "from/IN/B-PP/B-PNP up/IN/I-PP/I-PNP on/IN/I-PP/I-PNP the/DT/B-NP/I-PNP roof/NN/I-NP/I-PNP " \
            "with/IN/B-PP/B-PNP interest/NN/B-NP/I-PNP " \
            "././O/O"
        )
        print("pattern.en.parser.find_prepositions()")

    def test_find_lemmata(self):
        # Assert lemmata for nouns and verbs.
        v = en.parser.find_lemmata([["cats", "NNS"], ["wearing", "VBG"], ["hats", "NNS"]])
        self.assertEqual(v, [
            ["cats", "NNS", "cat"],
            ["wearing", "VBG", "wear"],
            ["hats", "NNS", "hat"]])
        print("pattern.en.parser.find_lemmata()")

    def test_named_entity_recognition(self):
        # Assert named entities.
        v = en.parser.parse("Arnold Schwarzenegger is cool.", chunks=False)
        self.assertEqual(v,
            "Arnold/NNP-PERS Schwarzenegger/NNP-PERS is/VBZ cool/JJ ./."
        )
        print("pattern.en.parser.entities.apply()")

    def test_parse(self):
        # Assert parsed output with Penn Treebank II tags (slash-formatted).
        # 1) "the black cat" is a noun phrase, "on the mat" is a prepositional noun phrase.
        v = en.parser.parse("The black cat sat on the mat.")
        self.assertEqual(v,
            "The/DT/B-NP/O black/JJ/I-NP/O cat/NN/I-NP/O " + \
            "sat/VBD/B-VP/O " + \
            "on/IN/B-PP/B-PNP the/DT/B-NP/I-PNP mat/NN/I-NP/I-PNP ././O/O"
        )
        # 2) "the black cat" is the subject, "a fish" is the object.
        v = en.parser.parse("The black cat is eating a fish.", relations=True)
        self.assertEqual(v,
            "The/DT/B-NP/O/NP-SBJ-1 black/JJ/I-NP/O/NP-SBJ-1 cat/NN/I-NP/O/NP-SBJ-1 " + \
            "is/VBZ/B-VP/O/VP-1 eating/VBG/I-VP/O/VP-1 " + \
            "a/DT/B-NP/O/NP-OBJ-1 fish/NN/I-NP/O/NP-OBJ-1 ././O/O/O"
        )
        # 3) "chasing" and "mice" lemmata are "chase" and "mouse".
        v = en.parser.parse("The black cat is chasing mice.", lemmata=True)
        self.assertEqual(v,
            "The/DT/B-NP/O/the black/JJ/I-NP/O/black cat/NN/I-NP/O/cat " + \
            "is/VBZ/B-VP/O/be chasing/VBG/I-VP/O/chase " + \
            "mice/NNS/B-NP/O/mouse ././O/O/."
        )
        # 4) Assert str.
        self.assertTrue(isinstance(v, str))
        # 5) Assert str for faulty input (bytestring with unicode characters).
        self.assertTrue(isinstance(en.parse("ø ü"), str))
        self.assertTrue(isinstance(en.parse("ø ü", tokenize=True, tags=False, chunks=False), str))
        self.assertTrue(isinstance(en.parse("ø ü", tokenize=False, tags=False, chunks=False), str))
        self.assertTrue(isinstance(en.parse("o u", encoding="ascii"), str))
        # 6) Assert optional parameters (i.e., setting all to False).
        self.assertEqual(en.parse("ø ü.", tokenize=True, tags=False, chunks=False), "ø ü .")
        self.assertEqual(en.parse("ø ü.", tokenize=False, tags=False, chunks=False), "ø ü.")
        # 7) Assert the accuracy of the English tagger.
        i, n = 0, 0
        for corpus, a in (("tagged-en-wsj.txt", (0.968, 0.945)), ("tagged-en-oanc.txt", (0.929, 0.932))):
            for sentence in open(os.path.join(PATH, "corpora", corpus)).readlines():
                sentence = sentence.strip()
                s1 = [w.split("/") for w in sentence.split(" ")]
                s2 = [[w for w, pos in s1]]
                s2 = en.parse(s2, tokenize=False)
                s2 = [w.split("/") for w in s2.split(" ")]
                for j in range(len(s1)):
                    if s1[j][1] == s2[j][1].split("-")[0]:
                        i += 1
                    n += 1
            #print(corpus, float(i) / n)
            self.assertTrue(float(i) / n > (en.parser.model and a[0] or a[1]))
        print("pattern.en.parse()")

    def test_tagged_string(self):
        # Assert splitable TaggedString with language and tags properties.
        v = en.parser.parse("The black cat sat on the mat.", relations=True, lemmata=True)
        self.assertEqual(v.language, "en")
        self.assertEqual(v.tags,
            ["word", "part-of-speech", "chunk", "preposition", "relation", "lemma"])
        self.assertEqual(v.split(text.TOKENS)[0][0],
            ["The", "DT", "B-NP", "O", "NP-SBJ-1", "the"])
        print("pattern.en.parse().split()")

    def test_parsetree(self):
        # Assert parsetree(s) == Text.
        v = en.parsetree("The cat purs.")
        self.assertTrue(isinstance(v, en.Text))
        print("pattern.en.parsetree()")

    def test_split(self):
        # Assert split(parse(s)) == Text.
        v = en.split(en.parse("The cat purs."))
        self.assertTrue(isinstance(v, en.Text))
        print("pattern.en.split()")

    def test_tag(self):
        # Assert [("black", "JJ"), ("cats", "NNS")].
        v = en.tag("black cats")
        self.assertEqual(v, [("black", "JJ"), ("cats", "NNS")])
        v = en.tag("")
        self.assertEqual(v, [])
        print("pattern.en.tag()")

    def test_ngrams(self):
        # Assert n-grams with and without punctuation marks / sentence marks.
        s = "The cat is napping."
        v1 = en.ngrams(s, n=2)
        v2 = en.ngrams(s, n=3, punctuation=en.PUNCTUATION.strip("."))
        self.assertEqual(v1, [("The", "cat"), ("cat", "is"), ("is", "napping")])
        self.assertEqual(v2, [("The", "cat", "is"), ("cat", "is", "napping"), ("is", "napping", ".")])
        s = "The cat purrs. The dog barks."
        v1 = en.ngrams(s, n=2)
        v2 = en.ngrams(s, n=2, continuous=True)
        self.assertEqual(v1, [("The", "cat"), ("cat", "purrs"), ("The", "dog"), ("dog", "barks")])
        self.assertEqual(v2, [("The", "cat"), ("cat", "purrs"), ("purrs", "The"), ("The", "dog"), ("dog", "barks")])
        print("pattern.en.ngrams()")

    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.en", "-s", "Nice cat.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read().decode('utf-8')
        v = v.strip()
        self.assertEqual(v, "Nice/JJ/B-NP/O/O/nice cat/NN/I-NP/O/O/cat ././O/O/O/.")
        print("python -m pattern.en")

#---------------------------------------------------------------------------------------------------


class TestParseTree(unittest.TestCase):

    def setUp(self):
        # Parse sentences to test on.
        # Creating a Text creates Sentence, Chunk, PNP and Word.
        # Creating a Sentence tests Sentence.append() and Sentence.parse_token().
        self.text = "I'm eating pizza with a fork. What a tasty pizza!"
        self.text = en.Text(en.parse(self.text, relations=True, lemmata=True))

    def test_copy(self):
        # Assert deepcopy of Text, Sentence, Chunk, PNP and Word.
        self.text = self.text.copy()
        print("pattern.en.Text.copy()")

    def test_xml(self):
        # Assert XML export and import.
        self.text = en.Text.from_xml(self.text.xml)
        print("pattern.en.Text.xml")
        print("pattern.en.Text.from_xml()")

    def test_text(self):
        # Assert Text.
        self.assertEqual(self.text.sentences[0].string, "I 'm eating pizza with a fork .")
        self.assertEqual(self.text.sentences[1].string, "What a tasty pizza !")
        print("pattern.en.Text")

    def test_sentence(self):
        # Assert Sentence.
        v = self.text[0]
        self.assertTrue(v.start == 0)
        self.assertTrue(v.stop == 8)
        self.assertTrue(v.string == "I 'm eating pizza with a fork .")
        self.assertTrue(v.subjects == [self.text[0].chunks[0]])
        self.assertTrue(v.verbs == [self.text[0].chunks[1]])
        self.assertTrue(v.objects == [self.text[0].chunks[2]])
        self.assertTrue(v.nouns == [self.text[0].words[3], self.text[0].words[6]])
        # Sentence.string must be unicode.
        self.assertTrue(isinstance(v.string, str))
        self.assertTrue(isinstance(str(v), str))
        print("pattern.en.Sentence")

    def test_sentence_constituents(self):
        # Assert in-order list of Chunk, PNP and Word.
        v = self.text[0].constituents(pnp=True)
        self.assertEqual(v, [
            self.text[0].chunks[0],
            self.text[0].chunks[1],
            self.text[0].chunks[2],
            self.text[0].pnp[0],
            self.text[0].words[7],
        ])
        print("pattern.en.Sentence.constituents()")

    def test_slice(self):
        # Assert sentence slice.
        v = self.text[0].slice(start=4, stop=6)
        self.assertTrue(v.parent == self.text[0])
        self.assertTrue(v.string == "with a")
        # Assert sentence slice tag integrity.
        self.assertTrue(v.words[0].type == "IN")
        self.assertTrue(v.words[1].chunk is None)
        print("pattern.en.Slice")

    def test_chunk(self):
        # Assert chunk with multiple words ("a fork").
        v = self.text[0].chunks[4]
        self.assertTrue(v.start == 5)
        self.assertTrue(v.stop == 7)
        self.assertTrue(v.string == "a fork")
        self.assertTrue(v.lemmata == ["a", "fork"])
        self.assertTrue(v.words == [self.text[0].words[5], self.text[0].words[6]])
        self.assertTrue(v.head == self.text[0].words[6])
        self.assertTrue(v.type == "NP")
        self.assertTrue(v.role is None)
        self.assertTrue(v.pnp is not None)
        # Assert chunk that is subject/object of the sentence ("pizza").
        v = self.text[0].chunks[2]
        self.assertTrue(v.role == "OBJ")
        self.assertTrue(v.relation == 1)
        self.assertTrue(v.related == [self.text[0].chunks[0], self.text[0].chunks[1]])
        self.assertTrue(v.subject == self.text[0].chunks[0])
        self.assertTrue(v.verb == self.text[0].chunks[1])
        self.assertTrue(v.object is None)
        # Assert chunk traversal.
        self.assertEqual(v.nearest("VP"), self.text[0].chunks[1])
        self.assertEqual(v.previous(), self.text[0].chunks[1])
        self.assertEqual(v.next(), self.text[0].chunks[3])
        print("pattern.en.Chunk")

    def test_chunk_conjunctions(self):
        # Assert list of conjunct/disjunct chunks ("black cat" AND "white cat").
        v = en.Sentence(en.parse("black cat and white cat"))
        self.assertEqual(v.chunk[0].conjunctions, [(v.chunk[1], en.AND)])
        print("pattern.en.Chunk.conjunctions()")

    def test_chunk_modifiers(self):
        # Assert list of nearby adjectives and adverbs with no role, for VP.
        v = en.Sentence(en.parse("Perhaps you should go."))
        self.assertEqual(v.chunk[2].modifiers, [v.chunk[0]]) # should <=> perhaps
        print("pattern.en.Chunk.modifiers")

    def test_pnp(self):
        # Assert PNP chunk ("with a fork").
        v = self.text[0].pnp[0]
        self.assertTrue(v.string == "with a fork")
        self.assertTrue(v.chunks == [self.text[0].chunks[3], self.text[0].chunks[4]])
        self.assertTrue(v.pp == self.text[0].chunks[3])
        print("pattern.en.PNP")

    def test_word(self):
        # Assert word tags ("fork" => NN).
        v = self.text[0].words[6]
        self.assertTrue(v.index == 6)
        self.assertTrue(v.string == "fork")
        self.assertTrue(v.lemma == "fork")
        self.assertTrue(v.type == "NN")
        self.assertTrue(v.chunk == self.text[0].chunks[4])
        self.assertTrue(v.pnp is not None)
        for i, tags in enumerate([
          ["I", "PRP", "B-NP", "O", "NP-SBJ-1", "i"],
          ["'m", "VBP", "B-VP", "O", "VP-1", "be"],
          ["eating", "VBG", "I-VP", "O", "VP-1", "eat"],
          ["pizza", "NN", "B-NP", "O", "NP-OBJ-1", "pizza"],
          ["with", "IN", "B-PP", "B-PNP", "O", "with"],
          ["a", "DT", "B-NP", "I-PNP", "O", "a"],
          ["fork", "NN", "I-NP", "I-PNP", "O", "fork"],
          [".", ".", "O", "O", "O", "."]]):
            self.assertEqual(self.text[0].words[i].tags, tags)
        print("pattern.en.Word")

    def test_word_custom_tags(self):
        # Assert word custom tags ("word/part-of-speech/.../some-custom-tag").
        s = en.Sentence("onion/NN/FOOD", token=[en.WORD, en.POS, "semantic_type"])
        v = s.words[0]
        self.assertEqual(v.semantic_type, "FOOD")
        self.assertEqual(v.custom_tags["semantic_type"], "FOOD")
        self.assertEqual(v.copy().custom_tags["semantic_type"], "FOOD")
        # Assert addition of new custom tags.
        v.custom_tags["taste"] = "pungent"
        self.assertEqual(s.token, [en.WORD, en.POS, "semantic_type", "taste"])
        print("pattern.en.Word.custom_tags")

    def test_find(self):
        # Assert first item for which given function is True.
        v = text.tree.find(lambda x: x > 10, [1, 2, 3, 11, 12])
        self.assertEqual(v, 11)
        print("pattern.text.tree.find()")

    def test_zip(self):
        # Assert list of zipped tuples, using default to balance uneven lists.
        v = text.tree.zip([1, 2, 3], [4, 5, 6, 7], default=0)
        self.assertEqual(v, [(1, 4), (2, 5), (3, 6), (0, 7)])
        print("pattern.text.tree.zip()")

    def test_unzip(self):
        v = text.tree.unzip(1, [(1, 4), (2, 5), (3, 6)])
        self.assertEqual(v, [4, 5, 6])
        print("pattern.text.tree.unzip()")

    def test_unique(self):
        # Assert list copy with unique items.
        v = text.tree.unique([1, 1, 1])
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], 1)
        print("pattern.text.tree.unique()")

    def test_map(self):
        # Assert dynamic Map().
        v = text.tree.Map(lambda x: x + 1, [1, 2, 3])
        self.assertEqual(list(v), [2, 3, 4])
        self.assertEqual(v.items[0], 1)
        print("pattern.text.tree.Map()")

#---------------------------------------------------------------------------------------------------


class TestModality(unittest.TestCase):

    def setUp(self):
        pass

    def test_imperative(self):
        # Assert True for sentences that are orders, commands, warnings.
        from pattern.text.en.modality import imperative
        for b, s in (
          (True, "Do your homework!"),
          (True, "Do not listen to me."),
          (True, "Turn that off, will you."),
          (True, "Let's help him."),
          (True, "Help me!"),
          (True, "You will help me."),
          (False, "Do it if you think it is necessary."),
          (False, "I hope you will help me."),
          (False, "I can help you."),
          (False, "I can help you if you let me.")):
            self.assertEqual(imperative(en.Sentence(en.parse(s))), b)
        print("pattern.en.modality.imperative()")

    def test_conditional(self):
        # Assert True for sentences that contain possible or imaginary situations.
        from pattern.text.en.modality import conditional
        for b, s in (
          (True, "We ought to help him."),
          (True, "We could help him."),
          (True, "I will help you."),
          (True, "I hope you will help me."),
          (True, "I can help you if you let me."),
          (False, "You will help me."),
          (False, "I can help you.")):
            self.assertEqual(conditional(en.Sentence(en.parse(s))), b)
        # Assert predictive mood.
        s = "I will help you."
        v = conditional(en.Sentence(en.parse(s)), predictive=False)
        self.assertEqual(v, False)
        # Assert speculative mood.
        s = "I will help you if you pay me."
        v = conditional(en.Sentence(en.parse(s)), predictive=False)
        self.assertEqual(v, True)
        print("pattern.en.modality.conditional()")

    def test_subjunctive(self):
        # Assert True for sentences that contain wishes, judgments or opinions.
        from pattern.text.en.modality import subjunctive
        for b, s in (
          (True, "I wouldn't do that if I were you."),
          (True, "I wish I knew."),
          (True, "I propose that you be on time."),
          (True, "It is a bad idea to be late."),
          (False, "I will be late.")):
            self.assertEqual(subjunctive(en.Sentence(en.parse(s))), b)
        print("pattern.en.modality.subjunctive()")

    def test_negated(self):
        # Assert True for sentences that contain "not", "n't" or "never".
        for b, s in (
          (True, "Not true?"),
          (True, "Never true."),
          (True, "Isn't true."),):
            self.assertEqual(en.negated(en.Sentence(en.parse(s))), b)
        print("pattern.en.negated()")

    def test_mood(self):
        # Assert imperative mood.
        v = en.mood(en.Sentence(en.parse("Do your homework!")))
        self.assertEqual(v, en.IMPERATIVE)
        # Assert conditional mood.
        v = en.mood(en.Sentence(en.parse("We ought to help him.")))
        self.assertEqual(v, en.CONDITIONAL)
        # Assert subjunctive mood.
        v = en.mood(en.Sentence(en.parse("I wouldn't do that if I were you.")))
        self.assertEqual(v, en.SUBJUNCTIVE)
        # Assert indicative mood.
        v = en.mood(en.Sentence(en.parse("The weather is nice today.")))
        self.assertEqual(v, en.INDICATIVE)
        print("pattern.en.mood()")

    def test_modality(self):
        # Assert -1.0 => +1.0 representing the degree of certainty.
        v = en.modality(en.Sentence(en.parse("I wish it would stop raining.")))
        self.assertTrue(v < 0)
        v = en.modality(en.Sentence(en.parse("It will surely stop raining soon.")))
        self.assertTrue(v > 0)
        # Assert the accuracy of the modality algorithm.
        # Given are the scores for the CoNLL-2010 Shared Task 1 Wikipedia uncertainty data:
        # http://www.inf.u-szeged.hu/rgai/conll2010st/tasks.html#task1
        # The baseline should increase (not decrease) when the algorithm is modified.
        from pattern.db import Datasheet
        from pattern.metrics import test
        sentences = []
        for certain, sentence in Datasheet.load(os.path.join(PATH, "corpora", "uncertainty-conll2010.csv")):
            sentence = en.parse(sentence, chunks=False, light=True)
            sentence = en.Sentence(sentence)
            sentences.append((sentence, int(certain) > 0))
        A, P, R, F = test(lambda sentence: en.modality(sentence) > 0.5, sentences)
        #print(A, P, R, F)
        self.assertTrue(A > 0.69)
        self.assertTrue(P > 0.72)
        self.assertTrue(R > 0.63)
        self.assertTrue(F > 0.68)
        print("pattern.en.modality()")

#---------------------------------------------------------------------------------------------------


class TestSentiment(unittest.TestCase):

    def setUp(self):
        pass

    def test_sentiment_avg(self):
        # Assert 2.5.
        from pattern.text import avg
        v = avg([1, 2, 3, 4])
        self.assertEqual(v, 2.5)
        print("pattern.text.avg")

    def test_sentiment(self):
        # Assert < 0 for negative adjectives and > 0 for positive adjectives.
        self.assertTrue(en.sentiment("wonderful")[0] > 0)
        self.assertTrue(en.sentiment("horrible")[0] < 0)
        self.assertTrue(en.sentiment(en.wordnet.synsets("horrible", pos="JJ")[0])[0] < 0)
        self.assertTrue(en.sentiment(en.Text(en.parse("A bad book. Really horrible.")))[0] < 0)
        # Assert that :) and :( are recognized.
        self.assertTrue(en.sentiment(":)")[0] > 0)
        self.assertTrue(en.sentiment(":(")[0] < 0)
        # Assert the accuracy of the sentiment analysis (for the positive class).
        # Given are the scores for Pang & Lee's polarity dataset v2.0:
        # http://www.cs.cornell.edu/people/pabo/movie-review-data/
        # The baseline should increase (not decrease) when the algorithm is modified.
        from pattern.db import Datasheet
        from pattern.metrics import test
        reviews = []
        for score, review in Datasheet.load(os.path.join(PATH, "corpora", "polarity-en-pang&lee1.csv")):
            reviews.append((review, int(score) > 0))
        from time import time
        t = time()
        A, P, R, F = test(lambda review: en.positive(review), reviews)
        #print(A, P, R, F)
        self.assertTrue(A > 0.752)
        self.assertTrue(P > 0.772)
        self.assertTrue(R > 0.715)
        self.assertTrue(F > 0.743)
        # Assert the accuracy of the sentiment analysis on short text (for the positive class).
        # Given are the scores for Pang & Lee's sentence polarity dataset v1.0:
        # http://www.cs.cornell.edu/people/pabo/movie-review-data/
        reviews = []
        for score, review in Datasheet.load(os.path.join(PATH, "corpora", "polarity-en-pang&lee2.csv")):
            reviews.append((review, int(score) > 0))
        A, P, R, F = test(lambda review: en.positive(review), reviews)
        #print(A, P, R, F)
        self.assertTrue(A > 0.654)
        self.assertTrue(P > 0.660)
        self.assertTrue(R > 0.636)
        self.assertTrue(F > 0.648)
        print("pattern.en.sentiment()")

    def test_sentiment_twitter(self):
        sanders = os.path.join(PATH, "corpora", "polarity-en-sanders.csv")
        if os.path.exists(sanders):
            # Assert the accuracy of the sentiment analysis on tweets.
            # Given are the scores for Sanders Twitter Sentiment Corpus:
            # http://www.sananalytics.com/lab/twitter-sentiment/
            # Positive + neutral is taken as polarity >= 0.0,
            # Negative is taken as polarity < 0.0.
            # Since there are a lot of neutral cases,
            # and the algorithm predicts 0.0 by default (i.e., majority class) the results are good.
            # Distinguishing negative from neutral from positive is a much harder task
            from pattern.db import Datasheet
            from pattern.metrics import test
            reviews = []
            for i, id, date, tweet, polarity, topic in Datasheet.load(sanders):
                if polarity != "irrelevant":
                    reviews.append((tweet, polarity in ("positive", "neutral")))
            A, P, R, F = test(lambda review: en.positive(review, threshold=0.0), reviews)
            #print(A, P, R, F)
            self.assertTrue(A > 0.824)
            self.assertTrue(P > 0.879)
            self.assertTrue(R > 0.911)
            self.assertTrue(F > 0.895)

    def test_sentiment_assessment(self):
        # Assert that en.sentiment() has a fine-grained "assessments" property.
        v = en.sentiment("A warm and pleasant day.").assessments
        self.assertTrue(v[1][0][0] == "pleasant")
        self.assertTrue(v[1][1] > 0)
        print("pattern.en.sentiment().assessments")

    def test_polarity(self):
        # Assert that en.polarity() yields en.sentiment()[0].
        s = "A great day!"
        self.assertTrue(en.polarity(s) == en.sentiment(s)[0])
        print("pattern.en.polarity()")

    def test_subjectivity(self):
        # Assert that en.subjectivity() yields en.sentiment()[1].
        s = "A great day!"
        self.assertTrue(en.subjectivity(s) == en.sentiment(s)[1])
        print("pattern.en.subjectivity()")

    def test_positive(self):
        # Assert that en.positive() yields polarity >= 0.1.
        s = "A great day!"
        self.assertTrue(en.positive(s))
        print("pattern.en.subjectivity()")

    def test_sentiwordnet(self):
        # Assert < 0 for negative words and > 0 for positive words.
        try:
            from pattern.text.en.wordnet import SentiWordNet
            lexicon = SentiWordNet()
            lexicon.load()
        except ImportError as e:
            # SentiWordNet data file is not installed in default location, stop test.
            print(e)
            return
        self.assertTrue(lexicon["wonderful"][0] > 0)
        self.assertTrue(lexicon["horrible"][0] < 0)
        print("pattern.en.sentiment.SentiWordNet")

#---------------------------------------------------------------------------------------------------


class TestWordNet(unittest.TestCase):

    def setUp(self):
        pass

    def test_normalize(self):
        # Assert normalization of simple diacritics (WordNet does not store diacritics).
        self.assertEqual(en.wordnet.normalize("cliché"), "cliche")
        self.assertEqual(en.wordnet.normalize("façade"), "facade")
        print("pattern.en.wordnet.normalize()")

    def test_version(self):
        print("WordNet " + en.wordnet.VERSION)

    def test_synsets(self):
        # Assert synsets by part-of-speech.
        for word, pos in (
             ("cat", en.wordnet.NOUN),
            ("purr", en.wordnet.VERB),
            ("nice", en.wordnet.ADJECTIVE),
          ("nicely", en.wordnet.ADVERB),
             ("cat", "nn"),
             ("cat", "NNS")):
            self.assertTrue(en.wordnet.synsets(word, pos) != [])
        # Assert TypeError when part-of-speech is not NOUN, VERB, ADJECTIVE or ADVERB.
        self.assertRaises(TypeError, en.wordnet.synsets, "cat", "unknown_pos")
        print("pattern.en.wordnet.synsets()")

    def test_synset(self):
        v = en.wordnet.synsets("puma")[0]
        # Assert Synset(id).
        self.assertEqual(v, en.wordnet.Synset(v.id))
        self.assertEqual(v.pos, en.wordnet.NOUN)
        self.assertAlmostEqual(v.ic, 0.0, places=1)
        self.assertTrue("cougar" in v.synonyms) # ["cougar", "puma", "catamount", ...]
        self.assertTrue("feline" in v.gloss)    # "large American feline resembling a lion"
        # Assert WordNet relations.
        s = en.wordnet.synsets
        v = s("tree")[0]
        self.assertTrue(v.hypernym          in v.hypernyms())
        self.assertTrue(s("woody plant")[0] in v.hypernyms())
        self.assertTrue(s("entity")[0]      in v.hypernyms(recursive=True))
        self.assertTrue(s("beech")[0]       in v.hyponyms())
        self.assertTrue(s("red beech")[0]   in v.hyponyms(recursive=True))
        self.assertTrue(s("trunk")[0]       in v.meronyms())
        self.assertTrue(s("forest")[0]      in v.holonyms())
        # Assert Lin-similarity.
        self.assertTrue(
            v.similarity(s("flower")[0]) >
            v.similarity(s("teapot")[0]))
        print("pattern.en.wordnet.Synset")

    def test_ancenstor(self):
        # Assert least-common-subsumer algorithm.
        v1 = en.wordnet.synsets("cat")[0]
        v2 = en.wordnet.synsets("dog")[0]
        self.assertTrue(en.wordnet.ancestor(v1, v2) == en.wordnet.synsets("carnivore")[0])
        print("pattern.en.wordnet.ancestor()")

    def test_map32(self):
        # Assert sense mapping from WN 3.0 to 2.1.
        self.assertEqual(en.wordnet.map32(18850, "JJ"), (19556, "JJ"))
        self.assertEqual(en.wordnet.map32(1382437, "VB"), (1370230, "VB"))
        print("pattern.en.wordnet.map32")

    def test_sentiwordnet(self):
        # Assert SentiWordNet is loaded correctly.
        if en.wordnet.sentiwordnet is None:
            return
        try:
            en.wordnet.sentiwordnet.load()
        except ImportError:
            return
        v = en.wordnet.synsets("anguish")[0]
        self.assertEqual(v.weight, (-0.625, 0.625))
        v = en.wordnet.synsets("enzymology")[0]
        self.assertEqual(v.weight, (0.125, 0.125))
        print("pattern.en.wordnet.sentiwordnet")

#---------------------------------------------------------------------------------------------------


class TestWordlists(unittest.TestCase):

    def setUp(self):
        pass

    def test_wordlist(self):
        # Assert lazy loading Wordlist.
        v = en.wordlist.STOPWORDS
        self.assertTrue("the" in v)
        # Assert Wordlist to dict.
        v = dict.fromkeys(en.wordlist.STOPWORDS, True)
        self.assertTrue("the" in v)
        # Assert new Wordlist by adding other Wordlists.
        v = en.wordlist.STOPWORDS + en.wordlist.ACADEMIC
        self.assertTrue("the" in v)
        self.assertTrue("dr." in v)
        print("pattern.en.wordlist.Wordlist")

#---------------------------------------------------------------------------------------------------


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestQuantification))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSpelling))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParseTree))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestModality))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestWordNet))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestWordlists))
    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
