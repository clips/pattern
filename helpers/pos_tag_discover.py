# CREDIT: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html

def lookup_full(pos_tag):
    dictionary = {"CC": "Coordinating conjunction",
                  "CD": "Cardinal number",
                  "DT": "Determiner",
                  "EX": "Existential there",
                  "FW": "Foreign word",
                  "IN": "Preposition or subordinating conjunction",
                  "JJ": "Adjective",
                  "JJR": "Adjective, comparative",
                  "JJS": "Adjective, superlative",
                  "LS": "List item marker",
                  "MD": "Modal",
                  "NN": "Noun, singular or mass",
                  "NNS": "Noun, plural",
                  "NNP": "Proper noun, singular",
                  "NNPS": "Proper noun, plural",
                  "PDT": "Predeterminer",
                  "POS": "Possessive ending",
                  "PRP": "Personal pronoun",
                  "PRP$": "Possessive pronoun",
                  "RB": "Adverb",
                  "RBR": "Adverb, comparative",
                  "RBS": "Adverb, superlative",
                  "RP": "Particle",
                  "SYM": "Symbol",
                  "TO": "to",
                  "UH": "Interjection",
                  "VB": "Verb, base form",
                  "VBD": "Verb, past tense",
                  "VBG": "Verb, gerund or present participle",
                  "VBN": "Verb, past participle",
                  "VBP": "Verb, non-3rd person singular present",
                  "VBZ": "Verb, 3rd person singular present",
                  "WDT": "Wh-determiner",
                  "WP": "Wh-pronoun",
                  "WP$": "Possessive wh-pronoun",
                  "WRB": "Wh-adverb"}
    if pos_tag in dictionary:
        return dictionary[pos_tag]
    else:
        raise ValueError("There is no POS tag,", pos_tag)


def lookup_short(part_of_speech):
    dictionary = {"CC": "Coordinating conjunction",
                  "CD": "Cardinal number",
                  "DT": "Determiner",
                  "EX": "Existential there",
                  "FW": "Foreign word",
                  "IN": "Preposition or subordinating conjunction",
                  "JJ": "Adjective",
                  "JJR": "Adjective, comparative",
                  "JJS": "Adjective, superlative",
                  "LS": "List item marker",
                  "MD": "Modal",
                  "NN": "Noun, singular or mass",
                  "NNS": "Noun, plural",
                  "NNP": "Proper noun, singular",
                  "NNPS": "Proper noun, plural",
                  "PDT": "Predeterminer",
                  "POS": "Possessive ending",
                  "PRP": "Personal pronoun",
                  "PRP$": "Possessive pronoun",
                  "RB": "Adverb",
                  "RBR": "Adverb, comparative",
                  "RBS": "Adverb, superlative",
                  "RP": "Particle",
                  "SYM": "Symbol",
                  "TO": "to",
                  "UH": "Interjection",
                  "VB": "Verb, base form",
                  "VBD": "Verb, past tense",
                  "VBG": "Verb, gerund or present participle",
                  "VBN": "Verb, past participle",
                  "VBP": "Verb, non-3rd person singular present",
                  "VBZ": "Verb, 3rd person singular present",
                  "WDT": "Wh-determiner",
                  "WP": "Wh-pronoun",
                  "WP$": "Possessive wh-pronoun",
                  "WRB": "Wh-adverb"}
    dictionary = {v: k for k, v in dictionary.items()}
    if part_of_speech in dictionary:
        return dictionary[part_of_speech]
    else:
        raise ValueError("There is no POS,", part_of_speech)
