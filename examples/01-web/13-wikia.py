# -*- coding: utf-8 *-*
import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Wikia, MediaWikiArticleSet

# This example retrieves an article from Wikipedia (http://en.wikipedia.org).
# A query requests the article's HTML source from the server, which can be quite slow.
# It is a good idea to cache results from Wikipedia locally,
# and to set a high timeout when calling Wikipedia.search().

domain = 'runescape' # popular wiki
if len(sys.argv) > 1:
    domain = sys.argv[1]

engine = Wikia(language="en",domain=domain)

set = MediaWikiArticleSet( engine, iterationLimit=200 )

for page in set:
    print page.title
    print page.source
