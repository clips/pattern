#### PATTERN | EN | PARSE TREE #####################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Implements a Sentence object to traverse sentence words, chunks and prepositions.
# This is probably what you will be working with when processing the output of the parser in Python.
# It is used internally in the PP-attacher and to generate XML and NLTK trees.

# Some basic terminology:
# - sentence: the basic unit of writing, expected to have a subject and a predicate.
# - word: a string of characters that expresses a meaningful concept.
# - token: a specific word with grammatical tags, the word "can" can appear many times in the sentence.
# - chunk: a phrase; a group of words that contains a single thought; phrases make up sentences.
# - argument: a phrase that is related to a verb in a clause, i.e. subject and object.
# - clause: subject + predicate.
# - subject: the person/thing the sentence is about, usually a noun phrase (NP); "[the oval] is white".
# - predicate: the remainder of the sentence tells us what the subject does; "the oval [is white]".
# - object: the person/thing affected by the action; "the shapes form [a circle]".
# - preposition: temporal, spatial or logical relationship; "the oval is [below the rectangle]".
# - copula: a word used to link subject and predicate, typically the verb "to be".
# - lemma: canonical form of a word: "run","runs", "running" are part of a lexeme, "run" is the lemma.
# - pos: part-of-speech, the role that a word or phrase plays in a sentence, e.g. NN (noun).

# Sentence is meant for analysis - no parsing functionality should be added to it.
# All parsing takes place in the parse() function.

try:
    from config import SLASH
    from config import WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA
    MBSP = True
except:
    SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA = \
        "&slash;", "word", "part-of-speech", "chunk", "preposition", "relation", "anchor", "lemma"
    MBSP = False

IOB  = "IOB"  # The I- part of I-NP.
ROLE = "role" # The SBJ part of NP-SBJ-1.

# IOB chunk tags:
BEGIN   = "B"  # Start of chunk, as in B-NP.
INSIDE  = "I"  # Inside a chunk, as in I-NP.
OUTSIDE = "O"  # Outside a chunk (punctuation etc.)

### LIST FUNCTIONS #################################################################################

def find(function, list):
    """ Returns the first item in the list for which function(item) is True, None otherwise.
    """
    for item in list:
        if function(item) == True:
            return item

_zip = zip
def zip(*lists, **default):
    """ Returns a list of tuples, where the i-th tuple contains the i-th element 
        from each of the argument sequences or iterables.
        The default value is appended to the shortest list to match the length of the longest list.
    """
    m = max([len(x) for x in lists])
    return _zip(*[x+[default.get("default", None)]*(m-len(x)) for x in lists])

def unzip(index, list):
    """ Returns the item at the given index from inside each tuple in the list.
    """
    return [item[index] for item in list]

def intersects(list1, list2):
    """ Returns True if list1 and list2 have at least one item in common.
    """
    return find(lambda item: item in list1, list2) is not None

def unique(list):
    """ Returns a copy of the list with unique items, in-order.
    """
    unique, v = [], {}
    for item in list: 
        if item in v: continue 
        unique.append(item); v[item]=1
    return unique

class dynamic_map(list):
    """ Behaves as lambda map() by executing a function on each item in the set.
        Different from map() it does not compute a list copy,
        but fetches items or an iterator on the fly.
    """
    def __init__(self, function=lambda item: item, set=[]):
        self.set = set
        self.function = function
    def __repr__(self):
        return repr([item for item in self])
    def __getitem__(self, index):
        return self.function(self.set[index])
    def __len__(self):
        return len(self.set)
    def __iter__(self):
        i = 0
        while i < len(self.set):
            yield self.function(self.set[i])
            i+=1

### SENTENCE #######################################################################################

encode_entities = lambda string: string.replace("/", SLASH)
decode_entities = lambda string: string.replace(SLASH, "/")

#--- WORD ------------------------------------------------------------------------------------------

class Word(object):

    def __init__(self, sentence, string, lemma=None, type=None, index=0):
        """ A word in the sentence.
            - lemma : base form of the word, e.g. "was" => "be".
            - type  : the part-of-speech tag, e.g. "NN" => a noun.
            - chunk : the chunk (or phrase) this word belongs to.
            - index : the index in the sentence.
        """
        try: string = string.decode("utf-8") # ensure Unicode
        except: 
            pass
        
        self.sentence = sentence
        self.index    = index
        self.string   = string        # laughed
        self.lemma    = lemma         # laugh
        self.type     = type          # VB
        self.chunk    = None          # Chunk object this word belongs to (e.g. VP).
        self.pnp      = None          # PNP chunk object this word belongs to.
                                      # word.chunk and word.pnp are set in chunk.append().
        self.custom_tags = Tags(self) # Additional user-defined tags (e.g. {SENTIMENT: "joy"}).
    
    def copy(self, chunk=None, pnp=None):
        w = Word(
            self.sentence,
            self.string,
            self.lemma,
            self.type,
            self.index)
        w.chunk = chunk
        w.pnp = pnp
        w.custom_tags = Tags(w, items=self.custom_tags)
        return w

    def _get_tag(self):
        return self.type    
    def _set_tag(self, v):
        self.type = v
    tag = pos = part_of_speech = property(_get_tag, _set_tag)
    
    @property
    def phrase(self):
        return self.chunk
    
    @property
    def prepositional_phrase(self):
        return self.pnp
    prepositional_noun_phrase = prepositional_phrase

    @property
    def tags(self):
        """ Yields a list of all the token tags as they appeared when the word was parsed.
            For example: ["was", "VBD", "B-VP", "O", "VP-1", "A1", "be"]
        """
        # See also. Sentence.__repr__()
        # Note: IOB-tags and relations tags can differ from the original MBSP output:
        # - B-VP N-NP I-NP <=> I-VP B-NP I-NP
        # - PP-CLR-1 NP-CLR-1 <=> PP-CLR-1 PP-CLR-1
        # This has no influence when creating a new tree from repr(Sentence).
        ch, I,O,B = self.chunk, INSIDE+"-", OUTSIDE, BEGIN+"-"
        tags = [OUTSIDE for i in range(len(self.sentence.token))]
        for i, tag in enumerate(self.sentence.token): # Default = [WORD, POS, CHUNK, PNP, RELATION, ANCHOR, LEMMA]
            if tag == WORD:
                tags[i] = encode_entities(self.string)
            elif tag == POS and self.type:
                tags[i] = self.type
            elif tag == CHUNK and ch and ch.type:
                tags[i] = (self == ch[0] and B or I) + ch.type
            elif tag == PNP and self.pnp:
                tags[i] = (self == self.pnp[0] and B or I) + "PNP"
            elif tag == REL and ch and len(ch.relations) > 0:
                tags[i] = ["-".join([str(x) for x in [ch.type]+list(reversed(r)) if x]) for r in ch.relations]
                tags[i] = "*".join(tags[i])
            elif tag == ANCHOR and ch:
                tags[i] = ch.anchor_id or OUTSIDE
            elif tag == LEMMA:
                tags[i] = encode_entities(self.lemma or "")
            elif tag in self.custom_tags:
                tags[i] = self.custom_tags.get(tag) or OUTSIDE
        return tags
    
    # User-defined tags are available as Word.tag attributes.
    def __getattr__(self, tag):
        if tag in self.__dict__.get("custom_tags",()):
            return self.__dict__["custom_tags"][tag]
        raise AttributeError, "Word instance has no attribute '%s'" % tag

    # Word.string and unicode(Word) are Unicode strings.
    # repr(Word) is a Python string (with Unicode characters encoded).
    def __unicode__(self):
        return self.string
    def __repr__(self):
        return "Word(%s)" % repr("%s/%s" % (
            encode_entities(self.string),
            self.type is not None and self.type or OUTSIDE))

    def __eq__(self, word):
        return id(self) == id(word)
    def __ne__(self, word):
        return id(self) != id(word)

class Tags(dict):
    
    def __init__(self, word, items=[]):
        # A dictionary of custom word tags.
        # If a new tag is introduced, ensures that is also in Word.sentence.token.
        # This way it won't be forgotten when exporting/importing as XML.
        dict.__init__(self, items)
        self.word = word
    
    def __setitem__(self, k, v):
        dict.__setitem__(self, k, v)
        if k not in reversed(self.word.sentence.token): 
            self.word.sentence.token.append(k)
            
    def setdefault(self, k, v):
        if k not in self: self.__setitem__(k, v); return self[k]

#--- CHUNK -----------------------------------------------------------------------------------------

class Chunk(object):
    
    def __init__(self, sentence, words=[], type=None, role=None, relation=None):
        """ A list of words that make up a phrase in the sentence.
            - type: the part-of-speech tag, e.g. "NP" => a noun phrase, like "the big statue".
            - role: the function of the phrase, e.g. "SBJ" => sentence subject.
            - relation: an id shared with other phrases (e.g. linking subject to object, ...)
        """
        # A chunk can have multiple roles and/or relations in the sentence.
        # Role and relation can therefore also be passed as a list.
        a, b = relation, role
        if not isinstance(a, (list, tuple)):
            a = isinstance(b, (list, tuple)) and [a for x in b] or [a]
        if not isinstance(b, (list, tuple)):
            b = isinstance(a, (list, tuple)) and [b for x in a] or [b]
        relations = [x for x in zip(a,b) if x[0] is not None or x[1] is not None]
        self.sentence     = sentence
        self.words        = []
        self.type         = type      # NP, VP, ADJP ...
        self.relations    = relations # NP-SBJ-1 => [(1, SBJ)]
        self.pnp          = None      # PNP chunk object this chunk belongs to.
        self.anchor       = None      # PNP chunk's anchor.
        self.attachments  = []        # PNP chunks attached to this anchor.
        self.conjunctions = Conjunctions(self)
        self._modifiers   = None
        self._head        = lambda self: self.words[-1]
        self.extend(words)

    def extend(self, words):
        [self.append(word) for word in words]
    
    def append(self, word):
        self.words.append(word)
        word.chunk = self
        
    def __getitem__(self, index):
        return self.words[index]
    def __len__(self):
        return len(self.words)
    def __iter__(self):
        return self.words.__iter__()

    def _get_tag(self):
        return self.type
    def _set_tag(self, v):
        self.type = v
    tag = pos = part_of_speech = property(_get_tag, _set_tag)

    @property
    def start(self):
        return self.words[0].index
    @property
    def stop(self):
        return self.words[-1].index + 1
    @property
    def range(self):
        return range(self.start, self.stop)
    @property
    def span(self):
        return (self.start, self.stop)

    @property
    def lemmata(self):
        return [word.lemma for word in self.words]

    @property
    def tagged(self):
        return [(word.string, word.type) for word in self.words]
    
    @property
    def head(self):
        """ The head of the chunk (i.e. the last word in the chunk).
        """
        return self._head(self) # self.words[-1]

    @property
    def relation(self):
        """ The first relation id of the chunk (i.e. chunk.relations[(2,OBJ), (3,OBJ)])] => 2).
        """
        return len(self.relations) > 0 and self.relations[0][0] or None
        
    @property
    def role(self):
        """ The first role of the chunk (i.e. chunk.relations[(1,SBJ), (1,OBJ)])] => SBJ).
        """
        return len(self.relations) > 0 and self.relations[0][1] or None

    @property
    def subject(self):
        ch = self.sentence.relations["SBJ"].get(self.relation, None)
        if ch != self: 
            return ch
    @property
    def object(self):
        ch = self.sentence.relations["OBJ"].get(self.relation, None)
        if ch != self: 
            return ch
    @property
    def verb(self):
        ch = self.sentence.relations["VP"].get(self.relation, None)
        if ch != self: 
            return ch
    @property
    def related(self):
        """ A list of all the chunks that have the same relation id.
        """
        return [ch for ch in self.sentence.chunks 
                    if ch != self and intersects(unzip(0, ch.relations), unzip(0, self.relations))]

    @property
    def prepositional_phrase(self):
        return self.pnp
    prepositional_noun_phrase = prepositional_phrase

    @property
    def anchor_id(self):
        """ Yields the anchor tag as parsed from the original token.
            For anchor chunks, it has the "A" prefix (e.g. "A1").
            For PNP's attached to an anchor (or chunks inside the PNP), it has the "P" prefix (e.g. "P1").
            A chunk inside a PNP can be both anchor and attachment (e.g. "P1-A2"), as in:
            "stand/A1 in/P1 front/P1-A2 of/P2 people/P2".
        """
        id = ""
        # Yields all anchor tags (e.g. A1, P1, ...) of the given chunk.
        f = lambda ch: filter(lambda k: self.sentence._anchors[k] == ch, self.sentence._anchors)
        if self.pnp and self.pnp.anchor:
            id += "-"+"-".join(f(self.pnp))
        if self.anchor:
            id += "-"+"-".join(f(self))
        if self.attachments:
            id += "-"+"-".join(f(self))
        return id.strip("-") or None

    @property
    def modifiers(self):
        """ For verb phrases (VP), yields a list of nearby adjectives and adverbs with no clear role:
            "the page is [cluttered] with red ovals", "maybe it is green" != "it is green", etc.
        """
        if self._modifiers is None:
            # Modifiers have not been initialized yet:
            # iterate over all the chunks and attach modifiers to their VP-anchor.
            is_modifier = lambda ch: ch.type in ("ADJP", "ADVP") and ch.relation is None
            for chunk in self.sentence.chunks:
                chunk._modifiers = []
            for chunk in filter(is_modifier, self.sentence.chunks):
                anchor = chunk.nearest("VP")
                if anchor: anchor._modifiers.append(chunk)
        return self._modifiers

    def nearest(self, type="VP"):
        """ Returns the nearest chunk in the sentence with the given type.
            We can use this to relate adverbs and adjectives to verbs. 
            For example: "the page [is] [cluttered] with ovals": is <=> cluttered.
        """
        candidate, d = None, len(self.sentence.chunks)
        if isinstance(self, PNPChunk):
            i = self.sentence.chunks.index(self.chunks[0])
        else:
            i = self.sentence.chunks.index(self)
        for j, chunk in enumerate(self.sentence.chunks):
            if chunk.type.startswith(type) and abs(i-j) < d:
                candidate, d = chunk, abs(i-j)
        return candidate
        
    def next(self, type=None):
        """ Returns the next chunk (of the given type) in the sentence.
        """
        i = self.stop
        while i < len(self.sentence):
            if self.sentence[i].chunk is not None and type in (self.sentence[i].chunk.type, None):
                return self.sentence[i].chunk
            i += 1

    def previous(self, type=None):
        """ Returns the next previous (of the given type) in the sentence.
        """
        i = self.start-1
        while i > 0:
            if self.sentence[i].chunk is not None and type in (self.sentence[i].chunk.type, None):
                return self.sentence[i].chunk
            i -= 1

    # Chunk.string and unicode(Chunk) are Unicode strings.
    # repr(Chunk) is a Python string (with Unicode characters encoded).
    @property
    def string(self):
        return u" ".join([word.string for word in self.words])
    def __unicode__(self):
        return self.string
    def __repr__(self):
        return "Chunk(%s)" %  repr("%s/%s%s%s") % (
                self.string,
                self.type is not None and self.type or OUTSIDE, 
                self.role is not None and ("-" + self.role) or "",
            self.relation is not None and ("-" + str(self.relation)) or "")
    
    def __eq__(self, chunk):
        return id(self) == id(chunk)
    def __ne__(self, chunk):
        return id(self) != id(chunk)

# Used in the chunked() function:
class Chink(Chunk):
    def __repr__(self):
        return Chunk.__repr__(self).replace("Chunk(", "Chink(", 1)

#--- PNP CHUNK -------------------------------------------------------------------------------------

class PNPChunk(Chunk):

    def __init__(self, *args, **kwargs):
        """ A chunk used to identify a prepositional noun phrase.
            When the Sentence class has functionality for PP-attachment,
            PNPChunk.anchor will point to the phrase clarified by the preposition,
            for example: "I eat pizza with a fork" => "eat" + "with a fork".
        """
        self.anchor     = None # The anchor chunk (e.g. "eat pizza with fork" => "eat" is anchor of "with fork").
        self.chunks     = []   # The chunks that make up the prepositional noun phrase.
        Chunk.__init__(self, *args, **kwargs)

    def append(self, word):
        self.words.append(word)
        word.pnp = self
        if word.chunk is not None:
            # Collect the chunks that are part of the preposition.
            # This usually involves a PP and a NP chunk ("below/PP the surface/NP"),
            # where the PP is the preposition that can be attached
            # to another phrase, e.g. "What goes on below the surface":
            # "below the surface" <=> "go".
            word.chunk.pnp = self
            if word.chunk not in self.chunks:
                self.chunks.append(word.chunk)

    @property
    def preposition(self):
        """ The first chunk in the prepositional noun phrase, which should be a PP-type chunk.
            PP-chunks are words such as "with" or "underneath".
        """
        return self.chunks[0]
    pp = preposition

    @property
    def phrases(self):
        return self.chunks

    def guess_anchor(self):
        """ Returns a possible anchor chunk for this prepositional noun phrase (without a PP-attacher).
            Often, the nearest verb phrase is a good guess.
        """
        return self.nearest("VP")

#--- CONJUNCTION -----------------------------------------------------------------------------------

CONJUNCT = AND = "AND"
DISJUNCT = OR  = "OR"

class Conjunctions(list):
    
    def __init__(self, chunk):
        """ A chunk property containing other chunks participating in a conjunction,
            e.g. "clear skies AND sunny beaches".
            Each item in the list is a (chunk, conjunction)-tuple, with conjunction either AND or OR.
        """
        list.__init__(self)
        self.anchor = chunk

    def append(self, chunk, type=CONJUNCT):
        list.append(self, (chunk, type))

#--- SENTENCE --------------------------------------------------------------------------------------

_UID = 0
def _uid():
    global _UID; _UID+=1; return _UID

def _is_tokenstring(string):
    # The class mbsp.TokenString stores the format of tags for each token.
    # Since it comes directly from MBSP.parse(), this format is always correct,
    # regardless of the given token format parameter for Sentence() or Text().
    return isinstance(string, unicode) and hasattr(string, "tags")

class Sentence:

    def __init__(self, string="", token=[WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA], language="en"):
        """ A search object for sentence words, chunks and prepositions.
            The input is a tagged string from MBSP.parse(). 
            The order in which token tags appear can be specified.
        """
        # Extract token format from TokenString if possible.
        if _is_tokenstring(string):
            token, language = string.tags, getattr(string, "language", language)
        # Ensure Unicode.
        if isinstance(string, str):
            for encoding in (("utf-8",), ("windows-1252",), ("utf-8", "ignore")):
                try: string = string.decode(*encoding)
                except:
                    pass
        self.parent      = None # Slices will refer to the sentence they are part of.
        self.text        = None # Text object this sentence is part of.
        self.language    = language
        self.id          = _uid()
        self.token       = list(token)
        self.words       = []
        self.chunks      = [] # Words grouped in chunk ranges.
        self.pnp         = [] # Words grouped in prepositional noun phrase ranges.
        self._anchors    = {} # Anchor tags related to anchor chunks or attached PNP's.
        self._relation   = None # Helper variable: the last chunk's relation and role.
        self._attachment = None # Helper variable: the last attachment tag (e.g. P1) parsed in _do_pnp().
        self._previous   = None # Helper variable: the last token parsed in parse_token().
        self.relations   = { "SBJ":{}, "OBJ":{}, "VP":{} }
        
        for chars in string.split(" "):
            if len(chars) > 0:
                # Split the slash-formatted token into the separate tags according to the given order.
                # Append Word and Chunk objects according to the token's tags.
                self.append(*self.parse_token(chars, token))

    @property
    def word(self):
        return self.words

    @property
    def lemmata(self):
        return dynamic_map(lambda w: w.lemma, self.words)
        #return [word.lemma for word in self.words]
    lemma = lemmata

    @property
    def parts_of_speech(self):
        return dynamic_map(lambda w: w.type, self.words)
        #return [word.type for word in self.words]
    pos = parts_of_speech

    @property
    def tagged(self):
        return [(word.string, word.type) for word in self]
        
    @property
    def phrases(self):
        return self.chunks
    chunk = phrases

    @property
    def prepositional_phrases(self):
        return self.pnp
    prepositional_noun_phrases = prepositional_phrases

    @property
    def start(self):
        return 0
    @property
    def stop(self):
        return self.start + len(self.words)

    @property
    def nouns(self):
        return [word for word in self if word.type.startswith("NN")]
    @property
    def verbs(self):
        return [word for word in self if word.type.startswith("VB")]
    @property
    def adjectives(self):
        return [word for word in self if word.type.startswith("JJ")]

    @property
    def subjects(self):
        return self.relations["SBJ"].values()
    @property
    def objects(self):
        return self.relations["OBJ"].values()
    @property
    def verbs(self):
        return self.relations["VP"].values()
        
    @property
    def anchors(self):
        return [chunk for chunk in self.chunks if len(chunk.attachments) > 0]

    @property
    def is_question(self):
        return len(self) > 0 and str(self[-1]) == "?"
    @property
    def is_exclamation(self):
        return len(self) > 0 and str(self[-1]) == "!"

    def __getitem__(self, index):
        return self.words[index]
    def __len__(self):
        return len(self.words)
    def __iter__(self):
        return self.words.__iter__()
    
    def append(self, word, lemma=None, type=None, chunk=None, role=None, relation=None, pnp=None, anchor=None, iob=None, custom={}):
        """ Appends the next word to the sentence and attaches words, chunks, prepositions.
            The tagged tokens from the parser's output simply need to be split and passed to Sentence.append().
            - word     : the current word.
            - lemma    : lemmatized form of the word.
            - type     : part-of-speech tag for the word (NN, JJ, ...).
            - chunk    : part-of-speech tag for the chunk this word is part of (NP, VP, ...).
            - role     : the chunk's grammatical role (SBJ, OBJ, ...).
            - relation : an id shared by other related chunks (e.g. SBJ-1 <=> VP-1).
            - pnp      : PNP if this word is in a prepositional noun phrase (BEGIN- prefix optional).
            - iob      : BEGIN if the word marks the start of a new chunk.
                         INSIDE (optional) if the word is part of the previous chunk.
            - custom   : a dictionary of (tag, value)-items for user-defined word tags.
        """
        self._do_word(word, lemma, type)           # Appends a new Word object.
        self._do_chunk(chunk, role, relation, iob) # Appends a new Chunk, or adds the last word to the last chunk.
        self._do_relation()
        self._do_pnp(pnp, anchor)
        self._do_anchor(anchor)
        self._do_custom(custom)
        self._do_conjunction()

    def parse_token(self, token, tags=[WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA]):
        """ Returns the arguments for Sentence.append() from a tagged token representation.
            The order in which token tags appear can be specified.
            The default order is: word, part-of-speech, (IOB-)chunk, (IOB-)preposition, 
            chunk(-relation)(-role), anchor, lemma, separated by slashes. 
            As in:
            I/PRP/B-NP/O/NP-SBJ-1/O/i 
            eat/VBP/B-VP/O/VP-1/A1/eat
            pizza/NN/B-NP/O/NP-OBJ-1/O/pizza 
            with/IN/B-PP/B-PNP/PP/P1/with 
            a/DT/B-NP/I-PNP/NP/P1/a 
            fork/NN/I-NP/I-PNP/NP/P1/fork 
            ././O/O/O/O/.
            Returns a (word, lemma, type, chunk, role, relation, preposition, anchor, iob, custom)-tuple,
            i.e. you can do Sentence.append(*Sentence.parse_token("airplane/NN"))
            The custom value is a dictionary of (tag, value)-items of unrecognized tags in the token.
        """
        p = { WORD: "", 
               POS: None, 
               IOB: None,
             CHUNK: None,
               PNP: None,
               REL: None,
              ROLE: None,
            ANCHOR: None,
             LEMMA: None }
        custom = [tag for tag in tags if tag not in p] # Tags for custom parsers, e.g. a SENTIMENT-tag.
        p.update(dict.fromkeys(custom, None))
        # Split the slash-formatted token into the separate tags according to the given order.
        # Convert &slash; characters (usually in words and lemmata).
        # Assume None for missing tags (except the word itself, which defaults to an empty string).
        token = token.split("/")
        for i in range(min(len(token), len(tags))):
            if token[i] != OUTSIDE \
             or tags[i] in (WORD, LEMMA): # In "O is part of the alphabet" => "O" != OUTSIDE.
                p[tags[i]] = decode_entities(token[i])
        # Split I/B prefix from the chunk tag:
        # B- marks the start of a new chunk, I- marks inside of a chunk.
        if p[CHUNK] is not None:
            x = p[CHUNK].split("-")
            if len(x) == 2: p[CHUNK] = x[1]; p[IOB] = x[0] # B-NP
            if len(x) == 1: p[CHUNK] = x[0]                # NP        
        # Split the role from the relation:
        # NP-SBJ-1 => relation id is 1 and role SBJ, VP-1 => relation id is 1 and no role.
        # Note: tokens can be tagged with multiple relations (e.g. NP-OBJ-1*NP-OBJ-3).
        if p[REL] is not None:
            ch, p[REL], p[ROLE] = self._parse_relation(p[REL])
            # We can derive a (missing) chunk tag from the relation tag (e.g. NP-SBJ-1 => NP).
            # For PP relation tags (e.g. PP-CLR-1), the first chunk is PP, the following chunks NP.
            if ch == "PP" and self._previous \
                            and self._previous[REL]  == p[REL] \
                            and self._previous[ROLE] == p[ROLE]: ch = "NP"
            if not p[CHUNK] and ch != OUTSIDE:
                p[CHUNK] = ch
        self._previous = p
        # Return the tags in the same order as the parameters for Sentence.append().
        custom = dict([(tag, p[tag]) for tag in custom])
        return p[WORD], p[LEMMA], p[POS], p[CHUNK], p[ROLE], p[REL], p[PNP], p[ANCHOR], p[IOB], custom
    
    def _parse_relation(self, tag):
        """ Parses the role and relation id from the token relation tag.
            About 20 percent of sentences parsed by MBSP have chunks with multiple relations:
            - VP                => VP, [], []
            - VP-1              => VP, [1], [None]
            - NP-SBJ-1          => NP, [1], [SBJ]
            - NP-OBJ-1*NP-OBJ-2 => NP, [1,2], [OBJ,OBJ]
            - NP-SBJ;NP-OBJ-1   => NP, [1,1], [SBJ,OBJ]
        """
        chunk, relation, role = None, [], []
        for s in tag.split("*"):
            if ";" in s:
                id = ([None]+s.split("-"))[-1] # NP-SBJ;NP-OBJ-1 => 1 relates to both SBJ and OBJ.
                id = id is not None and "-"+id or ""
                s = s.replace(";", id+";")
                s = s.split(";")
            else:
                s = [s]
            for s in s:
                s = s.split("-")
                if len(s) == 1: chunk = s[0]
                if len(s) == 2: chunk = s[0]; relation.append(s[1]); role.append(None)
                if len(s) >= 3: chunk = s[0]; relation.append(s[2]); role.append(s[1])
        for i, x in enumerate(relation):
            if x is not None:
                try: relation[i] = int(x)
                except: # Correct ADJP-PRD => ADJP, [PRD], [None] to ADJP, [None], [PRD].
                    relation[i], role[i] = None, x
        return chunk, relation, role
    
    def _do_word(self, word, lemma=None, type=None):
        """ Adds a new Word to the sentence.
            Other Sentence._do_[tag] functions assume a new word has just been appended.
        """
        # Improve 3rd person singular "'s" lemma to "be", e.g. as in "he's fine".
        if lemma == "'s" and type == "VBZ":
            lemma = "be"
        self.words.append(Word(self, word, lemma, type, index=len(self.words)))     

    def _do_chunk(self, type, role=None, relation=None, iob=None):
        """ Either adds a new Chunk to the sentence, or adds the last word to the previous chunk.
            The word is attached to the previous chunk if both type and relation match,
            and if the word's chunk tag does not start with "B-" (i.e. iob != BEGIN).
            Punctuation marks (or other "O" chunk tags) are not chunked.
        """
        O = (None, OUTSIDE)
        if type in O and relation in O and role in O: 
            return
        if len(self.chunks) > 0 \
         and self.chunks[-1].type == type \
         and self._relation == (relation, role) \
         and not iob == BEGIN \
         and not self.words[-2].chunk is None: # As for me, I'm off => me + I are different chunks
            self.chunks[-1].append(self.words[-1])
        else:
            ch = Chunk(self, [self.words[-1]], type, role, relation)
            self.chunks.append(ch)
            self._relation = (relation, role)
    
    def _do_relation(self):
        """ Attaches subjects, objects and verbs.
            If the previous chunk is a subject/object/verb it is stored in Sentence.relations{}.
        """
        if len(self.chunks) > 0:
            ch = self.chunks[-1]
            for ch_relation, ch_role in [x for x in ch.relations if x[1] in ("SBJ", "OBJ")]:
                self.relations[ch_role][ch_relation] = ch
            if ch.type in ("VP",):
                self.relations[ch.type][ch.relation] = ch

    def _do_pnp(self, pnp, anchor=None):
        """ Attach prepositional noun phrases.
            We can identify PNP's from either the PNP tag or the P-attachment tag.
            This does not yet determine the PP-anchor, only groups words in a PNP chunk.
        """
        P = find(lambda x: x.startswith("P"), anchor and anchor.split("-") or [])
        if pnp and pnp.endswith("PNP") or P is not None:
            if (pnp and pnp != "O" \
             and len(self.pnp) > 0 \
             and not pnp.startswith("B") \
             and not self.words[-2].pnp is None \
            ) or (P is not None and P == self._attachment):
                self.pnp[-1].append(self.words[-1])
            else:
                ch = PNPChunk(self, [self.words[-1]], type="PNP")
                self.pnp.append(ch)
            self._attachment = P
    
    def _do_anchor(self, anchor):
        """ Collect preposition anchors and attachments in a dictionary as we iterate words.
            Once the dictionary has an entry for both the anchor and the attachment we can link them.
        """
        for x in (anchor and anchor.split("-") or []):
            A, P = None, None
            if x.startswith("A") and len(self.chunks) > 0: # anchor
                A, P = x, x.replace("A","P")
                self._anchors[A] = self.chunks[-1]
            if x.startswith("P") and len(self.pnp) > 0:    # attachment (PNP)
                A, P = x.replace("P","A"), x
                self._anchors[P] = self.pnp[-1]
            if A in self._anchors and P in self._anchors and not self._anchors[P].anchor:
                pnp = self._anchors[P]
                pnp.anchor = self._anchors[A]
                pnp.anchor.attachments.append(pnp)
                
    def _do_custom(self, custom):
        """ Adds the user-defined tags to the last word.
            Custom tags can be used to add extra semantical meaning or metadata to words.
        """
        self.words[-1].custom_tags = Tags(self.words[-1], custom)

    def _do_conjunction(self):
        """ Attach conjunctions.
            CC-words like "and" / "or" between two chunks indicate a conjunction.
        """
        if len(self.words) > 2 and self.words[-2].type == "CC":
            if self.words[-2].chunk is None:
                cc  = self.words[-2].string.lower() == "and" and AND or OR
                ch1 = self.words[-3].chunk
                ch2 = self.words[-1].chunk
                if ch1 is not None and ch2 is not None:
                    ch1.conjunctions.append(ch2, cc)
                    ch2.conjunctions.append(ch1, cc)

    def get(self, index, tag=LEMMA):
        """ Returns a tag for the word at the given index.
            The tag can be WORD, LEMMA, POS, CHUNK, PNP, RELATION, ROLE, ANCHOR or a custom word tag.
        """
        if tag == WORD:
            return self.words[index]
        if tag == LEMMA:
            return self.words[index].lemma
        if tag == POS:
            return self.words[index].type
        if tag == CHUNK:
            return self.words[index].chunk
        if tag == PNP:
            return self.words[index].pnp
        if tag == REL:
            ch = self.words[index].chunk; return ch and ch.relation
        if tag == ROLE:
            ch = self.words[index].chunk; return ch and ch.role
        if tag == ANCHOR:
            ch = self.words[index].pnp; return ch and ch.anchor
        if tag in self.words[index].custom_tags:
            return self.words[index].custom_tags[tag]
        return None
        
    def loop(self, *tags):
        """ Iterates over the tags in the entire Sentence,
            e.g. Sentence.loop(POS, LEMMA) yields tuples of the part-of-speech tags and lemmata. 
            Possible tags: WORD, LEMMA, POS, CHUNK, PNP, RELATION, ROLE, ANCHOR or a custom word tag.
            Any order or combination of tags can be supplied.
        """
        for i in range(len(self.words)):
            yield tuple([self.get(i, tag=tag) for tag in tags])  

    def indexof(self, value, tag=WORD):
        """ Returns the indices of tokens in the sentence where the given token tag equals the string.
            The string can contain a wildcard "*" at the end (this way "NN*" will match "NN" and "NNS").
            The tag can be WORD, LEMMA, POS, CHUNK, PNP, RELATION, ROLE, ANCHOR or a custom word tag.
            For example: Sentence.indexof("VP", tag=CHUNK) 
            returns the indices of all the words that are part of a VP chunk.
        """
        match = lambda a, b: a.endswith("*") and b.startswith(a[:-1]) or a==b
        indices = []
        for i in range(len(self.words)):
            if match(value, unicode(self.get(i, tag))):
                indices.append(i)
        return indices

    def slice(self, start, stop):
        """ Returns a portion of the sentence from word start index to word stop index.
            The returned slice is a subclass of Sentence and a deep copy.
        """
        s = Slice(token=self.token, language=self.language)
        for i, word in enumerate(self.words[start:stop]):
            # The easiest way to copy (part of) a sentence
            # is by unpacking all of the token tags and passing them to Sentence.append().
            p0 = word.string                                                       # WORD
            p1 = word.lemma                                                        # LEMMA
            p2 = word.type                                                         # POS
            p3 = word.chunk is not None and word.chunk.type or None                # CHUNK
            p4 = word.pnp is not None and "PNP" or None                            # PNP
            p5 = word.chunk is not None and unzip(0, word.chunk.relations) or None # REL            
            p6 = word.chunk is not None and unzip(1, word.chunk.relations) or None # ROLE
            p7 = word.chunk and word.chunk.anchor_id or None                       # ANCHOR
            p8 = word.chunk and word.chunk.start == start+i and BEGIN or None      # IOB
            p9 = word.custom_tags                                                  # User-defined tags.
            # If the given range does not contain the chunk head, remove the chunk tags.
            if word.chunk is not None and (word.chunk.stop > stop):
                p3, p4, p5, p6, p7, p8 = None, None, None, None, None, None
            # If the word starts the preposition, add the IOB B-prefix (i.e. B-PNP).
            if word.pnp is not None and word.pnp.start == start+i:
                p4 = BEGIN+"-"+"PNP"
            # If the given range does not contain the entire PNP, remove the PNP tags.
            # The range must contain the entire PNP, 
            # since it starts with the PP and ends with the chunk head (and is meaningless without these).
            if word.pnp is not None and (word.pnp.start < start or word.chunk.stop > stop):
                p4, p7 = None, None
            s.append(word=p0, lemma=p1, type=p2, chunk=p3, pnp=p4, relation=p5, role=p6, anchor=p7, iob=p8, custom=p9)
        s.parent = self
        s.start = start
        return s

    def copy(self):
        return self.slice(0, len(self))
        
    def chunked(self):
        return chunked(self)
        
    def constituents(self, pnp=False):
        """ Returns an in-order list of the top Chunk and Word objects.
            With pnp=True, also contains PNPChunk objects whenever possible.
        """
        a = []
        for word in self.words:
            if pnp and word.pnp is not None:
                if len(a) == 0 or a[-1] != word.pnp:
                    a.append(word.pnp)
            elif word.chunk is not None:
                if len(a) == 0 or a[-1] != word.chunk:
                    a.append(word.chunk)
            else:
                a.append(word)
        return a

    # Sentence.string and unicode(Sentence) are Unicode strings.
    # repr(Sentence) is a Python strings (with Unicode characters encoded).
    @property
    def string(self):
        return u" ".join([word.string for word in self])
    def __unicode__(self):
        return self.string
    def __repr__(self):
        return "Sentence(%s)" % repr(" ".join(["/".join(word.tags) for word in self.words]).encode("utf-8"))
        
    def __eq__(self, other):
        if not isinstance(other, Sentence): return False
        return len(self) == len(other) \
          and repr(self) == repr(other)

    @property
    def xml(self):
        """ The sentence in XML format.
        """
        return parse_xml(self, tab="\t", id=self.id or "")
        
    @classmethod
    def from_xml(cls, xml):
        s = parse_string(xml)
        return Sentence(s.split("\n")[0], token=s.tags, language=s.language)
        
    def nltk_tree(self):
        """ The sentence as an nltk.tree object.
        """
        return nltk_tree(self)

class Slice(Sentence):
    pass

#---------------------------------------------------------------------------------------------------
# s = split(parse("black cats and white dogs"))
# s.words           => [Word('black/JJ'), Word('cats/NNS'), Word('and/CC'), Word('white/JJ'), Word('dogs/NNS')]
# s.chunks          => [Chunk('black cats/NP'), Chunk('white dogs/NP')]
# s.constituents(s) => [Chunk('black cats/NP'), Word('and/CC'), Chunk('white dogs/NP')]
# chunked(s)        => [Chunk('black cats/NP'), Chink('and/O'), Chunk('white dogs/NP')]

def chunked(sentence):
    """ Returns a list of Chunk and Chink objects from the given sentence.
        Chink is a subclass of Chunk used for words that have Word.chunk==None
        (e.g. punctuation marks, conjunctions).
    """
    # For example: to create an instance that uses the head of previous chunks as feature.
    # Doing this with Sentence.chunks would lose the punctuation and conjunction words
    # (Sentence.chunks only has Chunk objects) which can be useful as feature.
    chunks = []
    for word in sentence:
        if word.chunk is not None:
            if len(chunks) == 0 or chunks[-1] != word.chunk:
                chunks.append(word.chunk)
        else:
            ch = Chink(sentence)
            ch.append(word.copy(ch))
            chunks.append(ch)
    return chunks

#--- TEXT ------------------------------------------------------------------------------------------

class Text(list):
    
    def __init__(self, string, token=[WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA], language="en", encoding="utf-8"):
        """ A list of Sentence objects parsed from the given string.
            The string is the unicode return value from MBSP.parse().
        """
        self.encoding = encoding
        # Extract token format from TokenString if possible.
        if _is_tokenstring(string):
            token, language = string.tags, getattr(string, "language", language)
        if string:
            for s in string.split("\n"):
                self.append(Sentence(s, token, language))
    
    def insert(self, index, sentence):
        list.insert(self, index, sentence)
        self[-1].text = self
    def append(self, sentence):
        list.append(self, sentence)
        self[-1].text = self
    def extend(self, sentences):
        for s in sentences:
            self.append(s)
            
    def remove(self, sentence):
        list.remove(self, sentence)
        sentence.text = None
    def pop(self, index):
        sentence = list.pop(self, index)
        sentence.text = None
        return sentence
    
    @property
    def sentences(self):
        return list(self)
        
    def copy(self):
        t = Text("", encoding=self.encoding)
        for sentence in self:
            t.append(sentence.copy())
        return t
    
    # Text.string and unicode(Text) are Unicode strings.
    @property
    def string(self):
        return u"\n".join([unicode(sentence) for sentence in self])
    def __unicode__(self):
        return self.string
    #def __repr__(self):
    #    return "\n".join([repr(sentence) for sentence in self])

    @property
    def xml(self):
        """ The text in XML-format.
            This groups all the sentences and wraps them in a <text> element.
        """
        xml = []
        xml.append('<?xml version="1.0" encoding="%s"?>' % XML_ENCODING.get(self.encoding, self.encoding))
        xml.append("<%s>" % XML_TEXT)
        xml.extend([sentence.xml for sentence in self])
        xml.append("</%s>" % XML_TEXT)
        return "\n".join(xml)
        
    @classmethod
    def from_xml(cls, xml):
        return Text(parse_string(xml))

def split(string, token=[WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA]):
    """ Transforms the output from MBSP.parse() into a Text object.
        The token parameter lists the order of tags in each token in the input string.
    """
    return Text(string, token)

def xml(string, token=[WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA]):
    """ Transforms the output from MBSP.parse() into XML.
        The token parameter lists the order of tags in each token in the input string.
    """
    return Text(string, token).xml

### XML ############################################################################################

# Elements:
XML_TEXT     = "text"     # <text>, corresponds to Text object.
XML_SENTENCE = "sentence" # <sentence>, corresponds to Sentence object.
XML_CHINK    = "chink"    # <chink>, where word.chunk.type=None.
XML_CHUNK    = "chunk"    # <chunk>, corresponds to Chunk object.
XML_PNP      = "chunk"    # <chunk type="PNP">, corresponds to PNP chunk object.
XML_WORD     = "word"     # <word>, corresponds to Word object

# Attributes:
XML_LANGUAGE = "language" # <sentence language="">, defines the language used.
XML_TOKEN    = "token"    # <sentence token="">, defines the order of tags in a token.
XML_TYPE     = "type"     # <word type="">, <chunk type="">
XML_RELATION = "relation" # <chunk relation="">
XML_ID       = "id"       # <chunk id="">
XML_OF       = "of"       # <chunk of=""> corresponds to id-attribute.
XML_ANCHOR   = "anchor"   # <chunk anchor=""> corresponds to id-attribute.
XML_LEMMA    = "lemma"    # <word lemma="">

XML_ENCODING = {
            'utf8' : 'UTF-8', 
           'utf-8' : 'UTF-8', 
           'utf16' : 'UTF-16', 
          'utf-16' : 'UTF-16',
           'latin' : 'ISO-8859-1', 
          'latin1' : 'ISO-8859-1', 
         'latin-1' : 'ISO-8859-1', 
          'cp1252' : 'windows-1252', 
    'windows-1252' : 'windows-1252'
}

def xml_encode(string):
    """ Returns the string with XML-safe special characters.
    """
    string = string.replace("&", "&amp;")
    string = string.replace("<", "&lt;")
    string = string.replace(">", "&gt;")
    string = string.replace("\"","&quot;")
    string = string.replace(SLASH, "/")
    return string
    
def xml_decode(string):
    """ Returns the string with special characters decoded.
    """
    string = string.replace("&amp;", "&")
    string = string.replace("&lt;",  "<")
    string = string.replace("&gt;",  ">")
    string = string.replace("&quot;","\"")
    string = string.replace("/", SLASH)
    return string

#--- SENTENCE TO XML -------------------------------------------------------------------------------

# Relation id's in the XML output are relative to the sentence id,
# so relation 1 in sentence 2 = "2.1".
_UID_SEPARATOR = "."

def parse_xml(sentence, tab="\t", id=""):
    """ Returns the given Sentence object as an XML-string.
        The tab delimiter is used as indendation for nested elements.
        The id can be used as a unique identifier per sentence for chunk id's and anchors.
        For example: "I eat pizza with a fork." =>
        
        <sentence token="word, part-of-speech, chunk, preposition, relation, anchor, lemma" language="en">
            <chunk type="NP" relation="SBJ" of="1">
                <word type="PRP" lemma="i">I</word>
            </chunk>
            <chunk type="VP" relation="VP" id="1" anchor="A1">
                <word type="VBP" lemma="eat">eat</word>
            </chunk>
            <chunk type="NP" relation="OBJ" of="1">
                <word type="NN" lemma="pizza">pizza</word>
            </chunk>
            <chunk type="PNP" of="A1">
                <chunk type="PP">
                    <word type="IN" lemma="with">with</word>
                </chunk>
                <chunk type="NP">
                    <word type="DT" lemma="a">a</word>
                    <word type="NN" lemma="fork">fork</word>
                </chunk>
            </chunk>
            <chink>
                <word type="." lemma=".">.</word>
            </chink>
        </sentence>
    """
    uid  = lambda *parts: "".join([str(id), _UID_SEPARATOR ]+[str(x) for x in parts]).lstrip(_UID_SEPARATOR)
    push = lambda indent: indent+tab         # push() increases the indentation.
    pop  = lambda indent: indent[:-len(tab)] # pop() decreases the indentation.
    indent = tab
    xml = []
    # Start the sentence element:
    # <sentence token="word, part-of-speech, chunk, preposition, relation, anchor, lemma">
    xml.append('<%s%s %s="%s" %s="%s">' % (
        XML_SENTENCE,
        XML_ID and " %s=\"%s\"" % (XML_ID, str(id)) or "",
        XML_TOKEN, ", ".join(sentence.token),
        XML_LANGUAGE, sentence.language
    ))
    # Collect chunks that are PNP anchors and assign id.
    anchors = {}
    for chunk in sentence.chunks:
        if chunk.attachments:
            anchors[chunk.start] = len(anchors) + 1
    # Traverse all words in the sentence.
    for word in sentence.words:
        chunk = word.chunk
        pnp   = word.chunk and word.chunk.pnp or None
        # Start the PNP element if the chunk is the first chunk in PNP:
        # <chunk type="PNP" of="A1">
        if pnp and pnp.start == chunk.start:
            a = pnp.anchor and ' %s="%s"' % (XML_OF, uid("A", anchors.get(pnp.anchor.start, ""))) or ""
            xml.append(indent + '<%s %s="PNP"%s>' % (XML_CHUNK, XML_TYPE, a))
            indent = push(indent)
        # Start the chunk element if the word is the first word in the chunk:
        # <chunk type="VP" relation="VP" id="1" anchor="A1">
        if chunk and chunk.start == word.index:
            if chunk.relations:
                # Create the shortest possible attribute values for multiple relations, 
                # e.g. [(1,"OBJ"),(2,"OBJ")]) => relation="OBJ" id="1|2"
                r1 = unzip(0, chunk.relations) # Relation id's.
                r2 = unzip(1, chunk.relations) # Relation roles.
                r1 = [x is None and "-" or uid(x) for x in r1]
                r2 = [x is None and "-" or x for x in r2]
                r1 = not len(unique(r1)) == 1 and "|".join(r1) or (r1+[None])[0]
                r2 = not len(unique(r2)) == 1 and "|".join(r2) or (r2+[None])[0]
            xml.append(indent + '<%s%s%s%s%s%s>' % (
                XML_CHUNK,
                chunk.type and ' %s="%s"' % (XML_TYPE, chunk.type) or "",
                chunk.relations and chunk.role != None and ' %s="%s"' % (XML_RELATION, r2) or "",
                chunk.relation  and chunk.type == "VP" and ' %s="%s"' % (XML_ID, uid(chunk.relation)) or "",
                chunk.relation  and chunk.type != "VP" and ' %s="%s"' % (XML_OF, r1) or "",
                chunk.attachments and ' %s="%s"' % (XML_ANCHOR, uid("A",anchors[chunk.start])) or ""
            ))
            indent = push(indent)
        # Words outside of a chunk are wrapped in a <chink> tag:
        # <chink>
        if not chunk:
            xml.append(indent + '<%s>' % XML_CHINK)
            indent = push(indent)
        # Add the word element:
        # <word type="VBP" lemma="eat">eat</word>
        xml.append(indent + '<%s%s%s%s>%s</%s>' % (
            XML_WORD,
            word.type and ' %s="%s"' % (XML_TYPE, xml_encode(word.type)) or '',
            word.lemma and ' %s="%s"' % (XML_LEMMA, xml_encode(word.lemma)) or '',
            (" "+" ".join(['%s="%s"' % (k,v) for k,v in word.custom_tags.items() if v != None])).rstrip(),
            xml_encode(unicode(word)),
            XML_WORD
        ))
        if not chunk:
            # Close the <chink> element if outside of a chunk.
            indent = pop(indent); xml.append(indent + "</%s>" % XML_CHINK)
        if chunk and chunk.stop-1 == word.index:
            # Close the <chunk> element if this is the last word in the chunk.
            indent = pop(indent); xml.append(indent + "</%s>" % XML_CHUNK)
        if pnp and pnp.stop-1 == word.index:
            # Close the PNP element if this is the last word in the PNP.
            indent = pop(indent); xml.append(indent + "</%s>" % XML_CHUNK)
    xml.append("</%s>" % XML_SENTENCE)
    # Return as a plain str.
    return "\n".join(xml).encode("utf-8")

#--- XML TO SENTENCE(S) ----------------------------------------------------------------------------

# Helper functions for parsing XML:
def children(node):
    return node.childNodes
def value(node):
    return filter(lambda n: n.nodeType == n.TEXT_NODE, node.childNodes)[0].data
def attr(node, attribute, default=""):
    return node.getAttribute(attribute) or default
def is_tag(node, tag):
    return node.nodeType == node.ELEMENT_NODE and node.tagName == tag

# The structure of linked anchor chunks and PNP attachments
# is collected from _parse_token() calls.
_anchors     = {} # {u'A1': [[u'eat', u'VBP', u'B-VP', 'O', u'VP-1', 'O', u'eat', 'O']]}
_attachments = {} # {u'A1': [[[u'with', u'IN', u'B-PP', 'B-PNP', u'PP', 'O', u'with', 'O'], 
                  #           [u'a', u'DT', u'B-NP', 'I-PNP', u'NP', 'O', u'a', 'O'], 
                  #           [u'fork', u'NN', u'I-NP', 'I-PNP', u'NP', 'O', u'fork', 'O']]]}

# This is a fallback if for some reason we fail to import MBSP.TokenString,
# e.g. when tree.py is part of another project.
class TaggedString(unicode):
    def __new__(cls, string, tags=["word"], language="en"):
        if isinstance(string, unicode) and hasattr(string, "tags"): 
            tags, language = string.tags, getattr(string, "language", language)
        s = unicode.__new__(cls, string)
        s.tags = list(tags)
        s.language = language
        return s

def parse_string(xml):
    """ Returns a slash-formatted string from the given XML representation.
        The return value is a TokenString (see mbsp.py).
    """
    string = ""
    from xml.dom.minidom import parseString
    dom = parseString(xml)
    # Traverse all the <sentence> elements in the XML.
    for sentence in dom.getElementsByTagName(XML_SENTENCE):
        _anchors.clear()     # Populated by calling _parse_tokens().
        _attachments.clear() # Populated by calling _parse_tokens().
        # Parse the language from <sentence language="">.
        language = attr(sentence, XML_LANGUAGE, "en")
        # Parse the token tag format from <sentence token="">.
        # This information is returned in TokenString.tags,
        # so the format and order of the token tags is retained when exporting/importing as XML.
        format = attr(sentence, XML_TOKEN, [WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA])
        format = not isinstance(format, basestring) and format or format.replace(" ","").split(",")
        # Traverse all <chunk> and <chink> elements in the sentence.
        # Find the <word> elements inside and create tokens.
        tokens = []
        for chunk in children(sentence):
            tokens.extend(_parse_tokens(chunk, format))
        # Attach PNP's to their anchors.
        # Keys in _anchors have linked anchor chunks (each chunk is a list of tokens).
        # The keys correspond to the keys in _attachments, which have linked PNP chunks.
        if ANCHOR in format:
            A, P, a, i = _anchors, _attachments, 1, format.index(ANCHOR)
            for id in sorted(A.keys()):
                for token in A[id]:
                    token[i] += "-"+"-".join(["A"+str(a+p) for p in range(len(P[id]))])
                    token[i]  = token[i].strip("O-")
                for p, pnp in enumerate(P[id]):
                    for token in pnp: 
                        token[i] += "-"+"P"+str(a+p)
                        token[i]  = token[i].strip("O-")
                a += len(P[id])
        # Collapse the tokens to string.
        # Separate multiple sentences with a new line.
        tokens = ["/".join([tag for tag in token]) for token in tokens]
        tokens = " ".join(tokens)
        string += tokens + "\n"
    # Return a TokenString, which is a unicode string that transforms easily
    # into a plain str, a list of tokens, or a Sentence.
    try:
        if MBSP: from mbsp import TokenString
        return TokenString(string, tags=format, language=language)
    except:
        return TaggedString(string, tags=format, language=language)

def _parse_tokens(chunk, format=[WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA]):
    """ Parses tokens from <word> elements in the given XML <chunk> element.
        Returns a flat list of tokens, in which each token is [WORD, POS, CHUNK, PNP, RELATION, ANCHOR, LEMMA].
        If a <chunk type="PNP"> is encountered, traverses all of the chunks in the PNP.
    """
    tokens = []
    # Only process <chunk> and <chink> elements, 
    # text nodes in between return an empty list.
    if not (is_tag(chunk, XML_CHUNK) or is_tag(chunk, XML_CHINK)):
        return []
    type = attr(chunk, XML_TYPE, "O")
    if type == "PNP":
        # For, <chunk type="PNP">, recurse all the child chunks inside the PNP.
        for ch in children(chunk):
            tokens.extend(_parse_tokens(ch, format))
        # Tag each of them as part of the PNP.
        if PNP in format:
            i = format.index(PNP)
            for j, token in enumerate(tokens):
                token[i] = (j==0 and "B-" or "I-") + "PNP"
        # Store attachments so we can construct anchor id's in parse_string().
        # This has to be done at the end, when all the chunks have been found.
        a = attr(chunk, XML_OF).split(_UID_SEPARATOR)[-1]
        if a:
            _attachments.setdefault(a, [])
            _attachments[a].append(tokens)
        return tokens
    # For <chunk type-"VP" id="1">, the relation is VP-1.
    # For <chunk type="NP" relation="OBJ" of="1">, the relation is NP-OBJ-1.
    relation = _parse_relation(chunk, type)
    # Process all of the <word> elements in the chunk, for example:
    # <word type="NN" lemma="pizza">pizza</word> => [pizza, NN, I-NP, O, NP-OBJ-1, O, pizza]
    for word in filter(lambda n: is_tag(n, XML_WORD), children(chunk)):
        tokens.append(_parse_token(word, chunk=type, relation=relation, format=format))
    # Add the IOB chunk tags:
    # words at the start of a chunk are marked with B-, words inside with I-.
    if CHUNK in format:
        i = format.index(CHUNK)
        for j, token in enumerate(tokens):
            token[i] = token[i] != "O" and ((j==0 and "B-" or "I-") + token[i]) or "O"
    # The chunk can be the anchor of one or more PNP chunks.
    # Store anchors so we can construct anchor id's in parse_string().
    a = attr(chunk, XML_ANCHOR, "").split(_UID_SEPARATOR)[-1]
    if a: 
        _anchors[a] = tokens
    return tokens

def _parse_relation(chunk, type="O"):
    """ Returns a string of the roles and relations parsed from the given <chunk> element.
        The chunk type (which is part of the relation string) can be given as parameter.
    """
    r1 = attr(chunk, XML_RELATION)
    r2 = attr(chunk, XML_ID, attr(chunk, XML_OF))
    r1 = [x != "-" and x or None for x in r1.split("|")] or [None]
    r2 = [x != "-" and x or None for x in r2.split("|")] or [None]
    r2 = [x is not None and x.split(_UID_SEPARATOR )[-1] or x for x in r2]
    if len(r1) < len(r2): r1 = r1 + r1 * (len(r2)-len(r1)) # [1] ["SBJ", "OBJ"] => "SBJ-1;OBJ-1"
    if len(r2) < len(r1): r2 = r2 + r2 * (len(r1)-len(r2)) # [2,4] ["OBJ"] => "OBJ-2;OBJ-4"
    return ";".join(["-".join([x for x in (type, r1, r2) if x]) for r1, r2 in zip(r1, r2)])    

def _parse_token(word, chunk="O", pnp="O", relation="O", anchor="O", 
                 format=[WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA]):
    """ Returns a list of token tags parsed from the given <word> element.
        Tags that are not attributes in a <word> (e.g. relation) can be given as parameters.
    """
    tags = []
    for tag in format:
        if   tag == WORD   : tags.append(xml_decode(value(word)))
        elif tag == POS    : tags.append(xml_decode(attr(word, XML_TYPE, "O")))
        elif tag == CHUNK  : tags.append(chunk)
        elif tag == PNP    : tags.append(pnp)
        elif tag == REL    : tags.append(relation)
        elif tag == ANCHOR : tags.append(anchor)
        elif tag == LEMMA  : tags.append(xml_decode(attr(word, XML_LEMMA, "")))
        else:
            # Custom tags when MBSP has been extended, see also Word.custom_tags{}.
            tags.append(xml_decode(attr(word, tag, "O")))
    return tags

### NLTK TREE ######################################################################################

def nltk_tree(sentence):
    """ Returns an NLTK nltk.tree.Tree object from the given Sentence.
        The NLTK module should be on the search path somewhere.
    """
    from nltk import tree
    def do_pnp(pnp):
        # Returns the PNPChunk (and the contained Chunk objects) in NLTK bracket format.
        s = ' '.join([do_chunk(ch) for ch in pnp.chunks])
        return '(PNP %s)' % s
    
    def do_chunk(ch):
        # Returns the Chunk in NLTK bracket format. Recurse attached PNP's.
        s = ' '.join(['(%s %s)' % (w.pos, w.string) for w in ch.words])
        s+= ' '.join([do_pnp(pnp) for pnp in ch.attachments])
        return '(%s %s)' % (ch.type, s)
    
    T = ['(S']
    v = [] # PNP's already visited.
    for ch in sentence.chunked():
        if not ch.pnp and isinstance(ch, Chink):
            T.append('(%s %s)' % (ch.words[0].pos, ch.words[0].string))
        elif not ch.pnp:
            T.append(do_chunk(ch))
        #elif ch.pnp not in v:
        elif ch.pnp.anchor is None and ch.pnp not in v:
            # The chunk is part of a PNP without an anchor.
            T.append(do_pnp(ch.pnp))
            v.append(ch.pnp)
    T.append(')')
    return tree.bracket_parse(' '.join(T))

### GRAPHVIZ DOT ###################################################################################

BLUE = {
       '' : ("#f0f5ff", "#000000"),
     'VP' : ("#e6f0ff", "#000000"),
    'SBJ' : ("#64788c", "#ffffff"),
    'OBJ' : ("#64788c", "#ffffff"),
}

def _colorize(x, colors):
    s = ''
    if isinstance(x, Word):
        x = x.chunk
    if isinstance(x, Chunk):
        s = ',style=filled, fillcolor="%s", fontcolor="%s"' % ( \
            colors.get(x.role) or \
            colors.get(x.type) or \
            colors.get('') or ("none", "black"))
    return s

def graphviz_dot(sentence, font="Arial", colors=BLUE):
    """ Returns a dot-formatted string that can be visualized as a graph in GraphViz.
    """
    s  = 'digraph sentence {\n'
    s += '\tranksep=0.75;\n'
    s += '\tnodesep=0.15;\n'
    s += '\tnode [penwidth=1, fontname="%s", shape=record, margin=0.1, height=0.35];\n' % font
    s += '\tedge [penwidth=1];\n'
    s += '\t{ rank=same;\n'
    # Create node groups for words, chunks and PNP chunks.
    for w in sentence.words:
        s += '\t\tword%s [label="<f0>%s|<f1>%s"%s];\n' % (w.index, w.string, w.type, _colorize(w, colors))
    for w in sentence.words[:-1]:
        # Invisible edges forces the words into the right order:
        s += '\t\tword%s -> word%s [color=none];\n' % (w.index, w.index+1)
    s += '\t}\n'
    s += '\t{ rank=same;\n'        
    for i, ch in enumerate(sentence.chunks):
        s += '\t\tchunk%s [label="<f0>%s"%s];\n' % (i+1, "-".join([x for x in (
            ch.type, ch.role, str(ch.relation or '')) if x]) or '-', _colorize(ch, colors))
    for i, ch in enumerate(sentence.chunks[:-1]):
        # Invisible edges forces the chunks into the right order:
        s += '\t\tchunk%s -> chunk%s [color=none];\n' % (i+1, i+2)
    s += '}\n'
    s += '\t{ rank=same;\n'
    for i, ch in enumerate(sentence.pnp):
        s += '\t\tpnp%s [label="<f0>PNP"%s];\n' % (i+1, _colorize(ch, colors))
    s += '\t}\n'
    s += '\t{ rank=same;\n S [shape=circle, margin=0.25, penwidth=2]; }\n'
    # Connect words to chunks.
    # Connect chunks to PNP or S.
    for i, ch in enumerate(sentence.chunks):
        for w in ch:
            s += '\tword%s -> chunk%s;\n' % (w.index, i+1)
        if ch.pnp:
            s += '\tchunk%s -> pnp%s;\n' % (i+1, sentence.pnp.index(ch.pnp)+1)
        else:
            s += '\tchunk%s -> S;\n' % (i+1)
        if ch.type == 'VP':
            # Indicate related chunks with a dotted
            for r in ch.related:
                s += '\tchunk%s -> chunk%s [style=dotted, arrowhead=none];\n' % (
                    i+1, sentence.chunks.index(r)+1)
    # Connect PNP to anchor chunk or S.
    for i, ch in enumerate(sentence.pnp):
        if ch.anchor:
            s += '\tpnp%s -> chunk%s;\n' % (i+1, sentence.chunks.index(ch.anchor)+1)
            s += '\tpnp%s -> S [color=none];\n' % (i+1)
        else:
            s += '\tpnp%s -> S;\n' % (i+1)
    s += "}"
    return s

### STDOUT TABLE ###################################################################################

def table(sentence, fill=1, placeholder="-"):
    """ Returns a string where the tags of tokens in the sentence are organized in outlined columns.
    """
    tags  = [WORD, POS, IOB, CHUNK, ROLE, REL, PNP, ANCHOR, LEMMA]
    tags += [tag for tag in sentence.token if tag not in tags]
    def format(token, tag):
        # Returns the token tag as a string.
        if   tag == WORD   : s = token.string
        elif tag == POS    : s = token.type
        elif tag == IOB    : s = token.chunk and (token.index == token.chunk.start and "B" or "I")
        elif tag == CHUNK  : s = token.chunk and token.chunk.type
        elif tag == ROLE   : s = token.chunk and token.chunk.role
        elif tag == REL    : s = token.chunk and token.chunk.relation and str(token.chunk.relation)
        elif tag == PNP    : s = token.chunk and token.chunk.pnp and token.chunk.pnp.type
        elif tag == ANCHOR : s = token.chunk and token.chunk.anchor_id
        elif tag == LEMMA  : s = token.lemma
        else               : s = token.custom_tags.get(tag)
        return s or placeholder
    def outline(column, fill=1, padding=3, align="left"):
        # Add spaces to each string in the column so they line out to the highest width.
        n = max([len(x) for x in column]+[fill])
        if align == "left"  : return [x+" "*(n-len(x))+" "*padding for x in column]
        if align == "right" : return [" "*(n-len(x))+x+" "*padding for x in column]
    
    # Gather the tags of the tokens in the sentece per column.
    # If the IOB-tag is I-, mark the chunk tag with "^".
    # Add the tag names as headers in each column.
    columns = [[format(token, tag) for token in sentence] for tag in tags]
    columns[3] = [columns[3][i]+(iob == "I" and " ^" or "") for i, iob in enumerate(columns[2])]
    del columns[2]
    for i, header in enumerate(['word', 'tag', 'chunk', 'role', 'id', 'pnp', 'anchor', 'lemma']+tags[9:]):
        columns[i].insert(0, "")
        columns[i].insert(0, header.upper())
    # The left column (the word itself) is outlined to the right,
    # and has extra spacing so that words across sentences line out nicely below each other.
    for i, column in enumerate(columns):
        columns[i] = outline(column, fill+10*(i==0), align=("left","right")[i==0])
    # Anchor column is useful in MBSP but not in pattern.en.
    if not MBSP:
        del columns[6] 
    # Create a string with one row (i.e. one token) per line.
    return "\n".join(["".join([x[i] for x in columns]) for i in range(len(columns[0]))])
    