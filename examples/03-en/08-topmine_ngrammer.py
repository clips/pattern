from __future__ import print_function
from __future__ import unicode_literals

from builtins import str, bytes, dict, int

import os
import sys
import codecs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pattern.text as text_module
from pattern.text.en.wordlist import STOPWORDS

paths = []
for f in os.listdir('./texts'):
    paths.append('./texts/' + f)

texts = []
for p in paths:
    with codecs.open(p, "rb", encoding='latin-1') as f:
        if sys.version_info[0] < 3:
            texts.append(f.read())
        else:
            texts.append(str(f.read()))

ng = text_module.train_topmine_ngrammer(texts, threshhold=1, regexp="[^a-zA-Z0-9]")
ngrams = text_module.topmine_ngramms(texts[0], ng, threshhold=1)



print("\n")
bigrams = []
trigrams = []
for key in ngrams.keys():
    if len(key.split("_")) == 2:
        bigrams.append(key)
    elif len(key.split("_")) == 3:
        trigrams.append(key)

print("Extracted {} bigrams:\n".format(len(bigrams)))
print(bigrams)
print("\n")

print("Extracted {} trigrams:\n".format(len(trigrams)))
print(trigrams)
print("\n")


# as we can see the extracted ngrams contain many stopwords, so, it's important to delete all
# stopwords before applying the algorythm

ng = text_module.train_topmine_ngrammer(texts, threshhold=1, regexp="[^a-zA-Z0-9]", stopwords=STOPWORDS)
ngrams = text_module.topmine_ngramms(texts[0], ng, threshhold=1)


# as we can see the extracted ngrams contain many stopwords, so, it's important to delete all
# stopwords before applying the algorythm
print("\n")
bigrams = []
trigrams = []
for key in ngrams.keys():
    if len(key.split("_")) == 2:
        bigrams.append(key)
    elif len(key.split("_")) == 3:
        trigrams.append(key)

print("Extracted {} bigrams (removed stopwords):\n".format(len(bigrams)))
print(bigrams)
print("\n")

print("Extracted {} trigrams (removed stopwords):\n".format(len(trigrams)))
print(trigrams)
print("\n")
