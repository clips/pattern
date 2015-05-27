import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Newsfeed, plaintext, URL
from pattern.db  import date

# This example reads a given RSS or Atom newsfeed channel.
# Some example feeds to try out:
NATURE  = "http://feeds.nature.com/nature/rss/current"
SCIENCE = "http://www.sciencemag.org/rss/podcast.xml"
NYT     = "http://rss.nytimes.com/services/xml/rss/nyt/GlobalHome.xml"
TIME    = "http://feeds.feedburner.com/time/topstories"
CNN     = "http://rss.cnn.com/rss/edition.rss"

engine = Newsfeed()

for result in engine.search(CNN, cached=True):
    print(result.title.upper())
    print(plaintext(result.text))  # Remove HTML formatting.
    print(result.url)
    print(result.date)
    print("")

# News item URL's lead to the page with the full article.
# This page can have any kind of formatting.
# There is no default way to read it.
# But we could just download the source HTML and convert it to plain text:

#html = URL(result.url).download()
#print(plaintext(html))

# The resulting text may contain a lot of garbage.
# A better way is to use a DOM parser to select the HTML elements we want.
# This is demonstrated in one of the next examples.