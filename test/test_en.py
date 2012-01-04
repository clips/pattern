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

class TestParseTree(unittest.TestCase):
    
    def setUp(self):
        # Parse sentences to test on.
        # Creating a Text creates Sentence, Chunk, PNP and Word.
        # Creating a Sentence tests Sentence.append() and Sentence.parse_token().
        self.text = "I'm eating pizza with a fork. What a tasty pizza!"
        self.text = en.Text(en.parse(self.text, relations=True, lemmata=True))
    
    def test_copy(self):
        # Test deepcopy of Text, Sentence, Chunk, PNP and Word.
        self.text = self.text.copy()
        print "pattern.en.parser.Text.copy()"
        
    def test_xml(self):
        # Test XML export and import.
        self.text = en.Text.from_xml(self.text.xml)
        print "pattern.en.parser.Text.xml"
        print "pattern.en.parser.Text.from_xml()"
    
    def test_text(self):
        # Test text.
        self.assertEqual(self.text.sentences[0].string, "I 'm eating pizza with a fork .")
        self.assertEqual(self.text.sentences[1].string, "What a tasty pizza !")
        print "pattern.en.parser.tree.Text"
    
    def test_sentence(self):
        # Test sentence.
        v = self.text[0]
        self.assertTrue(v.start    == 0)
        self.assertTrue(v.stop     == 8)
        self.assertTrue(v.string   == "I 'm eating pizza with a fork .")
        self.assertTrue(v.subjects == [self.text[0].chunks[0]])
        self.assertTrue(v.verbs    == [self.text[0].chunks[1]])
        self.assertTrue(v.objects  == [self.text[0].chunks[2]])
        self.assertTrue(v.nouns    == [self.text[0].words[3], self.text[0].words[6]])
        # Sentence.string must be unicode.
        self.assertTrue(isinstance(v.string, unicode) == True)
        self.assertTrue(isinstance(unicode(v), unicode) == True)
        self.assertTrue(isinstance(str(v), str) == True)
        print "pattern.en.parser.tree.Sentence"
    
    def test_sentence_constituents(self):
        # Returns an in-order list of Chunk, PNP and Word.
        v = self.text[0].constituents(pnp=True)
        self.assertEqual(v, [
            self.text[0].chunks[0],
            self.text[0].chunks[1],
            self.text[0].chunks[2],
            self.text[0].pnp[0],
            self.text[0].words[7],
        ])
        print "pattern.en.parser.tree.Sentence.constituents()"
        
    def test_slice(self):
        # Test sentence slice.
        v = self.text[0].slice(start=4, stop=6)
        self.assertTrue(v.parent == self.text[0])
        self.assertTrue(v.string == "with a")
        # Test sentence slice tag integrity.
        self.assertTrue(v.words[0].type  == "IN")
        self.assertTrue(v.words[1].chunk == None)
        print "pattern.en.parser.tree.Slice"
    
    def test_chunk(self):
        # Test chunk with multiple words ("a fork").
        v = self.text[0].chunks[4]
        self.assertTrue(v.start   == 5)
        self.assertTrue(v.stop    == 7)
        self.assertTrue(v.string  == "a fork")
        self.assertTrue(v.lemmata == ["a", "fork"])
        self.assertTrue(v.words   == [self.text[0].words[5], self.text[0].words[6]])
        self.assertTrue(v.head    ==  self.text[0].words[6])
        self.assertTrue(v.type    == "NP")
        self.assertTrue(v.role    == None)
        self.assertTrue(v.pnp     != None)
        # Test chunk that is subject/object of the sentence ("pizza").
        v = self.text[0].chunks[2]
        self.assertTrue(v.role     == "OBJ")
        self.assertTrue(v.relation == 1)
        self.assertTrue(v.related  == [self.text[0].chunks[0], self.text[0].chunks[1]])
        self.assertTrue(v.subject  ==  self.text[0].chunks[0])
        self.assertTrue(v.verb     ==  self.text[0].chunks[1])
        self.assertTrue(v.object   == None)
        # Test chunk traversal.
        self.assertEqual(v.nearest("VP"), self.text[0].chunks[1])
        self.assertEqual(v.previous(), self.text[0].chunks[1])
        self.assertEqual(v.next(), self.text[0].chunks[3])
        print "pattern.en.parser.tree.Chunk"

    def test_chunk_conjunctions(self):
        # Returns a list of conjunct/disjunct chunks ("black cat" AND "white cat").
        v = en.Sentence(en.parse("black cat and white cat"))
        self.assertEqual(v.chunk[0].conjunctions, [(v.chunk[1], en.AND)])
        print "pattern.en.parser.tree.Chunk.conjunctions()"

    def test_chunk_modifiers(self):
        # Returns a list of nearby adjectives and adverbs with no role, for VP.
        v = en.Sentence(en.parse("Perhaps you should go."))
        self.assertEqual(v.chunk[2].modifiers, [v.chunk[0]]) # should <=> perhaps
        print "pattern.en.parser.tree.Chunk.modifiers"

    def test_pnp(self):
        # Test PNP chunk ("with a fork").
        v = self.text[0].pnp[0]
        self.assertTrue(v.string == "with a fork")
        self.assertTrue(v.chunks == [self.text[0].chunks[3], self.text[0].chunks[4]])
        self.assertTrue(v.pp     ==  self.text[0].chunks[3])
        print "pattern.en.parser.tree.PNP"
    
    def test_word(self):
        # Test word tags ("fork" => NN).
        v = self.text[0].words[6]
        self.assertTrue(v.index  == 6)
        self.assertTrue(v.string == "fork")
        self.assertTrue(v.lemma  == "fork")
        self.assertTrue(v.type   == "NN")
        self.assertTrue(v.chunk  == self.text[0].chunks[4])
        self.assertTrue(v.pnp    != None)
        for i, tags in enumerate([
          ["I", "PRP", "B-NP", "O", "NP-SBJ-1", "i"],
          ["'m", "VBP", "B-VP", "O", "VP-1", "'m"],
          ["eating", "VBG", "I-VP", "O", "VP-1", "eat"],
          ["pizza", "NN", "B-NP", "O", "NP-OBJ-1", "pizza"],
          ["with", "IN", "B-PP", "B-PNP", "O", "with"],
          ["a", "DT", "B-NP", "I-PNP", "O", "a"],
          ["fork", "NN", "I-NP", "I-PNP", "O", "fork"],
          [".", ".", "O", "O", "O", "."]]):
            self.assertEqual(self.text[0].words[i].tags, tags)
        print "pattern.en.parser.tree.Word"
        
    def test_word_custom_tags(self):
        # Test word custom tags ("word/part-of-speech/.../some-custom-tag").
        s = en.Sentence("onion/NN/FOOD", token=[en.WORD, en.POS, "semantic_type"])
        v = s.words[0]
        self.assertEqual(v.semantic_type, "FOOD")
        self.assertEqual(v.custom_tags["semantic_type"], "FOOD")
        self.assertEqual(v.copy().custom_tags["semantic_type"], "FOOD")
        # Test adding new custom tags.
        v.custom_tags["taste"] = "pungent"
        self.assertEqual(s.token, [en.WORD, en.POS, "semantic_type", "taste"])
        print "pattern.en.parser.tree.Word.custom_tags"
    
    def test_find(self):
        # Returns the first item for which given function is True.
        v = en.parser.tree.find(lambda x: x>10, [1,2,3,11,12])
        self.assertEqual(v, 11)
        print "pattern.en.parser.tree.find()"
        
    def test_zip(self):
        # Returns a list of zipped tuples, using default to balance uneven lists.
        v = en.parser.tree.zip([1,2,3], [4,5,6,7], default=0)
        self.assertEqual(v, [(1,4), (2,5), (3,6), (0,7)])
        print "pattern.en.parser.tree.zip()"
        
    def test_unzip(self):
        v = en.parser.tree.unzip(1, [(1,4), (2,5), (3,6)])
        self.assertEqual(v, [4,5,6])
        print "pattern.en.parser.tree.unzip()"
    
    def test_unique(self):
        # Returns a list copy with unique items.
        v = en.parser.tree.unique([1,1,1])
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], 1)
        print "pattern.en.parser.tree.unique()"
    
    def test_dynamic_map(self):
        # Returns an iterator map().
        v = en.parser.tree.dynamic_map(lambda x: x+1, [1,2,3])
        self.assertEqual(list(v), [2,3,4])
        self.assertEqual(v.set[0], 1)
        print "pattern.en.parser.tree.dynamic_map()"
        
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
            self.assertEqual(en.negated(en.Sentence(en.parse(s))), b)
        print "en.negated()"
        
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
        print "en.mood()"
        
    def test_modality(self):
        # Returns -1.0 => +1.0 representing the degree of certainty.
        v = en.modality(en.Sentence(en.parse("I wish it would stop raining.")))
        self.assertTrue(v < 0)
        v = en.modality(en.Sentence(en.parse("It will surely stop raining soon.")))
        self.assertTrue(v > 0)
        # Test the accuracy of the modality algorithm.
        # Given are the scores for the CoNLL-2010 Shared Task 1 Wikipedia uncertainty data:
        # http://www.inf.u-szeged.hu/rgai/conll2010st/tasks.html#task1
        # The baseline should increase (not decrease) when the algorithm is modified.
        from pattern.db import Datasheet
        from pattern.metrics import test
        sentences = []
        from time import time
        for certain, sentence in Datasheet.load(os.path.join("corpora", "conll2010-uncertainty.txt")):
            sentence = en.parse(sentence, chunks=False, light=True)
            sentence = en.Sentence(sentence)
            sentences.append((sentence, int(certain) > 0))
        A, P, R, F = test(lambda sentence: en.modality(sentence) > 0.5, sentences)
        self.assertTrue(A > 0.67)
        self.assertTrue(P > 0.69)
        self.assertTrue(R > 0.62)
        self.assertTrue(F > 0.65)
        print "en.modality()"

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
        self.assertTrue(A > 0.71)
        self.assertTrue(P > 0.72)
        self.assertTrue(R > 0.70)
        self.assertTrue(F > 0.71)
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
            # SentiWordNet data file is not installed in default location, stop test.
            return
        self.assertTrue(lexicon["wonderful"][0] > 0)
        self.assertTrue(lexicon["horrible"][0] < 0)
        print "pattern.en.parser.sentiment.SentiWordNet"

#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestParseTree))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestModality))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSentiment))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=1).run(suite())
