import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Bing, asynchronous, plaintext
from pattern.web import SEARCH, IMAGE, NEWS

import time

# This example retrieves results from Bing based on a given query.
# Yahoo can retrieve up to a 1000 results (10x100) for a query.

# You should obtain your own license key at:
# https://developer.apps.yahoo.com/wsregapp/
# Otherwise you will be sharing the default license with all users of this module.
engine = Bing(license=None, language="en")

# Quote a query to match it exactly:
q = "\"is more important than\""

# When you execute a query, the script will halt until all results are downloaded.
# In applications with an event loop (e.g. a GUI or an interactive animation)
# it is more useful if the app keeps on running while the search is executed in the background.
# This can be achieved with the asynchronous() command.
# It takes any function and the function's arguments and keyword arguments:
request = asynchronous(engine.search, q, start=1, count=100, type=SEARCH, timeout=10)

# This while-loop simulates an application event loop.
# In a real-world example you would have an app.update() or similar
# in which you can check request.done every now and then.
while not request.done:
    time.sleep(0.01)
    print ".",

print
print

# An error occured in engine.search(), raise it.
if request.error:
    raise request.error

# Retrieve the list of search results.
for result in request.value:
    print result.description
    print result.url
    print
    