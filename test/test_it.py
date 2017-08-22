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
import subprocess

from pattern import it

from io import open

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------


class TestInflection(unittest.TestCase):

    def setUp(self):
        pass

    def test_article(self):
        # Assert definite and indefinite article inflection.
        for a, n, g in (
          ("il" , "giorno"      , it.M),
          ("l'" , "altro giorno", it.M),
          ("lo" , "zio"         , it.M),
          ("l'" , "amica"       , it.F),
          ("la" , "nouva amica" , it.F),
          ("i"  , "giapponesi"  , it.M + it.PL),
          ("gli", "italiani"    , it.M + it.PL),
          ("gli", "zii"         , it.M + it.PL),
          ("le" , "zie"         , it.F + it.PL)):
            v = it.article(n, "definite", gender=g)
            self.assertEqual(a, v)
        for a, n, g in (
          ("uno", "zio"  , it.M),
          ("una", "zia"  , it.F),
          ("un" , "amico", it.M),
          ("un'", "amica", it.F)):
            v = it.article(n, "indefinite", gender=g)
            self.assertEqual(a, v)
        v = it.referenced("amica", gender="f")
        self.assertEqual(v, "un'amica")
        print("pattern.it.article()")
        print("pattern.it.referenced()")

    def test_gender(self):
        # Assert the accuracy of the gender disambiguation algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for pos, sg, pl, mf in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-it-wiktionary.csv")):
            g = it.gender(sg)
            if mf in g and it.PLURAL not in g:
                i += 1
            g = it.gender(pl)
            if mf in g and it.PLURAL in g:
                i += 1
            n += 2
        self.assertTrue(float(i) / n > 0.92)
        print("pattern.it.gender()")

    def test_pluralize(self):
        # Assert the accuracy of the pluralization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for pos, sg, pl, mf in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-it-wiktionary.csv")):
            if it.pluralize(sg) == pl:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.93)
        print("pattern.it.pluralize()")

    def test_singularize(self):
        # Assert the accuracy of the singularization algorithm.
        from pattern.db import Datasheet
        i, n = 0, 0
        for pos, sg, pl, mf in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-it-wiktionary.csv")):
            if it.singularize(pl) == sg:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.84)
        print("pattern.it.singularize()")

    def test_predicative(self):
        # Assert the accuracy of the predicative algorithm ("cruciali" => "cruciale").

        from pattern.db import Datasheet
        i, n = 0, 0
        for pos, sg, pl, mf in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-it-wiktionary.csv")):
            if pos != "j":
                continue
            if it.predicative(pl) == sg:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.87)
        print("pattern.it.predicative()")

    def test_find_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        i, n = 0, 0
        r = 0
        for v1, v2 in it.inflect.verbs.inflections.items():
            if it.inflect.verbs.find_lemma(v1) == v2:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.81)
        print("pattern.it.inflect.verbs.find_lemma()")

    def test_find_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in it.inflect.verbs.infinitives.items():
            lexeme2 = it.inflect.verbs.find_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.89)
        print("pattern.it.inflect.verbs.find_lexeme()")

    def test_conjugate(self):
        # Assert different tenses with different conjugations.
        for (v1, v2, tense) in (
          ("essere", "essere",     it.INFINITIVE),
          ("essere", "sono",      (it.PRESENT, 1, it.SINGULAR)),
          ("essere", "sei",       (it.PRESENT, 2, it.SINGULAR)),
          ("essere", "è",         (it.PRESENT, 3, it.SINGULAR)),
          ("essere", "siamo",     (it.PRESENT, 1, it.PLURAL)),
          ("essere", "siete",     (it.PRESENT, 2, it.PLURAL)),
          ("essere", "sono",      (it.PRESENT, 3, it.PLURAL)),
          ("essere", "essendo",   (it.PRESENT + it.PARTICIPLE)),
          ("essere", "stato",     (it.PAST + it.PARTICIPLE)),
          ("essere", "ero",       (it.IMPERFECT, 1, it.SINGULAR)),
          ("essere", "eri",       (it.IMPERFECT, 2, it.SINGULAR)),
          ("essere", "era",       (it.IMPERFECT, 3, it.SINGULAR)),
          ("essere", "eravamo",   (it.IMPERFECT, 1, it.PLURAL)),
          ("essere", "eravate",   (it.IMPERFECT, 2, it.PLURAL)),
          ("essere", "erano",     (it.IMPERFECT, 3, it.PLURAL)),
          ("essere", "fui",       (it.PRETERITE, 1, it.SINGULAR)),
          ("essere", "fosti",     (it.PRETERITE, 2, it.SINGULAR)),
          ("essere", "fu",        (it.PRETERITE, 3, it.SINGULAR)),
          ("essere", "fummo",     (it.PRETERITE, 1, it.PLURAL)),
          ("essere", "foste",     (it.PRETERITE, 2, it.PLURAL)),
          ("essere", "furono",    (it.PRETERITE, 3, it.PLURAL)),
          ("essere", "sarei",     (it.CONDITIONAL, 1, it.SINGULAR)),
          ("essere", "saresti",   (it.CONDITIONAL, 2, it.SINGULAR)),
          ("essere", "sarebbe",   (it.CONDITIONAL, 3, it.SINGULAR)),
          ("essere", "saremmo",   (it.CONDITIONAL, 1, it.PLURAL)),
          ("essere", "sareste",   (it.CONDITIONAL, 2, it.PLURAL)),
          ("essere", "sarebbero", (it.CONDITIONAL, 3, it.PLURAL)),
          ("essere", "sarò",      (it.FUTURE, 1, it.SINGULAR)),
          ("essere", "sarai",     (it.FUTURE, 2, it.SINGULAR)),
          ("essere", "sarà",      (it.FUTURE, 3, it.SINGULAR)),
          ("essere", "saremo",    (it.FUTURE, 1, it.PLURAL)),
          ("essere", "sarete",    (it.FUTURE, 2, it.PLURAL)),
          ("essere", "saranno",   (it.FUTURE, 3, it.PLURAL)),
          ("essere", "sii",       (it.PRESENT, 2, it.SINGULAR, it.IMPERATIVE)),
          ("essere", "sia",       (it.PRESENT, 3, it.SINGULAR, it.IMPERATIVE)),
          ("essere", "siamo",     (it.PRESENT, 1, it.PLURAL, it.IMPERATIVE)),
          ("essere", "siate",     (it.PRESENT, 2, it.PLURAL, it.IMPERATIVE)),
          ("essere", "siano",     (it.PRESENT, 3, it.PLURAL, it.IMPERATIVE)),
          ("essere", "sia",       (it.PRESENT, 1, it.SINGULAR, it.SUBJUNCTIVE)),
          ("essere", "sia",       (it.PRESENT, 2, it.SINGULAR, it.SUBJUNCTIVE)),
          ("essere", "sia",       (it.PRESENT, 3, it.SINGULAR, it.SUBJUNCTIVE)),
          ("essere", "siamo",     (it.PRESENT, 1, it.PLURAL, it.SUBJUNCTIVE)),
          ("essere", "siate",     (it.PRESENT, 2, it.PLURAL, it.SUBJUNCTIVE)),
          ("essere", "siano",     (it.PRESENT, 3, it.PLURAL, it.SUBJUNCTIVE)),
          ("essere", "fossi",     (it.PAST, 1, it.SINGULAR, it.SUBJUNCTIVE)),
          ("essere", "fossi",     (it.PAST, 2, it.SINGULAR, it.SUBJUNCTIVE)),
          ("essere", "fosse",     (it.PAST, 3, it.SINGULAR, it.SUBJUNCTIVE)),
          ("essere", "fossimo",   (it.PAST, 1, it.PLURAL, it.SUBJUNCTIVE)),
          ("essere", "foste",     (it.PAST, 2, it.PLURAL, it.SUBJUNCTIVE)),
          ("essere", "fossero",   (it.PAST, 3, it.PLURAL, it.SUBJUNCTIVE))):
            self.assertEqual(it.conjugate(v1, tense), v2)
        print("pattern.it.conjugate()")

    def test_lexeme(self):
        # Assert all inflections of "essere".
        v = it.lexeme("essere")
        self.assertEqual(v, [
            'essere', 'sono', 'sei', 'è', 'siamo', 'siete', 'essendo',
            'fui', 'fosti', 'fu', 'fummo', 'foste', 'furono', 'stato',
            'ero', 'eri', 'era', 'eravamo', 'eravate', 'erano',
            'sarò', 'sarai', 'sarà', 'saremo', 'sarete', 'saranno',
            'sarei', 'saresti', 'sarebbe', 'saremmo', 'sareste', 'sarebbero',
            'sii', 'sia', 'siate', 'siano',
            'fossi', 'fosse', 'fossimo', 'fossero'
        ])
        print("pattern.it.inflect.lexeme()")

    def test_tenses(self):
        # Assert tense recognition.
        self.assertTrue((it.PRESENT, 3, it.SG) in it.tenses("è"))
        self.assertTrue("2sg" in it.tenses("sei"))
        print("pattern.it.tenses()")

#---------------------------------------------------------------------------------------------------


class TestParser(unittest.TestCase):

    def setUp(self):
        pass

    def test_find_lemmata(self):
        # Assert lemmata for nouns, adjectives, verbs and determiners.
        v = it.parser.find_lemmata([
            ["I", "DT"], ["gatti", "NNS"], ["neri", "JJ"],
            ["seduti", "VB"], ["sul", "IN"], ["tatami", "NN"]])
        self.assertEqual(v, [
            ["I", "DT", "il"],
            ["gatti", "NNS", "gatto"],
            ["neri", "JJ", "nero"],
            ["seduti", "VB", "sedutare"],
            ["sul", "IN", "sul"],
            ["tatami", "NN", "tatami"]])
        print("pattern.it.parser.find_lemmata()")

    def test_parse(self):
        # Assert parsed output with Penn Treebank II tags (slash-formatted).
        # "il gatto nero" is a noun phrase, "sulla stuoia" is a prepositional noun phrase.
        v = it.parser.parse("Il gatto nero seduto sulla stuoia.")
        self.assertEqual(v,
            "Il/DT/B-NP/O gatto/NN/I-NP/O nero/JJ/I-NP/O " +
            "seduto/VB/B-VP/O " + \
            "sulla/IN/B-PP/B-PNP stuoia/NN/B-NP/I-PNP ././O/O"
        )
        # Assert the accuracy of the Italian tagger.
        i, n = 0, 0
        for sentence in open(os.path.join(PATH, "corpora", "tagged-it-wacky.txt")).readlines():
            sentence = sentence.strip()
            s1 = [w.split("/") for w in sentence.split(" ")]
            s2 = [[w for w, pos in s1]]
            s2 = it.parse(s2, tokenize=False)
            s2 = [w.split("/") for w in s2.split(" ")]
            for j in range(len(s1)):
                t1 = s1[j][1]
                t2 = s2[j][1]
                # WaCKy test set tags plural nouns as "NN", pattern.it as "NNS".
                # Some punctuation marks are also tagged differently,
                # but these are not necessarily errors.
                if t1 == t2 or (t1 == "NN" and t2.startswith("NN")) or s1[j][0] in "\":;)-":
                    i += 1
                n += 1
        #print(float(i) / n)
        self.assertTrue(float(i) / n > 0.92)
        print("pattern.it.parser.parse()")

    def test_tag(self):
        # Assert [("il", "DT"), ("gatto", "NN"), ("nero", "JJ")].
        v = it.tag("il gatto nero")
        self.assertEqual(v, [("il", "DT"), ("gatto", "NN"), ("nero", "JJ")])
        print("pattern.it.tag()")

    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.it", "-s", "Il gatto nero.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read().decode('utf-8')
        v = v.strip()
        self.assertEqual(v, "Il/DT/B-NP/O/O/il gatto/NN/I-NP/O/O/gatto nero/JJ/I-NP/O/O/nero ././O/O/O/.")
        print("python -m pattern.it")

#---------------------------------------------------------------------------------------------------


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
