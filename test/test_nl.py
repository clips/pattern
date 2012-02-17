# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest
import subprocess

from pattern import nl

#---------------------------------------------------------------------------------------------------

class TestInflection(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_pluralize(self):
        # Assert "auto's" as plural of "auto".
        self.assertEqual("auto's", nl.inflect.pluralize("auto"))
        # Assert the accuracy of the pluralization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, sg, pl in Datasheet.load(os.path.join("corpora", "celex-wordforms-nl.csv")):
            if nl.pluralize(sg) == pl:
                i +=1
            n += 1
        self.assertTrue(float(i) / n > 0.74)
        print "pattern.nl.pluralize()"
        
    def test_singularize(self):
        # Assert the accuracy of the singularization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, sg, pl in Datasheet.load(os.path.join("corpora", "celex-wordforms-nl.csv")):
            if nl.singularize(pl) == sg:
                i +=1
            n += 1
        self.assertTrue(float(i) / n > 0.88)
        print "pattern.nl.singularize()"

    def test_attributive(self):
        # Assert the accuracy of the attributive algorithm ("fel" => "felle").
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, sg, pl in Datasheet.load(os.path.join("corpora", "celex-wordforms-nl.csv")):
            if nl.attributive(pred) == attr:
                i +=1
            n += 1
        self.assertTrue(float(i) / n > 0.96)
        print "pattern.nl.attributive()"
        
    def test_predicative(self):
        # Assert the accuracy of the predicative algorithm ("felle" => "fel").
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, sg, pl in Datasheet.load(os.path.join("corpora", "celex-wordforms-nl.csv")):
            if nl.predicative(attr) == pred:
                i +=1
            n += 1
        self.assertTrue(float(i) / n > 0.96)
        print "pattern.nl.predicative()"

    def test_parse_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        # Note: the accuracy is higher (90%) when measured on CELEX word forms
        # (presumably because nl.inflect.VERBS has high percentage irregular verbs).
        i, n = 0, 0
        for v in nl.inflect.VERBS.infinitives:
            for tense in nl.inflect.VERBS.TENSES:
                if nl.inflect._parse_lemma(nl.conjugate(v, tense)) == v: 
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.83)
        print "pattern.nl.inflect._parse_lemma()"
        
    def test_parse_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in nl.inflect.VERBS.infinitives.items():
            lexeme2 = nl.inflect._parse_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == lexeme2[j] or \
                   lexeme1[j] == "" and \
                   lexeme1[j>5 and 10 or 0] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.79)
        print "pattern.nl.inflect._parse_lexeme()"

    def test_conjugate(self):
        # Assert different tenses with different conjugations.
        for (v1, v2, tense) in (
          ("zijn",  "zijn",     nl.INFINITIVE),
          ("zijn",  "ben",      nl.PRESENT_1ST_PERSON_SINGULAR),
          ("zijn",  "bent",     nl.PRESENT_2ND_PERSON_SINGULAR),
          ("zijn",  "is",       nl.PRESENT_3RD_PERSON_SINGULAR),
          ("zijn",  "zijn",     nl.PRESENT_PLURAL),
          ("zijn",  "zijnd",    nl.PRESENT_PARTICIPLE),
          ("zijn",  "was",      nl.PAST_1ST_PERSON_SINGULAR),
          ("zijn",  "was",      nl.PAST_2ND_PERSON_SINGULAR),
          ("zijn",  "was",      nl.PAST_3RD_PERSON_SINGULAR),
          ("zijn",  "waren",    nl.PAST_PLURAL),
          ("zijn",  "was",      nl.PAST),
          ("zijn",  "geweest",  nl.PAST_PARTICIPLE),
          ("had",   "hebben",   "inf"),
          ("had",   "heb",      "1sg"),
          ("had",   "hebt",     "2sg"),
          ("had",   "heeft",    "3sg"),
          ("had",   "hebben",   "pl"),
          ("had",   "hebbend",  "part"),
          ("heeft", "had",      "1sgp"),
          ("heeft", "had",      "2sgp"),
          ("heeft", "had",      "3sgp"),
          ("heeft", "hadden",   "ppl"),
          ("heeft", "had",      "p"),
          ("heeft", "gehad",    "ppart"),
          ("smsen", "smste",    "3sgp")):
            self.assertEqual(nl.conjugate(v1, tense), v2)
        print "pattern.nl.conjugate()"

#---------------------------------------------------------------------------------------------------

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass
   
    def test_wotan2penntreebank(self):
        # Assert tag translation.
        for penntreebank, wotan in (
          ("NNP",  "N(eigen,ev,neut)"),
          ("NNPS", "N(eigen,mv,neut)"),
          ("NN",   "N(soort,ev,neut)"),
          ("NNS",  "N(soort,mv,neut)"),
          ("VBZ",  "V(refl,ott,3,ev)"),
          ("VBP",  "V(intrans,ott,1_of_2_of_3,mv)"),
          ("VBD",  "V(trans,ovt,1_of_2_of_3,mv)"),
          ("VBN",  "V(trans,verl_dw,onverv)"),
          ("VBG",  "V(intrans,teg_dw,onverv)"),
          ("VB",   "V(intrans,inf)"),
          ("MD",   "V(hulp_of_kopp,ott,3,ev)"),
          ("JJ",   "Adj(attr,stell,onverv)"),
          ("JJR",  "Adj(adv,vergr,onverv)"),
          ("JJS",  "Adj(attr,overtr,verv_neut)"),
          ("RP",   "Adv(deel_v)"),
          ("RB",   "Adv(gew,geen_func,stell,onverv)"),
          ("DT",   "Art(bep,zijd_of_mv,neut)"),
          ("CC",   "Conj(neven)"),
          ("CD",   "Num(hoofd,bep,zelfst,onverv)"),
          ("TO",   "Prep(voor_inf)"),
          ("IN",   "Prep(voor)"),
          ("PRP",  "Pron(onbep,neut,attr)"),
          ("PRP$", "Pron(bez,2,ev,neut,attr)"),
          (",",    "Punc(komma)"),
          ("(",    "Punc(haak_open)"),
          (")",    "Punc(haak_sluit)"),
          (".",    "Punc(punt)"),
          ("UH",   "Int"),
          ("SYM",  "Misc(symbool)")):
            self.assertEqual(nl.parser.wotan2penntreebank(wotan), penntreebank)
        print "pattern.nl.parser.wotan2penntreebank()"
        
    def test_find_lemmata(self):
        # Assert lemmata for nouns and verbs.
        v = nl.parser.find_lemmata([["katten", "NNS"], ["droegen", "VBD"], ["hoeden", "NNS"]])
        self.assertEqual(v, [
            ["katten", "NNS", "kat"], 
            ["droegen", "VBD", "dragen"], 
            ["hoeden", "NNS", "hoed"]])
        print "pattern.nl.parser.find_lemmata()"
    
    def test_parse(self):
        # Assert parsed output with Penn Treebank II tags (slash-formatted).
        # 1) "de zwarte kat" is a noun phrase, "op de mat" is a prepositional noun phrase.
        v = nl.parser.parse("De zwarte kat zat op de mat.")
        self.assertEqual(v,
            "De/DT/B-NP/O zwarte/JJ/I-NP/O kat/NN/I-NP/O " + \
            "zat/VBD/B-VP/O " + \
            "op/IN/B-PP/O de/DT/O/O mat/JJ/B-ADJP/O ././O/O"
        )
        # 2) "jaagt" and "vogels" lemmata are "jagen" and "vogel".
        v = nl.parser.parse("De zwarte kat jaagt op vogels.", lemmata=True)
        self.assertEqual(v,
            "De/DT/B-NP/O/de zwarte/JJ/I-NP/O/zwart kat/NN/I-NP/O/kat " + \
            "jaagt/VBZ/B-VP/O/jagen " + \
            "op/IN/B-PP/B-PNP/op vogels/NNS/B-NP/I-PNP/vogel ././O/O/."
        )
        print "pattern.nl.parser.parse()"

    def test_tag(self):
        # Assert [("zwarte", "JJ"), ("panters", "NNS")].
        v = nl.parser.tag("zwarte panters")
        self.assertEqual(v, [("zwarte", "JJ"), ("panters", "NNS")])
        print "pattern.nl.parser.tag()"
    
    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.nl.parser", "-s", "Leuke kat.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "Leuke/JJ/B-NP/O/O/leuk kat/NN/I-NP/O/O/kat ././O/O/O/.")
        print "python -m pattern.nl.parser"

#---------------------------------------------------------------------------------------------------

class TestSentiment(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_sentiment(self):
        # Assert < 0 for negative adjectives and > 0 for positive adjectives.
        self.assertTrue(nl.sentiment("geweldig")[0] > 0)
        self.assertTrue(nl.sentiment("verschrikkelijk")[0] < 0)
        # Assert the accuracy of the sentiment analysis.
        # Given are the scores for 3,000 book reviews.
        # The baseline should increase (not decrease) when the algorithm is modified.
        from pattern.db import Datasheet
        from pattern.metrics import test
        reviews = []
        for score, review in Datasheet.load(os.path.join("corpora", "bol.com-polarity.csv")):
            reviews.append((review, int(score) > 0))
        A, P, R, F = test(lambda review: nl.positive(review), reviews)
        self.assertTrue(A > 0.79)
        self.assertTrue(P > 0.77)
        self.assertTrue(R > 0.82)
        self.assertTrue(F > 0.79)
        print "pattern.nl.sentiment()"

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
