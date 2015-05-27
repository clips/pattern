import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Google, plaintext
from pattern.web import SEARCH

# The pattern.web module has a SearchEngine class,
# with a SearchEngine.search() method that yields a list of Result objects.
# Each Result has url, title, text, language, author and date and properties.
# Subclasses of SearchEngine include: 
# Google, Bing, Yahoo, Twitter, Facebook, Wikipedia, Wiktionary, Flickr, ...

# This example retrieves results from Google based on a given query.
# The Google search engine can handle SEARCH type searches.
# Other search engines may also handle IMAGE, NEWS, ...

# Google's "Custom Search API" is a paid service.
# The pattern.web module uses a test account by default,
# with a 100 free queries per day shared by all Pattern users.
# If this limit is exceeded, SearchEngineLimitError is raised.
# You should obtain your own license key at: 
# https://code.google.com/apis/console/
# Activate "Custom Search API" under "Services" and get the key under "API Access".
# Then use Google(license=[YOUR_KEY]).search().
# This will give you 100 personal free queries, or 5$ per 1000 queries.
engine = Google(license=None, language="en")

# Veale & Hao's method for finding similes using wildcards (*):
# http://afflatus.ucd.ie/Papers/LearningFigurative_CogSci07.pdf
# This will match results such as:
# - "as light as a feather",
# - "as cute as a cupcake",
# - "as drunk as a lord",
# - "as snug as a bug", etc.
q = "as * as a *"

# Google is very fast but you can only get up to 100 (10x10) results per query.
for i in range(1, 2):
    for result in engine.search(q, start=i, count=10, type=SEARCH, cached=True):
        print(plaintext(result.text)) # plaintext() removes all HTML formatting.
        print(result.url)
        print(result.date)
        print("")