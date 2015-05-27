import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import time

from pattern.web import Twitter

# Another way to mine Twitter is to set up a stream.
# A Twitter stream maintains an open connection to Twitter, 
# and waits for data to pour in.
# Twitter.search() allows us to look at older tweets,
# Twitter.stream() gives us the most recent tweets.

# It might take a few seconds to set up the stream.
stream = Twitter().stream("I hate", timeout=30)

#while True:
for i in range(10):
    print(i)
    # Poll Twitter to see if there are new tweets.
    stream.update()
    # The stream is a list of buffered tweets so far,
    # with the latest tweet at the end of the list.
    for tweet in reversed(stream):
        print(tweet.text)
        print(tweet.language)
    # Clear the buffer every so often.
    stream.clear()
    # Wait awhile between polls.
    time.sleep(1)