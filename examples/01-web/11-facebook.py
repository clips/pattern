import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Facebook
from pattern.db  import Datasheet, pprint

# This example retrieves Facebook public status updates containing given keyword.

try: 
    # We store status in a Datasheet that can be saved as a text file.
    # In the first column, we'll store a unique ID for each tweet.
    # We only want to add the latest Facebook status, i.e. those we haven't previously encountered.
    # With an index on the first column we can quickly check if an ID already exists.
    # The index becomes important once more and more rows are added to the table (speed).
    table = Datasheet.load("travel.txt")
    index = dict.fromkeys(table.columns[0], True)
except:
    table = Datasheet()
    index = {}

engine = Facebook()

# With cached=False, a live request is sent to Facebook,
# so we get the latest results for the query instead of those in the local cache.
for status in engine.search("Travelling to", count=25, cached=False):
    print status.description
    print status.author
    print status.date
    print
    id = status.url
    # Only add the status update to the table if it doesn't already contain this ID.
    if len(table) == 0 or id not in index:
        table.append([id, status.description])
        index[id] = True

table.save("travel.txt")

print "Total results:", len(table)
print

