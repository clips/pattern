#### PATTERN | EN | MOOD & MODALITY ################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

### LIST FUNCTIONS #################################################################################

def find(function, list):
    """ Returns the first item in the list for which function(item) is True, None otherwise.
    """
    for item in list:
        if function(item) == True:
            return item

### MOOD ###########################################################################################

INDICATIVE  = "indicative"  # They went for a walk.
IMPERATIVE  = "imperative"  # Let's go for a walk!
CONDITIONAL = "conditional" # It might be nice to go for a walk when it stops raining.
SUBJUNCTIVE = "subjunctive" # It would be nice to go for a walk sometime.

def s(word):
    return word.string.lower()
def join(words):
    return " ".join([w.string.lower() for w in words])
def question(sentence):
    return len(sentence) > 0 and sentence[-1].string == "?"
def verb(word):
    return word.type.startswith(("VB","MD")) and (word.chunk is None or word.chunk.type.endswith("VP"))
def verbs(sentence, i=0, j=None):
    return [w for w in sentence[i:j or len(sentence)] if verb(w)]

def imperative(sentence, **kwargs):
    """ The imperative mood is used to give orders, commands, warnings, instructions, 
        or to make requests (if used with "please").
        It is marked by the infinitive form of the verb, without "to":
        "For goodness sake, just stop it!"
    """
    S = sentence
    if question(S):
        return False
    if S.subjects and s(S.subjects[0]) not in ("you", "yourself"):
        # The subject can only identify as "you" (2sg): "Control yourself!".
        return False
    r = s(S).rstrip(" .!")
    for cc in ("if", "assuming", "provided that", "given that"):
        # A conjunction can also indicate conditional mood.
        if cc+" " in r:
            return False
    for i, w in enumerate(S):
        if verb(w):
            if s(w) in ("do", "let") and w == verbs(S)[0]:
                # "Do your homework!"
                return True
            if s(w) in ("do", "let"):
                # "Let's not argue."
                continue
            if s(w) in ("would", "should", "'d", "could", "can", "may", "might"):
                # "You should leave." => conditional.
                return False
            if s(w) in ("will", "shall") and i > 0 and s(S[i-1]) == "you" and not verbs(S,0,i):
                # "You will eat your dinner."
                continue
            if w.type == "VB" and (i == 0 or s(S[i-1]) != "to"):
                # "Come here!"
                return True
            # Break on any other verb form.
            return False
    return False

#from __init__ import parse
#from tree import Sentence
#for str in (
#  "Do your homework!",                   # True
#  "Do whatever you want.",               # True
#  "Do not listen to me.",                # True
#  "Do it if you think it is necessary.", # False
#  "Turn that off, will you.",            # True
#  "Let's help him.",                     # True
#  "Help me!",                            # True
#  "You will help me.",                   # True
#  "I hope you will help me.",            # False
#  "I can help you.",                     # False
#  "I can help you if you let me."):      # False
#    print str
#    print parse(str)
#    print imperative(Sentence(parse(str)))
#    print

def conditional(sentence, predictive=True, **kwargs):
    """ The conditional mood is used to talk about possible or imaginary situations.
        It is marked by the infinitive form of the verb, preceded by would/could/should:
        "we should be going", "we could have stayed longer".
        With predictive=False, sentences with will/shall need an explicit if/when/once-clause:
        - "I will help you" => predictive.
        - "I will help you if you pay me" => speculative.
        Sentences with can/may always need an explicit if-clause.
    """
    S = sentence
    if question(S):
        return False
    i = find(lambda w: s(w) == "were", S)
    i = i and i.index or 0 
    if i > 0 and (s(S[i-1]) in ("i", "it", "he", "she") or S[i-1].type == "NN"):
        # "As if it were summer already." => subjunctive (wish).
        return False
    for i, w in enumerate(S):
        if w.type == "MD":
            if s(w) == "ought" and i < len(S) and s(S[i+1]) == "to":
                # "I ought to help you."
                return True
            if s(w) in ("would", "should", "'d", "could", "might"):
                # "I could help you."
                return True
            if s(w) in ("will", "shall", "'ll") and i > 0 and s(S[i-1]) == "you" and not verbs(S,0,i):
                # "You will help me." => imperative.
                return False
            if s(w) in ("will", "shall", "'ll") and predictive:
                # "I will help you." => predictive.
                return True
            if s(w) in ("will", "shall", "'ll", "can", "may"):
                # "I will help you when I get back." => speculative.
                r = s(S).rstrip(" .!")
                for cc in ("if", "when", "once", "as soon as", "assuming", "provided that", "given that"):
                    if cc+" " in r:
                        return True
    return False
    
#from __init__ import parse
#from tree import Sentence
#for str in (
#  "We ought to help him.",          # True
#  "We could help him.",             # True
#  "I will help you.",               # True
#  "You will help me.",              # False (imperative)
#  "I hope you will help me.",       # True (predictive)
#  "I can help you.",                # False
#  "I can help you if you let me."): # True
#    print str
#    print parse(str)
#    print conditional(Sentence(parse(str)))
#    print

subjunctive1 = [
    "advise", "ask", "command", "demand", "desire", "insist", 
    "propose", "recommend", "request", "suggest", "urge"]
subjunctive2 = [
    "best", "crucial", "desirable", "essential", "imperative",
    "important", "recommended", "urgent", "vital"]
    
for w in list(subjunctive1): # Inflect.
    subjunctive1.append(w+"s")
    subjunctive1.append(w.rstrip("e")+"ed")

def subjunctive(sentence, classical=True, **kwargs):
    """ The subjunctive mood is a classical mood used to express a wish, judgment or opinion.
        It is marked by the verb wish/were, or infinitive form of a verb
        preceded by an "it is"-statement:
        "It is recommended that he bring his own computer."
    """
    S = sentence
    if question(S):
        return False
    for i, w in enumerate(S):
        b = False
        if w.type.startswith("VB"):
            if s(w).startswith("wish"):
                # "I wish I knew."
                return True
            if s(w) == "were" and i > 0 and (s(S[i-1]) in ("i", "it", "he", "she") or S[i-1].type == "NN"):
                # "It is as though she were here." => counterfactual.
                return True
            if s(w) in subjunctive1:
                # "I propose that you be on time."
                b = True
            elif s(w) == "is" and 0 < i < len(S)-1 and s(S[i-1]) == "it" \
             and s(S[i+1]) in subjunctive2:
                # "It is important that you be there." => but you aren't (yet).
                b = True 
            elif s(w) == "is" and 0 < i < len(S)-3 and s(S[i-1]) == "it" \
             and s(S[i+2]) in ("good", "bad") and s(S[i+3]) == "idea":
                # "It is a good idea that you be there."
                b = True
        if b:
            # With classical=False, "It is important that you are there." passes.
            # This is actually an informal error: it states a fact, not a wish.
            v = find(lambda w: w.type.startswith("VB"), S[i+1:])
            if v and classical is True and v and v.type == "VB":
                return True
            if v and classical is False:
                return True
    return False

#from __init__ import parse
#from tree import Sentence
#for str in (
#  "I wouldn't do that if I were you.", # True
#  "I wish I knew.",                    # True
#  "I propose that you be on time.",    # True
#  "It is a bad idea to be late.",      # True
#  "I will be dead."):                  # False, predictive
#    print str
#    print parse(str)
#    print subjunctive(Sentence(parse(str)))
#    print

def negated(sentence, negative=("not", "n't", "never")):
    if hasattr(sentence, "string"):
        # Sentence object => string.
        sentence = sentence.string
    S = " %s " % (sentence).strip(".?!").lower()
    for w in negative:
        if " %s " % w in S: 
            return True
    return False
        
def mood(sentence, **kwargs):
    """ Returns IMPERATIVE (command), CONDITIONAL (possibility), SUBJUNCTIVE (wish) or INDICATIVE (fact).
    """
    if imperative(sentence, **kwargs):
        return IMPERATIVE
    if conditional(sentence, **kwargs):
        return CONDITIONAL
    if subjunctive(sentence, **kwargs):
        return SUBJUNCTIVE
    else:
        return INDICATIVE

### MODALITY #######################################################################################

def d(*args):
    return dict.fromkeys(args, True)

AUXILLARY = {
      "be": ["be", "am", "m", "are", "is", "being", "was", "were" "been"],
     "can": ["can", "ca", "could"],
    "dare": ["dare", "dares", "daring", "dared"], 
      "do": ["do", "does", "doing", "did", "done"],
    "have": ["have", "ve", "has", "having", "had"], 
     "may": ["may", "might"], 
    "must": ["must"], 
    "need": ["need", "needs", "needing", "needed"],
   "ought": ["ought"], 
   "shall": ["shall", "sha"], 
    "will": ["will", "ll", "wo", "willing", "would", "d"]
}

MODIFIERS = ("fully", "highly", "most", "much", "strongly", "very")

EPISTEMIC = "epistemic" # Expresses degree of possiblity.

# -1.00 = NEGATIVE
# -0.75 = NEGATIVE, with slight doubts
# -0.50 = NEGATIVE, with doubts
# -0.25 = NEUTRAL, slightly negative
# +0.00 = NEUTRAL
# +0.25 = NEUTRAL, slightly positive
# +0.50 = POSITIVE, with doubts
# +0.75 = POSITIVE, with slight doubts
# +1.00 = POSITIVE

epistemic_MD = { # would => could => can => should => shall => will => must
    -1.00: d(),
    -0.75: d(),
    -0.50: d("would"),
    -0.25: d("could", "dare", "might"),
     0.00: d("can", "ca", "may"),
    +0.25: d("ought", "should"),
    +0.50: d("shall", "sha"),
    +0.75: d("will", "ll", "wo"),
    +1.00: d("have", "has", "must", "need"),
}

epistemic_VB = { # wish => feel => believe => seem => think => know => prove + THAT
    -1.00: d(),
    -0.75: d(),
    -0.50: d("doubt", "question"),
    -0.25: d("hope", "want", "wish"),
     0.00: d("guess", "imagine"),
    +0.25: d("appear", "feel", "hear", "rumor", "rumour", "seem", "sense", "speculate", "suspect", 
             "suppose"),
    +0.50: d("allude", "anticipate", "assume", "believe", "conjecture", "expect", "hypothesize", 
             "imply", "indicate", "infer", "postulate", "predict", "presume", "propose", 
             "suggest", "think"),
    +0.75: d("know", "look", "see", "show"),
    +1.00: d("certify", "demonstrate", "prove", "verify"),
}

epistemic_RB = { # unlikely => supposedly => maybe => probably => usually => clearly => definitely
    -1.00: d("impossibly"),
    -0.75: d("hardly"),
    -0.50: d("presumptively", "rarely", "scarcely", "seldom", "seldomly", "uncertainly", "unlikely"),
    -0.25: d("almost", "allegedly", "debatably", "nearly", "presumably", "purportedly", "reportedly", 
             "reputedly", "rumoredly", "rumouredly", "supposedly"),
     0.00: d("barely", "hypothetically", "maybe", "occasionally", "perhaps", "possibly", "putatively", 
             "sometimes", "sporadically"),
    +0.25: d("admittedly", "apparently", "arguably", "believably", "conceivably", "feasibly", 
             "hopefully", "likely", "ostensibly", "potentially", "probably", "quite", "seemingly"),
    +0.50: d("commonly", "credibly", "defendably", "defensibly", "effectively", "frequently", 
             "generally", "noticeably", "often", "plausibly", "reasonably", "regularly", 
             "relatively", "typically", "usually"),
    +0.75: d("assuredly", "certainly", "clearly", "doubtless", "evidently", "evitably", "manifestly", 
             "necessarily", "observably", "ostensively", "patently", "plainly", "positively", 
             "really", "surely", "truly", "undoubtably", "undoubtedly", "verifiably"),
    +1.00: d("absolutely", "always", "definitely", "incontestably", "indisputably", "indubitably", 
             "ineluctably", "inescapably", "inevitably", "invariably", "obviously", "unarguably", 
             "unavoidably", "undeniably", "unquestionably")
}

epistemic_JJ = {
    -1.00: d("absurd", "impossible", "prepostoreous", "ridiculous"),
    -0.75: d("inconceivable", "unthinkable"),
    -0.50: d("unlikely"),
    -0.25: d("doubtful", "uncertain", "unclear", "unsure"),
     0.00: d("possible", "unknown"),
    +0.25: d("potential", "probable", "some"),
    +0.50: d("generally", "likely", "many", "putative", "several"),
    +0.75: d("credible", "necessary", "positive", "sure"),
    +1.00: d("certain", "confirmed", "definite"),
}

epistemic_NN = {
    -1.00: d("fantasy", "fiction", "lie", "myth", "nonsense"),
    -0.75: d(),
    -0.50: d(),
    -0.25: d("chance", "speculation"),
     0.00: d("guess", "possibility"),
    +0.25: d("assumption", "expectation", "hypothesis", "notion"),
    +0.50: d("belief", "theory"),
    +0.75: d(),
    +1.00: d("fact", "truth"),
}

epistemic_CC_DT_IN = {
     0.00: d("either", "whether"),
    +0.25: d("some")
}

epistemic_phrase = {
    -1.00: d(),
    -0.75: d(),
    -0.50: d(),
    -0.25: d(),
     0.00: d("a number of", "sort of", "some cases", "some people", "in some way"),
    +0.25: d("at first blush", "at first sight", "at first glance", "many of these"),
    +0.50: d("all else being equal", "all in all", "all things considered", "for several reasons",
             "has been argued", "is considered", "said to be"),
    +0.75: d("as a matter of fact"),
    +1.00: d("without a doubt", "of course"),
}

def modality(sentence, type=EPISTEMIC):
    """ Returns the sentence's modality as a weight between -1.0 and +1.0.
        Currently, the only type implemented is EPISTEMIC.
        Epistemic modality is used to express possibility (i.e. how truthful is what is being said).
    """
    S, n, m = sentence, 0.0, 0
    if type == EPISTEMIC:
        r = s(S).rstrip(" .!")
        for k,v in epistemic_phrase.items():
            for phrase in v:
                if phrase in r:
                    n += k
                    m += 1
        for i, w in enumerate(S):
            for type, dict, weight in (
              ("MD", epistemic_MD, 2), 
              ("VB", epistemic_VB, 2), 
              ("RB", epistemic_RB, 2), 
              ("JJ", epistemic_JJ, 1),
              ("NN", epistemic_NN, 1),
              ("CC", epistemic_CC_DT_IN, 1),
              ("DT", epistemic_CC_DT_IN, 1),
              ("IN", epistemic_CC_DT_IN, 1)):
                if i < 0 and s(S[i-1]) in MODIFIERS:
                    # "likely" => weight 1, "very likely" => weight 2
                    weight += 1
                if w.type.startswith(type):
                    # likely" => score 0.25 (neutral inclining towards positive).
                    for k,v in dict.items():
                        if (w.lemma or s(w)) in v: # Prefer lemmata.
                            #print w, weight, k
                            n += weight * k
                            m += weight
                            break
    if m == 0:
        return 1.0 # No modal verbs/adverbs used, so statement must be true.
    return n / (m or 1)

#from __init__ import parse
#from tree import Sentence
#for str in (
#  "I wish it would stop raining.",
#  "It will surely stop raining soon."):
#    print str
#    print parse(str)
#    print modality(Sentence(parse(str)))
#    print

#---------------------------------------------------------------------------------------------------

# Celle, A. (2009). Hearsay adverbs and modality, in: Modality in English, Mouton.
# Allegedly, presumably, purportedly, ... are in the negative range because
# they introduce a fictious point of view by referring to an unclear source.

#---------------------------------------------------------------------------------------------------

# Tseronis, A. (2009). Qualifying standpoints. LOT Dissertation Series: 233.
# Following adverbs are not epistemic but indicate the way in which things are said.
# 1) actually, admittedly, avowedly, basically, bluntly, briefly, broadly, candidly, 
#    confidentially, factually, figuratively, frankly, generally, honestly, hypothetically, 
#    in effect, in fact, in reality, indeed, literally, metaphorically, naturally, 
#    of course, objectively, personally, really, roughly, seriously, simply, sincerely, 
#    strictly, truly, truthfully.
# 2) bizarrely, commendably, conveniently, curiously, disappointingly, fortunately, funnily, 
#    happily, hopefully, illogically, interestingly, ironically, justifiably, justly, luckily, 
#    oddly, paradoxically, preferably, regretfully, regrettably, sadly, significantly, 
#    strangely, surprisingly, tragically, unaccountably, unfortunately, unhappily unreasonably

#---------------------------------------------------------------------------------------------------

# The modality() function was tested with BioScope and Wikipedia training data from CoNLL2010 Shared Task 1.
# See for example Morante, R., Van Asch, V., Daelemans, W. (2010): 
# Memory-Based Resolution of In-Sentence Scopes of Hedge Cues
# http://www.aclweb.org/anthology/W/W10/W10-3006.pdf
# Sentences in the training corpus are labelled as "certain" or "uncertain".
# For Wikipedia sentences, 2000 "certain" and 2000 "uncertain":
# modality(sentence) > 0.5 => A 0.67 P 0.70 R 0.63 F1 0.66