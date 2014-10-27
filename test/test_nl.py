# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
import subprocess

from pattern import nl

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

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
        for pred, attr, sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-nl-celex.csv")):
            if nl.pluralize(sg) == pl:
                i +=1
            n += 1
        self.assertTrue(float(i) / n > 0.74)
        print("pattern.nl.pluralize()")
        
    def test_singularize(self):
        # Assert the accuracy of the singularization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-nl-celex.csv")):
            if nl.singularize(pl) == sg:
                i +=1
            n += 1
        self.assertTrue(float(i) / n > 0.88)
        print("pattern.nl.singularize()")

    def test_attributive(self):
        # Assert the accuracy of the attributive algorithm ("fel" => "felle").
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-nl-celex.csv")):
            if nl.attributive(pred) == attr:
                i +=1
            n += 1
        self.assertTrue(float(i) / n > 0.96)
        print("pattern.nl.attributive()")
        
    def test_predicative(self):
        # Assert the accuracy of the predicative algorithm ("felle" => "fel").
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-nl-celex.csv")):
            if nl.predicative(attr) == pred:
                i +=1
            n += 1
        self.assertTrue(float(i) / n > 0.96)
        print("pattern.nl.predicative()")

    def test_find_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        # Note: the accuracy is higher (90%) when measured on CELEX word forms
        # (presumably because nl.inflect.verbs has high percentage irregular verbs).
        i, n = 0, 0
        for v1, v2 in nl.inflect.verbs.inflections.items():
            if nl.inflect.verbs.find_lemma(v1) == v2: 
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.83)
        print("pattern.nl.inflect.verbs.find_lemma()")
        
    def test_find_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in nl.inflect.verbs.infinitives.items():
            lexeme2 = nl.inflect.verbs.find_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == lexeme2[j] or \
                   lexeme1[j] == "" and \
                   lexeme1[j > 5 and 10 or 0] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.79)
        print("pattern.nl.inflect.verbs.find_lexeme()")

    def test_conjugate(self):
        # Assert different tenses with different conjugations.
        for (v1, v2, tense) in (
          ("zijn",  "zijn",     nl.INFINITIVE),
          ("zijn",  "ben",     (nl.PRESENT, 1, nl.SINGULAR)),
          ("zijn",  "bent",    (nl.PRESENT, 2, nl.SINGULAR)),
          ("zijn",  "is",      (nl.PRESENT, 3, nl.SINGULAR)),
          ("zijn",  "zijn",    (nl.PRESENT, 0, nl.PLURAL)),
          ("zijn",  "zijnd",   (nl.PRESENT + nl.PARTICIPLE,)),
          ("zijn",  "was",     (nl.PAST, 1, nl.SINGULAR)),
          ("zijn",  "was",     (nl.PAST, 2, nl.SINGULAR)),
          ("zijn",  "was",     (nl.PAST, 3, nl.SINGULAR)),
          ("zijn",  "waren",   (nl.PAST, 0, nl.PLURAL)),
          ("zijn",  "was",     (nl.PAST, 0, None)),
          ("zijn",  "geweest", (nl.PAST + nl.PARTICIPLE,)),
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
        print("pattern.nl.conjugate()")

    def test_lexeme(self):
        # Assert all inflections of "zijn".
        v = nl.lexeme("zijn")
        self.assertEqual(v, [
            "zijn", "ben", "bent", "is", "zijnd", "waren", "was", "geweest"
        ])
        print("pattern.nl.inflect.lexeme()")

    def test_tenses(self):
        # Assert tense recognition.
        self.assertTrue((nl.PRESENT, 3, "sg") in nl.tenses("is"))
        self.assertTrue("3sg" in nl.tenses("is"))
        print("pattern.nl.tenses()")

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
            self.assertEqual(nl.wotan2penntreebank("", wotan)[1], penntreebank)
        print("pattern.nl.wotan2penntreebank()")
        
    def test_find_lemmata(self):
        # Assert lemmata for nouns and verbs.
        v = nl.parser.find_lemmata([["katten", "NNS"], ["droegen", "VBD"], ["hoeden", "NNS"]])
        self.assertEqual(v, [
            ["katten", "NNS", "kat"], 
            ["droegen", "VBD", "dragen"], 
            ["hoeden", "NNS", "hoed"]])
        print("pattern.nl.parser.find_lemmata()")
    
    def test_parse(self):
        # Assert parsed output with Penn Treebank II tags (slash-formatted).
        # 1) "de zwarte kat" is a noun phrase, "op de mat" is a prepositional noun phrase.
        v = nl.parser.parse("De zwarte kat zat op de mat.")
        self.assertEqual(v,
            "De/DT/B-NP/O zwarte/JJ/I-NP/O kat/NN/I-NP/O " + \
            "zat/VBD/B-VP/O " + \
            "op/IN/B-PP/B-PNP de/DT/B-NP/I-PNP mat/NN/I-NP/I-PNP ././O/O"
        )
        # 2) "jaagt" and "vogels" lemmata are "jagen" and "vogel".
        v = nl.parser.parse("De zwarte kat jaagt op vogels.", lemmata=True)
        self.assertEqual(v,
            "De/DT/B-NP/O/de zwarte/JJ/I-NP/O/zwart kat/NN/I-NP/O/kat " + \
            "jaagt/VBZ/B-VP/O/jagen " + \
            "op/IN/B-PP/B-PNP/op vogels/NNS/B-NP/I-PNP/vogel ././O/O/."
        )
        # Assert the accuracy of the Dutch tagger.
        i, n = 0, 0
        for sentence in open(os.path.join(PATH, "corpora", "tagged-nl-twnc.txt")).readlines():
            sentence = sentence.decode("utf-8").strip()
            s1 = [w.split("/") for w in sentence.split(" ")]
            s1 = [nl.wotan2penntreebank(w, tag) for w, tag in s1]
            s2 = [[w for w, pos in s1]]
            s2 = nl.parse(s2, tokenize=False)
            s2 = [w.split("/") for w in s2.split(" ")]
            for j in range(len(s1)):
                if s1[j][1] == s2[j][1]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.90)
        print("pattern.nl.parser.parse()")

    def test_tag(self):
        # Assert [("zwarte", "JJ"), ("panters", "NNS")].
        v = nl.tag("zwarte panters")
        self.assertEqual(v, [("zwarte", "JJ"), ("panters", "NNS")])
        print("pattern.nl.tag()")
    
    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.nl", "-s", "Leuke kat.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "Leuke/JJ/B-NP/O/O/leuk kat/NN/I-NP/O/O/kat ././O/O/O/.")
        print("python -m pattern.nl")

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
        for score, review in Datasheet.load(os.path.join(PATH, "corpora", "polarity-nl-bol.com.csv")):
            reviews.append((review, int(score) > 0))
        A, P, R, F = test(lambda review: nl.positive(review), reviews)
        #print(A, P, R, F)
        self.assertTrue(A > 0.808)
        self.assertTrue(P > 0.780)
        self.assertTrue(R > 0.860)
        self.assertTrue(F > 0.818)
        print("pattern.nl.sentiment()")

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
