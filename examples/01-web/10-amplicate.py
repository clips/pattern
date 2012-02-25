import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import re

from pattern.web import Google, URL
from pattern.web import Document, plaintext

# An interesting experiment on how to use the Google API 
# and http://amplicate.com for opinion mining.
# (let's hope we get a real Amplicate API soon!)

query = "chicken"

# An example result, containing all the information we need:
#   URL: http://amplicate.com/love/george-w-bush
# Title: <b>George</b> W <b>Bush</b> Hate - 64% People Agree (803 opinions)
for r in Google().search(query+" site:amplicate.com"):
    print r.title
    u = URL(r.url)
    if "love" in u.path \
    or "hate" in u.path:
        b = True
        p = u.page.lower().replace("-", "")
        for i, w in enumerate(query.lower().replace("-", " ").split()):
            if i == 0 and not p.startswith(w):
                b=False; break
            if w not in p: 
                b=False; break
        if b:
            love = "love" in u.path
            f = int(re.search("([0-9]{1,3})%", r.title).group(1)) * 0.01
            n = int(re.search("\(([0-9]+) opinions", r.title).group(1))
            print r.title
            print r.url
            print "love:", love and f or (1-f)
            print "hate:", love and (1-f) or f
            print "opinions:", int(round(n / f))
            print
            # Of course we can dig in deeper by following the link to r.url,
            # but that would classify as screen-scraping.
            #dom = Document(u.download())
            #for p in dom.by_tag("p.comment-body"):
            #    print plaintext(p.content)
            #    print
            #break
            
