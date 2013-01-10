# -*- coding: utf-8 *-*
import os, sys, pprint; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Wikia

# This example retrieves articled from Wikia (http://www.wikia.com),
# a collection of thousands of wikis based on MediaWiki (i.e., what Wikipedia uses too).
# A query requests the article's HTML source from the server, which can be quite slow.

domain = "runescape" # A popular wiki...
if len(sys.argv) > 1:
    domain = sys.argv[1]

w = Wikia(domain, language="en")

# Just like Wikipedia, we can search for article titles.
# However, we may not know what articles exist.
# We can iterate through all articles with the Wikia.articles() method.
# Note that Wikipedia also has a Wikipedia.articles() method.

# The "count" parameter sets the number of article titles
# to retrieve per query to Wikia. Retrieving the full article
# for each article takes another query, so the process can be quite slow.
i = 0
for article in w.articles(count=2, cached=True):
    print
    print article.title
    #print article.plaintext()
    i += 1
    if i >= 3:
        break

# We can retrieve just the titles, and only retrieve the full articles
# of the ones we need:
i = 0
for title in w.list(count=2):
    print
    print title
    #article = w.search(title)
    #print article.plaintext()
    i += 1
    if i >= 3:
        break
