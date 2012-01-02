import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest
import subprocess

from pattern import en

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_tokenize(self):
        # Returns a list with two sentences.
        # The tokenizer should at least handle common abbreviations and punctuation.
        v = en.parser.tokenize("The cat is eating (e.g., a fish). Yum!")
        self.assertEqual(v, ["The cat is eating ( e.g. , a fish ) .", "Yum !"])
        print "en.parser.tokenize()"

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
        #return
        v = self._test_lexical_rules(function=en.parser.apply_default_rules)
        self.assertTrue(v[0] > 0.91) # NN
        self.assertTrue(v[1] > 0.22) # VB
        self.assertTrue(v[2] > 0.44) # JJ
        self.assertTrue(v[3] > 0.61) # RB
        print "en.parser.apply_default_rules()"
    
    def test_apply_lexical_rules(self):
        # Returns improved part-of-speech tag for unknown tokens, using Brill's lexical rules.
        #return
        v = self._test_lexical_rules(function=en.parser.lexicon.lexical_rules.apply)
        self.assertTrue(v[0] > 0.88) # NN
        self.assertTrue(v[1] > 0.22) # VB
        self.assertTrue(v[2] > 0.53) # JJ
        self.assertTrue(v[3] > 0.61) # RB
        print "en.parser.lexicon.lexical_rules.apply()"
        
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
        print "en.parser.lexicon.contextual_rules.apply()"
    
    def test_find_tags(self):
        # Returns the token input annotated with part-of-speech-tags.
        v = en.parser.find_tags(["black", "cat"])
        self.assertEqual(v, [["black", "JJ"], ["cat", "NN"]])
        self.assertEqual(en.parser.find_tags(["felix"])[0][1], "NN")
        self.assertEqual(en.parser.find_tags(["Felix"])[0][1], "NNP")
        print "en.parser.find_tags()"
        
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
        print "en.parser.find_chunks()"
        
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
        print "en.parser.find_relations()"
        
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
        print "en.parser.find_prepositions()"
        
    def test_find_lemmata(self):
        # Returns the tagged token input annotated with lemmata (for nouns and verbs).
        v = en.parser.find_lemmata([["cats", "NNS"], ["wearing", "VBG"], ["hats", "NNS"]])
        self.assertEqual(v, [
            ["cats", "NNS", "cat"], 
            ["wearing", "VBG", "wear"], 
            ["hats", "NNS", "hat"]])
        print "en.parser.find_lemmata()"
    
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
        print "en.parser.parse()"

    def test_tagged_string(self):
        # Returns a splitable TaggedString with language and tags properties.
        v = en.parser.parse("The black cat sat on the mat.", relations=True, lemmata=True)
        self.assertEqual(v.language, "en")
        self.assertEqual(v.tags, 
            ["word", "part-of-speech", "chunk", "preposition", "relation", "lemma"])
        self.assertEqual(v.split(en.parser.TOKENS)[0][0], 
            ["The", "DT", "B-NP", "O", "NP-SBJ-1", "the"])
        print "en.parser.TaggedString"
    
    def test_tag(self):
        # Returns [("black", "JJ"), ("cats", "NNS")].
        v = en.parser.tag("black cats")
        self.assertEqual(v, [("black", "JJ"), ("cats", "NNS")])
        print "en.parser.tag()"
    
    def test_command_line(self):
        # Returns parsed output from the command-line (example from the documentation).
        p = ["python", "-m", "pattern.en.parser", "-s", "Nice cat.", "-OTCRL"]
        p = subprocess.Popen(p, stdout=subprocess.PIPE)
        p.wait()
        v = p.stdout.read()
        v = v.strip()
        self.assertEqual(v, "Nice/JJ/B-NP/O/O/nice cat/NN/I-NP/O/O/cat ././O/O/O/.")
        print "python -m pattern.en.parser"
    
if __name__ == '__main__':
    unittest.main()