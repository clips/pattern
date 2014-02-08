import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.server import App, template, threadsafe

from codecs import open

# This example demonstrates a simple wiki served by pattern.server.
# A wiki is a web app where each page can be edited (e.g, Wikipedia).
# We will store the contents of each page as a file in /data.

app = App(name="wiki")

# Our wiki app has a single URL handler listening at the root ("/").
# It takes any combination of positional and keyword arguments.
# This means that any URL will be routed to the index() function.
# For example, http://127.0.0.1:8080/pages/bio.html?edit calls index()
# with path=("pages", "bio.html") and data={"edit": ""}.

@app.route("/")
def index(*path, **data):
    #print "path:", path
    #print "data:", data
    # Construct a file name in /data from the URL path.
    # For example, path=("pages", "bio.html")
    # is mapped to "/data/pages/bio.html.txt".
    page = "/".join(path)
    page = page if page else "index.html"
    page = page.replace(" ", "-")
    page = page + ".txt"
    page = os.path.join(app.path, "data", page) # Absolute paths are safer.
    #print "page:", page
    
    # If the URL ends in "?save", update the page content.
    if "save" in data and "content" in data:
        return save(page, src=data["content"])
    # If the URL ends in "?edit", show the page editor.
    if "edit" in data:
        return edit(page)
    # If the page does not exist, show the page editor.
    if not os.path.exists(page):
        return edit(page)
    # Show the page.
    else:
        return view(page)

# The pattern.server module has a simple template() function
# that takes a file path or a string and optional parameters.
# Placeholders in the template source (e.g., "$name") 
# are replaced with the parameter values.

# Below is a template with placeholders for page name and content.
# The page content is loaded from a file stored in /data. 
# The page name is parsed from the filename,
# e.g., "/data/index.html.txt" => "index.html".

wiki = """
<!doctype html>
<html>
<head>
    <title>$name</title>
    <meta charset="utf-8">
</head>
<body>
    <h3>$name</h3>
    $content
    <br>
    <a href="?edit">edit</a>
</body>
</html>
"""

# The name() function takes a file path (e.g., "/data/index.html.txt")
# and returns the page name ("index.html").

def name(page):
    name = os.path.basename(page)     # "/data/index.html.txt" => "index.html.txt"
    name = os.path.splitext(name)[0]  # ("index.html", ".txt") => "index.html"
    return name
    
# We could also have a function for a *display* name (e.g., "Index").
# Something like:

def displayname(page):
    return name(name(page)).replace("-", " ").title()

# The view() function is called when a page needs to be displayed.
# Our template has two placeholders: the page $name and $content.
# We load the $content from the contents of the given file path.
# We load the $name using the name() function above.

def view(page):
    print displayname(page)
    return template(wiki, name=name(page), content=open(page).read())

# The edit() function is called when a URL ends in "?edit",
# e.g., http://127.0.0.1:8080/index.html?edit.
# In this case, we don't show the contents of "/data/index.html.txt" directly, 
# but wrapped inside a <textarea> for editing instead.
# Once the user is done editing and clicks "Submit",
# the browser redirects to http://127.0.0.1:8080/index.html?save,
# posting the data inside the <textarea> to the server.
# We can catch it as the optional "content" parameter of the index() function
# (since the name of the <textarea> is "content").
    
def edit(page):
    s = open(page).read() if os.path.exists(page) else ""
    s = '<form method="post" action="?save">' \
        '<textarea name="content" rows="10" cols="80">%s</textarea><br>' \
        '<input type="submit">' \
        '</form>' % s
    return template(wiki, name=name(page), content=s)

# The save() function is called when edited content is posted to the server.
# It creates a file in /data and stores the content.

@threadsafe
def save(page, src):
    f = open(page, "w")
    f.write(src.encode("utf-8"))
    f.close()
    return view(page)
    
# Writing HTML by hand in the <textarea> becomes tedious after a while,
# so we could for example extend save() with a parser for Markdown syntax:
# http://en.wikipedia.org/wiki/Markdown,
# http://pythonhosted.org/Markdown/,
# or replace the <textarea> with a visual TinyMCE editor:
# http://www.tinymce.com.
    
app.run("127.0.0.1", port=8080)