#### PATTERN | EN | MOOD & MODALITY ################################################################
# -*- coding: utf-8 -*-
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
# Functions take Sentence objects, see pattern.text.tree.Sentence and pattern.text.parsetree().

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
    if not (hasattr(S, "words") and hasattr(S, "parse_token")):
        raise TypeError("%s object is not a parsed Sentence" % repr(S.__class__.__name__))
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

#from __init__ import parse, Sentence
#
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
    if not (hasattr(S, "words") and hasattr(S, "parse_token")):
        raise TypeError("%s object is not a parsed Sentence" % repr(S.__class__.__name__))
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
    
#from __init__ import parse, Sentence
#
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
    if not (hasattr(S, "words") and hasattr(S, "parse_token")):
        raise TypeError("%s object is not a parsed Sentence" % repr(S.__class__.__name__))
    if question(S):
        return False
    for i, w in enumerate(S):
        b = False
        if w.type.startswith("VB"):
            if s(w).startswith("wish"):
                # "I wish I knew."
                return True
            if s(w) == "hope" and i > 0 and s(S[i-1]) in ("i", "we"):
                # "I hope ..."
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

#from __init__ import parse, Sentence
#
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
    if isinstance(sentence, basestring):
        try:
            # A Sentence is expected but a string given.
            # Attempt to parse the string on-the-fly.
            from pattern.en import parse, Sentence
            sentence = Sentence(parse(sentence))
        except ImportError:
            pass
    if imperative(sentence, **kwargs):
        return IMPERATIVE
    if conditional(sentence, **kwargs):
        return CONDITIONAL
    if subjunctive(sentence, **kwargs):
        return SUBJUNCTIVE
    else:
        return INDICATIVE

### MODALITY #######################################################################################
# Functions take Sentence objects, see pattern.text.tree.Sentence and pattern.text.parsetree().

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
    +0.75: d("will", "'ll", "wo"),
    +1.00: d("have", "has", "must", "need"),
}

epistemic_VB = { # wish => feel => believe => seem => think => know => prove + THAT
    -1.00: d(),
    -0.75: d(),
    -0.50: d("dispute", "disputed", "doubt", "question"),
    -0.25: d("hope", "want", "wish"),
     0.00: d("guess", "imagine", "seek"),
    +0.25: d("appear", "bet", "feel", "hear", "rumor", "rumour", "say", "said", "seem", "seemed",
             "sense", "speculate", "suspect", "suppose", "wager"),
    +0.50: d("allude", "anticipate", "assume", "claim", "claimed", "believe", "believed", 
             "conjecture", "consider", "considered", "decide", "expect", "find", "found", 
             "hypothesize", "imply", "indicate", "infer", "postulate", "predict", "presume", 
             "propose", "report", "reported", "suggest", "suggested", "tend", 
             "think", "thought"),
    +0.75: d("know", "known", "look", "see", "show", "shown"),
    +1.00: d("certify", "demonstrate", "prove", "proven", "verify"),
}

epistemic_RB = { # unlikely => supposedly => maybe => probably => usually => clearly => definitely
    -1.00: d("impossibly"),
    -0.75: d("hardly"),
    -0.50: d("presumptively", "rarely", "scarcely", "seldomly", "uncertainly", "unlikely"),
    -0.25: d("almost", "allegedly", "debatably", "nearly", "presumably", "purportedly", "reportedly", 
             "reputedly", "rumoredly", "rumouredly", "supposedly"),
     0.00: d("barely", "hypothetically", "maybe", "occasionally", "perhaps", "possibly", "putatively", 
             "sometimes", "sporadically", "traditionally", "widely"),
    +0.25: d("admittedly", "apparently", "arguably", "believably", "conceivably", "feasibly", "fairly", 
             "hopefully", "likely", "ostensibly", "potentially", "probably", "quite", "seemingly"),
    +0.50: d("commonly", "credibly", "defendably", "defensibly", "effectively", "frequently", 
             "generally", "largely", "mostly", "normally", "noticeably", "often", "plausibly", 
             "reasonably", "regularly", "relatively", "typically", "usually"),
    +0.75: d("assuredly", "certainly", "clearly", "doubtless", "evidently", "evitably", "manifestly", 
             "necessarily", "nevertheless", "observably", "ostensively", "patently", "plainly", 
             "positively", "really", "surely", "truly", "undoubtably", "undoubtedly", "verifiably"),
    +1.00: d("absolutely", "always", "definitely", "incontestably", "indisputably", "indubitably", 
             "ineluctably", "inescapably", "inevitably", "invariably", "obviously", "unarguably", 
             "unavoidably", "undeniably", "unquestionably")
}

epistemic_JJ = {
    -1.00: d("absurd", "prepostoreous", "ridiculous"),
    -0.75: d("inconceivable", "unthinkable"),
    -0.50: d("misleading", "scant", "unlikely", "unreliable"),
    -0.25: d("customer-centric", "doubtful", "ever", "ill-defined, ""inadequate", "late", 
             "uncertain", "unclear", "unrealistic", "unspecified", "unsure", "wild"),
     0.00: d("dynamic", "possible", "unknown"),
    +0.25: d("according", "creative", "likely", "local", "innovative", "interesting", 
             "potential", "probable", "several", "some", "talented", "viable"),
    +0.50: d("certain", "generally", "many", "notable", "numerous", "performance-oriented", 
             "promising", "putative", "well-known"),
    +0.75: d("concrete", "credible", "famous", "important", "major", "necessary", "original", 
             "positive", "significant", "real", "robust", "substantial", "sure"),
    +1.00: d("confirmed", "definite", "prime", "undisputable"),
}

epistemic_NN = {
    -1.00: d("fantasy", "fiction", "lie", "myth", "nonsense"),
    -0.75: d("controversy"),
    -0.50: d("criticism", "debate", "doubt"),
    -0.25: d("belief", "chance", "faith", "luck", "perception", "speculation"),
     0.00: d("challenge", "guess", "feeling", "hunch", "opinion", "possibility", "question"),
    +0.25: d("assumption", "expectation", "hypothesis", "notion", "others", "team"),
    +0.50: d("example", "proces", "theory"),
    +0.75: d("conclusion", "data", "evidence", "majority", "proof", "symptom", "symptoms"),
    +1.00: d("fact", "truth", "power"),
}

epistemic_CC_DT_IN = {
     0.00: d("either", "whether"),
    +0.25: d("however", "some"),
    +1.00: d("despite")
}

epistemic_PRP = {
    +0.25: d("I", "my"),
    +0.50: d("our"),
    +0.75: d("we")
}

epistemic_weaseling = {
    -0.75: d("popular belief"),
    -0.50: d("but that", "but this", "have sought", "might have", "seems to"),
    -0.25: d("may also", "may be", "may have", "may have been", "some have", "sort of"),
    +0.00: d("been argued", "believed to", "considered to", "claimed to", "is considered", "is possible", 
             "overall solutions", "regarded as", "said to"),
    +0.25: d("a number of", "in some", "one of", "some of", 
             "many modern", "many people", "most people", "some people", "some cases", "some studies", 
             "scientists", "researchers"),
    +0.50: d("in several", "is likely", "many of", "many other", "of many", "of the most", "such as",
             "several reasons", "several studies", "several universities", "wide range"),
    +0.75: d("almost always", "and many", "and some", "around the world", "by many", "in many", "in order to", 
             "most likely"),
    +1.00: d("i.e.", "'s most", "of course", "There are", "without doubt"),
}

def modality(sentence, type=EPISTEMIC):
    """ Returns the sentence's modality as a weight between -1.0 and +1.0.
        Currently, the only type implemented is EPISTEMIC.
        Epistemic modality is used to express possibility (i.e. how truthful is what is being said).
    """
    if isinstance(sentence, basestring):
        try:
            # A Sentence is expected but a string given.
            # Attempt to parse the string on-the-fly.
            from pattern.en import parse, Sentence
            sentence = Sentence(parse(sentence))
        except ImportError:
            pass
    S, n, m = sentence, 0.0, 0
    if not (hasattr(S, "words") and hasattr(S, "parse_token")):
        raise TypeError("%s object is not a parsed Sentence" % repr(S.__class__.__name__))
    if type == EPISTEMIC:
        r = S.string.rstrip(" .!")
        for k, v in epistemic_weaseling.items():
            for phrase in v:
                if phrase in r:
                    n += k
                    m += 2
        for i, w in enumerate(S.words):
            for type, dict, weight in (
              (  "MD", epistemic_MD, 4), 
              (  "VB", epistemic_VB, 2), 
              (  "RB", epistemic_RB, 2), 
              (  "JJ", epistemic_JJ, 1),
              (  "NN", epistemic_NN, 1),
              (  "CC", epistemic_CC_DT_IN, 1),
              (  "DT", epistemic_CC_DT_IN, 1),
              (  "IN", epistemic_CC_DT_IN, 1),
              ("PRP" , epistemic_PRP, 1),
              ("PRP$", epistemic_PRP, 1),
              ( "WP" , epistemic_PRP, 1)):
                # "likely" => weight 1, "very likely" => weight 2
                if i > 0 and s(S[i-1]) in MODIFIERS:
                    weight += 1
                # likely" => score 0.25 (neutral inclining towards positive).
                if w.type and w.type.startswith(type):
                    for k, v in dict.items():
                        # Prefer lemmata.
                        if (w.lemma or s(w)) in v: 
                            # Reverse score for negated terms.
                            if i > 0 and s(S[i-1]) in ("not", "n't", "never", "without"):
                                k = -k * 0.5
                            n += weight * k
                            m += weight
                            break
            # Numbers, citations, explanations make the sentence more factual.
            if w.type in ("CD", "\"", "'", ":", "("):
                n += 0.75
                m += 1
    if m == 0:
        return 1.0 # No modal verbs/adverbs used, so statement must be true.
    return max(-1.0, min(n / (m or 1), +1.0))

def uncertain(sentence, threshold=0.5):
    return modality(sentence) <= threshold

#from __init__ import parse, Sentence
#
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
# modality(sentence) > 0.5 => A 0.70 P 0.73 R 0.64 F1 0.68