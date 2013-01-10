import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Facebook, NEWS, COMMENTS, LIKES
from pattern.db  import Datasheet, pprint

# The Facebook API can be used to search public status updates (no license needed).
# It can also be used to get status updates, comments, and names of the persons
# that liked it, from a given profile or product page, but this requires a
# personal license key. You can obtain a license key here:
# http://www.clips.ua.ac.be/media/pattern-fb.html

# 1) Searching for public status updates.

try: 
    # We'll store the results in a Datasheet that can be saved as a text file.
    # In the first column, we'll store a unique ID for each tweet.
    # We only want to add the latest Facebook statuses, i.e. those we haven't previously encountered.
    # With an index on the first column we can quickly check if an ID already exists.
    # The index becomes important once more and more rows are added to the table (speed).
    table = Datasheet.load("negative.txt")
    index = dict.fromkeys(table.columns[0], True)
except:
    table = Datasheet()
    index = {}

fb = Facebook()

# With cached=False, a live request is sent to Facebook,
# so we get the latest results for the query instead of those in the local cache.
for status in fb.search("horrible", count=25, cached=False):
    print status.text
    print status.author
    print status.date
    print
    id = status.id
    # Only add the status update to the table if it doesn't already contain this ID.
    if len(table) == 0 or id not in index:
        table.append([id, status.text])
        index[id] = True

table.save("negative.txt")

# 2) Status updates from profiles.

# You need a personal license key first:
# http://www.clips.ua.ac.be/media/pattern-fb.html
license = ""

if license != "":
    fb = Facebook(license)
    # Facebook.profile() returns an (id, name, date of birth, gender, locale)-tuple.
    # By default, this is your own profile. 
    # You can also supply the id of another profile.
    me = fb.profile()[0]
    for status in fb.search(me, type=NEWS, count=10, cached=False):
        print status.id   # Status update unique ID.
        print status.text # Status update text.
        print status.url  # Status update image, external link, ...
        if status.comments > 0:
            # Retrieve comments on the status update.
            print "%s comments:" % status.comments
            print [(x.text, x.author) for x in fb.search(status.id, type=COMMENTS)]
        if status.likes > 0:
            # Retrieve likes on the status update.
            print "%s likes:" % status.likes
            print [x.author for x in fb.search(status.id, type=LIKES)]
        print