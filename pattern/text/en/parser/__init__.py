#### PATTERN | EN | RULE-BASED SHALLOW PARSER ######################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Fast tagger-chunker using regular expressions.

import re
import os

try: 
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

# Make pattern.en.parser.brill available from the command line:
import sys; sys.path.append(MODULE)

from brill import Lexicon

#### TOKENIZER #####################################################################################

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
ABBREVIATIONS = abbreviations = dict.fromkeys([
    "a.m.", "cf.", "e.g.", "ex.", "etc.", "fig.", "i.e.", "Mr.", "p.m.", "vs.",
], True)
a1 = re.compile("^[A-Za-z]\.$")                                    # single letter, "T. De Smedt"
a2 = re.compile("^([A-Za-z]\.)+$")                                 # alternating letters, "U.S."
a3 = re.compile("^[A-Z]["+"|".join("bcdfghjklmnpqrstvwxz")+"]+.$") # capital followed by consonants, "Mr."

# Handle common word punctuation:
PUNCTUATION = \
punctuation = tuple([ch for ch in ",;:!?()[]{}`''\"@#$^&*+-|=~_"])

def tokenize(string, punctuation=PUNCTUATION, abbreviations=abbreviations, replace=replacements):
    """ Returns a list of sentences. Each sentence is a space-separated string of tokens (words).
        Handles common cases ("etc.") of abbreviations.
    """
    for a,b in replace.items():
        string = re.sub(a, b, string)
    # Collapse whitespace.
    string = re.sub(r"\s+", " ", string)
    tokens = []
    for t in token.findall(string+" "):
        if len(t) > 0:
            tail = []
            while t.startswith(punctuation) and not t in replace:
                # Split leading punctuation.
                if t.startswith(punctuation):
                    tokens.append(t[0]); t=t[1:]
            while t.endswith(punctuation+(".",)):
                # Split trailing punctuation.
                if t.endswith(punctuation):
                    tail.append(t[-1]); t=t[:-1]
                # Split ellipsis before checking for period.
                if t.endswith("..."):
                    tail.append("..."); t=t[:-3].rstrip(".")
                # Split period (if not an abbreviation).
                if t.endswith("."):
                    if t in abbreviations or \
                      a1.match(t) is not None or \
                      a2.match(t) is not None or \
                      a3.match(t) is not None:
                        break
                    else:
                        tail.append(t[-1]); t=t[:-1]
            if t != "":
                tokens.append(t)
            tokens.extend(reversed(tail))
    sentences, i, j = [[]], 0, 0
    while j < len(tokens):
        # A period token always breaks the sentence.
        if tokens[j] in ("...",".","!","?"):
            # But it might have a parenthesis trailing behind it.
            while j < len(tokens) and tokens[j] in ("...",".","!","?",")","'","\""): j+=1
            sentences[-1].extend(tokens[i:j]);
            sentences.append([])
            i = j
        j += 1
    sentences[-1].extend(tokens[i:j]);
    return [" ".join(s) for s in sentences if len(s) > 0]

# MBSP's tokenizer.py is pretty fast and a lot more robust so we could try to load it.
# You could also do parser.tokenize = my_module.tokenize
#try: from MBSP.tokenizer import split as tokenize
#except:
#    pass

#### TAGGER ########################################################################################

#--- BRILL TAGGER ----------------------------------------------------------------------------------

LEXICON = lexicon = Lexicon() # Lazy dictionary based on Brill_lexicon.txt.

def find_tags(tokens, default="NN", light=False, lexicon=LEXICON, language="en", map=None):
    """ Returns a list of [token, tag]-items for the given list of tokens.
        For example: 
         ['That', 'is', 'interesting', '.'] => 
         [['That', 'DT'], ['is', 'VBZ'], ['interesting', 'JJ'], ['.', '.']]
        With light=True uses Brill's lexical and contextual rules to improve token tags.
        With light=False uses a faster set of arbitrary rules (Jason Wiener's rules).
        If map is a function, apply it to each tag after lexical and contextual rules.
    """
    tagged = []
    for token in tokens:
        # By default, all tokens are tagged NN unless we find an entry in the lexicon.
        # Words that are not in the lexicon are then improved with lexical rules.
        # Words that start with a capital letter are tagged with NNP by default,
        # unless the language is German (which capitalizes all nouns).
        tagged.append([token, lexicon.get(token, lexicon.get(token.lower(), None))])
    f = light and apply_default_rules or lexicon.lexical_rules.apply
    for i, (token, tag) in enumerate(tagged):
        if tag == None:
            if len(token) > 0 \
            and token[0].isupper() \
            and token[0].isalpha() \
            and language != "de":
                tagged[i] = [token, lexicon.named_entities.tag]
            else:
                tagged[i] = [token, default]
                tagged[i] = f(tagged[i],
                    previous = i>0 and tagged[i-1] or (None, None), 
                        next = i<len(tagged)-1 and tagged[i+1] or (None, None))
    if not light:
        tagged = lexicon.contextual_rules.apply(tagged)
        tagged = lexicon.named_entities.apply(tagged)
    if map is not None:
        tagged = [[token, map(tag) or default] for token, tag in tagged]
    return tagged

def apply_default_rules(token, previous=(None,None), next=(None,None)):
    """ Returns the token with its tag updated according to a few simple rules.
        Jason Wiener's rules are less accurate than Brill's lexical rules, but they are faster (5-10x).
    """
    # Based on Jason Wiener's implementation of a rule-based part-of-speech Brill tagger.
    # Rule 1: convert a common noun ending with "ing" to a present participle verb (i.e., a gerund).
    # Rule 2: convert any type to adverb if it ends in "ly".
    # Rule 3: if a word has been categorized as a common noun and it ends with "s",
    #         then set its type to plural common noun (NNS)
    # Rule 4: convert a noun to a number (CD) if "." appears in the word.
    # Rule 5: convert a common noun (NN or NNS) to a adjective if it ends with "able", "al", "ient", etc.
    #         or if there is a hyphen ("-") in the word.
    # Rule 6: convert a noun to a past participle if word ends with "ed".
    # Rule 7: DT, {VBD | VBP} --> DT, NN
    # Rule 8: convert a noun to a verb if it ends with "ate", "ify", "ise", "ize", etc.
    # Rule 9: convert a noun to a verb if the preceeding word is "would".
    word, pos = token
    if pos.startswith("NN") and word.endswith("ing"):
        pos = "VBG"
    elif word.endswith("ly"):
        pos = "RB"
    elif pos == "NN" and word.endswith("s") and not word.endswith(("ous","ss")):
        pos = "NNS"
    elif pos.startswith("NN") and word.isdigit():
        pos = "CD"
    elif pos.startswith("NN") and word[:1].isdigit() and word.replace(".","").isdigit():
        pos = "CD"
    elif pos.startswith("NN") and word.endswith(("able","al","ful","ible","ient","ish","ive","less","tic","ous")) or "-" in word:
        pos = "JJ"
    elif pos.startswith("NN") and word.endswith("ed"):
        pos = "VBN"
    elif pos in ("VBD", "VBP", "VB") and previous[1] == "DT":
        pos = "NN"
    elif pos.startswith("NN") and word.endswith(("ate", "ify", "ise", "ize")):
        pos = "VBP"
    elif pos.startswith("NN") and previous[0] == "would":
        pos = "VB"
    return [word, pos]

#### CHUNKER #######################################################################################

SEPARATOR = "/"
VB = "VB|VBD|VBG|VBN|VBP|VBZ"
JJ = "JJ|JJR|JJS"
RB = "(?<!W)RB|RBR|RBS"
NN = "NN|NNS|NNP|NNPS|PRP|PRP\$"
rules = [[ 
    # Germanic: RB + JJ precedes NN: "the round table".
    ("NP",   re.compile(r"(("+NN+")/)*((DT|CD|CC)/)*(("+RB+"|"+JJ+")/)*(("+NN+")/)+")),
    ("VP",   re.compile(r"(((MD|"+RB+")/)*(("+VB+")/)+)+")),
    ("VP",   re.compile(r"((MD)/)")),
    ("PP",   re.compile(r"((IN|TO)/)")),
    ("ADJP", re.compile(r"((CC|"+RB+"|"+JJ+")/)*(("+JJ+")/)+")),
    ("ADVP", re.compile(r"(("+RB+"|WRB)/)+")),
], [ 
    # Romance: RB + JJ precedes or follows NN: "la table ronde", "une jolie fille".
    ("NP",   re.compile(r"(("+NN+")/)*((DT|CD|CC)/)*(("+RB+"|"+JJ+")/)*(("+NN+")/)+(("+RB+"|"+JJ+")/)*")),
    ("VP",   re.compile(r"(((MD|"+RB+")/)*(("+VB+")/)+(("+RB+")/)*)+")),
    ("VP",   re.compile(r"((MD)/)")),
    ("PP",   re.compile(r"((IN|TO)/)")),
    ("ADJP", re.compile(r"((CC|"+RB+"|"+JJ+")/)*(("+JJ+")/)+")),
    ("ADVP", re.compile(r"(("+RB+"|WRB)/)+")),
]]
rules[0].insert(1, rules[0].pop(3)) # Handle ADJP before VP (RB prefers next ADJP over previous VP).
rules[1].insert(1, rules[1].pop(3))

def find_chunks(tagged, iob=True, language="en"):
    """ The input is a list of [token, tag]-items.
        The output is a list of [token, tag, chunk]-items.
        For example:
        The/DT nice/JJ fish/NN is/VBZ dead/JJ ./. => 
        The/DT/B-NP nice/JJ/I-NP fish/NN/I-NP is/VBZ/B-VP dead/JJ/B-ADJP ././O
    """
    chunked = [x for x in tagged]
    tags = "".join("%s%s"%(tag,SEPARATOR) for token, tag in tagged)
    # Use Germanic (en/de/nl) or Romance (es/fr) rules according to given language.
    for tag, rule in rules[int(language in ("es", "fr"))]:
        for m in rule.finditer(tags):
            # Find the start of the pattern inside the tag-string.
            # The number of preceding separators = the number of preceding tokens.
            i = m.start()
            j = tags[:i].count(SEPARATOR)
            n = m.group(0).count(SEPARATOR)
            for k in range(j, j+n):
                if len(chunked[k]) == 3:
                    continue
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
    # Corrections.
    for i, (word, tag, chunk) in enumerate(chunked):
        if tag.startswith("RB") and chunk == "B-NP":
            if i < len(chunked)-1 and not chunked[i+1][1].startswith("JJ"):
                # "Very nice work" (NP) <=> "Perhaps" (ADVP) + "you" (NP).
                chunked[i+0][2] = "B-ADVP"
                chunked[i+1][2] = "B-NP"
    return chunked

#### RELATION FINDER ###############################################################################
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

#### PNP FINDER ####################################################################################

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

#### LEMMATIZER ####################################################################################
# Word lemmas using singularization and verb conjugation from the inflect module.

try: 
    from ..inflect import singularize, conjugate
except:
    try:
        sys.path.append(os.path.join(MODULE, ".."))
        from inflect import singularize, conjugate
    except:
        try: 
            from pattern.en.inflect import singularize, conjugate
        except:
            singularize = lambda w: w
            conjugate = lambda w,t: w

def lemma(word, pos="NN"):
    """ Returns the lemma of the given word, e.g. horses/NNS => horse, am/VBP => be.
        Words must be lowercase.
    """
    if pos == "NNS":
        return singularize(word)
    if pos is not None and \
       pos.startswith(("VB","MD")):
        return conjugate(word, "infinitive") or word
    return word
	
def find_lemmata(tagged):
    """ Appends the lemma to the given list of (token, tag)-tuples.
    """
    for token in tagged:
        token.append(lemma(token[0].lower(), pos=len(token)>1 and token[1] or None))
    return tagged

#### PARSER ########################################################################################

_tokenize = tokenize

def parse(s, tokenize=True, tags=True, chunks=True, relations=False, lemmata=False, encoding="utf-8", **kwargs):
    """ Takes a string (sentences) and returns a tagged Unicode string. 
        Sentences in the output are separated by newlines.
    """
    if tokenize is True:
        s = _tokenize(s)
    if isinstance(s, (list, tuple)):
        s = [isinstance(s, basestring) and s.split(" ") or s for s in s]
    if isinstance(s, basestring):
        s = [s.split(" ") for s in s.split("\n")]
    for i in range(len(s)):
        for j in range(len(s[i])):
            # Convert tokens to Unicode.
            if isinstance(s[i][j], str):
                s[i][j] = s[i][j].decode(encoding)
        if tags or chunks or relations or lemmata:
            # Tagger is required by chunker, relation finder and lemmatizer.
            s[i] = find_tags(s[i], 
                    default = kwargs.get("default", "NN"), 
                      light = kwargs.get("light", False), 
                    lexicon = kwargs.get("lexicon", LEXICON),
                   language = kwargs.get("language", "en"),
                        map = kwargs.get("map", None))
        else:
            s[i] = [[w] for w in s[i]]
        if chunks or relations:
            s[i] = find_chunks(s[i], language=kwargs.get("language", "en"))
        if chunks or relations:
            s[i] = find_prepositions(s[i])
        if relations:
            s[i] = find_relations(s[i])
        if lemmata:
            s[i] = find_lemmata(s[i])
    # Include the format of a token in the parsed output string.
    # This allows a Sentence (see tree.py) to figure out the order of the tags.
    format = ["word"]
    if tags:
        format.append("part-of-speech")
    if chunks:
        format.extend(("chunk", "preposition"))
    if relations:
        format.append("relation")
    if lemmata:
        format.append("lemma")
    # With collapse=False, returns the raw [[[token, tag], [token, tag]], ...].
    # Note that we can't pass this output to Sentence (format is not stored).
    if not kwargs.get("collapse", True) or kwargs.get("split", False):
        return s
    # Collapse the output.
    # Sentences are separated by newlines, tokens by spaces, tags by slashes.
    # Slashes in words are encoded with &slash;
    for i in range(len(s)):
        for j in range(len(s[i])):
            s[i][j][0] = s[i][j][0].replace("/", "&slash;")
            s[i][j] = "/".join(s[i][j])
        s[i] = " ".join(s[i])
    s = "\n".join(s)
    s = TaggedString(s, tags=format, language=kwargs.get("language","en"))
    return s

#--- TAGGED STRING ---------------------------------------------------------------------------------
# The parse() function returns a unicode string with an extra "tags" attribute.
# The Sentence tree object uses this attribute to determine the token format.
# The TaggedString class emulates the TokenString class in the MBSP module,
# which has additional functionality besides a "tags" attribute.

TOKENS = "tokens"

class TaggedString(unicode):
    
    def __new__(self, string, tags=["word"], language="en"):
        if isinstance(string, unicode) and hasattr(string, "tags"): 
            tags, language = string.tags, string.language
        s = unicode.__new__(self, string)
        s.tags = list(tags)
        s.language = language
        return s
    
    def split(self, sep=TOKENS):
        """ Returns a list of sentences, where each sentence is a list of tokens,
            where each token is a list of word + tags.
        """
        if sep != TOKENS:
            return unicode.split(self, sep)
        if len(self) == 0:
            return []
        return [[[x.replace("&slash;", "/") for x in token.split("/")] 
            for token in sentence.split(" ")] 
                for sentence in unicode.split(self, "\n")]

def tag(s, tokenize=True, encoding="utf-8"):
    """ Returns a list of (token, tag)-tuples from the given string.
    """
    tags = []
    for sentence in parse(s, tokenize, True, False, False, False, encoding).split():
        for token in sentence:
            tags.append((token[0], token[1]))
    return tags

#### COMMAND LINE ##################################################################################
# From the folder that contains the "pattern" folder:
# python -m pattern.en.parser xml -s "Hello, my name is Dr. Sbaitso. Nice to meet you." -OTCLI

def commandline(parse=parse):
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
    commandline(parse)