import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import GOOGLE, YAHOO, BING, sort

# The pattern.web module includes an interesting sort() algorithm.
# Ir classifies search terms according to a search engine's total results count.
# When a context is defined, it sorts according to relevancy to the context:
# sort(terms=["black", "green", "red"], context="Darth Vader") =>
# yields "black" as the best candidate, 
# because "black Darth Vader" yields more search results.

results = sort(
      terms = [
        "arnold schwarzenegger", 
        "chuck norris", 
        "dolph lundgren", 
        "steven seagal",
        "sylvester stallone", 
        "mickey mouse",
        ],
    context = "dangerous", # Term used for sorting.
    service = BING,        # GOOGLE, YAHOO, BING, ...
    license = None,        # You should supply your own API license key for the given service.
     strict = True,        # Wraps the query in quotes, i.e. 'mac sweet'. 
    reverse = True,        # Reverses term and context: 'sweet mac' instead of 'mac sweet'.
     cached = True)
    
for weight, term in results:
    print "%5.2f" % (weight * 100) + "%", term