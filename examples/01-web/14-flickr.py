import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Flickr, extension
from pattern.web import RELEVANCY, LATEST, INTERESTING  # Image sort order.
from pattern.web import SMALL, MEDIUM, LARGE            # Image size.

# This example downloads an image from Flickr (http://flickr.com).
# Acquiring the image data takes three Flickr queries:
# 1) Flickr.search() retrieves a list of results,
# 2) FlickrResult.url retrieves the image URL (behind the scenes),
# 3) FlickrResult.download() visits FlickrResult.url and downloads the content.

# It is a good idea to cache results from Flickr locally,
# which is what the cached=True parameter does.

# You should obtain your own license key at:
# http://www.flickr.com/services/api/
# Otherwise you will be sharing the default key with all users of pattern.web.
engine = Flickr(license=None)

q = "duracell bunny"
results = engine.search(q, size=MEDIUM, sort=RELEVANCY, cached=False)
for img in results:
    #print(img.url)  # Retrieving the actual image URL executes a query.
    print(img.text)
    print(img.author)
    print("")

# Download and save one of the images:
img = results[0]
data = img.download()
path = q.replace(" ", "_") + extension(img.url)
f = open(path, "wb")
f.write(data)
f.close()
print("Download: %s" % img.url)
print("Saved as: %s" % path)