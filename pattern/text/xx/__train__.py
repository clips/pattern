#### PATTERN | XX | PARSER | BRILL TRAINER ##########################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2013 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Utility script for training a Brill-based part-of-speech tagger, using NLTK.

# The output is three files:
# - xx-lexicon.txt: a lexicon of tagged words,
# - xx-morphology.txt: lexical suffix rules,
# - xx-context.txt: contextual rules.

# The input is:
# - a treebank: a corpus of tagged text (1M words),
# - a parser: a function for extracting (word, tag)-tuples from the treebank (see wikicorpus_es()),
# - a DEFAULT tag.

# The main part of the code to tweak is the preprocessing step.
# Other tweaks can include:
# - number of train and test sentences,
# - number of morphological rules to generate,
# - number of contextual rules to generate,
# - percentage of named entities in lexicon,
# - suffix frequency threshold when learning lexical rules.

# Import NLTK.
from nltk.tag import UnigramTagger, BigramTagger
from nltk.tag import FastBrillTaggerTrainer
from nltk.tag.brill import SymmetricProximateTokensTemplate
from nltk.tag.brill import ProximateTokensTemplate
from nltk.tag.brill import ProximateTagsRule
from nltk.tag.brill import ProximateWordsRule

# Import Pattern.
from pattern.web import u
from pattern.text import find_tags
from pattern.text import Lexicon

from glob import glob
from codecs import BOM_UTF8
from random import choice

#### CORPORA #######################################################################################
# Each parser must return a (sentences, lemmata, entities)-tuple.
# Each sentence must be a list of (word, tag)-tuples.
# Optionally, lemmata is a dictionary of (word, lemma)-items.
# Optionally, entities is a dictionary of (words, frequency)-items.

def wikicorpus_es(n=200, m=3, map=lambda tag: tag, offset=0):
    """ Returns a (sentences, lemmata, entities)-tuple from the Spanish Wikicorpus:
        http://www.lsi.upc.edu/%7Enlp/wikicorpus/
        Each sentence in the list of n sentences is a list of (word, tag)-tuples.
        Each sentence has at least m words.
        Tags are mapped using the given map function.
        The lemmata is a dictionary of (word, lemma)-items.
        The entities is a dictionary of (words, frequency)-items.
    """
    # <doc id="267233" title="Deltoide" dbindex="85004">
    # ; ; Fx 0
    # En en NP00000 0
    # geometríıa geometríıa NCFS000 0
    # , , Fc 0
    # un uno DI0MS0 0
    # deltoide deltoide NCFS000 0
    # es ser VSIP3S0 01775973
    # un uno DI0MS0 0
    # cuadrilátero cuadrilátero NCMS000 0
    # no no RN 0
    # regular regular AQ0CS0 01891762
    # ...
    # </doc>
    sentences, lemmata, entities = [], {}, {}
    sentence = []
    i = 0
    for f in glob("tagged.es/*")[offset:]:
        for s in u(open(f).read()).encode("utf-8").split("\n"):
            if s and not s.startswith(("<doc", "</doc")):
                word, lemma, tag, x = s.split(" ")
                word, lemma = word.replace("_", " "), lemma.replace("_", " ")
                if word in ("ENDOFARTICLE", "REDIRECT", "Acontecimientos", "Fallecimientos", "Nacimientos"):
                    continue
                if not " " in word:
                    lemmata[word] = lemma
                # Wikicorpus sometimes bundles consecutive words,
                # but the Brill tagger only handles unigrams,
                # so we split into individual words.
                for word in word.split(" "):
                    sentence.append((word, map(tag)))
                    if tag.startswith("NP"):
                        entities[word] = entities.get(word, 0) + 1
                    if tag == "Fp" and word == "." and len(sentence) >= m:
                        sentences.append(sentence)
                        sentence = []
                        i += 1
                        #if i % 100 == 0:
                        #    print i
                    if i >= n:
                        return sentences, lemmata, entities

#### PREPROCESSING #################################################################################

# Corpus, number of sentences, minimum number of words per sentence.
CORPUS, n, m = wikicorpus_es, 100000, 1

# Mapping function for tags.
map = lambda tag: tag.startswith("V")  and  tag[:3] \
               or tag.startswith("NC") and (tag[:2] + tag[3]).rstrip("0N") \
               or tag.startswith("Fp") and  tag[:3] \
               or tag[:2]

DEFAULT = "NC" # What is the default tag in the corpus?

# 1) Parse the corpus.
sentences, lemmata, entities = CORPUS(n, m, map, offset=1)
print len(sentences), "sentences"
print sum(len(s) for s in sentences), "words"
print len(entities), "entities"
print

# 2) Divide available data into train and test.
train = sentences[:int(len(sentences) * 0.65)]
test = sentences[-int(len(sentences) * 0.35):]
print "Train:", len(train), "sentences", sum(len(s) for s in train), "words"
print "Test:", len(test), "sentences", sum(len(s) for s in test), "words"
print

# For pattern.es we used:
# Wikicorpus tagged.es/spanishEtiquetado_10000_15000
# 65,000 (1,401,261)
# 35,000 (877,159)
# 300 rules out of 99,955

# 3) Anonymize named entities in the training data,
#    so the lexicon doesn't flood with named entities.
#    We want a grammatical tagger, not a named entity recognizer.
NE = None
for s in train:
    for i in range(len(s)):
        if s[i][1] in ("NP", "NNP", "NE", "N(eigen,ev)"):
            s[i] = ("Named_Entity", s[i][1])
            NE = s[i][1]

#### TRAINING ######################################################################################

# 4) Train a base tagger that just uses tag frequency for each word.
base = UnigramTagger(train)
#base = BigramTagger(train)

# 5) Define the Brill contextual ruleset.
ruleset = [
    SymmetricProximateTokensTemplate(ProximateTagsRule,  (1, 1)),
    SymmetricProximateTokensTemplate(ProximateTagsRule,  (1, 2)),
    SymmetricProximateTokensTemplate(ProximateTagsRule,  (1, 3)),
    SymmetricProximateTokensTemplate(ProximateTagsRule,  (2, 2)),
    SymmetricProximateTokensTemplate(ProximateWordsRule, (0, 0)),
    SymmetricProximateTokensTemplate(ProximateWordsRule, (1, 1)),
    SymmetricProximateTokensTemplate(ProximateWordsRule, (1, 2)),
    ProximateTokensTemplate(ProximateTagsRule, (-1, -1), (1, 1)),
]

# 6) Train the Brill tagger.
print "Training..."
learner = FastBrillTaggerTrainer(base, ruleset, trace=2)
tagger = learner.train(train, max_rules=250, min_score=3) # Number of rules to generate.
print
print "Testing..."
print tagger.evaluate(test)

#### CONVERSION ####################################################################################

# 7) Convert NLTK ProximateRules to Brill's text file format.
#    Note that not all rules can be mapped.
print "Generating contextual rules..."
contextual_rules = []
for rule in tagger.rules():
    a = rule.original_tag
    b = rule.replacement_tag
    C = rule._conditions
    r = None
    t1 = None
    t2 = None
    # Context tag rules.
    if isinstance(rule, ProximateTagsRule):
        if len(C) == 1 and C[0][:2] == (-1, -1):
            r, t1 = "PREVTAG", C[0][2]
        if len(C) == 1 and C[0][:2] == (+1, +1):
            r, t1 = "NEXTTAG", C[0][2]
        if len(C) == 1 and C[0][:2] == (-2, -1):
            r, t1 = "PREV1OR2TAG", C[0][2]
        if len(C) == 1 and C[0][:2] == (+1, +2):
            r, t1 = "NEXT1OR2TAG", C[0][2]
        if len(C) == 1 and C[0][:2] == (-3, -1):
            r, t1 = "PREV1OR2OR3TAG", C[0][2]
        if len(C) == 1 and C[0][:2] == (+1, +3):
            r, t1 = "NEXT1OR2OR3TAG", C[0][2]
        if len(C) == 1 and C[0][:2] == (-2, -2):
            r, t1 = "PREV2TAG", C[0][2]
        if len(C) == 1 and C[0][:2] == (+2, +2):
            r, t1 = "NEXT2TAG", C[0][2]
        if len(C) == 2 and C[0][:2] == (-1, -1) and C[1][:2] == (+1, +1):
            r, t1, t2 = "SURROUNDTAG", C[0][2], C[1][2]
    # Context word rules.
    if isinstance(rule, ProximateWordsRule):
        if len(C) == 1 and C[0][:2] == (+0, +0):
            r, t1 = "CURWD", C[0][2]
        if len(C) == 1 and C[0][:2] == (-1, -1):
            r, t1 = "PREVWD", C[0][2]
        if len(C) == 1 and C[0][:2] == (+1, +1):
            r, t1 = "NEXTWD", C[0][2]
        if len(C) == 1 and C[0][:2] == (-2, -1):
            r, t1 = "PREV1OR2WD", C[0][2]
        if len(C) == 1 and C[0][:2] == (+1, +2):
            r, t1 = "NEXT1OR2WD", C[0][2]
        if r == "Named_Entity":
            continue
    contextual_rules.append(("%s %s %s %s %s" % (a, b, r, t1, t2 or "")).strip())

open("brill-contextual.txt", "w").write("\n".join(contextual_rules))

# 8) Construct simple lexical rules based on suffix frequency.
#    These amount to <1% accuracy or so.
print "Generating lexical rules..."
suffix = {}
for s in train:
    for word, tag in s:
        x = word[-3:] # Last 3 characters.
        if x and len(x) < len(word) and tag != DEFAULT: 
            if x not in suffix:
                suffix[x] = {}
            # Count 3-gram tag frequency.
            suffix[x][tag] = suffix[x].get(tag, 0) + 1
for x in suffix:
    # Relative frequency of each tag.
    f = float(sum(suffix[x].values()))
    for tag in suffix[x]:
        suffix[x][tag] /= f
    # Sort by word frequency and top tag frequency.
    suffix[x] = [(v, k) for k, v in suffix[x].items()]
    suffix[x] = sorted(suffix[x], reverse=True)
    suffix[x] = (f, suffix[x][0])

# Keep high tag frequency (v[1][0] > 80%) for suffix.
# Remove infrequent words (v[0] < 10).
# You can play around with the 80&/10 threshold to see if accuracy increases.
suffix = [(v, k) for k, v in suffix.items() if 1.0 >= v[1][0] >= 0.80 and v[0] >= 10]
suffix = sorted(suffix, reverse=True)

lexical = []
for (count, (frequency, tag)), x in suffix:
    x = u(x).encode("utf-8")
    r = "%s %s fhassuf %s %s x" % (DEFAULT, x, len(u(x)), tag)
    lexical.append(r)
    if len(lexical) == 100: # Number of lexical rules.
        break

open("brill-lexical.txt", "w").write("\n".join(lexical))

# 9) Convert NLTK base tagger to Brill's text file format.
#    Exclude the anonymized Named_Entity, we'll add top NE in the next step.
print "Generating lexicon..."
lexicon, seen = {}, {}
for x in base._context_to_tag.items():
    if isinstance(base, UnigramTagger):
        word, tag = x
    if isinstance(base, BigramTagger):
        (prev, word), tag = x
    if " " not in word and word != "Named_Entity":
        if word not in lexicon:
            lexicon[word] = {}
        if tag not in lexicon[word]:
            lexicon[word][tag] = 0
        lexicon[word][tag] += 1
        seen[word] = True

# Majority vote for words with multiple tags.
lexicon = [(word, max(zip(tags.values(), tags.keys()))[1]) for word, tags in lexicon.items()]
lexicon = [word+" "+tag for word, tag in lexicon]
lexicon = sorted(lexicon)

# 10) Add top most frequent named entities: 40% of lexicon.
#     Do not overwrite words already in the lexicon (which appears to result in <10% accuracy).
top = [(v, k) for k, v in entities.items() if " " not in k]
top = sorted(top, reverse=True)[:int(len(lexicon) * 0.4)] # percentage
top = [k for v, k in top]
for ne in top:
    if ne not in seen:
        lexicon.append(ne+" "+NE)
lexicon = sorted(lexicon)

open("brill-lexicon.txt", "w").write("\n".join(lexicon))

#### TEST ##########################################################################################
# Create a Pattern Brill tagger and evaluate accuracy on the test data.

# 11) Load lexicon data (it is a lazy-loading object).
lexicon = Lexicon()
lexicon.path = "brill-lexicon.txt"
lexicon.lexical_rules.path = "brill-lexical.txt"
lexicon.contextual_rules.path = "brill-contextual.txt"
lexicon.named_entities.tag = "NP"
lexicon.load()
lexicon.lexical_rules.load()
lexicon.contextual_rules.load()
lexicon.named_entities.load()

# For testing with or without lexical and contextual rules:
#for i in reversed(range(len(lexicon.lexical_rules)-1)):
#    del lexicon.lexical_rules[i]
#for i in reversed(range(len(lexicon.contextual_rules)-1)):
#    del lexicon.contextual_rules[i]

# For random test data:
#test, x, xx = CORPUS(1000, 1, map, offset=8)

tags = [tag for s in test for word, tag in s]
tags = list(set(tags))
print "Corpus tagset:"
print sorted(tags)

# 12) Evaluate accuracy:
i = 0
n = 0
for ii, s1 in enumerate(test):
    #s2 = [(u(word), choice(tags)) for word, tag in s1] # Random tag baseline
    #s2 = [(u(word), DEFAULT) for word, tag in s1] # Default tag baseline.
    s2 = [u(word) for word, tag in s1]
    s2 = find_tags(s2, DEFAULT, lexicon=lexicon)
    s2 = [(word, (tag=="NNP" and NE or tag)) for word, tag in s2]
    for j in range(len(s1)):
        if s1[j][1] == s2[j][1]:
            i += 1
        n += 1
print
print "Accuracy:"
print i, n
print i / float(n)