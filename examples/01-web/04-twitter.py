import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Twitter, hashtags
from pattern.db  import Datasheet, pprint, pd

# This example retrieves tweets containing given keywords from Twitter.

try: 
    # We'll store tweets in a Datasheet.
    # A Datasheet is a table of rows and columns that can be exported as a CSV-file.
    # In the first column, we'll store a unique id for each tweet.
    # We only want to add the latest tweets, i.e., those we haven't seen yet.
    # With an index on the first column we can quickly check if an id already exists.
    # The pd() function returns the parent directory of this script + any given path.
    table = Datasheet.load(pd("cool.csv"))
    index = set(table.columns[0])
except:
    table = Datasheet()
    index = set()

engine = Twitter(language="en")

# With Twitter.search(cached=False), a "live" request is sent to Twitter:
# we get the most recent results instead of those in the local cache.
# Keeping a local cache can also be useful (e.g., while testing)
# because a query is instant when it is executed the second time.
prev = None
for i in range(2):
    print(i)
    for tweet in engine.search("is cooler than", start=prev, count=25, cached=False):
        print("")
        print(tweet.text)
        print(tweet.author)
        print(tweet.date)
        print(hashtags(tweet.text))  # Keywords in tweets start with a "#".
        print("")
        # Only add the tweet to the table if it doesn't already exists.
        if len(table) == 0 or tweet.id not in index:
            table.append([tweet.id, tweet.text])
            index.add(tweet.id)
        # Continue mining older tweets in next iteration.
        prev = tweet.id

# Create a .csv in pattern/examples/01-web/
table.save(pd("cool.csv"))

print("Total results: %s" % len(table))
print("")

# Print all the rows in the table.
# Since it is stored as a CSV-file it grows comfortably each time the script runs.
# We can also open the table later on: in other scripts, for further analysis, ...

pprint(table, truncate=100)

# Note: you can also search tweets by author:
# Twitter().search("from:tom_de_smedt")
