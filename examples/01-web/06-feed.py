import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Newsfeed, plaintext, URL
from pattern.db  import date

# This example reads a given RSS or Atom newsfeed channel.
# Some sample newsfeeds to try out:
NATURE  = "http://www.nature.com/nature/current_issue/rss/index.html"
SCIENCE = "http://www.sciencemag.org/rss/podcast.xml"
HERALD  = "http://www.iht.com/rss/frontpage.xml"
TIME    = "http://feeds.feedburner.com/time/topstories"
CNN     = "http://rss.cnn.com/rss/edition.rss"

engine = Newsfeed()

for result in engine.search(CNN, cached=True):
    print result.title.upper()
    print plaintext(result.description) # Remove HTML formatting.
    print result.url
    print result.date
    print

# Newsfeed item URL's lead to the page with the full article.
# Since this page can have any kind of formatting, there is no default way to read it,
# but we can simply download the source HTML and convert it to plain text:
#html = URL(result.url).download()
#print plaintext(html)

# The resulting text can contain a lot of garbage.
# An better way to do this is to use a DOM parser and select the HTML elements we want.
# This is demonstrated in the next example.