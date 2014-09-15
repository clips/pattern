# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
import subprocess

from pattern import de

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------

class TestInflection(unittest.TestCase):

    def setUp(self):
        pass
    
    def test_gender(self):
        # Assert der Hund => MASCULINE
        # Assert die Studentin => FEMININE
        # Assert das Auto => NEUTRAL
        self.assertEqual(de.gender("Hund"), de.MASCULINE)
        self.assertEqual(de.gender("Studentin"), de.FEMININE)
        self.assertEqual(de.gender("Auto"), de.NEUTRAL)
    
    def test_pluralize(self):
        # Assert the accuracy of the pluralization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for tag, sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-de-celex.csv")):
            if tag == "n":
                if de.pluralize(sg) == pl:
                    i +=1
                n += 1
        self.assertTrue(float(i) / n > 0.69)
        print("pattern.de.pluralize()")
        
    def test_singularize(self):
        # Assert the accuracy of the singularization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for tag, sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-de-celex.csv")):
            if tag == "n":
                if de.singularize(pl) == sg:
                    i +=1
                n += 1
        self.assertTrue(float(i) / n > 0.82)
        print("pattern.de.singularize()")

    def test_attributive(self):
        # Assert "groß" => "großer" (masculine, nominative), and others.
        for lemma, inflected, gender, role, article in (
          (u"groß", u"großer", de.MALE,    de.SUBJECT,  None),
          (u"groß", u"großen", de.MALE,    de.OBJECT,   None),
          (u"groß", u"großem", de.MALE,    de.INDIRECT, None),
          (u"groß", u"großen", de.MALE,    de.PROPERTY, None),
          (u"groß", u"große",  de.FEMALE,  de.SUBJECT,  None),
          (u"groß", u"große",  de.FEMALE,  de.OBJECT,   None),
          (u"groß", u"großer", de.FEMALE,  de.INDIRECT, None),
          (u"groß", u"großes", de.NEUTRAL, de.SUBJECT,  None),
          (u"groß", u"großes", de.NEUTRAL, de.OBJECT,   None),
          (u"groß", u"großen", de.MALE,    de.PROPERTY, "mein"),
          (u"groß", u"großen", de.FEMALE,  de.PROPERTY, "jeder"),
          (u"groß", u"großen", de.FEMALE,  de.PROPERTY, "mein"),
          (u"groß", u"großen", de.PLURAL,  de.INDIRECT, "jede"),
          (u"groß", u"großen", de.PLURAL,  de.PROPERTY, "jeder")):
            v = de.attributive(lemma, gender, role, article)
            self.assertEqual(v, inflected)
        print("pattern.de.attributive()")
        
    def test_predicative(self):
        # Assert the accuracy of the predicative algorithm ("großer" => "groß").
        from pattern.db import Datasheet
        i, n = 0, 0
        for tag, pred, attr in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-de-celex.csv")):
            if tag == "a":
                if de.predicative(attr) == pred:
                    i +=1
                n += 1
        self.assertTrue(float(i) / n > 0.98)
        print("pattern.de.predicative()")

    def test_find_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        # Note: the accuracy is higher (88%) when measured on CELEX word forms
        # (presumably because de.inflect.verbs has high percentage irregular verbs).
        i, n = 0, 0
        for v1, v2 in de.inflect.verbs.inflections.items():
            if de.inflect.verbs.find_lemma(v1) == v2: 
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.86)
        print("pattern.de.inflect.verbs.find_lemma()")
        
    def test_find_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in de.inflect.verbs.infinitives.items():
            lexeme2 = de.inflect.verbs.find_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == "":
                    continue
                if lexeme1[j] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.86)
        print("pattern.de.inflect.verbs.find_lexeme()")

    def test_conjugate(self):
        # Assert different tenses with different conjugations.
        for (v1, v2, tense) in (
          ("sein",  "sein",     de.INFINITIVE),
          ("sein",  "bin",     (de.PRESENT, 1, de.SINGULAR)),
          ("sein",  "bist",    (de.PRESENT, 2, de.SINGULAR)),
          ("sein",  "ist",     (de.PRESENT, 3, de.SINGULAR)),
          ("sein",  "sind",    (de.PRESENT, 1, de.PLURAL)),
          ("sein",  "seid",    (de.PRESENT, 2, de.PLURAL)),
          ("sein",  "sind",    (de.PRESENT, 3, de.PLURAL)),
          ("sein",  "seiend",  (de.PRESENT + de.PARTICIPLE)),
          ("sein",  "war",     (de.PAST, 1, de.SINGULAR)),
          ("sein",  "warst",   (de.PAST, 2, de.SINGULAR)),
          ("sein",  "war",     (de.PAST, 3, de.SINGULAR)),
          ("sein",  "waren",   (de.PAST, 1, de.PLURAL)),
          ("sein",  "wart",    (de.PAST, 2, de.PLURAL)),
          ("sein",  "waren",   (de.PAST, 3, de.PLURAL)),
          ("sein",  "gewesen", (de.PAST + de.PARTICIPLE)),
          ("sein",  "sei",     (de.PRESENT, 2, de.SINGULAR, de.IMPERATIVE)),
          ("sein",  "seien",   (de.PRESENT, 1, de.PLURAL, de.IMPERATIVE)),
          ("sein",  "seid",    (de.PRESENT, 2, de.PLURAL, de.IMPERATIVE)),
          ("sein", u"sei",     (de.PRESENT, 1, de.SINGULAR, de.SUBJUNCTIVE)),
          ("sein", u"seiest",  (de.PRESENT, 2, de.SINGULAR, de.SUBJUNCTIVE)),
          ("sein", u"sei",     (de.PRESENT, 3, de.SINGULAR, de.SUBJUNCTIVE)),
          ("sein", u"seien",   (de.PRESENT, 1, de.PLURAL, de.SUBJUNCTIVE)),
          ("sein", u"seiet",   (de.PRESENT, 2, de.PLURAL, de.SUBJUNCTIVE)),
          ("sein", u"seien",   (de.PRESENT, 3, de.PLURAL, de.SUBJUNCTIVE)),
          ("sein", u"wäre",    (de.PAST, 1, de.SINGULAR, de.SUBJUNCTIVE)),
          ("sein", u"wärest",  (de.PAST, 2, de.SINGULAR, de.SUBJUNCTIVE)),
          ("sein", u"wäre",    (de.PAST, 3, de.SINGULAR, de.SUBJUNCTIVE)),
          ("sein", u"wären",   (de.PAST, 1, de.PLURAL, de.SUBJUNCTIVE)),
          ("sein", u"wäret",   (de.PAST, 2, de.PLURAL, de.SUBJUNCTIVE)),
          ("sein", u"wären",   (de.PAST, 3, de.PLURAL, de.SUBJUNCTIVE))):
            self.assertEqual(de.conjugate(v1, tense), v2)
        print("pattern.de.conjugate()")

    def test_lexeme(self):
        # Assert all inflections of "sein".
        v = de.lexeme("sein")
        self.assertEqual(v, [
            "sein", "bin", "bist", "ist", "sind", "seid", "seiend", 
            "war", "warst", "waren", "wart", "gewesen", 
            "sei", "seien", "seiest", "seiet", 
            u"wäre", u"wärest", u"wären", u"wäret"
        ])
        print("pattern.de.inflect.lexeme()")

    def test_tenses(self):
        # Assert tense recognition.
        self.assertTrue((de.PRESENT, 3, de.SG) in de.tenses("ist"))
        self.assertTrue("2sg" in de.tenses("bist"))
        print("pattern.de.tenses()")

#---------------------------------------------------------------------------------------------------

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_find_lemmata(self):
        # Assert lemmata for nouns, adjectives and verbs.
        v = de.parser.find_lemmata([["Ich", "PRP"], ["sage", "VB"], [u"schöne", "JJ"], [u"Dinge", "NNS"]])
        self.assertEqual(v, [
            ["Ich", "PRP", "ich"], 
            ["sage", "VB", "sagen"], 
            [u"schöne", "JJ", u"schön"], 
            ["Dinge", "NNS", "ding"]])
        print("pattern.de.parser.find_lemmata()")
    
    def test_parse(self):
        # Assert parsed output with Penn Treebank II tags (slash-formatted).
        # 1) "der große Hund" is a noun phrase, "auf der Matte" is a prepositional noun phrase.
        v = de.parser.parse(u"Der große Hund sitzt auf der Matte.")
        self.assertEqual(v,
            u"Der/DT/B-NP/O große/JJ/I-NP/O Hund/NN/I-NP/O " + \
            u"sitzt/VB/B-VP/O " + \
            u"auf/IN/B-PP/B-PNP der/DT/B-NP/I-PNP Matte/NN/I-NP/I-PNP ././O/O"
        )
        # 2) "große" and "sitzt" lemmata are "groß" and "sitzen".
        # Note how articles are problematic ("der" can be male subject but also plural possessive).
        v = de.parser.parse(u"Der große Hund sitzt auf der Matte.", lemmata=True)
        self.assertEqual(v,
            u"Der/DT/B-NP/O/der große/JJ/I-NP/O/groß Hund/NN/I-NP/O/hund " + \
            u"sitzt/VB/B-VP/O/sitzen " + \
            u"auf/IN/B-PP/B-PNP/auf der/DT/B-NP/I-PNP/der Matte/NN/I-NP/I-PNP/matte ././O/O/."
        )
        # 3) Assert the accuracy of the German tagger.
        i, n = 0, 0
        for sentence in open(os.path.join(PATH, "corpora", "tagged-de-tiger.txt")).readlines():
            sentence = sentence.decode("utf-8").strip()
            s1 = [w.split("/") for w in sentence.split(" ")]
            s1 = [de.stts2penntreebank(w, pos) for w, pos in s1]
            s2 = [[w for w, pos in s1]]
            s2 = de.parse(s2, tokenize=False)
            s2 = [w.split("/") for w in s2.split(" ")]
            for j in range(len(s1)):
                if s1[j][1] == s2[j][1]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.844)
        print("pattern.de.parse()")

    def test_tag(self):
        # Assert [("der", "DT"), ("grosse", "JJ"), ("Hund", "NN")].
        v = de.tag("der grosse Hund")
        self.assertEqual(v, [("der", "DT"), ("grosse", "JJ"), ("Hund", "NN")])
        print("pattern.de.tag()")
    
    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.de", "-s", "Der grosse Hund.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "Der/DT/B-NP/O/O/der grosse/JJ/I-NP/O/O/gross Hund/NN/I-NP/O/O/hund ././O/O/O/.")
        print("python -m pattern.de")

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
