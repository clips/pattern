# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(".."))
import unittest
import subprocess

from pattern import de

try:
    PATH = os.path.dirname(os.path.abspath(__file__))
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
        for tag, sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "celex-wordforms-de.csv")):
            if tag == "n":
                if de.pluralize(sg) == pl:
                    i +=1
                n += 1
        self.assertTrue(float(i) / n > 0.69)
        print "pattern.de.pluralize()"
        
    def test_singularize(self):
        # Assert the accuracy of the singularization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for tag, sg, pl in Datasheet.load(os.path.join(PATH, "corpora", "celex-wordforms-de.csv")):
            if tag == "n":
                if de.singularize(pl) == sg:
                    i +=1
                n += 1
        self.assertTrue(float(i) / n > 0.81)
        print "pattern.de.singularize()"

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
        print "pattern.de.attributive()"
        
    def test_predicative(self):
        # Assert the accuracy of the predicative algorithm ("großer" => "groß").
        from pattern.db import Datasheet
        i, n = 0, 0
        for tag, pred, attr in Datasheet.load(os.path.join(PATH, "corpora", "celex-wordforms-de.csv")):
            if tag == "a":
                if de.predicative(attr) == pred:
                    i +=1
                n += 1
        self.assertTrue(float(i) / n > 0.98)
        print "pattern.de.predicative()"

    def test_parse_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        # Note: the accuracy is higher (88%) when measured on CELEX word forms
        # (presumably because de.inflect.VERBS has high percentage irregular verbs).
        i, n = 0, 0
        for v in de.inflect.VERBS.infinitives:
            for tense in de.inflect.VERBS.TENSES:
                if de.conjugate(v, tense, parse=False) is None:
                    continue
                if de.inflect._parse_lemma(de.conjugate(v, tense)) == v: 
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.85)
        print "pattern.de.inflect._parse_lemma()"
        
    def test_parse_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in de.inflect.VERBS.infinitives.items():
            lexeme2 = de.inflect._parse_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == "":
                    continue
                if lexeme1[j] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.86)
        print "pattern.de.inflect._parse_lexeme()"

    def test_conjugate(self):
        # Assert different tenses with different conjugations.
        for (v1, v2, tense) in (
          ("sein",  "sein",     de.INFINITIVE),
          ("sein",  "bin",      de.PRESENT_1ST_PERSON_SINGULAR),
          ("sein",  "bist",     de.PRESENT_2ND_PERSON_SINGULAR),
          ("sein",  "ist",      de.PRESENT_3RD_PERSON_SINGULAR),
          ("sein",  "sind",     de.PRESENT_1ST_PERSON_PLURAL),
          ("sein",  "seid",     de.PRESENT_2ND_PERSON_PLURAL),
          ("sein",  "sind",     de.PRESENT_3RD_PERSON_PLURAL),
          ("sein",  "seiend",   de.PRESENT_PARTICIPLE),
          ("sein",  "war",      de.PAST_1ST_PERSON_SINGULAR),
          ("sein",  "warst",    de.PAST_2ND_PERSON_SINGULAR),
          ("sein",  "war",      de.PAST_3RD_PERSON_SINGULAR),
          ("sein",  "waren",    de.PAST_1ST_PERSON_PLURAL),
          ("sein",  "wart",     de.PAST_2ND_PERSON_PLURAL),
          ("sein",  "waren",    de.PAST_3RD_PERSON_PLURAL),
          ("sein",  "gewesen",  de.PAST_PARTICIPLE),
          ("sein",  "sei",      de.IMPERATIVE_2ND_PERSON_SINGULAR),
          ("sein",  "seien",    de.IMPERATIVE_1ST_PERSON_PLURAL),
          ("sein",  "seid",     de.IMPERATIVE_2ND_PERSON_PLURAL),
          ("sein",  "seien",    de.IMPERATIVE_3RD_PERSON_PLURAL),
          ("sein", u"sei",      de.PRESENT_SUBJUNCTIVE_1ST_PERSON_SINGULAR),
          ("sein", u"seiest",   de.PRESENT_SUBJUNCTIVE_2ND_PERSON_SINGULAR),
          ("sein", u"sei",      de.PRESENT_SUBJUNCTIVE_3RD_PERSON_SINGULAR),
          ("sein", u"seien",    de.PRESENT_SUBJUNCTIVE_1ST_PERSON_PLURAL),
          ("sein", u"seiet",    de.PRESENT_SUBJUNCTIVE_2ND_PERSON_PLURAL),
          ("sein", u"seien",    de.PRESENT_SUBJUNCTIVE_3RD_PERSON_PLURAL),
          ("sein", u"wäre",     de.PAST_SUBJUNCTIVE_1ST_PERSON_SINGULAR),
          ("sein", u"wärest",   de.PAST_SUBJUNCTIVE_2ND_PERSON_SINGULAR),
          ("sein", u"wäre",     de.PAST_SUBJUNCTIVE_3RD_PERSON_SINGULAR),
          ("sein", u"wären",    de.PAST_SUBJUNCTIVE_1ST_PERSON_PLURAL),
          ("sein", u"wäret",    de.PAST_SUBJUNCTIVE_2ND_PERSON_PLURAL),
          ("sein", u"wären",    de.PAST_SUBJUNCTIVE_3RD_PERSON_PLURAL)):
            self.assertEqual(de.conjugate(v1, tense), v2)
        print "pattern.de.conjugate()"

    def test_lexeme(self):
        # Assert all inflections of "sein".
        v = de.lexeme("sein")
        self.assertEqual(v, [
            "sein", "bin", "bist", "ist", "sind", "seid", "seiend", 
            "war", "warst", "waren", "wart", "gewesen", 
            "sei", "seien", "seiest", "seiet", 
            u"wäre", u"wärest", u"wären", u"wäret"
        ])
        print "pattern.de.inflect.lexeme()"

    def test_tenses(self):
        # Assert tense of "is".
        self.assertTrue(de.PRESENT_3RD_PERSON_SINGULAR in de.tenses("ist"))
        self.assertTrue("2sg" in de.tenses("bist"))
        print "pattern.de.tenses()"

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
            ["Dinge", "NNS", "Ding"]])
        print "pattern.de.parser.find_lemmata()"
    
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
        print "pattern.de.parser.parse()"

    def test_tag(self):
        # Assert [("der", "DT"), ("grosse", "JJ"), ("Hund", "NN")].
        v = de.parser.tag("der grosse Hund")
        self.assertEqual(v, [("der", "DT"), ("grosse", "JJ"), ("Hund", "NN")])
        print "pattern.de.parser.tag()"
    
    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.de.parser", "-s", "Der grosse Hund.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "Der/DT/B-NP/O/O/der grosse/JJ/I-NP/O/O/gross Hund/NN/I-NP/O/O/hund ././O/O/O/.")
        print "python -m pattern.de.parser"

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
