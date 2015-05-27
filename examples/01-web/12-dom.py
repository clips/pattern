import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import URL, DOM, plaintext
from pattern.web import NODE, TEXT, COMMENT, ELEMENT, DOCUMENT

# The pattern.web module has a number of convenient search engines, as demonstrated.
# But often you will need to handle the HTML in web pages of your interest manually.
# The DOM object can be used for this, similar to the Javascript DOM.
# The DOM (Document Object Model) parses a string of HTML
# and returns a tree of nested Element objects.
# The DOM elements can then be searched by tag name, CSS id, CSS class, ...

# For example, top news entries on Reddit are coded as:
# <div class="entry">
#     <p class="title">
#         <a class="title " href="http://i.imgur.com/yDyPu8P.jpg">Bagel the bengal, destroyer of boxes</a>
#     ...
# </div>
#
# ... which - naturally - is a picture of a cat.
url = URL("http://www.reddit.com/top/")
dom = DOM(url.download(cached=True))
#print(dom.body.content)
for e in dom.by_tag("div.entry")[:5]: # Top 5 reddit entries.
    for a in e.by_tag("a.title")[:1]: # First <a class="title"> in entry.
        print(plaintext(a.content))
        print(a.attrs["href"])
        print(""))

# The links in the HTML source code may be relative,
# e.g., "../img.jpg" instead of "www.domain.com/img.jpg".
# We can get the absolute URL by prepending the base URL.
# However, this can get messy with anchors, trailing slashes and redirected URL's.
# A good way to get absolute URL's is to use the module's abs() function:
from pattern.web import abs
url = URL("http://nodebox.net")
for link in DOM(url.download()).by_tag("a"):
    link = link.attrs.get("href", "")
    link = abs(link, base=url.redirect or url.string)
    #print(link)

# The DOM object is a tree of nested Element and Text objects.
# All objects inherit from Node (check the source code).

# Node.type       : NODE, TEXT, COMMENT, ELEMENT or DOM
# Node.parent     : Parent Node object.
# Node.children   : List of child Node objects.
# Node.next       : Next Node in Node.parent.children.
# Node.previous   : Previous Node in Node.parent.children.

# DOM.head        : Element with tag name "head".
# DOM.body        : Element with tag name "body".

# Element.tag     : Element tag name, e.g. "body".
# Element.attrs   : Dictionary of tag attributes, e.g. {"class": "header"}
# Element.content : Element HTML content as a string.
# Element.source  : Element tag + content

# Element.get_element_by_id(value)
# Element.get_elements_by_tagname(value)
# Element.get_elements_by_classname(value)
# Element.get_elements_by_attribute(name=value)

# You can also use shorter aliases (we prefer them):
# Element.by_id(), by_tag(), by_class(), by_attr().

# The tag name passed to Element.by_tag() can include
# a class (e.g., "div.message") or an id (e.g., "div#header").

# For example:
# In the <head> tag, retrieve the <meta name="keywords"> element.
# Get the string value of its "content" attribute and split into a list:
dom = DOM(URL("http://www.clips.ua.ac.be").download())
kw = dom.head.by_attr(name="keywords")[0]
kw = kw.attrs["content"]
kw = [x.strip() for x in kw.split(",")]
print(kw)
print("")

# If you know CSS, you can also use short and handy CSS selectors:
# http://www.w3.org/TR/CSS2/selector.html
# Element(selector) will return a list of nested elements that match the given string.
dom = DOM(URL("http://www.clips.ua.ac.be").download())
for e in dom("div#sidebar-left li div:first-child span"):
    print(plaintext(e.content))
    print("")