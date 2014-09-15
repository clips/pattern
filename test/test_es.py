# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
import subprocess

from pattern import es

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------

class TestInflection(unittest.TestCase):

    def setUp(self):
        pass
    
    def test_pluralize(self):
        # Assert the accuracy of the pluralization algorithm.
        from pattern.db import Datasheet
        test = {}
        for w, lemma, tag, f in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-es-davies.csv")):
            if tag == "n": test.setdefault(lemma, []).append(w)
        i, n = 0, 0
        for sg, pl in test.items():
            pl = sorted(pl, key=len, reverse=True)[0]
            if es.pluralize(sg) == pl:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.77)
        print("pattern.es.pluralize()")
        
    def test_singularize(self):
        # Assert the accuracy of the singularization algorithm.
        from pattern.db import Datasheet
        test = {}
        for w, lemma, tag, f in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-es-davies.csv")):
            if tag == "n": test.setdefault(lemma, []).append(w)
        i, n = 0, 0
        for sg, pl in test.items():
            pl = sorted(pl, key=len, reverse=True)[0]
            if es.singularize(pl) == sg:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.93)
        print("pattern.es.singularize()")

    def test_attributive(self):
        # Assert "alto" => "altos" (masculine, plural), and others.
        for lemma, inflected, gender in (
          (u"alto",  u"alto",   es.MALE   + es.SINGULAR),
          (u"alto",  u"altos",  es.MALE   + es.PLURAL),
          (u"alto",  u"alta",   es.FEMALE + es.SINGULAR),
          (u"alto",  u"altas",  es.FEMALE + es.PLURAL),
          (u"verde", u"verdes", es.MALE   + es.PLURAL),
          (u"verde", u"verdes", es.FEMALE + es.PLURAL)):
            v = es.attributive(lemma, gender)
            self.assertEqual(v, inflected)
        print("pattern.es.attributive()")
        
    def test_predicative(self):
        # Assert the accuracy of the predicative algorithm ("horribles" => "horrible").
        from pattern.db import Datasheet
        test = {}
        for w, lemma, tag, f in Datasheet.load(os.path.join(PATH, "corpora", "wordforms-es-davies.csv")):
            if tag == "j": test.setdefault(lemma, []).append(w)
        i, n = 0, 0
        for pred, attr in test.items():
            attr = sorted(attr, key=len, reverse=True)[0]
            if es.predicative(attr) == pred:
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.92)
        print("pattern.es.predicative()")

    def test_find_lemma(self):
        # Assert the accuracy of the verb lemmatization algorithm.
        i, n = 0, 0
        for v1, v2 in es.inflect.verbs.inflections.items():
            if es.inflect.verbs.find_lemma(v1) == v2: 
                i += 1
            n += 1
        self.assertTrue(float(i) / n > 0.80)
        print("pattern.es.inflect.verbs.find_lemma()")
        
    def test_find_lexeme(self):
        # Assert the accuracy of the verb conjugation algorithm.
        i, n = 0, 0
        for v, lexeme1 in es.inflect.verbs.infinitives.items():
            lexeme2 = es.inflect.verbs.find_lexeme(v)
            for j in range(len(lexeme2)):
                if lexeme1[j] == lexeme2[j]:
                    i += 1
                n += 1
        self.assertTrue(float(i) / n > 0.85)
        print("pattern.es.inflect.verbs.find_lexeme()")

    def test_conjugate(self):
        # Assert different tenses with different conjugations.
        for (v1, v2, tense) in (
          ("ser", u"ser",        es.INFINITIVE),
          ("ser", u"soy",       (es.PRESENT, 1, es.SINGULAR)),
          ("ser", u"eres",      (es.PRESENT, 2, es.SINGULAR)),
          ("ser", u"es",        (es.PRESENT, 3, es.SINGULAR)),
          ("ser", u"somos",     (es.PRESENT, 1, es.PLURAL)),
          ("ser", u"sois",      (es.PRESENT, 2, es.PLURAL)),
          ("ser", u"son",       (es.PRESENT, 3, es.PLURAL)),
          ("ser", u"siendo",    (es.PRESENT + es.PARTICIPLE)),
          ("ser", u"sido",      (es.PAST + es.PARTICIPLE)),
          ("ser", u"era",       (es.IMPERFECT, 1, es.SINGULAR)),
          ("ser", u"eras",      (es.IMPERFECT, 2, es.SINGULAR)),
          ("ser", u"era",       (es.IMPERFECT, 3, es.SINGULAR)),
          ("ser", u"éramos",    (es.IMPERFECT, 1, es.PLURAL)),
          ("ser", u"erais",     (es.IMPERFECT, 2, es.PLURAL)),
          ("ser", u"eran",      (es.IMPERFECT, 3, es.PLURAL)),
          ("ser", u"fui",       (es.PRETERITE, 1, es.SINGULAR)),
          ("ser", u"fuiste",    (es.PRETERITE, 2, es.SINGULAR)),
          ("ser", u"fue",       (es.PRETERITE, 3, es.SINGULAR)),
          ("ser", u"fuimos",    (es.PRETERITE, 1, es.PLURAL)),
          ("ser", u"fuisteis",  (es.PRETERITE, 2, es.PLURAL)),
          ("ser", u"fueron",    (es.PRETERITE, 3, es.PLURAL)),
          ("ser", u"sería",     (es.CONDITIONAL, 1, es.SINGULAR)),
          ("ser", u"serías",    (es.CONDITIONAL, 2, es.SINGULAR)),
          ("ser", u"sería",     (es.CONDITIONAL, 3, es.SINGULAR)),
          ("ser", u"seríamos",  (es.CONDITIONAL, 1, es.PLURAL)),
          ("ser", u"seríais",   (es.CONDITIONAL, 2, es.PLURAL)),
          ("ser", u"serían",    (es.CONDITIONAL, 3, es.PLURAL)),
          ("ser", u"seré",      (es.FUTURE, 1, es.SINGULAR)),
          ("ser", u"serás",     (es.FUTURE, 2, es.SINGULAR)),
          ("ser", u"será",      (es.FUTURE, 3, es.SINGULAR)),
          ("ser", u"seremos",   (es.FUTURE, 1, es.PLURAL)),
          ("ser", u"seréis",    (es.FUTURE, 2, es.PLURAL)),
          ("ser", u"serán",     (es.FUTURE, 3, es.PLURAL)),
          ("ser", u"sé",        (es.PRESENT, 2, es.SINGULAR, es.IMPERATIVE)),
          ("ser", u"sed",       (es.PRESENT, 2, es.PLURAL, es.IMPERATIVE)),
          ("ser",  u"sea",      (es.PRESENT, 1, es.SINGULAR, es.SUBJUNCTIVE)),
          ("ser",  u"seas",     (es.PRESENT, 2, es.SINGULAR, es.SUBJUNCTIVE)),
          ("ser",  u"sea",      (es.PRESENT, 3, es.SINGULAR, es.SUBJUNCTIVE)),
          ("ser",  u"seamos",   (es.PRESENT, 1, es.PLURAL, es.SUBJUNCTIVE)),
          ("ser",  u"seáis",    (es.PRESENT, 2, es.PLURAL, es.SUBJUNCTIVE)),
          ("ser",  u"sean",     (es.PRESENT, 3, es.PLURAL, es.SUBJUNCTIVE)),
          ("ser",  u"fuera",    (es.PAST, 1, es.SINGULAR, es.SUBJUNCTIVE)),
          ("ser",  u"fueras",   (es.PAST, 2, es.SINGULAR, es.SUBJUNCTIVE)),
          ("ser",  u"fuera",    (es.PAST, 3, es.SINGULAR, es.SUBJUNCTIVE)),
          ("ser",  u"fuéramos", (es.PAST, 1, es.PLURAL, es.SUBJUNCTIVE)),
          ("ser",  u"fuerais",  (es.PAST, 2, es.PLURAL, es.SUBJUNCTIVE)),
          ("ser",  u"fueran",   (es.PAST, 3, es.PLURAL, es.SUBJUNCTIVE))):
            self.assertEqual(es.conjugate(v1, tense), v2)
        print("pattern.es.conjugate()")

    def test_lexeme(self):
        # Assert all inflections of "ser".
        v = es.lexeme("ser")
        self.assertEqual(v, [
            u'ser', u'soy', u'eres', u'es', u'somos', u'sois', u'son', u'siendo', 
            u'fui', u'fuiste', u'fue', u'fuimos', u'fuisteis', u'fueron', u'sido', 
            u'era', u'eras', u'éramos', u'erais', u'eran', 
            u'seré', u'serás', u'será', u'seremos', u'seréis', u'serán', 
            u'sería', u'serías', u'seríamos', u'seríais', u'serían', 
            u'sé', u'sed', 
            u'sea', u'seas', u'seamos', u'seáis', u'sean', 
            u'fuera', u'fueras', u'fuéramos', u'fuerais', u'fueran'
        ])
        print("pattern.es.inflect.lexeme()")

    def test_tenses(self):
        # Assert tense recognition.
        self.assertTrue((es.PRESENT, 3, es.SG) in es.tenses("es"))
        self.assertTrue("2sg" in es.tenses("eres"))
        # The CONDITIONAL is sometimes described as a mood, 
        # and sometimes as a tense of the indicative mood (e.g., in Spanish):
        t1 = (es.CONDITIONAL, 1, es.SG)
        t2 = (es.PRESENT, 1, es.SG, es.CONDITIONAL)
        self.assertTrue("1sg->" in es.tenses(u"sería"))
        self.assertTrue(t1 in es.tenses(u"sería"))
        self.assertTrue(t2 in es.tenses(u"sería"))
        self.assertTrue(t1 in es.tenses(es.conjugate("ser", mood=es.INDICATIVE, tense=es.CONDITIONAL)))
        self.assertTrue(t2 in es.tenses(es.conjugate("ser", mood=es.CONDITIONAL)))
        print("pattern.es.tenses()")

#---------------------------------------------------------------------------------------------------

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_find_lemmata(self):
        # Assert lemmata for nouns, adjectives, verbs and determiners.
        v = es.parser.find_lemmata([
            ["Los", "DT"], ["gatos", "NNS"], [u"negros", "JJ"], ["se", "PRP"], [u"sentó", "VB"],
            ["en", "IN"], ["la", "DT"], ["alfombra", "NN"]])
        self.assertEqual(v, [
            ["Los", "DT", "el"], 
            ["gatos", "NNS", "gato"], 
            ["negros", "JJ", "negro"], 
            ["se", "PRP", "se"], 
            [u"sentó", "VB", "sentar"],
            ["en", "IN", "en"], 
            ["la", "DT", "el"], 
            ["alfombra", "NN", "alfombra"]])
        print("pattern.es.parser.find_lemmata()")

    def test_parse(self):
        # Assert parsed output with Penn Treebank II tags (slash-formatted).
        # "el gato negro" is a noun phrase, "en la alfombra" is a prepositional noun phrase.
        v = es.parser.parse(u"El gato negro se sentó en la alfombra.")
        self.assertEqual(v, # XXX - shouldn't "se" be part of the verb phrase?
            u"El/DT/B-NP/O gato/NN/I-NP/O negro/JJ/I-NP/O " + \
            u"se/PRP/B-NP/O sentó/VB/B-VP/O " + \
            u"en/IN/B-PP/B-PNP la/DT/B-NP/I-PNP alfombra/NN/I-NP/I-PNP ././O/O"
        )
        # Assert the accuracy of the Spanish tagger.
        i, n = 0, 0
        for sentence in open(os.path.join(PATH, "corpora", "tagged-es-wikicorpus.txt")).readlines():
            sentence = sentence.decode("utf-8").strip()
            s1 = [w.split("/") for w in sentence.split(" ")]
            s2 = [[w for w, pos in s1]]
            s2 = es.parse(s2, tokenize=False, tagset=es.PAROLE)
            s2 = [w.split("/") for w in s2.split(" ")]
            for j in range(len(s1)):
                if s1[j][1] == s2[j][1]:
                    i += 1
                n += 1
        #print(float(i) / n)
        self.assertTrue(float(i) / n > 0.92)
        print("pattern.es.parser.parse()")

    def test_tag(self):
        # Assert [("el", "DT"), ("gato", "NN"), ("negro", "JJ")].
        v = es.tag("el gato negro")
        self.assertEqual(v, [("el", "DT"), ("gato", "NN"), ("negro", "JJ")])
        print("pattern.es.tag()")
    
    def test_command_line(self):
        # Assert parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.es", "-s", "El gato negro.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "El/DT/B-NP/O/O/el gato/NN/I-NP/O/O/gato negro/JJ/I-NP/O/O/negro ././O/O/O/.")
        print("python -m pattern.es")

#---------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestInflection))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
