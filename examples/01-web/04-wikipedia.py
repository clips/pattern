import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Wikipedia

# This example retrieves an article from Wikipedia (http://en.wikipedia.org).
# A query requests the article's HTML source from the server, which can be quite slow.
# It is a good idea to cache results from Wikipedia locally,
# and to set a high timeout when calling Wikipedia.search().

engine = Wikipedia(language="en")

# Contrary to other search engines in the module,
# Wikipedia simply returns one MediaWikiArticle object (or None) instead of a list of results.
article = engine.search("alice in wonderland", cached=True, timeout=30)

print article.title               # Article title (may differ from the search query).
print
print article.languages["fr"]     # Article in French, can be retrieved with Wikipedia(language="fr").
print article.links[:10], "..."   # List of linked Wikipedia articles.
print article.external[:5], "..." # List of external URL's.
print

#print article.source # The full article content as HTML.
#print article.string # The full article content, plain text with HTML tags stripped.

# An article is made up of different sections with a title.
# MediaWikiArticle.sections is a list of MediaWikiSection objects.
# Each section has a title + content and can have a linked parent section or child sections.
for s in article.sections:
    print s.title.upper()
    print 
    print s.content # = ArticleSection.string, minus the title.
    print
    