#### PATTERN | EN | RULE-BASED SHALLOW PARSER ########################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

######################################################################################################
# Fast tagger-chunker using regular expressions.

import re

#### TOKENIZER #######################################################################################

token = re.compile(r"(\S+)\s")

# Handle common contractions, 
# we don't want the parser to break on something simple like "I'm eating".
replacements = {
     "'m" : " 'm", 
    "'re" : " 're", 
    "'ve" : " 've", 
    "'ll" : " 'll", 
     "'s" : " 's",
    "n't" : " n't"
}

# Handle common abbreviations.
abrreviations = dict.fromkeys([
    "a.m.", "cf.", "e.g.", "ex.", "etc.", "fig.", "i.e.", "Mr.", "p.m."
], True)
a1 = re.compile("^[A-Za-z]\.$")                                    # single letter, "T. De Smedt"
a2 = re.compile("^([A-Za-z]\.)+$")                                 # alternating letters, "U.S."
a3 = re.compile("^[A-Z]["+"|".join("bcdfghjklmnpqrstvwxz")+"]+.$") # capital followed by consonants, "Mr."

# Handle common word punctuation:
punctuation = (
    ("(","[","\""), 
    (":",";",",","!","?","]",")","\"", "'")
)

def tokenize(string):
    """ Returns a list of sentences. Each sentence is a space-separated string of tokens (words).
        Aside from a few common cases ("etc.") no attempt is made to disambiguate abbreviations
        from sentence periods.
    """
    for a,b in replacements.items():
        string = re.sub(a, b, string)
    # Collapse whitespace.
    string = re.sub(r"\s+", " ", string)
    tokens = []
    for t in token.findall(string+" "):
        if len(t) > 0:
            tail = []
            # Split leading punctuation.
            if t.startswith(punctuation[0]):
                tokens.append(t[0]); t=t[1:]
            if t.startswith("'") and not t in replacements:
                tokens.append(t[0]); t=t[1:]
            for i in range(2):
                # Split trailing punctuation.
                if t.endswith(punctuation[1]):
                    tail.append(t[-1]); t=t[:-1]
                # Split ellipsis before checking for period.
                if t.endswith("..."):
                    tail.append("..."); t=t[:-3]
                # Split period (if not an abbreviation).
                if t.endswith(".") and not t in abrreviations and \
                   a1.match(t) is None and \
                   a2.match(t) is None and \
                   a3.match(t) is None:
                    tail.append(t[-1]); t=t[:-1]
            tokens.append(t)
            tokens.extend(reversed(tail))
    sentences = [[]]
    for t in tokens:
        sentences[-1].append(t)
        # A period token always breaks the sentence.
        if t == ".": sentences.append([])
    return [" ".join(s) for s in sentences if len(s) > 0]

# MBSP's tokenizer.py is pretty fast and a lot more robust so we could try to load it.
# You could also do parser.tokenize = my_module.tokenize
#try: from MBSP.tokenizer import split as tokenize
#except:
#    pass

#### TAGGER ##########################################################################################

#--- BRILL TAGGER ------------------------------------------------------------------------------------
# Based on Jason Wiener's implementation of a rule-based part-of-speech Brill tagger.

# Original Copyright (C) Mark Watson.  All rights reserved.
# Python port by Jason Wiener (http://www.jasonwiener.com)
# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
# KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
# PARTICULAR PURPOSE.

import os
try: 
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""
    
class Lexicon:
    
    def __init__(self):
        self._words = None
    
    def load(self):
        # Brill's lexicon is a list of common tokens and their part-of-speech tag.
        # It takes a while to load but this happens only once when parse() is called.
        # Create a dictionary from the entries:
        self._words = open(os.path.join(MODULE, "Brill_lexicon.txt")).read().splitlines()
        self._words = dict([x.split(" ") for x in self._words])
        self["crunchy"] = "JJ" # The lexicon can be updated easily.
    
    def get(self, word, default=None):
        return word in self and self._words[word] or default
    
    def __contains__(self, word):
        try:
            return word in self._words
        except:
            self.load()
            return word in self._words
    
    def __getitem__(self, word):
        if self._words is None: 
            self.load()
        return self._words[word]      
    
    def __setitem__(self, word, pos):
        if self._words is None: 
            self.load()
        self._words[word] = pos
        
lexicon = Lexicon()

def find_tags(tokens, default="NN", light=False):
    """ Returns a list of [token, tag]-items for the given list of tokens.
        For example: 
        ['That', 'is', 'interesting', '.'] => 
        [['That', 'DT'], ['is', 'VBZ'], ['interesting', 'JJ'], ['.', '.']]
        With light=True uses Brill's lexical and contextual rules to improve token tags.
        With light=False uses a faster set of arbitrary rules (Jason Wiener's rules).
    """
    tagged = []
    for token in tokens:
        # By default, all tokens are tagged NN unless we find an entry in the lexicon.
        # Words that start with a capital letter are tagged with NNP by default.
        # Words that are not in the lexicon are then improved with lexical rules.
        tagged.append([token, lexicon.get(token, lexicon.get(token.lower(), None))])
    f = light and apply_default_rules or apply_lexical_rules
    for i, (token, tag) in enumerate(tagged):
        if tag == None:
            if len(token) > 0 and token[0] == token[0].upper() and token[0].isalpha():
                tagged[i] = [token, "NNP"]
            else:
                tagged[i] = [token, default]
                tagged[i] = f(tagged[i],
                    previous = i>0 and tagged[i-1] or (None, None), 
                        next = i<len(tagged)-1 and tagged[i+1] or (None, None))
    if not light:
        apply_contextual_rules(tagged)
    return tagged

def apply_default_rules(token, previous=(None,None), next=(None,None)):
    """ Returns the token with its tag updated according to a few simple rules.
        Jason Wiener's rules are less accurate than Brill's lexical rules, but they are faster (5-10x).
    """
    # By comparison, WordNet has 12401 adjectives not in the Brill lexicon.
    # Brill's lexical rules corrected 11961 of them, in 1.71 seconds.
    # Jason Wiener's rules corrected 9948, in 0.19 seconds.
    #              errors   fixed: Brill   Wiener
    #      verbs    26197          15983    13525
    # adjectives    12401          11986     9948
    #
    # Rule 1: convert a common noun ending with "ing" to a present participle verb (i.e., a gerund).
    # Rule 2: convert any type to adverb if it ends in "ly".
    # Rule 3: if a word has been categorized as a common noun and it ends with "s",
    #         then set its type to plural common noun (NNS)
    # Rule 4: convert a noun to a number (CD) if "." appears in the word.
    # Rule 5: convert a common noun (NN or NNS) to a adjective if it ends with "al", "ient", "ish", "less"
    #         or if there is a hyphen ("-") in the word.
    # Rule 6: convert a noun to a past participle if word ends with "ed".
    # Rule 7: DT, {VBD | VBP} --> DT, NN
    # Rule 8: convert a noun to a verb if the preceeding word is "would".
    word, pos = token
    if pos.startswith("NN") and word.endswith("ing"):
        pos = "VBG"
    elif word.endswith("ly"):
        pos = "RB"
    elif pos == "NN" and word.endswith("s") and not word.endswith("ss"):
        pos = "NNS"
    elif pos.startswith("NN") and word.isdigit():
        pos = "CD"
    elif pos.startswith("NN") and word[:1].isdigit() and word.replace(".","").isdigit():
        pos = "CD"
    elif pos.startswith("NN") and word.endswith(("al","ient","ish","less")) or "-" in word:
        pos = "JJ"
    elif pos.startswith("NN") and word.endswith("ed"):
        pos = "VBN"
    elif i > 0 and previous[1] == "DT" and pos in ("VBD", "VBP", "VB"):
        pos = "NN"
    elif i > 0 and pos.startswith("NN") and previous[0] == "would":
        pos = "VB"
    return [word, pos]

#--- BRILL RULES -------------------------------------------------------------------------------------

lexical_commands = ["char", "hassuf", "deletesuf", "addsuf", "haspref", "deletepref", "addpref", "goodleft", "goodright"]
lexical_commands.extend(["f"+x for x in lexical_commands])

# Brill's lexical rules.
# An entry looks like: ('fhassuf', ['NN', 's', 'fhassuf', '1', 'NNS', 'x']).
# The first item is the lookup command.
# If it is prefixed with an "f", it means that the token needs to have the first given tag (NN).
# In this case, if the NN-word ends with an "s", it is tagged as NNS.
lexical_rules = open(os.path.join(MODULE, "Brill_lexical_rules.txt")).read()
lexical_rules = lexical_rules.strip().split("\n")
for i, rule in enumerate(lexical_rules):
    rule = rule.split()
    for cmd in lexical_commands:
        if cmd in rule:
            lexical_rules[i] = (cmd, rule)
            break
            
def apply_lexical_rules(token, previous=(None,None), next=(None,None)):
    """ Applies the lexical rules to the given token.
        A token is a [word,tag]-item whose tag might change if it matches a rule.
        Rules are lexically based on word characters, prefixes and suffixes.
    """
    word, pos = token[0], token[1]
    if word[:1].isdigit() and word.replace(".","").isdigit():
        return [word, "CD"]
    for cmd, rule in lexical_rules:
        pos = rule[-2]
        x = rule[0]
        if cmd.startswith("f"): 
            # Word must be tagged as the f-rule states.
            cmd = cmd[1:]
            if token[1] != rule[0]: continue
            x = rule[1]
        if (cmd == "char"       and x in word) \
        or (cmd == "hassuf"     and word.endswith(x)) \
        or (cmd == "deletesuf"  and word.endswith(x) and word[:-len(x)] in lexicon) \
        or (cmd == "haspref"    and word.startswith(x)) \
        or (cmd == "deletepref" and word.startswith(x) and word[len(x):] in lexicon) \
        or (cmd == "addsuf"     and word+x in lexicon) \
        or (cmd == "addpref"    and x+word in lexicon) \
        or (cmd == "goodleft"   and x == previous[0]) \
        or (cmd == "goodright"  and x == next[0]):
            return [word, pos]
        else:
            return token

# Brill's contextual rules.
# An entry looks like: ('PREVTAG', ['VBD', 'VB', 'PREVTAG', 'TO']).
# The first item is the lookup command.
# The example rule reads like:
# "If the previous word is tagged TO, change this word's tag from VBD to VB (if it is VBD)".
contextual_rules = open(os.path.join(MODULE, "Brill_contextual_rules.txt")).read()
contextual_rules = contextual_rules.strip().split("\n")
for i, rule in enumerate(contextual_rules):
    rule = rule.split()
    cmd = rule[2]
    contextual_rules[i] = (cmd, rule)

def apply_contextual_rules(tokens):
    """ Applies the contextual rules to the given list of tokens. 
        Each token is a [word,tag]-item whose tag might change if it matches a rule.
        Rules are contextually based on the token's position in the sentence.
    """
    b = [(None,"STAART")] * 3 # Add empty tokens so we can scan ahead and behind.
    T = b + tokens + b
    for i, token in enumerate(T):
        for cmd, rule in contextual_rules:
            # If the word is tagged differently than required by the rule, skip it.
            if token[1] != rule[0]: 
                continue
            # Never allow rules to tag "be" anything but infinitive.
            if token[0] == "be" and token[1] == "VB":
                continue
            # A rule involves scanning the previous/next word or tag, 
            # and all combinations thereof.
            x = rule[3]
            if (cmd == "PREVTAG"        and x == T[i-1][1]) \
            or (cmd == "NEXTTAG"        and x == T[i+1][1]) \
            or (cmd == "PREV1OR2TAG"    and x in (T[i-1][1], T[i-2][1])) \
            or (cmd == "NEXT1OR2TAG"    and x in (T[i+1][1], T[i+2][1])) \
            or (cmd == "PREV1OR2OR3TAG" and x in (T[i-1][1], T[i-2][1], T[i-3][1])) \
            or (cmd == "NEXT1OR2OR3TAG" and x in (T[i+1][1], T[i+2][1], T[i+3][1])) \
            or (cmd == "SURROUNDTAG"    and x == T[i-1][1] and rule[4] == T[i+1][1]) \
            or (cmd == "PREVBIGRAM"     and x == T[i-2][1] and rule[4] == T[i-1][1]) \
            or (cmd == "NEXTBIGRAM"     and x == T[i+1][1] and rule[4] == T[i+2][1]) \
            or (cmd == "PREV2TAG"       and x == T[i-2][1]) \
            or (cmd == "NEXT2TAG"       and x == T[i+2][1]) \
            or (cmd == "CURWD"          and x == T[i][0]) \
            or (cmd == "PREVWD"         and x == T[i-1][0]) \
            or (cmd == "NEXTWD"         and x == T[i+1][0]) \
            or (cmd == "PREV1OR2WD"     and x in (T[i-1][0], T[i-2][0])) \
            or (cmd == "NEXT1OR2WD"     and x in (T[i+1][0], T[i+2][0])) \
            or (cmd == "WDPREVTAG"      and x == T[i][0] and rule[4] == T[i-1][1]) \
            or (cmd == "WDNEXTTAG"      and x == T[i][0] and rule[4] == T[i+1][1]):
                tokens[i-len(b)] = [tokens[i-len(b)][0], rule[1]]

#### CHUNKER #########################################################################################

SEPARATOR = "/"
VB = "VB|VBD|VBG|VBN|VBP|VBZ"
JJ = "JJ|JJR|JJS"
RB = "[^W]RB|RBR|RBS"
NN = "NN|NNS|NNP|NNPS|PRP|PRP\$"
rules = [
    ("NP",   re.compile(r"(("+NN+")/)*((DT|CD|CC)/)*(("+RB+"|"+JJ+")/)*(("+NN+")/)+")),
    ("VP",   re.compile(r"(((MD|"+RB+")/)*(("+VB+")/)+)+")),
    ("VP",   re.compile(r"((MD)/)")),
    ("PP",   re.compile(r"((IN|TO)/)")),
    ("ADJP", re.compile(r"((CC|"+RB+"|"+JJ+")/)*(("+JJ+")/)+")),
    ("ADVP", re.compile(r"(("+RB+"|WRB)/)+")),
]
rules.insert(1, rules.pop(3)) # Handle ADJP before VP (RB prefers next ADJP over previous VP).

def find_chunks(tagged, iob=True):
    """ The input is a list of (token, tag)-tuples.
        The output is a list of (token, tag, chunk)-tuples.
        For example:
        The/DT nice/JJ fish/NN is/VBZ dead/JJ ./. => 
        The/DT/B-NP nice/JJ/I-NP fish/NN/I-NP is/VBZ/B-VP dead/JJ/B-ADJP ././O
    """
    chunked = [x for x in tagged]
    tags = "".join("%s%s"%(tag,SEPARATOR) for token, tag in tagged)
    for tag, rule in rules:
        for m in rule.finditer(tags):
            # Find the start of the pattern inside the tag-string.
            # The number of preceding separators = the number of preceding tokens.
            i = m.start()
            j = tags[:i].count(SEPARATOR)
            n = m.group(0).count(SEPARATOR)
            for k in range(j, j+n):
                # Don't overwrite tokens already chunked.
                if len(chunked[k]) < 3:
                    if k == j and chunked[k][1] == "CC":
                        # A CC-tag can never be start of a chunk.
                        j += 1
                    elif k == j:
                        # Mark the start of a chunk with the "B"-tag.
                        chunked[k].append("B-"+tag)
                    else:
                        chunked[k].append("I-"+tag)
    # Chinks are tokens outside of a chunk, we add the O-tag.
    for chink in filter(lambda x: len(x)<3, chunked):
        chink.append("O")
    return chunked

#### RELATION FINDER #################################################################################
# Naive approach.

BE = dict.fromkeys(("be", "am", "are", "is", "being", "was", "were", "been"), True)
GO = dict.fromkeys(("go", "goes", "going", "went"), True)

def find_relations(chunked):
    """ The input is a list of (token, tag, chunk)-tuples.
        The output is a list of (token, tag, chunk, relation)-tuples.
        A noun phrase preceding a verb phrase is perceived as sentence subject.
        A noun phrase following a verb phrase is perceived as sentence object.
    """
    tag = lambda token: token[2].split("-")[-1]
    # Group consecutive tokens with the same chunk-tag.
    # Tokens in a chunk that are not part of a relation just get the O-tag.
    chunks = []
    for token in chunked:
        if len(chunks) == 0 \
        or token[2].startswith("B-") \
        or tag(token) != tag(chunks[-1][-1]):
            chunks.append([])
        chunks[-1].append(token+["O"])
    # If a VP is preceded by a NP, the NP is tagged as NP-SBJ-(id).
    # If a VP is followed by a NP, the NP is tagged as NP-OBJ-(id).
    id = 0
    for i, chunk in enumerate(chunks):
        if tag(chunk[-1]) == "VP" and i > 0 and tag(chunks[i-1][-1]) == "NP":
            if chunk[-1][-1] == "O":
                id += 1
            for token in chunk: 
                token[-1] = "VP-"+str(id)
            for token in chunks[i-1]: 
                token[-1] += "*NP-SBJ-"+str(id)
                token[-1] = token[-1].lstrip("O-*")
        if tag(chunk[-1]) == "VP" and i < len(chunks)-1 and tag(chunks[i+1][-1]) == "NP":
            if chunk[-1][-1] == "O":
                id += 1
            for token in chunk: 
                token[-1] = "VP-"+str(id)
            for token in chunks[i+1]: 
                token[-1] = "*NP-OBJ-"+str(id)
                token[-1] = token[-1].lstrip("O-*")
    # This is more a proof-of-concept than useful in practice:
    # PP-LOC = be + in|at + the|my
    # PP-DIR = go + to|towards + the|my
    for i, chunk in enumerate(chunks):
        if 0 < i < len(chunks)-1 and len(chunk)==1 and chunk[-1][-1] == "O":
            t0, t1, t2 = chunks[i-1][-1], chunks[i][0], chunks[i+1][0] # previous / current / next
            if tag(t1) == "PP" and t2[1] in ("DT", "PRP$"):
                if t0[0] in BE and t1[0] in ("in", "at")      : t1[-1] = "PP-LOC"
                if t0[0] in GO and t1[0] in ("to", "towards") : t1[-1] = "PP-DIR"
    related = []; [related.extend(chunk) for chunk in chunks]
    return related

#### PNP FINDER ######################################################################################

def find_prepositions(chunked):
    """ The input is a list of (token, tag, chunk)-tuples.
        The output is a list of (token, tag, chunk, preposition)-tuples.
        PP-chunks followed by NP-chunks make up a PNP-chunk.
    """
    n = len(chunked) > 0 and len(chunked[0]) or 0
    for i, chunk in enumerate(chunked):
        if chunk[2].endswith("PP") and i<len(chunked)-1 and chunked[i+1][2].endswith("NP"):
            chunk.append("B-PNP")
            for ch in chunked[i+1:]:
                if not ch[2].endswith("NP"): 
                    break
                ch.append("I-PNP")
    # Tokens that are not part of a preposition just get the O-tag.
    for chunk in filter(lambda x: len(x) < n+1, chunked):
        chunk.append("O")
    return chunked

#### LEMMATIZER ######################################################################################
# Word lemmas using singularization and verb conjugation from the inflect module.

try: from pattern.en.inflect import singularize, conjugate
except:
    try: 
        import os, sys; sys.path.append(os.path.join(MODULE, ".."))
        from inflect import singularize, conjugate
    except:
        singularize = lambda w: w
        conjugate = lambda w,t: w

def lemma(word, pos="NN"):
    """ Returns the lemma of the given word, e.g. horses/NNS => horse, am/VBP => be.
        Words must be lowercase.
    """
    if pos == "NNS":
        return singularize(word)
    if pos.startswith("VB"):
        return conjugate(word, "infinitive") or word
    return word
	
def find_lemmata(tagged):
    """ Appends the lemma to the given (token, tag)-tuple.
    """
    for token in tagged:
        token.append(lemma(token[0].lower(), pos=len(token)>1 and token[1] or None))
    return tagged

#### PARSER ##########################################################################################

_tokenize = tokenize

def parse(s, tokenize=True, tags=True, chunks=True, relations=False, lemmata=False, encoding="utf-8", default="NN", light=False):
    """ Takes a string (sentences) and returns a tagged Unicode string. 
        Sentences in the output are separated by newlines.
    """
    if isinstance(s, str):
        s = s.decode(encoding)
    if tokenize:
        s = _tokenize(s)
        s = [s.split(" ") for s in s]
    for i in range(len(s)):
        if tags or chunks or prepositions or lemmata:
            s[i] = find_tags(s[i], default, light)
        if chunks or relations:
            s[i] = find_chunks(s[i])
        if chunks or relations:
            s[i] = find_prepositions(s[i])
        if relations:
            s[i] = find_relations(s[i])
        if lemmata:
            s[i] = find_lemmata(s[i])
    # Include the format of a token in the parsed output string.
    # This allows a Sentence (see tree.py) to figure out the order of the tags.
    format = ["word"]
    if tags      : format.append("part-of-speech")
    if chunks    : format.extend(("chunk", "preposition"))
    if relations : format.append("relation")
    if lemmata   : format.append("lemma")
    # Collapse the output.
    # Sentences are separated by newlines, tokens by spaces, tags by slashes.
    # Slashes in words are encoded with &slash;
    for i in range(len(s)):
        for j in range(len(s[i])):
            s[i][j][0] = s[i][j][0].replace("/", "&slash;")
            s[i][j] = "/".join(s[i][j])
        s[i] = " ".join(s[i])
    s = "\n".join(s)
    s = TaggedString(s, tags=format)
    return s

#--- TAGGED STRING -----------------------------------------------------------------------------------
# The parse() command returns a unicode string with an extra "tags" attribute.
# The Sentence tree object uses this attribute to determine the token format.
# The TaggedString class emulates the TokenString class in the MBSP module,
# which has additional functionality besides a "tags" attribute.

TOKENS = "tokens"

class TaggedString(unicode):
    
    def __new__(self, string, tags=["word"]):
        if isinstance(string, unicode) and hasattr(string, "tags"): 
            tags = string.tags
        s = unicode.__new__(self, string)
        s.tags = list(tags)
        return s
    
    def split(self, sep=TOKENS):
        """ Returns a list of sentences, where each sentence is a list of tokens,
            where each token is a list of word + tags.
        """
        if sep != TOKENS:
            return unicode.split(self, sep)
        return [[token.split("/") for token in s.split(" ")] for s in unicode.split(self, "\n")]

def tag(s, tokenize=True, encoding="utf-8", default="NN", light=False):
    """ Returns a list of (token,tag)-tuples from the given string.
    """
    tags = []
    for sentence in parse(s, tokenize, True, False).split():
        for token in sentence:
            tags.append((token[0], token[1]))
    return tags

#### COMMAND LINE ####################################################################################
# From the folder that contains the "pattern" folder:
# python -m pattern.en.parser xml -s "Hello, my name is Dr. Sbaitso. Nice to meet you." -OTCLI

def main():
    import optparse
    import codecs
    p = optparse.OptionParser()
    p.add_option("-f", "--file", dest="file", action="store", help="text file to parse", metavar="FILE")
    p.add_option("-s", "--string", dest="string", action="store", help="text string to parse", metavar="STRING")
    p.add_option("-O", "--tokenize", dest="tokenize", action="store_true", help="tokenize the input")
    p.add_option("-T", "--tags", dest="tags", action="store_true", help="parse part-of-speech tags")
    p.add_option("-C", "--chunks", dest="chunks", action="store_true", help="parse chunk tags")
    p.add_option("-R", "--relations", dest="relations", action="store_true", help="find verb/predicate relations")
    p.add_option("-L", "--lemmata", dest="lemmata", action="store_true", help="find word lemmata")
    p.add_option("-I", "--light", dest="light", action="store_true", help="disable contextual rules")
    p.add_option("-e", "--encoding", dest="encoding", action="store_true", default="utf-8", help="character encoding")
    p.add_option("-v", "--version", dest="version", action="store_true", help="version info")
    o, arguments = p.parse_args()
    # Version info.
    if o.version:
        from pattern import __version__
        print __version__
    # Either a text file (-f) or a text string (-s) must be supplied.
    s = o.file and codecs.open(o.file, "r", o.encoding).read() or o.string
    # The given text can be parsed in two modes: 
    # - implicit: parse everything (tokenize, tag/chunk, find relations, lemmatize).
    # - explicit: define what to parse manually.
    if s:
        explicit = False
        for option in [o.tokenize, o.tags, o.chunks, o.relations, o.lemmata]:
            if option is not None: explicit=True; break
        if not explicit:
            a = {"encoding": o.encoding,
                    "light": o.light     or False}
        else:
            a = {"tokenize": o.tokenize  or False,
                     "tags": o.tags      or False,
                   "chunks": o.chunks    or False,
                "relations": o.relations or False,
                  "lemmata": o.lemmata   or False,
                    "light": o.light     or False,
                 "encoding": o.encoding }
        s = parse(s, **a)
        # The output can be either slash-formatted string or XML.
        if "xml" in arguments:
            from pattern.en.parser.tree import Text
            s = Text(s, s.tags).xml
        print s

if __name__ == "__main__":
    main()