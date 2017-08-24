#### PATTERN | TEXT | PATTERN MATCHING #############################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from io import open

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

import re
import itertools

from functools import cmp_to_key

#--- TEXT, SENTENCE AND WORD -----------------------------------------------------------------------
# The search() and match() functions work on Text, Sentence and Word objects (see pattern.text.tree),
# i.e., the parse tree including part-of-speech tags and phrase chunk tags.

# The pattern.text.search Match object will contain matched Word objects,
# emulated with the following classes if the original input was a plain string:

PUNCTUATION = ".,;:!?()[]{}`'\"@#$^&*+-|=~_"

RE_PUNCTUATION = "|".join(map(re.escape, PUNCTUATION))
RE_PUNCTUATION = re.compile("(%s)" % RE_PUNCTUATION)


class Text(list):

    def __init__(self, string="", token=["word"]):
        """ A list of sentences, where each sentence is separated by a period.
        """
        list.__init__(self, (Sentence(s + ".", token) for s in string.split(".")))

    @property
    def sentences(self):
        return self

    @property
    def words(self):
        return list(chain(*self))


class Sentence(list):

    def __init__(self, string="", token=["word"]):
        """ A list of words, where punctuation marks are split from words.
        """
        s = RE_PUNCTUATION.sub(" \\1 ", string) # Naive tokenization.
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r" ' (d|m|s|ll|re|ve)", " '\\1", s)
        s = s.replace("n ' t", " n't")
        s = s.split(" ")
        list.__init__(self, (Word(self, w, index=i) for i, w in enumerate(s)))

    @property
    def string(self):
        return " ".join(w.string for w in self)

    @property
    def words(self):
        return self

    @property
    def chunks(self):
        return []


class Word(object):

    def __init__(self, sentence, string, tag=None, index=0):
        """ A word with a position in a sentence.
        """
        self.sentence, self.string, self.tag, self.index = sentence, string, tag, index

    def __repr__(self):
        return "Word(%s)" % repr(self.string)

    def _get_type(self):
        return self.tag

    def _set_type(self, v):
        self.tag = v

    type = property(_get_type, _set_type)

    @property
    def chunk(self):
        return None

    @property
    def lemma(self):
        return None

#--- STRING MATCHING -------------------------------------------------------------------------------

WILDCARD = "*"
regexp = type(re.compile(r"."))


def _match(string, pattern):
    """ Returns True if the pattern matches the given word string.
        The pattern can include a wildcard (*front, back*, *both*, in*side),
        or it can be a compiled regular expression.
    """
    p = pattern
    try:
        if p[:1] == WILDCARD and (p[-1:] == WILDCARD and p[1:-1] in string or string.endswith(p[1:])):
            return True
        if p[-1:] == WILDCARD and not p[-2:-1] == "\\" and string.startswith(p[:-1]):
            return True
        if p == string:
            return True
        if WILDCARD in p[1:-1]:
            p = p.split(WILDCARD)
            return string.startswith(p[0]) and string.endswith(p[-1])
    except:
        # For performance, calling isinstance() last is 10% faster for plain strings.
        if isinstance(p, regexp):
            return p.search(string) is not None
    return False

#--- LIST FUNCTIONS --------------------------------------------------------------------------------
# Search patterns can contain optional constraints,
# so we need to find all possible variations of a pattern.


def unique(iterable):
    """ Returns a list copy in which each item occurs only once (in-order).
    """
    seen = set()
    return [x for x in iterable if x not in seen and not seen.add(x)]


def find(function, iterable):
    """ Returns the first item in the list for which function(item) is True, None otherwise.
    """
    for x in iterable:
        if function(x) is True:
            return x


def combinations(iterable, n):
    # Backwards compatibility.
    return product(iterable, repeat=n)


def product(*args, **kwargs):
    """ Yields all permutations with replacement:
        list(product("cat", repeat=2)) => 
        [("c", "c"), 
         ("c", "a"), 
         ("c", "t"), 
         ("a", "c"), 
         ("a", "a"), 
         ("a", "t"), 
         ("t", "c"), 
         ("t", "a"), 
         ("t", "t")]
    """
    p = [[]]
    for iterable in map(tuple, args) * kwargs.get("repeat", 1):
        p = [x + [y] for x in p for y in iterable]
    for p in p:
        yield tuple(p)

try:
    from itertools import product
except:
    pass


def variations(iterable, optional=lambda x: False):
    """ Returns all possible variations of a sequence with optional items.
    """
    # For example: variations(["A?", "B?", "C"], optional=lambda s: s.endswith("?"))
    # defines a sequence where constraint A and B are optional:
    # [("A?", "B?", "C"), ("B?", "C"), ("A?", "C"), ("C")]
    iterable = tuple(iterable)
    # Create a boolean sequence where True means optional:
    # ("A?", "B?", "C") => [True, True, False]
    o = [optional(x) for x in iterable]
    # Find all permutations of the boolean sequence:
    # [True, False, True], [True, False, False], [False, False, True], [False, False, False].
    # Map to sequences of constraints whose index in the boolean sequence yields True.
    a = set()
    for p in product([False, True], repeat=sum(o)):
        p = list(p)
        v = [b and (b and p.pop(0)) for b in o]
        v = tuple(iterable[i] for i in range(len(v)) if not v[i])
        a.add(v)
    # Longest-first.
    f = lambda x, y: len(y) - len(x)
    return sorted(a, key=cmp_to_key(f))

#### TAXONOMY ######################################################################################

#--- ORDERED DICTIONARY ----------------------------------------------------------------------------
# A taxonomy is based on an ordered dictionary
# (i.e., if a taxonomy term has multiple parents, the most recent parent is the default).


class odict(dict):

    def __init__(self, items=[]):
        """ A dictionary with ordered keys (first-in last-out).
        """
        dict.__init__(self)
        self._o = [] # List of ordered keys.
        if isinstance(items, dict):
            items = reversed(list(items.items()))
        for k, v in items:
            self.__setitem__(k, v)

    @classmethod
    def fromkeys(cls, keys=[], v=None):
        return cls((k, v) for k in keys)

    def push(self, kv):
        """ Adds a new item from the given (key, value)-tuple.
            If the key exists, pushes the updated item to the head of the dict.
        """
        if kv[0] in self:
            self.__delitem__(kv[0])
        self.__setitem__(kv[0], kv[1])
    append = push

    def __iter__(self):
        return reversed(self._o)

    def __setitem__(self, k, v):
        if k not in self:
            self._o.append(k)
        dict.__setitem__(self, k, v)

    def __delitem__(self, k):
        self._o.remove(k)
        dict.__delitem__(self, k)

    def update(self, d):
        for k, v in reversed(list(d.items())):
            self.__setitem__(k, v)

    def setdefault(self, k, v=None):
        if k not in self:
            self.__setitem__(k, v)
        return self[k]

    def pop(self, k, *args, **kwargs):
        if k in self:
            self._o.remove(k)
        return dict.pop(self, k, *args, **kwargs)

    def popitem(self):
        k = self._o[-1] if self._o else None
        return (k, self.pop(k))

    def clear(self):
        self._o = []
        dict.clear(self)

    def iterkeys(self):
        return reversed(self._o)

    def itervalues(self):
        return map(self.__getitem__, reversed(self._o))

    def iteritems(self):
        return iter(zip(self.iterkeys(), self.itervalues()))

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def copy(self):
        return self.__class__(reversed(list(self.items())))

    def __repr__(self):
        return "{%s}" % ", ".join("%s: %s" % (repr(k), repr(v)) for k, v in self.items())

#--- TAXONOMY --------------------------------------------------------------------------------------


class Taxonomy(dict):

    def __init__(self):
        """ Hierarchical tree of words classified by semantic type.
            For example: "rose" and "daffodil" can be classified as "flower":
            >>> taxonomy.append("rose", type="flower")
            >>> taxonomy.append("daffodil", type="flower")
            >>> print(taxonomy.children("flower"))
            Taxonomy terms can be used in a Pattern:
            FLOWER will match "flower" as well as "rose" and "daffodil".
            The taxonomy is case insensitive by default.
        """
        self.case_sensitive = False
        self._values = {}
        self.classifiers = []

    def _normalize(self, term):
        try:
            return not self.case_sensitive and term.lower() or term
        except: # Not a string.
            return term

    def __contains__(self, term):
        # Check if the term is in the dictionary.
        # If the term is not in the dictionary, check the classifiers.
        term = self._normalize(term)
        if dict.__contains__(self, term):
            return True
        for classifier in self.classifiers:
            if classifier.parents(term) \
            or classifier.children(term):
                return True
        return False

    def append(self, term, type=None, value=None):
        """ Appends the given term to the taxonomy and tags it as the given type.
            Optionally, a disambiguation value can be supplied.
            For example: taxonomy.append("many", "quantity", "50-200")
        """
        term = self._normalize(term)
        type = self._normalize(type)
        self.setdefault(term, (odict(), odict()))[0].push((type, True))
        self.setdefault(type, (odict(), odict()))[1].push((term, True))
        self._values[term] = value

    def classify(self, term, **kwargs):
        """ Returns the (most recently added) semantic type for the given term ("many" => "quantity").
            If the term is not in the dictionary, try Taxonomy.classifiers.
        """
        term = self._normalize(term)
        if dict.__contains__(self, term):
            return list(self[term][0].keys())[-1]
        # If the term is not in the dictionary, check the classifiers.
        # Returns the first term in the list returned by a classifier.
        for classifier in self.classifiers:
            # **kwargs are useful if the classifier requests extra information,
            # for example the part-of-speech tag.
            v = classifier.parents(term, **kwargs)
            if v:
                return v[0]

    def parents(self, term, recursive=False, **kwargs):
        """ Returns a list of all semantic types for the given term.
            If recursive=True, traverses parents up to the root.
        """
        def dfs(term, recursive=False, visited={}, **kwargs):
            if term in visited: # Break on cyclic relations.
                return []
            visited[term], a = True, []
            if dict.__contains__(self, term):
                a = list(self[term][0].keys())
            for classifier in self.classifiers:
                a.extend(classifier.parents(term, **kwargs) or [])
            if recursive:
                for w in a:
                    a += dfs(w, recursive, visited, **kwargs)
            return a
        return unique(dfs(self._normalize(term), recursive, {}, **kwargs))

    def children(self, term, recursive=False, **kwargs):
        """ Returns all terms of the given semantic type: "quantity" => ["many", "lot", "few", ...]
            If recursive=True, traverses children down to the leaves.
        """
        def dfs(term, recursive=False, visited={}, **kwargs):
            if term in visited: # Break on cyclic relations.
                return []
            visited[term], a = True, []
            if dict.__contains__(self, term):
                a = list(self[term][1].keys())
            for classifier in self.classifiers:
                a.extend(classifier.children(term, **kwargs) or [])
            if recursive:
                for w in a:
                    a += dfs(w, recursive, visited, **kwargs)
            return a
        return unique(dfs(self._normalize(term), recursive, {}, **kwargs))

    def value(self, term, **kwargs):
        """ Returns the value of the given term ("many" => "50-200")
        """
        term = self._normalize(term)
        if term in self._values:
            return self._values[term]
        for classifier in self.classifiers:
            v = classifier.value(term, **kwargs)
            if v is not None:
                return v

    def remove(self, term):
        if dict.__contains__(self, term):
            for w in self.parents(term):
                self[w][1].pop(term)
            dict.pop(self, term)

# Global taxonomy:
TAXONOMY = taxonomy = Taxonomy()

#taxonomy.append("rose", type="flower")
#taxonomy.append("daffodil", type="flower")
#taxonomy.append("flower", type="plant")
#print(taxonomy.classify("rose"))
#print(taxonomy.children("plant", recursive=True))

#c = Classifier(parents=lambda term: term.endswith("ness") and ["quality"] or [])
#taxonomy.classifiers.append(c)
#print(taxonomy.classify("roughness"))

#--- TAXONOMY CLASSIFIER ---------------------------------------------------------------------------


class Classifier(object):

    def __init__(self, parents=lambda term: [], children=lambda term: [], value=lambda term: None):
        """ A classifier uses a rule-based approach to enrich the taxonomy, for example:
            c = Classifier(parents=lambda term: term.endswith("ness") and ["quality"] or [])
            taxonomy.classifiers.append(c)
            This tags any word ending in -ness as "quality".
            This is much shorter than manually adding "roughness", "sharpness", ...
            Other examples of useful classifiers: calling en.wordnet.Synset.hyponyms() or en.number().
        """
        self.parents = parents
        self.children = children
        self.value = value

# Classifier(parents=lambda word: word.endswith("ness") and ["quality"] or [])
# Classifier(parents=lambda word, chunk=None: chunk=="VP" and [ACTION] or [])


class WordNetClassifier(Classifier):

    def __init__(self, wordnet=None):
        if wordnet is None:
            try:
                from pattern.en import wordnet
            except:
                try:
                    from .en import wordnet
                except:
                    pass
        Classifier.__init__(self, self._parents, self._children)
        self.wordnet = wordnet

    def _children(self, word, pos="NN"):
        try:
            return [w.synonyms[0] for w in self.wordnet.synsets(word, pos[:2])[0].hyponyms()]
        except:
            pass

    def _parents(self, word, pos="NN"):
        try:
            return [w.synonyms[0] for w in self.wordnet.synsets(word, pos[:2])[0].hypernyms()]
        except:
            pass

#from en import wordnet
#taxonomy.classifiers.append(WordNetClassifier(wordnet))
#print(taxonomy.parents("ponder", pos="VB"))
#print(taxonomy.children("computer"))

#### PATTERN #######################################################################################

#--- PATTERN CONSTRAINT ----------------------------------------------------------------------------

# Allowed chunk, role and part-of-speech tags (Penn Treebank II):
CHUNKS = dict.fromkeys(["NP", "PP", "VP", "ADVP", "ADJP", "SBAR", "PRT", "INTJ"], True)
ROLES = dict.fromkeys(["SBJ", "OBJ", "PRD", "TMP", "CLR", "LOC", "DIR", "EXT", "PRP"], True)
TAGS = dict.fromkeys(["CC", "CD", "CJ", "DT", "EX", "FW", "IN", "JJ", "JJR", "JJS", "JJ*",
                        "LS", "MD", "NN", "NNS", "NNP", "NNP*", "NNPS", "NN*", "NO", "PDT", "PR",
                        "PRP", "PRP$", "PR*", "PRP*", "PT", "RB", "RBR", "RBS", "RB*", "RP",
                        "SYM", "TO", "UH", "VB", "VBZ", "VBP", "VBD", "VBN", "VBG", "VB*",
                        "WDT", "WP*", "WRB", "X", ".", ",", ":", "(", ")"], True)

ALPHA = re.compile("[a-zA-Z]")
has_alpha = lambda string: ALPHA.match(string) is not None


class Constraint(object):

    def __init__(self, words=[], tags=[], chunks=[], roles=[], taxa=[], optional=False, multiple=False, first=False, taxonomy=TAXONOMY, exclude=None, custom=None):
        """ A range of words, tags and taxonomy terms that matches certain words in a sentence.        
            For example: 
            Constraint.fromstring("with|of") matches either "with" or "of".
            Constraint.fromstring("(JJ)") optionally matches an adjective.
            Constraint.fromstring("NP|SBJ") matches subject noun phrases.
            Constraint.fromstring("QUANTITY|QUALITY") matches quantity-type and quality-type taxa.
        """
        self.index    = 0
        self.words    = list(words)  # Allowed words/lemmata (of, with, ...)
        self.tags     = list(tags)   # Allowed parts-of-speech (NN, JJ, ...)
        self.chunks   = list(chunks) # Allowed chunk types (NP, VP, ...)
        self.roles    = list(roles)  # Allowed chunk roles (SBJ, OBJ, ...)
        self.taxa     = list(taxa)   # Allowed word categories.
        self.taxonomy = taxonomy
        self.optional = optional
        self.multiple = multiple
        self.first    = first
        self.exclude  = exclude      # Constraint of words that are *not* allowed, or None.
        self.custom   = custom       # Custom function(Word) returns True if word matches constraint.

    @classmethod
    def fromstring(cls, s, **kwargs):
        """ Returns a new Constraint from the given string.
            Uppercase words indicate either a tag ("NN", "JJ", "VP")
            or a taxonomy term (e.g., "PRODUCT", "PERSON").
            Syntax:
            ( defines an optional constraint, e.g., "(JJ)".
            [ defines a constraint with spaces, e.g., "[Mac OS X | Windows Vista]".
            _ is converted to spaces, e.g., "Windows_Vista".
            | separates different options, e.g., "ADJP|ADVP".
            ! can be used as a word prefix to disallow it.
            * can be used as a wildcard character, e.g., "soft*|JJ*".
            ? as a suffix defines a constraint that is optional, e.g., "JJ?".
            + as a suffix defines a constraint that can span multiple words, e.g., "JJ+".
            ^ as a prefix defines a constraint that can only match the first word.
            These characters need to be escaped if used as content: "\(".
        """
        C = cls(**kwargs)
        s = s.strip()
        s = s.strip("{}")
        s = s.strip()
        for i in range(3):
            # Wrapping order of control characters is ignored:
            # (NN+) == (NN)+ == NN?+ == NN+? == [NN+?] == [NN]+?
            if s.startswith("^"):
                s = s[1:]; C.first = True
            if s.endswith("+") and not s.endswith("\+"):
                s = s[0:-1]; C.multiple = True
            if s.endswith("?") and not s.endswith("\?"):
                s = s[0:-1]; C.optional = True
            if s.startswith("(") and s.endswith(")"):
                s = s[1:-1]; C.optional = True
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1]
        s = re.sub(r"^\\\^", "^", s)
        s = re.sub(r"\\\+$", "+", s)
        s = s.replace("\_", "&uscore;")
        s = s.replace("_", " ")
        s = s.replace("&uscore;", "_")
        s = s.replace("&lparen;", "(")
        s = s.replace("&rparen;", ")")
        s = s.replace("&lbrack;", "[")
        s = s.replace("&rbrack;", "]")
        s = s.replace("&lcurly;", "{")
        s = s.replace("&rcurly;", "}")
        s = s.replace("\(", "(")
        s = s.replace("\)", ")")
        s = s.replace("\[", "[")
        s = s.replace("\]", "]")
        s = s.replace("\{", "{")
        s = s.replace("\}", "}")
        s = s.replace("\*", "*")
        s = s.replace("\?", "?")
        s = s.replace("\+", "+")
        s = s.replace("\^", "^")
        s = s.replace("\|", "&vdash;")
        s = s.split("|")
        s = [v.replace("&vdash;", "|").strip() for v in s]
        for v in s:
            C._append(v)
        return C

    def _append(self, v):
        if v.startswith("!") and self.exclude is None:
            self.exclude = Constraint()
        if v.startswith("!"):
            self.exclude._append(v[1:]); return
        if "!" in v:
            v = v.replace("\!", "!")
        if v != v.upper():
            self.words.append(v.lower())
        elif v in TAGS:
            self.tags.append(v)
        elif v in CHUNKS:
            self.chunks.append(v)
        elif v in ROLES:
            self.roles.append(v)
        elif v in self.taxonomy or has_alpha(v):
            self.taxa.append(v.lower())
        else:
            # Uppercase words indicate tags or taxonomy terms.
            # However, this also matches "*" or "?" or "0.25".
            # Unless such punctuation is defined in the taxonomy, it is added to Range.words.
            self.words.append(v.lower())

    def match(self, word):
        """ Return True if the given Word is part of the constraint:
            - the word (or lemma) occurs in Constraint.words, OR
            - the word (or lemma) occurs in Constraint.taxa taxonomy tree, AND
            - the word and/or chunk tags match those defined in the constraint.
            Individual terms in Constraint.words or the taxonomy can contain wildcards (*).
            Some part-of-speech-tags can also contain wildcards: NN*, VB*, JJ*, RB*, PR*.
            If the given word contains spaces (e.g., proper noun),
            the entire chunk will also be compared.
            For example: Constraint(words=["Mac OS X*"]) 
            matches the word "Mac" if the word occurs in a Chunk("Mac OS X 10.5").
        """
        # If the constraint has a custom function it must return True.
        if self.custom is not None and self.custom(word) is False:
            return False
        # If the constraint can only match the first word, Word.index must be 0.
        if self.first and word.index > 0:
            return False
        # If the constraint defines excluded options, Word can not match any of these.
        if self.exclude and self.exclude.match(word):
            return False
        # If the constraint defines allowed tags, Word.tag needs to match one of these.
        if self.tags:
            if find(lambda w: _match(word.tag, w), self.tags) is None:
                return False
        # If the constraint defines allowed chunks, Word.chunk.tag needs to match one of these.
        if self.chunks:
            ch = word.chunk and word.chunk.tag or None
            if find(lambda w: _match(ch, w), self.chunks) is None:
                return False
        # If the constraint defines allowed role, Word.chunk.tag needs to match one of these.
        if self.roles:
            R = word.chunk and [r2 for r1, r2 in word.chunk.relations] or []
            if find(lambda w: w in R, self.roles) is None:
                return False
        # If the constraint defines allowed words,
        # Word.string.lower() OR Word.lemma needs to match one of these.
        b = True # b==True when word in constraint (or Constraints.words=[]).
        if len(self.words) + len(self.taxa) > 0:
            s1 = word.string.lower()
            s2 = word.lemma
            b = False
            for w in itertools.chain(self.words, self.taxa):
                # If the constraint has a word with spaces (e.g., a proper noun),
                # compare it to the entire chunk.
                try:
                    if " " in w and (s1 in w or s2 and s2 in w or "*" in w):
                        s1 = word.chunk and word.chunk.string.lower() or s1
                        s2 = word.chunk and " ".join(x or "" for x in word.chunk.lemmata) or s2
                except Exception as e:
                    s1 = s1
                    s2 = None
                # Compare the word to the allowed words (which can contain wildcards).
                if _match(s1, w):
                    b = True
                    break
                # Compare the word lemma to the allowed words, e.g.,
                # if "was" is not in the constraint, perhaps "be" is, which is a good match.
                if s2 and _match(s2, w):
                    b = True
                    break

        # If the constraint defines allowed taxonomy terms,
        # and the given word did not match an allowed word, traverse the taxonomy.
        # The search goes up from the given word to its parents in the taxonomy.
        # This is faster than traversing all the children of terms in Constraint.taxa.
        # The drawback is that:
        # 1) Wildcards in the taxonomy are not detected (use classifiers instead),
        # 2) Classifier.children() has no effect, only Classifier.parent().
        if self.taxa and (not self.words or (self.words and not b)):
            for s in (
              word.string, # "ants"
              word.lemma,  # "ant"
              word.chunk and word.chunk.string or None, # "army ants"
              word.chunk and " ".join([x or "" for x in word.chunk.lemmata]) or None): # "army ant"
                if s is not None:
                    if self.taxonomy.case_sensitive is False:
                        s = s.lower()
                    # Compare ancestors of the word to each term in Constraint.taxa.
                    for p in self.taxonomy.parents(s, recursive=True):
                        if find(lambda s: p == s, self.taxa): # No wildcards.
                            return True
        return b

    def __repr__(self):
        s = []
        for k, v in (
          ( "words", self.words),
          (  "tags", self.tags),
          ("chunks", self.chunks),
          ( "roles", self.roles),
          (  "taxa", self.taxa)):
            if v:
                s.append("%s=%s" % (k, repr(v)))
        return "Constraint(%s)" % ", ".join(s)

    @property
    def string(self):
        a = self.words + self.tags + self.chunks + self.roles + [w.upper() for w in self.taxa]
        a = (escape(s) for s in a)
        a = (s.replace("\\*", "*") for s in a)
        a = [s.replace(" ", "_") for s in a]
        if self.exclude:
            a.extend("!" + s for s in self.exclude.string[1:-1].split("|"))
        return (self.optional and "%s(%s)%s" or "%s[%s]%s") % (
            self.first and "^" or "", "|".join(a), self.multiple and "+" or "")

#--- PATTERN ---------------------------------------------------------------------------------------

STRICT = "strict"
GREEDY = "greedy"


class Pattern(object):

    def __init__(self, sequence=[], *args, **kwargs):
        """ A sequence of constraints that matches certain phrases in a sentence.
            The given list of Constraint objects can contain nested lists (groups).
        """
        # Parse nested lists and tuples from the sequence into groups.
        # [DT [JJ NN]] => Match.group(1) will yield the JJ NN sequences.
        def _ungroup(sequence, groups=None):
            for v in sequence:
                if isinstance(v, (list, tuple)):
                    if groups is not None:
                        groups.append(list(_ungroup(v, groups=None)))
                    for v in _ungroup(v, groups):
                        yield v
                else:
                    yield v
        self.groups = []
        self.sequence = list(_ungroup(sequence, groups=self.groups))
        # Assign Constraint.index:
        i = 0
        for constraint in self.sequence:
            constraint.index = i
            i += 1
        # There are two search modes: STRICT and GREEDY.
        # - In STRICT, "rabbit" matches only the string "rabbit".
        # - In GREEDY, "rabbit|NN" matches the string "rabbit" tagged "NN".
        # - In GREEDY, "rabbit" matches "the big white rabbit" (the entire chunk is a match).
        # - Pattern.greedy(chunk, constraint) determines (True/False) if a chunk is a match.
        self.strict = kwargs.get("strict", STRICT in args and GREEDY not in args)
        self.greedy = kwargs.get("greedy", lambda chunk, constraint: True)

    def __iter__(self):
        return iter(self.sequence)

    def __len__(self):
        return len(self.sequence)

    def __getitem__(self, i):
        return self.sequence[i]

    @classmethod
    def fromstring(cls, s, *args, **kwargs):
        """ Returns a new Pattern from the given string.
            Constraints are separated by a space.
            If a constraint contains a space, it must be wrapped in [].
        """
        s = s.replace("\(", "&lparen;")
        s = s.replace("\)", "&rparen;")
        s = s.replace("\[", "&lbrack;")
        s = s.replace("\]", "&rbrack;")
        s = s.replace("\{", "&lcurly;")
        s = s.replace("\}", "&rcurly;")
        p = []
        i = 0
        for m in re.finditer(r"\[.*?\]|\(.*?\)", s):
            # Spaces in a range encapsulated in square brackets are encoded.
            # "[Windows Vista]" is one range, don't split on space.
            p.append(s[i:m.start()])
            p.append(s[m.start():m.end()].replace(" ", "&space;")); i = m.end()
        p.append(s[i:])
        s = "".join(p)
        s = s.replace("][", "] [")
        s = s.replace(")(", ") (")
        s = s.replace("\|", "&vdash;")
        s = re.sub(r"\s+\|\s+", "|", s)
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"\{\s+", "{", s)
        s = re.sub(r"\s+\}", "}", s)
        s = s.split(" ")
        s = [v.replace("&space;", " ") for v in s]
        P = cls([], *args, **kwargs)
        G, O, i = [], [], 0
        for s in s:
            constraint = Constraint.fromstring(s.strip("{}"), taxonomy=kwargs.get("taxonomy", TAXONOMY))
            constraint.index = len(P.sequence)
            P.sequence.append(constraint)
            # Push a new group on the stack if string starts with "{".
            # Parse constraint from string, add it to all open groups.
            # Pop latest group from stack if string ends with "}".
            # Insert groups in opened-first order (i).
            while s.startswith("{"):
                s = s[1:]
                G.append((i, []))
                i += 1
                O.append([])
            for g in G:
                g[1].append(constraint)
            while s.endswith("}"):
                s = s[:-1]
                if G:
                    O[G[-1][0]] = G[-1][1]
                    G.pop()
        P.groups = [g for g in O if g]
        return P

    def scan(self, string):
        """ Returns True if search(Sentence(string)) may yield matches.
            If is often faster to scan prior to creating a Sentence and searching it.
        """
        # In the following example, first scan the string for "good" and "bad":
        # p = Pattern.fromstring("good|bad NN")
        # for s in open("parsed.txt"):
        #     if p.scan(s):
        #         s = Sentence(s)
        #         m = p.search(s)
        #         if m:
        #             print(m)
        w = (constraint.words for constraint in self.sequence if not constraint.optional)
        w = itertools.chain(*w)
        w = [w.strip(WILDCARD) for w in w if WILDCARD not in w[1:-1]]
        if w and not any(w in string.lower() for w in w):
            return False
        return True

    def search(self, sentence):
        """ Returns a list of all matches found in the given sentence.
        """
        if sentence.__class__.__name__ == "Sentence":
            pass
        elif isinstance(sentence, list) or sentence.__class__.__name__ == "Text":
            a = []
            [a.extend(self.search(s)) for s in sentence]
            return a
        elif isinstance(sentence, str):
            sentence = Sentence(sentence)
        elif isinstance(sentence, Match) and len(sentence) > 0:
            sentence = sentence[0].sentence.slice(sentence[0].index, sentence[-1].index + 1)
        a = []
        v = self._variations()
        u = {}
        m = self.match(sentence, _v=v)
        while m:
            a.append(m)
            m = self.match(sentence, start=m.words[-1].index + 1, _v=v, _u=u)
        return a

    def match(self, sentence, start=0, _v=None, _u=None):
        """ Returns the first match found in the given sentence, or None.
        """
        if sentence.__class__.__name__ == "Sentence":
            pass
        elif isinstance(sentence, list) or sentence.__class__.__name__ == "Text":
            return find(lambda m: m is not None, (self.match(s, start, _v) for s in sentence))
        elif isinstance(sentence, str):
            sentence = Sentence(sentence)
        elif isinstance(sentence, Match) and len(sentence) > 0:
            sentence = sentence[0].sentence.slice(sentence[0].index, sentence[-1].index + 1)
        # Variations (_v) further down the list may match words more to the front.
        # We need to check all of them. Unmatched variations are blacklisted (_u).
        # Pattern.search() calls Pattern.match() with a persistent blacklist (1.5x faster).
        a = []
        for sequence in (_v is not None and _v or self._variations()):
            if _u is not None and id(sequence) in _u:
                continue
            m = self._match(sequence, sentence, start)
            if m is not None:
                a.append((m.words[0].index, len(m.words), m))
            if m is not None and m.words[0].index == start:
                return m
            if m is None and _u is not None:
                _u[id(sequence)] = False
        # Return the leftmost-longest.
        if len(a) > 0:
            return sorted(a, key = lambda x: (x[0], -x[1]))[0][-1]

    def _variations(self):
        v = variations(self.sequence, optional=lambda constraint: constraint.optional)
        v = sorted(v, key=len, reverse=True)
        return v

    def _match(self, sequence, sentence, start=0, i=0, w0=None, map=None, d=0):
        # Backtracking tree search.
        # Finds the first match in the sentence of the given sequence of constraints.
        # start : the current word index.
        #     i : the current constraint index.
        #    w0 : the first word that matches a constraint.
        #   map : a dictionary of (Word index, Constraint) items.
        #     d : recursion depth.

        # XXX - We can probably rewrite all of this using (faster) regular expressions.

        if map is None:
            map = {}

        n = len(sequence)

        # --- MATCH ----------
        if i == n:
            if w0 is not None:
                w1 = sentence.words[start - 1]
                # Greedy algorithm:
                # - "cat" matches "the big cat" if "cat" is head of the chunk.
                # - "Tom" matches "Tom the cat" if "Tom" is head of the chunk.
                # - This behavior is ignored with POS-tag constraints:
                #   "Tom|NN" can only match single words, not chunks.
                # - This is also True for negated POS-tags (e.g., !NN).
                w01 = [w0, w1]
                for j in (0, -1):
                    constraint, w = sequence[j], w01[j]
                    if self.strict is False and w.chunk is not None:
                        if not constraint.tags:
                            if not constraint.exclude or not constraint.exclude.tags:
                                if constraint.match(w.chunk.head):
                                    w01[j] = w.chunk.words[j]
                                if constraint.exclude and constraint.exclude.match(w.chunk.head):
                                    return None
                                if self.greedy(w.chunk, constraint) is False: # User-defined.
                                    return None
                w0, w1 = w01
                # Update map for optional chunk words (see below).
                words = sentence.words[w0.index:w1.index + 1]
                for w in words:
                    if w.index not in map and w.chunk:
                        wx = find(lambda w: w.index in map, reversed(w.chunk.words))
                        if wx:
                            map[w.index] = map[wx.index]
                # Return matched word range, we'll need the map to build Match.constituents().
                return Match(self, words, map)
            return None

        # --- RECURSION --------
        constraint = sequence[i]
        for w in sentence.words[start:]:
            #print(" "*d, "match?", w, sequence[i].string) # DEBUG
            if i < n and constraint.match(w):
                #print(" "*d, "match!", w, sequence[i].string) # DEBUG
                map[w.index] = constraint
                if constraint.multiple:
                    # Next word vs. same constraint if Constraint.multiple=True.
                    m = self._match(sequence, sentence, w.index + 1, i, w0 or w, map, d + 1)
                    if m:
                        return m
                # Next word vs. next constraint.
                m = self._match(sequence, sentence, w.index + 1, i + 1, w0 or w, map, d + 1)
                if m:
                    return m
            # Chunk words other than the head are optional:
            # - Pattern.fromstring("cat") matches "cat" but also "the big cat" (overspecification).
            # - Pattern.fromstring("cat|NN") does not match "the big cat" (explicit POS-tag).
            if w0 and not constraint.tags:
                if not constraint.exclude and not self.strict and w.chunk and w.chunk.head != w:
                    continue
                break
            # Part-of-speech tags match one single word.
            if w0 and constraint.tags:
                break
            if w0 and constraint.exclude and constraint.exclude.tags:
                break

    @property
    def string(self):
        return " ".join(constraint.string for constraint in self.sequence)

_cache = {}
_CACHE_SIZE = 100 # Number of dynamic Pattern objects to keep in cache.


def compile(pattern, *args, **kwargs):
    """ Returns a Pattern from the given string or regular expression.
        Recently compiled patterns are kept in cache
        (if they do not use taxonomies, which are mutable dicts).
    """
    id, p = repr(pattern) + repr(args), pattern
    if id in _cache and not kwargs:
        return _cache[id]
    if isinstance(pattern, str):
        p = Pattern.fromstring(pattern, *args, **kwargs)
    if isinstance(pattern, regexp):
        p = Pattern([Constraint(words=[pattern], taxonomy=kwargs.get("taxonomy", TAXONOMY))], *args, **kwargs)
    if len(_cache) > _CACHE_SIZE:
        _cache.clear()
    if isinstance(p, Pattern) and not kwargs:
        _cache[id] = p
    if isinstance(p, Pattern):
        return p
    else:
        raise TypeError("can't compile '%s' object" % pattern.__class__.__name__)


def scan(pattern, string, *args, **kwargs):
    """ Returns True if pattern.search(Sentence(string)) may yield matches.
        If is often faster to scan prior to creating a Sentence and searching it.
    """
    return compile(pattern, *args, **kwargs).scan(string)


def match(pattern, sentence, *args, **kwargs):
    """ Returns the first match found in the given sentence, or None.
    """
    return compile(pattern, *args, **kwargs).match(sentence)


def search(pattern, sentence, *args, **kwargs):
    """ Returns a list of all matches found in the given sentence.
    """
    return compile(pattern, *args, **kwargs).search(sentence)


def escape(string):
    """ Returns the string with control characters for Pattern syntax escaped.
        For example: "hello!" => "hello\!".
    """
    for ch in ("{", "}", "[", "]", "(", ")", "_", "|", "!", "*", "+", "^"):
        string = string.replace(ch, "\\" + ch)
    return string

#--- PATTERN MATCH ---------------------------------------------------------------------------------


class Match(object):

    def __init__(self, pattern, words=[], map={}):
        """ Search result returned from Pattern.match(sentence),
            containing a sequence of Word objects.
        """
        self.pattern = pattern
        self.words = words
        self._map1 = dict() # Word index to Constraint.
        self._map2 = dict() # Constraint index to list of Word indices.
        for w in self.words:
            self._map1[w.index] = map[w.index]
        for k, v in self._map1.items():
            self._map2.setdefault(self.pattern.sequence.index(v), []).append(k)
        for k, v in self._map2.items():
            v.sort()

    def __len__(self):
        return len(self.words)

    def __iter__(self):
        return iter(self.words)

    def __getitem__(self, i):
        return self.words.__getitem__(i)

    @property
    def start(self):
        return self.words and self.words[0].index or None

    @property
    def stop(self):
        return self.words and self.words[-1].index + 1 or None

    def constraint(self, word):
        """ Returns the constraint that matches the given Word, or None.
        """
        if word.index in self._map1:
            return self._map1[word.index]

    def constraints(self, chunk):
        """ Returns a list of constraints that match the given Chunk.
        """
        a = [self._map1[w.index] for w in chunk.words if w.index in self._map1]
        b = []
        [b.append(constraint) for constraint in a if constraint not in b]
        return b

    def constituents(self, constraint=None):
        """ Returns a list of Word and Chunk objects, 
            where words have been grouped into their chunks whenever possible.
            Optionally, returns only chunks/words that match given constraint(s), or constraint index.
        """
        # Select only words that match the given constraint.
        # Note: this will only work with constraints from Match.pattern.sequence.
        W = self.words
        n = len(self.pattern.sequence)
        if isinstance(constraint, (int, Constraint)):
            if isinstance(constraint, int):
                i = constraint
                i = i < 0 and i % n or i
            else:
                i = self.pattern.sequence.index(constraint)
            W = self._map2.get(i, [])
            W = [self.words[i - self.words[0].index] for i in W]
        if isinstance(constraint, (list, tuple)):
            W = []
            [W.extend(self._map2.get(j < 0 and j % n or j, [])) for j in constraint]
            W = [self.words[i - self.words[0].index] for i in W]
            W = unique(W)
        a = []
        i = 0
        while i < len(W):
            w = W[i]
            if w.chunk and W[i:i + len(w.chunk)] == w.chunk.words:
                i += len(w.chunk) - 1
                a.append(w.chunk)
            else:
                a.append(w)
            i += 1
        return a

    def group(self, index, chunked=False):
        """ Returns a list of Word objects that match the given group.
            With chunked=True, returns a list of Word + Chunk objects - see Match.constituents().
            A group consists of consecutive constraints wrapped in { }, e.g.,
            search("{JJ JJ} NN", Sentence(parse("big black cat"))).group(1) => big black.
        """
        if index < 0 or index > len(self.pattern.groups):
            raise IndexError("no such group")
        if index > 0 and index <= len(self.pattern.groups):
            g = self.pattern.groups[index - 1]
        if index == 0:
            g = self.pattern.sequence
        if chunked is True:
            return Group(self, self.constituents(constraint=[self.pattern.sequence.index(x) for x in g]))
        return Group(self, [w for w in self.words if self.constraint(w) in g])

    @property
    def string(self):
        return " ".join(w.string for w in self.words)

    def __repr__(self):
        return "Match(words=%s)" % repr(self.words)

#--- PATTERN MATCH GROUP ---------------------------------------------------------------------------


class Group(list):

    def __init__(self, match, words):
        list.__init__(self, words)
        self.match = match

    @property
    def words(self):
        return list(self)

    @property
    def start(self):
        return self and self[0].index or None

    @property
    def stop(self):
        return self and self[-1].index + 1 or None

    @property
    def string(self):
        return " ".join(w.string for w in self)
