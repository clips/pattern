import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.server import App
from pattern.server import static
from pattern.server import HTTPError

# The pattern.server module allows you to run a pure-Python web server.
# It is built on CherryPy and inspired by Flask and bottle.py.

# This example demonstrates a basic web app.
# At the bottom of the script is a call to app.run().
# So, to start the web server, run this script.

# If you make any changes to the script and save it,
# the server automatically restarts to reflect the changes.
# If the server is running in "production mode", i.e., app.run(debug=False),
# it will not restart automatically.

app = App(name="basic", static="static/")

# Here are some properties of the app.
# app.path yields the absolute path to the app folder.
# app.static yields the absolute path to the folder for static content.

print app.name
print app.path
print app.static

# The @app.route() decorator can be used to define a URL path handler.
# A path handler is simply a Python function that returns a string,
# which will be displayed in the browser.
# For example, visit http://127.0.0.1:8080/:

@app.route("/")
def index():
    return "Hello world!"

# The index() function handles requests at http://127.0.0.1:8080/,
# but no other paths. If you'd visit http://127.0.0.1:8080/ponies,
# a 404 error will be raised, since there is no "/ponies" handler.

# The @app.error() decorator can be used to catch errors.
# In this case it prints out the error status and a traceback.

# The traceback will always be an empty string 
# when you are running a production server, i.e., app.run(debug=False).
# You want to see errors during development, i.e., app.run(debug=True).
# You don't want to confront users with them when the app is live
# (or let hackers learn from them).

@app.error("404")
def error_404(error):
    return "<h1>%s</h1>\n%s\n<pre>%s</pre>" % (
        error.status, 
        error.message, 
        error.traceback
    )
    
# URL handler functions can take positional arguments and keyword arguments.
# Positional arguments correspond to the URL path.
# Keyword arguments correspond to query parameters.

# The products() function below handles requests at http://127.0.0.1:8080/products/.
# Notice how it takes an "name" parameter, which is a subpath.
# When you browse http://127.0.0.1:8080/products/, name=None.
# When you browse http://127.0.0.1:8080/products/iphone, name="iphone".
# When you browse http://127.0.0.1:8080/products/iphone/reviews, a 404 error is raised.

@app.route("/products")
def products(name):
    return (
        "<html>",
        "<head></head>",
        "<body>View product: " + (name or "") + "</body>",
        "</html>"
    )
    
# To catch any kind of subpath, use Python's *path notation.
# For http://127.0.0.1:8080/products2/, path=().
# For http://127.0.0.1:8080/products2/iphone, path=("iphone",).
# For http://127.0.0.1:8080/products2/iphone/reviews, path=("iphone", "reviews")

@app.route("/products2")
def products2(*path):
    #print path
    if len(path) == 0:
        return "product overview"
    if len(path) == 1:
        return "product %s detail page" % path[0]
    if len(path) == 2 and path[1] == "reviews":
        return "product reviews for %s" % path[0]
    # Uncaught subpaths raise a 404 error.
    raise HTTPError(404)
    
# You can also use keyword arguments.
# These correspond to query parameters (i.e., the "?x=y" part of a URL).
# Query parameters from HTML forms can be sent to the server by GET or POST.
# GET sends the parameters as part of the URL.
# POST sends the parameters in the background. They can hold longer strings.
# For example, browse to http://127.0.0.1:8080/review and fill in the form.
# Observe the URL when you click "submit".
# Observe how the data in <textarea name='text'> is passed to
# the function's optional "text" parameter:

@app.route("/review")
def review(text=""):
    if text:
        s = "You wrote: " + text
    else:
        s = ""
    return (
        s, 
        "<form method='get'>",
        "<textarea name='text'></textarea>",
        "<br><input type='submit'>",
        "</form>"
    )
    
# To accept any number of query parameters, use Python's **data notation.
# The keyword argument "data" will be a dictionary with all query parameters.

# Images, CSS, etc. can be placed in the static folder.
# Take a look in /01-basic/static. There's a "cat.jpg".
# Static files are accessible from the web, e.g.,
# http://127.0.0.1:8080/cat.jpg

# So, you can refer to them in HTML code:
# http://127.0.0.1:8080/cat
@app.route("/cat")
def cat():
    return "<p>A cat.</p><img src='cat.jpg'>"

# http://127.0.0.1:8080/cat-alias.jpg
@app.route("/cat-alias.jpg")
def cat_alias():
    return static("cat.jpg", root=app.static)

# That's it. There is lot more you can do, but the general idea is:
# 1) Create an App.
# 2) Register URL handlers with @app.route().
# 3) Start the server with app.run().

app.run("127.0.0.1", port=8080, debug=True)