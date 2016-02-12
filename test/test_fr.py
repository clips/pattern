# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
import subprocess

from pattern import fr

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------

class TestInflection(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_predicative(self):
        # Assert the accuracy of the predicative algorithm ("belles" => "beau").
        from pattern.db import Datasheet
        i, n = 0, 0
        for pred, attr, tag in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-fr-lexique.csv")):
            if tag == "a":
                if fr.predicative(attr) == pred:
                    i +=1
                n += 1
        self.assertTrue(float(i) / n > 0.95)
        print("pattern.fr.predicative()")

    def test_find_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        i, n = 0, 0
        for v1, v2 in fr.inflect.verbs.inflections.items():
            if fr.inflect.verbs.find_lemma(v1) == v2: 
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.80)
        print("pattern.fr.inflect.verbs.find_lemma()")
        
    def test_find_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in fr.inflect.verbs.infinitives.items():
            lexeme2 = fr.inflect.verbs.find_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.85)
        print("pattern.fr.inflect.verbs.find_lexeme()")

    def test_conjugate(self):
        # Assert different tenses with different conjugations.
        for (v1, v2, tense) in (
          (u"être", u"être",      fr.INFINITIVE),
          (u"être", u"suis",     (fr.PRESENT, 1, fr.SINGULAR)),
          (u"être", u"es",       (fr.PRESENT, 2, fr.SINGULAR)),
          (u"être", u"est",      (fr.PRESENT, 3, fr.SINGULAR)),
          (u"être", u"sommes",   (fr.PRESENT, 1, fr.PLURAL)),
          (u"être", u"êtes",     (fr.PRESENT, 2, fr.PLURAL)),
          (u"être", u"sont",     (fr.PRESENT, 3, fr.PLURAL)),
          (u"être", u"étant",    (fr.PRESENT + fr.PARTICIPLE)),
          (u"être", u"été",      (fr.PAST + fr.PARTICIPLE)),
          (u"être", u"étais",    (fr.IMPERFECT, 1, fr.SINGULAR)),
          (u"être", u"étais",    (fr.IMPERFECT, 2, fr.SINGULAR)),
          (u"être", u"était",    (fr.IMPERFECT, 3, fr.SINGULAR)),
          (u"être", u"étions",   (fr.IMPERFECT, 1, fr.PLURAL)),
          (u"être", u"étiez",    (fr.IMPERFECT, 2, fr.PLURAL)),
          (u"être", u"étaient",  (fr.IMPERFECT, 3, fr.PLURAL)),
          (u"être", u"fus",      (fr.PRETERITE, 1, fr.SINGULAR)),
          (u"être", u"fus",      (fr.PRETERITE, 2, fr.SINGULAR)),
          (u"être", u"fut",      (fr.PRETERITE, 3, fr.SINGULAR)),
          (u"être", u"fûmes",    (fr.PRETERITE, 1, fr.PLURAL)),
          (u"être", u"fûtes",    (fr.PRETERITE, 2, fr.PLURAL)),
          (u"être", u"furent",   (fr.PRETERITE, 3, fr.PLURAL)),
          (u"être", u"serais",   (fr.CONDITIONAL, 1, fr.SINGULAR)),
          (u"être", u"serais",   (fr.CONDITIONAL, 2, fr.SINGULAR)),
          (u"être", u"serait",   (fr.CONDITIONAL, 3, fr.SINGULAR)),
          (u"être", u"serions",  (fr.CONDITIONAL, 1, fr.PLURAL)),
          (u"être", u"seriez",   (fr.CONDITIONAL, 2, fr.PLURAL)),
          (u"être", u"seraient", (fr.CONDITIONAL, 3, fr.PLURAL)),
          (u"être", u"serai",    (fr.FUTURE, 1, fr.SINGULAR)),
          (u"être", u"seras",    (fr.FUTURE, 2, fr.SINGULAR)),
          (u"être", u"sera",     (fr.FUTURE, 3, fr.SINGULAR)),
          (u"être", u"serons",   (fr.FUTURE, 1, fr.PLURAL)),
          (u"être", u"serez",    (fr.FUTURE, 2, fr.PLURAL)),
          (u"être", u"seront",   (fr.FUTURE, 3, fr.PLURAL)),
          (u"être", u"sois",     (fr.PRESENT, 2, fr.SINGULAR, fr.IMPERATIVE)),
          (u"être", u"soyons",   (fr.PRESENT, 1, fr.PLURAL, fr.IMPERATIVE)),
          (u"être", u"soyez",    (fr.PRESENT, 2, fr.PLURAL, fr.IMPERATIVE)),
          (u"être", u"sois",     (fr.PRESENT, 1, fr.SINGULAR, fr.SUBJUNCTIVE)),
          (u"être", u"sois",     (fr.PRESENT, 2, fr.SINGULAR, fr.SUBJUNCTIVE)),
          (u"être", u"soit",     (fr.PRESENT, 3, fr.SINGULAR, fr.SUBJUNCTIVE)),
          (u"être", u"soyons",   (fr.PRESENT, 1, fr.PLURAL, fr.SUBJUNCTIVE)),
          (u"être", u"soyez",    (fr.PRESENT, 2, fr.PLURAL, fr.SUBJUNCTIVE)),
          (u"être", u"soient",   (fr.PRESENT, 3, fr.PLURAL, fr.SUBJUNCTIVE)),
          (u"être", u"fusse",    (fr.PAST, 1, fr.SINGULAR, fr.SUBJUNCTIVE)),
          (u"être", u"fusses",   (fr.PAST, 2, fr.SINGULAR, fr.SUBJUNCTIVE)),
          (u"être", u"fût",      (fr.PAST, 3, fr.SINGULAR, fr.SUBJUNCTIVE)),
          (u"être", u"fussions", (fr.PAST, 1, fr.PLURAL, fr.SUBJUNCTIVE)),
          (u"être", u"fussiez",  (fr.PAST, 2, fr.PLURAL, fr.SUBJUNCTIVE)),
          (u"être", u"fussent",  (fr.PAST, 3, fr.PLURAL, fr.SUBJUNCTIVE))):
            self.assertEqual(fr.conjugate(v1, tense), v2)
        print("pattern.fr.conjugate()")

    def test_lexeme(self):
        # Assert all inflections of "être".
        v = fr.lexeme(u"être")
        self.assertEqual(v, [
            u"être", u"suis", u"es", u"est", u"sommes", u"êtes", u"sont", u"étant", u"été", 
            u"fus", u"fut", u"fûmes", u"fûtes", u"furent", 
            u"étais", u"était", u"étions", u"étiez", u"étaient", 
            u"serai", u"seras", u"sera", u"serons", u"serez", u"seront", 
            u"serais", u"serait", u"serions", u"seriez", u"seraient", 
            u"sois", u"soyons", u"soyez", u"soit", u"soient", 
            u"fusse", u"fusses", u"fût", u"fussions", u"fussiez", u"fussent"
        ])
        print("pattern.fr.inflect.lexeme()")

    def test_tenses(self):
        # Assert tense recognition.
        self.assertTrue((fr.PRESENT, 3, fr.SG) in fr.tenses("est"))
        self.assertTrue("2sg" in fr.tenses("es"))
        print("pattern.fr.tenses()")

#---------------------------------------------------------------------------------------------------

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_find_prepositions(self):
        v = fr.parser.parse("Parce que c'est comme ça.")

    def test_find_lemmata(self):
        # Assert lemmata for nouns, adjectives, verbs and determiners.
        v = fr.parser.find_lemmata([
            ["Les", "DT"], ["chats", "NNS"], ["noirs", "JJ"], ["s'", "PRP"], [u"étaient", "VB"], ["assis", "VB"],
            ["sur", "IN"], ["le", "DT"], ["tapis", "NN"]])
        self.assertEqual(v, [
            ["Les", "DT", "le"], 
            ["chats", "NNS", "chat"], 
            ["noirs", "JJ", "noir"], 
            ["s'", "PRP", "se"], 
            [u"étaient", "VB", u"être"],
            ["assis", "VB", "asseoir"],
            ["sur", "IN", "sur"], 
            ["le", "DT", "le"], 
            ["tapis", "NN", "tapis"]])
        print("pattern.fr.parser.find_lemmata()")

    def test_parse(self):
        # Assert parsed output with Penn Treebank II tags (slash-formatted).
        # "le chat noir" is a noun phrase, "sur le tapis" is a prepositional noun phrase.
        v = fr.parser.parse(u"Le chat noir s'était assis sur le tapis.")
        self.assertEqual(v,
            u"Le/DT/B-NP/O chat/NN/I-NP/O noir/JJ/I-NP/O " + \
            u"s'/PRP/B-NP/O était/VB/B-VP/O assis/VBN/I-VP/O " + \
            u"sur/IN/B-PP/B-PNP le/DT/B-NP/I-PNP tapis/NN/I-NP/I-PNP ././O/O"
        )
        # Assert the accuracy of the French tagger.
        f = fr.penntreebank2universal
        i, n = 0, 0
        for sentence in open(os.path.join(PATH, "corpora", "tagged-fr-wikinews.txt")).readlines():
            sentence = sentence.decode("utf-8").strip()
            s1 = [w.split("/") for w in sentence.split(" ")]
            s2 = [[w for w, pos in s1]]
            s2 = fr.parse(s2, tokenize=False)
            s2 = [w.split("/") for w in s2.split(" ")]
            for j in range(len(s1)):
                if f(*s1[j][:2])[1] == f(*s2[j][:2])[1]:
                    i += 1
                n += 1
        #print(float(i) / n)
        self.assertTrue(float(i) / n > 0.85)
        print("pattern.fr.parser.parse()")

    def test_tag(self):
        # Assert [("le", "DT"), ("chat", "NN"), ("noir", "JJ")].
        v = fr.tag("le chat noir")
        self.assertEqual(v, [("le", "DT"), ("chat", "NN"), ("noir", "JJ")])
        print("pattern.fr.tag()")

    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.fr", "-s", u"Le chat noir.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "Le/DT/B-NP/O/O/le chat/NN/I-NP/O/O/chat noir/JJ/I-NP/O/O/noir ././O/O/O/.")
        print("python -m pattern.fr")

#---------------------------------------------------------------------------------------------------

class TestSentiment(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_sentiment(self):
        # Assert < 0 for negative adjectives and > 0 for positive adjectives.
        self.assertTrue(fr.sentiment("fabuleux")[0] > 0)
        self.assertTrue(fr.sentiment("terrible")[0] < 0)
        # Assert the accuracy of the sentiment analysis.
        # Given are the scores for 1,500 book reviews.
        # The baseline should increase (not decrease) when the algorithm is modified.
        from pattern.db import Datasheet
        from pattern.metrics import test
        reviews = []
        for review, score in Datasheet.load(os.path.join(PATH, "corpora", "polarity-fr-amazon.csv")):
            reviews.append((review, int(score) > 0))
        A, P, R, F = test(lambda review: fr.positive(review), reviews)
        #print(A, P, R, F)
        self.assertTrue(A > 0.751)
        self.assertTrue(P > 0.765)
        self.assertTrue(R > 0.725)
        self.assertTrue(F > 0.744)
        print("pattern.fr.sentiment()")
        
    def test_tokenizer(self):
        # Assert that french sentiment() uses French tokenizer. ("t'aime" => "t' aime").
        v1 = fr.sentiment("je t'aime")
        v2 = fr.sentiment("je ne t'aime pas")
        self.assertTrue(v1[0] > 0)
        self.assertTrue(v2[0] < 0)
        self.assertTrue(v1.assessments[0][0] == ["aime"])
        self.assertTrue(v2.assessments[0][0] == ["ne", "aime"])

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
