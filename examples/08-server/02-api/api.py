import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.server import App
from pattern.server import MINUTE, HOUR, DAY

from pattern.text import language

app = App("api")

# The language() function in pattern.text guesses the language of a given string. 
# For example: language("In French, goodbye is au revoir.") returns ("en", 0.83).
# It can handle "en", "es", "de", "fr", "nl", "it" with reasonable accuracy.

# To create a web service like Google Translate with pattern.server is easy.
# Normally, URL handlers return a string with the contents of that web page.
# If we return a dictionary instead, it will be formatted as a JSON-string,
# the data interchange format used by many popular web services.

# So clients (e.g., a user's Python script) can query the web service URL
# and catch the JSON reply.

# There is only one tricky part: rate limiting.
# Note the "limit", "time" and "key" parameters in @app.route() below.
# We'll explain them in more detail.

# First, run the script and visit:
# http://127.0.0.1:8080/language?q=in+french+goodbye+is+au+revoir

# You should see some JSON-output:
# {"language": "en", "confidence": 0.83}

@app.route("/language", limit=100, time=HOUR)
def predict_language(q=""):
    #print q
    iso, confidence = language(q) # (takes some time to load the first time)
    return {
          "language": iso, 
        "confidence": round(confidence, 2)
    }
    
# When you set up a web service, expect high traffic peaks.
# For example, a user may have 10,000 sentences
# and send them all at once in a for-loop to our web service:

# import urrlib
# import json
# for s in sentences[:10000]:
#     url = "http://127.0.0.1:8080/language?q=" + s.replace(" ", "-")
#     data = urllib.urlopen(url).read()
#     data = json.loads(data)

# Rate limiting caps the number of allowed requests for a user.
# In this example, limit=100 and time=HOUR means up to a 100 requests/hour.
# After that, the user will get a HTTP 429 Too Many Requests error.

# The example below demonstrates how rates can be set up per user.
# In this case, only the user with key=1234 is allowed access.
# All other requests will generate a HTTP 403 Forbidden error.
# A user can pass his personal key as a query parameter, e.g.,
# http://127.0.0.1:8080/language/paid?q=hello&key=1234

# Check personal keys instead of IP-address:
@app.route("/language/paid", limit=True, key=lambda data: data.get("key"))
def predict_language_paid(q="", key=None):
    return {"language": language(q)[0]}
    
# Create an account for user with key=1234 (do once).
# You can generate fairly safe keys with app.rate.key().
if not app.rate.get(key="1234", path="/language/paid"):
    app.rate.set(key="1234", path="/language/paid", limit=10000, time=DAY)
    
# Try it out with the key and without the key:
# http://127.0.0.1:8080/language/paid?q=hello&key=1234
# http://127.0.0.1:8080/language/paid?q=hello           (403 error)

# A rate.db SQLite database was created in the current folder.
# If you want to give it another name, use App(rate="xxx.db").
# To view the contents of the database,we use the free 
# SQLite Database Browser (http://sqlitebrowser.sourceforge.net).

# If the web service is heavily used,
# we may want to use more threads for concurrent requests
# (default is 30 threads with max 20 queueing):

app.run("127.0.0.1", port=8080, threads=100, queue=50)