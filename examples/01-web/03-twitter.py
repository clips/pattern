import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Twitter, hashtags
from pattern.db  import Datasheet, pprint

# This example retrieves tweets containing given keywords from Twitter (http://twitter.com).

try: 
    # We store tweets in a Datasheet that can be saved as a text file (comma-separated).
    # In the first column, we'll store a unique ID for each tweet.
    # We only want to add the latest tweets, i.e., those we haven't previously encountered.
    # With an index on the first column we can quickly check if an ID already exists.
    # The index becomes important once more and more rows are added to the table (speed).
    table = Datasheet.load("cool.txt")
    index = dict.fromkeys(table.columns[0], True)
except:
    table = Datasheet()
    index = {}

engine = Twitter(language="en")

# With cached=False, a live request is sent to Twitter,
# so we get the latest results for the query instead of those in the local cache.
for tweet in engine.search("is cooler than", count=25, cached=False):
    print tweet.description
    print tweet.author
    print tweet.date
    print hashtags(tweet.description) # Keywords in tweets start with a #.
    print
    # Create a unique ID based on the tweet content and author.
    id = hash(tweet.author + tweet.description)
    # Only add the tweet to the table if it doesn't already contain this ID.
    if len(table) == 0 or id not in index:
        table.append([id, tweet.description])
        index[id] = True

table.save("cool.txt")

print "Total results:", len(table)
print

# Print all the rows in the table.
# Since it is stored as a file it can grow comfortably each time the script runs.
# We can also open the table later on, in other scripts, for further analysis.
#pprint(table)

# Note: you can also search tweets by author:
# Twitter().search("from:tom_de_smedt")
