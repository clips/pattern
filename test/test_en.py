import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest
import subprocess

from pattern import en

#-----------------------------------------------------------------------------------------------------

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_tokenize(self):
        # Returns a list with two sentences.
        # The tokenizer should at least handle common abbreviations and punctuation.
        v = en.parser.tokenize("The cat is eating (e.g., a fish). Yum!")
        self.assertEqual(v, ["The cat is eating ( e.g. , a fish ) .", "Yum !"])
        print "pattern.en.parser.tokenize()"

    def _test_lexical_rules(self, function=en.parser.lexicon.lexical_rules.apply):
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
            for word in lexicon:
                word = word.form
                if word not in en.parser.lexicon:
                    if function([word, "NN"])[1].startswith(tag):
                        i += 1
                    n += 1
            scores.append(float(i) / n)
        return scores
    
    def test_apply_default_rules(self):
        # Returns improved part-of-speech tag for unknown tokens, using Jason Wiener's ruleset.
        for a, b in (
          (["eating",  "NN"], ["eating",  "VBG"]),
          (["tigers",  "NN"], ["tigers",  "NNS"]),
          (["really",  "NN"], ["really",  "RB"]),
          (["foolish", "NN"], ["foolish", "JJ"])):
            self.assertEqual(en.parser.apply_default_rules(a), b)
        # Test words in WordNet that are not in Brill's lexicon.
        # Given are the scores for detection of nouns, verbs, adjectives and adverbs.
        # The baseline should increase (not decrease) when the algorithm is modified.
        v = self._test_lexical_rules(function=en.parser.apply_default_rules)
        self.assertTrue(v[0] > 0.91) # NN
        self.assertTrue(v[1] > 0.22) # VB
        self.assertTrue(v[2] > 0.44) # JJ
        self.assertTrue(v[3] > 0.61) # RB
        print "pattern.en.parser.apply_default_rules()"
    
    def test_apply_lexical_rules(self):
        # Returns improved part-of-speech tag for unknown tokens, using Brill's lexical rules.
        v = self._test_lexical_rules(function=en.parser.lexicon.lexical_rules.apply)
        self.assertTrue(v[0] > 0.88) # NN
        self.assertTrue(v[1] > 0.22) # VB
        self.assertTrue(v[2] > 0.53) # JJ
        self.assertTrue(v[3] > 0.61) # RB
        print "pattern.en.parser.lexicon.lexical_rules.apply()"
        
    def test_apply_contextual_rules(self):
        # Returns improved part-of-speech tags based on word context.
        for a, b in (                                                                 # Rule:
          ([["", "JJ"], ["", "JJ"], ["", ","]], [["", "JJ"], ["", "NN"], ["", ","]]), # SURROUNDTAG
          ([["", "NNP"], ["", "RB"]],           [["", "NNP"], ["", "NNP"]]),          # PREVTAG
          ([["", "NN"], ["", "PRP$"]],          [["", "VB"], ["", "PRP$"]]),          # NEXTTAG
          ([["phone", ""], ["", "VBZ"]],        [["phone", ""], ["", "NNS"]]),        # PREVWD
          ([["", "VB"], ["countries", ""]],     [["", "JJ"], ["countries", ""]]),     # NEXTWD
          ([["close", "VB"], ["to", ""]],       [["close", "RB"], ["to", ""]]),       # RBIGRAM
          ([["very", ""], ["much", "JJ"]],      [["very", ""], ["much", "RB"]]),      # LBIGRAM
          ([["such", "JJ"], ["as", "DT"]],      [["such", "JJ"], ["as", "IN"]]),
          ([["be", "VB"]],                      [["be", "VB"]])):
            self.assertEqual(en.parser.lexicon.contextual_rules.apply(a), b)
        print "pattern.en.parser.lexicon.contextual_rules.apply()"
    
    def test_find_tags(self):
        # Returns the token input annotated with part-of-speech-tags.
        v = en.parser.find_tags(["black", "cat"])
        self.assertEqual(v, [["black", "JJ"], ["cat", "NN"]])
        self.assertEqual(en.parser.find_tags(["felix"])[0][1], "NN")
        self.assertEqual(en.parser.find_tags(["Felix"])[0][1], "NNP")
        print "pattern.en.parser.find_tags()"
        
    def test_find_chunks(self):
        # Returns the tagged token input annotated with chunk tags.
        v = en.parser.find_chunks([["black", "JJ"], ["cat", "NN"]])
        self.assertEqual(v, [['black', 'JJ', 'B-NP'], ['cat', 'NN', 'I-NP']])
        # Test the accuracy of the chunker.
        # For example, in "That very black cat must be really meowing really loud in the yard.":
        # - "The very black" (NP)
        # - "must be really meowing" (VP)
        # - "really loud" (ADJP)
        # - "in" (PP)
        # - "the yard" (NP)
        v = en.parser.find_chunks([
            ["","DT"], ["","RB"], ["","JJ"], ["","NN"],
            ["","MD"], ["","RB"], ["","VBZ"], ["","VBG"],
            ["","RB"], ["","JJ"],
            ["","IN"],
            ["","CD"], ["","NNS"]
        ])
        self.assertEqual(v, [
            ["", "DT", "B-NP"], ["", "RB", "I-NP"], ["", "JJ", "I-NP"], ["", "NN", "I-NP"], 
            ["", "MD", "B-VP"], ["", "RB", "I-VP"], ["", "VBZ", "I-VP"], ["", "VBG", "I-VP"], 
            ["", "RB", "B-ADJP"], ["", "JJ", "I-ADJP"], 
            ["", "IN", "B-PP"], 
            ["", "CD", "B-NP"], ["", "NNS", "I-NP"]])
        print "pattern.en.parser.find_chunks()"
        
    def test_find_relations(self):
        # Returns the chunked token input annotated with relation tags (SBJ/OBJ).
        v = en.parser.find_relations([
            ["", "", "NP"], ["", "", "NP"], 
            ["", "", "VP"], ["", "", "VP"],
            ["", "", "NP"]])
        self.assertEqual(v, [
            ["", "", "NP", "NP-SBJ-1"], ["", "", "NP", "NP-SBJ-1"], 
            ["", "", "VP", "VP-1"], ["", "", "VP", "VP-1"], 
            ["", "", "NP", "NP-OBJ-1"]])
        print "pattern.en.parser.find_relations()"
        
    def test_find_prepositions(self):
        # Returns the chunked token input annotated with preposition tags (PP + NP).
        v = en.parser.find_prepositions([
            ["", "", "NP"],
            ["", "", "VP"],
            ["", "", "PP"],
            ["", "", "NP"], 
            ["", "", "NP"],])
        self.assertEqual(v, [
            ["", "", "NP", "O"], 
            ["", "", "VP", "O"], 
            ["", "", "PP", "B-PNP"], 
            ["", "", "NP", "I-PNP"], 
            ["", "", "NP", "I-PNP"]])
        print "pattern.en.parser.find_prepositions()"
        
    def test_find_lemmata(self):
        # Returns the tagged token input annotated with lemmata (for nouns and verbs).
        v = en.parser.find_lemmata([["cats", "NNS"], ["wearing", "VBG"], ["hats", "NNS"]])
        self.assertEqual(v, [
            ["cats", "NNS", "cat"], 
            ["wearing", "VBG", "wear"], 
            ["hats", "NNS", "hat"]])
        print "pattern.en.parser.find_lemmata()"
    
    def test_parse(self):
        # Returns the parsed sentence with Penn Treebank II tags (slash-formatted).
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
        # 4) Return value must be unicode.
        self.assertTrue(isinstance(v, unicode))
        print "pattern.en.parser.parse()"

    def test_tagged_string(self):
        # Returns a splitable TaggedString with language and tags properties.
        v = en.parser.parse("The black cat sat on the mat.", relations=True, lemmata=True)
        self.assertEqual(v.language, "en")
        self.assertEqual(v.tags, 
            ["word", "part-of-speech", "chunk", "preposition", "relation", "lemma"])
        self.assertEqual(v.split(en.parser.TOKENS)[0][0], 
            ["The", "DT", "B-NP", "O", "NP-SBJ-1", "the"])
        print "pattern.en.parser.TaggedString"
    
    def test_tag(self):
        # Returns [("black", "JJ"), ("cats", "NNS")].
        v = en.parser.tag("black cats")
        self.assertEqual(v, [("black", "JJ"), ("cats", "NNS")])
        print "pattern.en.parser.tag()"
        
    def test_ngrams(self):
        pass
        print "pattern.en.parser.ngrams()"
    
    def test_command_line(self):
        # Returns parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.en.parser", "-s", "Nice cat.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "Nice/JJ/B-NP/O/O/nice cat/NN/I-NP/O/O/cat ././O/O/O/.")
        print "python -m pattern.en.parser"

#-----------------------------------------------------------------------------------------------------

class TestModality(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_imperative(self):
        # Returns True for sentences that are orders, commands, warnings.
        for b, s in (
          (True,  "Do your homework!"),
          (True,  "Do whatever you want."),
          (True,  "Do not listen to me."),
          (True,  "Turn that off, will you."),
          (True,  "Let's help him."),
          (True,  "Help me!"),
          (True,  "You will help me."),
          (False, "Do it if you think it is necessary."),
          (False, "I hope you will help me."),
          (False, "I can help you."),
          (False, "I can help you if you let me.")):
            self.assertEqual(en.parser.modality.imperative(en.Sentence(en.parse(s))), b)
        print "en.parser.modality.imperative()"
        
    def test_conditional(self):
        # Returns True for sentences that contain possible or imaginary situations.
        for b, s in (
          (True,  "We ought to help him."),
          (True,  "We could help him."),
          (True,  "I will help you."),
          (True,  "I hope you will help me."),
          (True,  "I can help you if you let me."),
          (False, "You will help me."),
          (False, "I can help you.")):
            self.assertEqual(en.parser.modality.conditional(en.Sentence(en.parse(s))), b)
        # Test predictive mood.
        s = "I will help you."
        v = en.parser.modality.conditional(en.Sentence(en.parse(s)), predictive=False)
        self.assertEqual(v, False)
        # Test speculative mood.
        s = "I will help you if you pay me."
        v = en.parser.modality.conditional(en.Sentence(en.parse(s)), predictive=False)
        self.assertEqual(v, True)
        print "en.parser.modality.conditional()"

    def test_subjunctive(self):
        # Returns True for sentences that contain wishes, judgments or opinions.
        for b, s in (
          (True,  "I wouldn't do that if I were you."),
          (True,  "I wish I knew."),
          (True,  "I propose that you be on time."),
          (True,  "It is a bad idea to be late."),
          (False, "I will be late.")):
            self.assertEqual(en.parser.modality.subjunctive(en.Sentence(en.parse(s))), b)
        print "en.parser.modality.subjunctive()"
        
    def test_negated(self):
        # Returns True for sentences that contain "not", "n't" or "never".
        for b, s in (
          (True,  "Not true?"),
          (True,  "Never true."),
          (True,  "Isn't true."),):
            self.assertEqual(en.parser.modality.negated(en.Sentence(en.parse(s))), b)
        print "en.parser.modality.negated()"
        
    def test_mood(self):
        # Test imperative mood.
        v = en.mood(en.Sentence(en.parse("Do your homework!")))
        self.assertEqual(v, en.IMPERATIVE)
        # Test conditional mood.
        v = en.mood(en.Sentence(en.parse("We ought to help him.")))
        self.assertEqual(v, en.CONDITIONAL)
        # Test subjunctive mood.
        v = en.mood(en.Sentence(en.parse("I wouldn't do that if I were you.")))
        self.assertEqual(v, en.SUBJUNCTIVE)
        # Test indicative mood.
        v = en.mood(en.Sentence(en.parse("The weather is nice today.")))
        self.assertEqual(v, en.INDICATIVE)
        print "en.parser.modality.mood()"

#-----------------------------------------------------------------------------------------------------

class TestSentiment(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_sentiment_avg(self):
        # Returns 2.5.
        v = en.parser.sentiment.avg([1,2,3,4])
        self.assertEqual(v, 2.5)
        print "pattern.en.parser.sentiment.avg"

    def test_sentiment_column(self):
        # Returns [1,4].
        v = en.parser.sentiment.column([[1,2,3], [4,5,6]], 0)
        self.assertEqual(v, [1,4])
        print "pattern.en.parser.sentiment.column"

    def test_sentiment(self):
        # Returns < 0 for negative adjectives and > 0 for positive adjectives.
        self.assertTrue(en.sentiment("wonderful")[0] > 0)
        self.assertTrue(en.sentiment("horrible")[0] < 0)
        self.assertTrue(en.sentiment(en.wordnet.synsets("horrible", pos="JJ")[0])[0] < 0)
        self.assertTrue(en.sentiment(en.Text(en.parse("A bad book. Really horrible.")))[0] < 0)
        # Test the accuracy of the sentiment analysis.
        # Given are the scores for Pang & Lee's polarity dataset v2.0:
        # http://www.cs.cornell.edu/people/pabo/movie-review-data/
        # The baseline should increase (not decrease) when the algorithm is modified.
        from pattern.db import Datasheet
        from pattern.metrics import test
        reviews = []
        for score, review in Datasheet.load(os.path.join("corpora", "pang&lee-polarity.txt")):
            reviews.append((review, int(score) > 0))
        A, P, R, F = test(lambda review: en.positive(review), reviews)
        self.assertTrue(A > 0.715)
        self.assertTrue(P > 0.720)
        self.assertTrue(R > 0.705)
        self.assertTrue(F > 0.710)
        print "pattern.en.sentiment()"
        
    def test_sentiment_assessment(self):
        # Return value of en.sentiment() has a fine-grained "assessments" property.
        v = en.sentiment("A warm and pleasant day.").assessments
        self.assertTrue(v[1][0] == "pleasant")
        self.assertTrue(v[1][1] > 0)
        print "pattern.en.sentiment().assessments"
    
    def test_sentiwordnet(self):
        # Returns < 0 for negative words and > 0 for positive words.
        try:
            lexicon = en.parser.sentiment.SentiWordNet()
            lexicon.load()
        except ImportError:
            # SentiWordNet data file is not installed in default location.
            return
        self.assertTrue(lexicon["wonderful"][0] > 0)
        self.assertTrue(lexicon["horrible"][0] < 0)
        print "pattern.en.parser.sentiment.SentiWordNet"

#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestModality))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=1).run(suite())
