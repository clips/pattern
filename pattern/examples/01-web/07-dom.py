import os, sys; sys.path.append(os.path.join("..", "..", ".."))

from pattern.web import URL, Document, plaintext
from pattern.web import NODE, TEXT, COMMENT, ELEMENT, DOCUMENT

# The web module has a number of convenient search engines,
# but often you will need to handle the HTML in web pages of your interest manually.
# The Document object can be used for this, similar to the Javascript DOM.

# For example:
url = URL("http://www.reddit.com/top/")
dom = Document(url.download(cached=True))
for e in dom.get_elements_by_tagname("div.entry")[:5]: # Top 5 reddit entries.
    for a in e.get_elements_by_tagname("a.title")[:1]: # First <a class="title"> in entry.
        print plaintext(a.content)
        print a.attributes["href"]
        print

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
