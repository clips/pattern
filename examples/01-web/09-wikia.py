# -*- coding: utf-8 *-*
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Wikia

# This example retrieves articled from Wikia (http://www.wikia.com).
# Wikia is a collection of thousands of wikis based on MediaWiki.
# Wikipedia is based on MediaWiki too.
# Wikia queries request the article HTML source from the server. This can be slow.

domain = "monkeyisland"  # "Look behind you, a three-headed monkey!"

# Alternatively, you can call this script from the commandline
# and specify another domain: python 09-wikia.py "Bieberpedia".
if len(sys.argv) > 1:
    domain = sys.argv[1]

w = Wikia(domain, language="en")

# Like Wikipedia, we can search for articles by title with Wikia.search():
print(w.search("Three Headed Monkey"))

# However, we may not know exactly what kind of articles exist,
# three-headed monkey" for example does not redirect to the above article.

# We can iterate through all articles with the Wikia.articles() method
# (note that Wikipedia also has a Wikipedia.articles() method).
# The "count" parameter sets the number of article titles to retrieve per query. 
# Retrieving the full article for each article takes another query. This can be slow.
i = 0
for article in w.articles(count=2, cached=True):
    print("")
    print(article.title)
    #print(article.plaintext())
    i += 1
    if i >= 3:
        break

# Alternatively, we can retrieve just the titles, 
# and only retrieve the full articles for the titles we need:
i = 0
for title in w.index(count=2):
    print("")
    print(title)
    #article = w.search(title)
    #print(article.plaintext())
    i += 1
    if i >= 3:
        break
