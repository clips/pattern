#### PATTERN | EN | PARSER | BRILL LEXICON #########################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Brill lexicon with lexical and contextual rules, using lazy-loading.

import os
import re

try: 
    MODULE = os.path.dirname(__file__)
except:
    MODULE = ""

#### BRILL LEXICAL RULES ###########################################################################

LEXICAL  = ["char", "hassuf", "deletesuf", "addsuf", "haspref", "deletepref", "addpref"]
LEXICAL += ["goodleft", "goodright"]
LEXICAL.extend(["f"+x for x in LEXICAL])
LEXCIAL  = dict.fromkeys(LEXICAL, True) 

class LexicalRules(list):
        
    def __init__(self, lexicon, path=os.path.join(MODULE, "brill-lexical.txt")):
        # Brill's lexical rules.
        # An entry looks like: ('fhassuf', ['NN', 's', 'fhassuf', '1', 'NNS', 'x']).
        # The first item is the lookup command.
        # If prefixed with an "f", it means that the token needs to have the first given tag (NN).
        # In this case, if the NN-word ends with an "s", it is tagged as NNS.
        self.lexicon = lexicon
        self.path = path

    def load(self):
        for i, rule in enumerate(open(self.path).read().decode("utf8").strip().split("\n")):
            if not rule.startswith(";;;   "): # comment
                rule = rule.split()
                for cmd in rule:
                    if cmd in LEXICAL:
                        list.append(self, (cmd, rule)); break
        
    def __iter__(self):
        if len(self) == 0:
            self.load()
        return list.__iter__(self)

    def apply(self, token, previous=(None,None), next=(None,None)):
        """ Applies the lexical rules to the given token.
            A token is a [word, tag]-item whose tag might change if it matches a rule.
            Rules are lexically based on word characters, prefixes and suffixes.
        """
        word, pos = token[0], token[1]
        if word[:1].isdigit() and word.replace(".","").isdigit():
            return [word, "CD"]
        for cmd, rule in iter(self):
            pos = rule[-2]
            x = rule[0]
            if cmd.startswith("f"): 
                # Word must be tagged as the f-rule states.
                cmd = cmd[1:]
                if token[1] != rule[0]: continue
                x = rule[1]
            if (cmd == "char"       and x in word) \
            or (cmd == "hassuf"     and word.endswith(x)) \
            or (cmd == "deletesuf"  and word.endswith(x) and word[:-len(x)] in self.lexicon) \
            or (cmd == "haspref"    and word.startswith(x)) \
            or (cmd == "deletepref" and word.startswith(x) and word[len(x):] in self.lexicon) \
            or (cmd == "addsuf"     and word+x in self.lexicon) \
            or (cmd == "addpref"    and x+word in self.lexicon) \
            or (cmd == "goodleft"   and x == next[0]) \
            or (cmd == "goodright"  and x == previous[0]):
                return [word, pos]
        return token

#### BRILL CONTEXTUAL RULES ########################################################################

CONTEXTUAL  = ["PREVTAG", "NEXTTAG", "PREV1OR2TAG", "NEXT1OR2TAG", "PREV1OR2OR3TAG", "NEXT1OR2OR3TAG"]
CONTEXTUAL += ["SURROUNDTAG", "PREVBIGRAM", "NEXTBIGRAM", "LBIGRAM", "RBIGRAM", "PREV2TAG", "NEXT2TAG"]
CONTEXTUAL += ["CURWD", "PREVWD", "NEXTWD", "PREV1OR2WD", "NEXT1OR2WD", "WDPREVTAG"]
CONTEXTUAL  = dict.fromkeys(CONTEXTUAL, True)

class ContextualRules(list):
    
    def __init__(self, lexicon, path=os.path.join(MODULE, "brill-contextual.txt")):
        # Brill's contextual rules.
        # An entry looks like: ('PREVTAG', ['VBD', 'VB', 'PREVTAG', 'TO']).
        # The first item is the lookup command.
        # The example rule means:
        # "If the previous word is tagged TO, change this word's tag from VBD to VB (if it is VBD)".
        self.lexicon = lexicon
        self.path = path

    def load(self):
        for i, rule in enumerate(open(self.path).read().decode("utf8").strip().split("\n")):
            if not rule.startswith(";;;   "): # comment
                rule = rule.split()
                for cmd in rule:
                    if cmd in CONTEXTUAL:
                        list.append(self, (cmd, rule)); break
        
    def __iter__(self):
        if len(self) == 0:
            self.load()
        return list.__iter__(self)

    def apply(self, tokens):
        """ Applies the contextual rules to the given list of tokens. 
            Each token is a [word, tag]-item whose tag might change if it matches a rule.
            Rules are contextually based on the token's position in the sentence.
        """
        b = [(None,"STAART")] * 3 # Add empty tokens so we can scan ahead and behind.
        T = b + tokens + b
        for i, token in enumerate(T):
            for cmd, rule in iter(self):
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
                or (cmd == "LBIGRAM"        and x == T[i-1][0] and rule[4] == T[i][0]) \
                or (cmd == "RBIGRAM"        and x == T[i][0] and rule[4] == T[i+1][0]) \
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
                    
            # Brill's contextual rules assign tags based on a statistical majority vote.
            # Corrections, primarily based on user-feedback.
            # English: with/IN
            if token[0] == "with":
                tokens[i-len(b)][1] = "IN"
            # English: such/JJ as/IN
            if i > 0 and T[i-1][0] == "such" and token[0] == "as":
                tokens[i-1-len(b)][1] = "JJ"
                tokens[i-0-len(b)][1] = "IN"
            # English: a/DT burning/VBG candle/NN => a/DT burning/JJ candle/NN
            if token[1] == "VBG":
                if T[i-1][1] == "DT" and T[i+1][1].startswith("NN"):
                    tokens[i-len(b)][1] = "JJ"
            # Dutch: een/DT brandende/VBG kaars/NN => een/DT brandende/JJ kaars/NN
            if token[1].startswith("V(") and "teg_dw" in token[1]:
                if T[i-1][1].startswith("Art(") and T[i+1][1].startswith("N("):
                    tokens[i-len(b)][1] = "JJ"
            # German: und/KON
            if token[0] == "und" and token[1] == "KON":
                tokens[i-len(b)][1] = "KON"
            # German: durch den Sturm zerstört worden/VAPP => zerstört/VVPP worden/VAPP (passiv)
            if i > 0 and token[0] == "worden" and token[1] == "VAPP":
                tokens[i-1-len(b)][1] = "VVPP"
        return tokens

#### BRILL NAMED ENTITIES ##########################################################################

RE_EMAIL = re.compile(r"^[\w\-\.\+]+@(\w[\w\-]+\.)+[\w\-]+$")

class NamedEntities(dict):
    
    def __init__(self, lexicon, path=os.path.join(MODULE, "brill-entities.txt"), tag="NNP"):
        # Named Entity Recognition.
        # An entry looks like: {"george": [["george", "washington"], ["george", "w.", "bush"]]}
        # The named entities are (among other) compiled from the most viewed Wikipedia articles.
        # They should be language-independent.
        self.lexicon = lexicon
        self.path = path
        self.tag = tag

    def load(self):
        for entity in open(self.path).read().decode("utf8").strip().split("\n"):
            if not entity.startswith(";;;   "): # comment
                entity = entity.split() # ["George", "Washington"]
                entity = [v.lower() for v in entity]
                if entity[0] not in self:
                    self[entity[0]] = []
                self[entity[0]].append(entity)
        self = dict((k, sorted(v, key=len, reverse=True)) for k, v in self.items())

    def apply(self, tokens):
        """ Applies the named entity recognizer to the given list of tokens. 
            Each token is a [word, tag]-item whose tag might change to NNP if it is part of an entity.
        """
        if len(self) == 0:
            self.load()
        i = 0
        while i < len(tokens):
            w = tokens[i][0].lower()
            # URL 1: http://domain.com/path
            if w.startswith("http://"):
                tokens[i][1] = self.tag
            # URL 2: www.domain.com
            elif w.startswith("www.") and w.endswith((".com", ".org", ".net")):
                tokens[i][1] = self.tag
            # E-mail address.
            elif "@" in w and RE_EMAIL.match(w):
                tokens[i][1] = self.tag
            # Word matches first word of a named entity.
            # Look ahead to see if consecutive words also match the named entity.
            elif w in self:
                for entity in self[w]:
                    b = True
                    for j, e in enumerate(entity):
                        if i+j >= len(tokens) or tokens[i+j][0].lower() != e:
                            b = False; break
                    if b:
                        for j in range(j+1):
                            tokens[i+j][1] = self.tag
                        i += j
                        break
            i += 1
        return tokens

#### BRILL LEXICON #################################################################################

class Lexicon(dict):
    
    def __init__(self, path=os.path.join(MODULE, "brill-lexicon.txt")):
        self.path = path
        self.lexical_rules = LexicalRules(self)
        self.contextual_rules = ContextualRules(self)
        self.named_entities = NamedEntities(self)
    
    def load(self):
        # Brill's lexicon is a list of common tokens and their part-of-speech tag.
        # It takes a while to load but this happens only once when pattern.en.parser.parse() is called.
        # Create a dictionary from the entries:
        for x in open(self.path).read().decode("utf8").splitlines():
            if not x.startswith(";;;   "): # comment
                x = x.split(" ")[:2]
                dict.__setitem__(self, x[0], x[1])
        
        #dict.__init__(self, (x.split(" ")[:2] for x in open(self.path).read().decode("utf8").splitlines()))
    
    def get(self, word, default=None):
        return word in self and dict.__getitem__(self, word) or default

    def __len__(self):
        if dict.__len__(self) == 0:
            self.load()
        return dict.__len__(self)
    
    def __contains__(self, word):
        if dict.__len__(self) == 0:
            self.load()
        return dict.__contains__(self, word)
    
    def __getitem__(self, word):
        if dict.__len__(self) == 0:
            self.load()
        return dict.__getitem__(self, word)  
    
    def __setitem__(self, word, pos):
        if dict.__len__(self) == 0:
            self.load()
        return dict.__setitem__(self, word, pos)

    def keys(self):
        if dict.__len__(self) == 0:
            self.load()
        return dict.keys(self)

    def values(self):
        if dict.__len__(self) == 0:
            self.load()
        return dict.values(self)

    def items(self):
        if dict.__len__(self) == 0:
            self.load()
        return dict.items(self)