import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Flickr, extension
from pattern.web import RELEVANCY, LATEST, INTERESTING # Image sort order.
from pattern.web import SMALL, MEDIUM, LARGE           # Image size.

# This example downloads an image from Flickr (http://flickr.com).
# Acquiring the image data takes three Flickr queries: 
# - the first query with Flickr.search() retrieves a list of results,
# - the second query is executed behind the scenes in the FlickResult.url property,
# - the third query downloads the actual image data using this URL.
# It is a good idea to cache results from Flickr locally,
# which is what the cached=True parameter does.

# You should obtain your own license key at:
# http://www.flickr.com/services/api/
# Otherwise you will be sharing the default key with all users of this module.
engine = Flickr(license=None)

q = "duracell bunny"
results = engine.search(q, size=MEDIUM, sort=RELEVANCY, cached=True)
for img in results:
    #print img.url # Retrieving the actual image URL executes an additional query.
    print img.description
    print img.author
    print

# Download and save the image:
img = results[0]
data = img.download()
path = q.replace(" ","_") + extension(img.url)
f = open(path, "wb")
f.write(data)
f.close()
print "Download:", img.url
print "Saved as:", path