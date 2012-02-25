import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Google, plaintext
from pattern.web import SEARCH

# The web module has a SearchEngine class with a search() method 
# that yields a list of Result objects.
# Each Result has url, title, description, language, author and date and properties.
# Subclasses of SearchEngine include: 
# Google, Yahoo, Bing, Twitter, Facebook, Wikipedia, Flickr.

# This example retrieves results from Google based on a given query.
# The Google search engine can handle SEARCH type searches.

# Google's "Custom Search API" is a paid service.
# The web module uses a test account with a 100 free queries per day, shared with all users.
# If the limit is exceeded, SearchEngineLimitError is raised.
# You can obtain your own license key at: https://code.google.com/apis/console/
# Activate "Custom Search API" under "Services" and get the key under "API Access".
# Then use Google(license=[YOUR_KEY]).search().
# This will give you 100 personal free queries, or 5$ per 1000 queries.
engine = Google(license=None, language="en")

# Veale & Hao's method for finding simile using Google's wildcard (*) support.
# http://afflatus.ucd.ie/Papers/LearningFigurative_CogSci07.pdf)
# This will match results such as "as light as a feather", "as cute as a cupcake", etc.
q = "as * as a *"

# Google is very fast but you can only get up to 100 (10x10) results per query.
for i in range(1,2):
    for result in engine.search(q, start=i, count=10, type=SEARCH):
        print plaintext(result.description) # plaintext() removes HTML formatting.
        print result.url
        print result.date
        print