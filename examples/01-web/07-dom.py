import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import URL, Document, plaintext
from pattern.web import NODE, TEXT, COMMENT, ELEMENT, DOCUMENT

# The web module has a number of convenient search engines,
# but often you will need to handle the HTML in web pages of your interest manually.
# The Document object can be used for this, similar to the Javascript DOM.

# For example:
url = URL("http://www.reddit.com/top/")
dom = Document(url.download(cached=True))
print dom.body.content.__class__
for e in dom.get_elements_by_tagname("div.entry")[:5]: # Top 5 reddit entries.
    for a in e.get_elements_by_tagname("a.title")[:1]: # First <a class="title"> in entry.
        print plaintext(a.content)
        print a.attributes["href"]
        print
        
# Some of the links can be relative, for example starting with "../".
# We can get the absolute URL by prepending the base URL.
# However, this might get messy with anchors, trailing slashes and redirected URL's.
# A good way to get absolute URL's is to use the module's abs() function:
from pattern.web import abs
url = URL("http://nodebox.net")
for link in Document(url.download()).by_tag("a"):
    link = link.attributes.get("href","")
    link = abs(link, base=url.redirect or url.string)
    #print link

# The Document object is a tree of Element and Text objects.
# All objects inherit from Node, Document also inherits from Element.

# Node.type          => NODE, TEXT, COMMENT, ELEMENT, DOCUMENT
# Node.parent        => Parent Node object.
# Node.children      => List of child Node objects.
# Node.next          => Next Node in Node.parent.children.
# Node.previous      => Previous Node in Node.parent.children.

# Document.head      => Element with tag name "head".
# Document.body      => Element with tag name "body".

# Element.tag        => Element tag name, e.g. "body".
# Element.attributes => Dictionary of tag attribute, e.g. {"class": "header"}
# Element.content    => Element HTML content as a string.
# Element.source     => Element tag + content

# Element.get_element_by_id(value)
# Element.get_elements_by_tagname(value)
# Element.get_elements_by_classname(value)
# Element.get_elements_by_attribute(name=value)

# You can also use short aliases: by_id(), by_tag(), by_class(), by_attribute()
# The tag name passed to Element.by_tag()
# can include a class ("div.message") or an id ("div#header"). 

# For example:
# In the <head> tag, retrieve the <meta name="keywords"> element.
# Get the string value of its "content" attribute and split into a list:
dom = Document(URL("http://www.clips.ua.ac.be").download())
kw = dom.head.by_attribute(name="keywords")[0]
kw = kw.attributes["content"]
kw = [x.strip() for x in kw.split(",")]
print kw
