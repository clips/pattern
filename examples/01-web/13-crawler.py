import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Crawler, DEPTH, BREADTH, FIFO, LIFO

# This example demonstrates how to use the Crawler class for web crawling.

# -------------------------------------------------------------------------------------------------
# First, we need a subclass of Crawler with its own Crawler.visit() method.
# The visit() method takes two parameters: the visited link and the HTML source.
# We could parse the HTML DOM to extract information we need, for example.
# Anything that is not HTML (e.g., a JPEG file) is passed to Crawler.fail().

class SimpleCrawler1(Crawler):

    def visit(self, link, source=None):
        print("visiting: %s from: %s" % (link.url, link.referrer))

    def fail(self, link):
        print("failed: %s" % link.url)

# Create a new crawler.
# 1) The links parameter is a list of URL's to visit.
#    The crawler will visit the first link, extract new links from the HTML, and queue these for a visit too.
# 2) The domains parameter is a list of allowed domains.
#    The crawler will never leave these domains.
# 3) The delay parameter specifies a number of seconds to wait before revisiting the same domain.
#    In the meantime, other queued links will be crawled if possible.

crawler1 = SimpleCrawler1(
      links=["http://www.clips.ua.ac.be/pages/pattern/"], 
    domains=["ua.ac.be"], 
      delay=0.0
)

print("CRAWLER 1 " + "-" * 50)
while len(crawler1.visited) < 5:  # Crawler.visited is a dictionary of all URL's visited so far.
    # The Crawler.crawl() method has the same optional parameters as URL.download(),
    # for example: cached=True, proxy=("proxy.com", "https"), ...
    crawler1.crawl(cached=False)

# -------------------------------------------------------------------------------------------------
# Typically, you'll want a crawler that runs in an endless loop as a background process,
# and just keeps on visiting new URL's. In this case, it is rude to use a delay of 0.0,
# because you will keep hammering servers with automated requests.
# A higher delay (in a real-world scenario, say 30 seconds) is better:

crawler2 = SimpleCrawler1(
      links=["http://www.clips.ua.ac.be/pages/pattern/"], 
    domains=["ua.ac.be"], 
      delay=0.1
)

print("")
print("CRAWLER 2 " + "-" * 50)
while True:
    crawler2.crawl(cached=False)
    print("wait...")
    # Of course we don't want this example to run forever,
    # so we still add a stop condition:
    if len(crawler2.visited) > 2:
        break

# -------------------------------------------------------------------------------------------------
# If you create a crawler without a domains=[..] restriction, it is free to roam the entire web.
# What to visit first? You can use Crawler.crawl() with an optional "method" parameter.
# When set to DEPTH, it prefers to visit links in the same domain.
# When set to BREADTH, it prefers to visit links to other domains.
# Observe the difference between crawler3 and crawler4,
# which use DEPTH and BREADTH respectively.

crawler3 = SimpleCrawler1(
    links=["http://www.clips.ua.ac.be/pages/pattern/"], 
    delay=0.0
)

print("")
print("CRAWLER 3 " + "-" * 50)
while len(crawler3.visited) < 3:
    crawler3.crawl(method=DEPTH)
    
crawler4 = SimpleCrawler1(
    links=["http://www.clips.ua.ac.be/pages/pattern/"], 
    delay=0.0
)

print("")
print("CRAWLER 4 " + "-" * 50)
while len(crawler4.visited) < 3:
    crawler4.crawl(method=BREADTH)

# -------------------------------------------------------------------------------------------------
# With Crawler.crawl(method=DEPTH) and a delay,
# the crawler will wait between requests to the same domain.
# In the meantime, it will visit other links.
# Usually this means that it will alternate between a couple of domains:

crawler5 = SimpleCrawler1(
    links=["http://www.clips.ua.ac.be/pages/pattern/"], 
    delay=0.1
)

print("")
print("CRAWLER 5 " + "-" * 50)
while len(crawler5.visited) < 4:
    crawler5.crawl(method=DEPTH)

# -------------------------------------------------------------------------------------------------
# A BREADTH-crawler in an endless crawl loop will eventually queue the entire web for a visit.
# But this is not possible of course: we can't keep the entire web in memory.
# When the number of queued links exceeds Crawler.QUEUE (10,000 by default),
# less relevant queued links will be discarded.
# "Less relevant" depends on two settings:
# 1) First, there is the Crawler.priority() method that returns a number between 0.0-1.0 for a link.
#    Links with a higher priority are more relevant and will be visited sooner.
# 2) Links with an equal priority are queued either FIFO or LIFO.
#    FIFO means first-in-first-out: the earliest queued links will be visited sooner.
#    LIFO means last-in-first-out: more recently queued links will be visited sooner.

class SimpleCrawler2(Crawler):

    def visit(self, link, source=None):
        print("visiting: %s from: %s" % (link.url, link.referrer))

    def priority(self, link, method=DEPTH):
        if "?" in link.url:
            # This ignores links with a querystring.
            return 0.0
        else:
            # Otherwise use the default priority ranker,
            # i.e. the priority depends on DEPTH or BREADTH crawl mode.
            return Crawler.priority(self, link, method)

# Note the LIFO sort order.
# This will make more recently queued links more relevant.
# If you observe the given URL in a browser,
# you'll notice that the last external link at the bottom of the page is now visited first.
crawler6 = SimpleCrawler2(
    links=["http://www.clips.ua.ac.be/pages/pattern/"], 
    delay=0.1, 
     sort=LIFO
)

print("")
print("CRAWLER 6 " + "-" * 50)
while len(crawler6.visited) < 4:
    crawler6.crawl(method=BREADTH)

# -------------------------------------------------------------------------------------------------
# In the long run, the Crawler.visited dictionary will start filling up memory too.
# If you want a single crawler that runs forever, you should empty the dictionary every now and then,
# and instead use a strategy with a persistent database of visited links,
# in combination with Crawler.follow().
# Another strategy would be to use different DEPTH-crawlers for different domains,
# and delete them when they are done.