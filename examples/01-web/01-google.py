import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Google, plaintext
from pattern.web import SEARCH, IMAGE, NEWS, BLOG

# The web module has a SearchEngine class with a search() method 
# that yields a list of Result objects.
# Each Result has url, title, date, description, date and author properties.
# Subclasses of SearchEngine include: 
# Google, Yahoo, Bing, Twitter, Wikipedia, Flickr.

# This example retrieves results from Google based on a given query.
# The Google search engine can handle SEARCH, IMAGE, NEWS and BLOG type searches.

# You should obtain your own license key at:
# http://code.google.com/apis/ajaxsearch/signup.html
# Otherwise you will be sharing the default key with all users of this module.
engine = Google(license=None)

q = "as * as a *"
# Veale & Hao's method for finding simile using Google's wildcard (*) support.
# http://afflatus.ucd.ie/Papers/LearningFigurative_CogSci07.pdf)
# This will match results such as 
# - "as light as a feather",
# - "as cute as a cupcake", 
# - "as mad as a hatter", 
# etc.

# Google is very fast but you can only get up to 64 (8x8) results per query.
for i in range(1,8):
    for result in engine.search(q, start=i, type=SEARCH):
        print plaintext(result.description) # plaintext() removes HTML formatting.
        print result.url
        print