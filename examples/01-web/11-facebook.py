import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Facebook, NEWS, COMMENTS, LIKES
from pattern.db  import Datasheet, pprint, pd

# The Facebook API can be used to search public status updates (no license needed).

# It can also be used to get status updates, comments and persons that liked it,
# from a given profile or product page.
# This requires a personal license key.
# If you are logged in to Facebook, you can get a license key here:
# http://www.clips.ua.ac.be/pattern-facebook
# (We don't / can't store your information).

# 1) Searching for public status updates.
#    Search for all status updates that contain the word "horrible".

try:
    # We'll store the status updates in a Datasheet.
    # A Datasheet is a table of rows and columns that can be exported as a CSV-file.
    # In the first column, we'll store a unique id for each status update.
    # We only want to add new status updates, i.e., those we haven't seen yet.
    # With an index on the first column we can quickly check if an id already exists.
    table = Datasheet.load(pd("opinions.csv"))
    index = set(table.columns[0])
except:
    table = Datasheet()
    index = set()

fb = Facebook()

# With Facebook.search(cached=False), a "live" request is sent to Facebook:
# we get the most recent results instead of those in the local cache.
# Keeping a local cache can also be useful (e.g., while testing)
# because a query is instant when it is executed the second time.
for status in fb.search("horrible", count=25, cached=False):
    print("=" * 100)
    print(status.id)
    print(status.text)
    print(status.author)  # Yields an (id, name)-tuple.
    print(status.date)
    print(status.likes)
    print(status.comments)
    print("")
    # Only add the tweet to the table if it doesn't already exists.
    if len(table) == 0 or status.id not in index:
        table.append([status.id, status.text])
        index.add(status.id)

# Create a .csv in pattern/examples/01-web/
table.save(pd("opinions.csv"))

# 2) Status updates from specific profiles.
#    For this you need a personal license key:
#    http://www.clips.ua.ac.be/pattern-facebook

license = ""

if license != "":
    fb = Facebook(license)
    # Facebook.profile() returns a dictionary with author info.
    # By default, this is your own profile.
    # You can also supply the id of another profile,
    # or the name of a product page.
    me = fb.profile()["id"]
    for status in fb.search(me, type=NEWS, count=30, cached=False):
        print("-" * 100)
        print(status.id)     # Status update unique id.
        print(status.title)  # Status title (i.e., the id of the page or event given as URL).
        print(status.text)   # Status update text.
        print(status.url)    # Status update image, external link, ...
        if status.comments > 0:
            # Retrieve comments on the status update.
            print("%s comments:" % status.comments)
            print([(x.author, x.text, x.likes) 
                for x in fb.search(status.id, type=COMMENTS)])
        if status.likes > 0:
            # Retrieve likes on the status update.
            print("%s likes:" % status.likes)
            print([x.author for x in fb.search(status.id, type=LIKES)])
        print("")