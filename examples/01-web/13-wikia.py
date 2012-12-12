# -*- coding: utf-8 *-*
import os, sys, pprint; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Wikia, WikiaArticleSet, URLTimeout

# This example retrieves an article from Wikipedia (http://en.wikipedia.org).
# A query requests the article's HTML source from the server, which can be quite slow.
# It is a good idea to cache results from Wikipedia locally,
# and to set a high timeout when calling Wikipedia.search().

domain = 'runescape' # popular wiki
if len(sys.argv) > 1:
    domain = sys.argv[1]

engine = Wikia(language="en",domain=domain)

ArticleSet = WikiaArticleSet( engine, iterationLimit=200 )

counter = 0
try:
    for page in ArticleSet:
        print counter, page.title
        counter = counter + 1
except URLTimeout:
    print "Timeout error."
