import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Spider, DEPTH, BREADTH, FIFO, LIFO

# This example demonstrates how to use the Spider class for web crawling.

# First, we need a subclass of Spider with an implemented Spider.visit() method.
# The visit() method has two parameters: the link being visited and the source HTML.
# For example, in visit() we could parse the source with the Document class to extract information.
# Anything that is not HTML (e.g., a zip download link) is passed to the Spider.fail() method.

class SimpleSpider1(Spider):
    
    def visit(self, link, source=None):
        print "visiting:", link.url, "from:", link.referrer
        
    def fail(self, link):
        print "failed:", link.url

# Create a new spider.
# 1) The links parameter is a list of URL's to start with.
#    The spider will visit the first link, extract new links from the HTML, and queue them for a visit.
# 2) The domains parameter is a list of allowed domains.
#    The spider will never leave these domains.
# 3) The delay parameter specifies a number of seconds to wait before revisiting the same domain.
#    In the meantime, other queued links will be crawled if possible.

spider1 = SimpleSpider1(links=["http://www.clips.ua.ac.be/pages/pattern/"], domains=["ua.ac.be"], delay=0.0)

print "SPIDER 1 " + "-" * 50
while len(spider1.visited) < 5: # Spider.visited is a dictionary of all URL's visited so far.
    # The crawl() method has the same optional parameters as URL.download(),
    # for example for caching, proxy, ...
    spider1.crawl(cached=False)
    
# Typically, you will want a spider that runs in an endless loop as a background process,
# and just keeps on visiting new URL's. In this case, it is rude to use a delay of 0.0,
# because you will keep hammering the server with automated requests.
# A higher delay (in a real scenario, say 30 seconds) is better:

spider2 = SimpleSpider1(links=["http://www.clips.ua.ac.be/pages/pattern/"], domains=["ua.ac.be"], delay=0.1)

print
print "SPIDER 2 " + "-" * 50
while True:
    spider2.crawl(cached=False)
    print "wait..."
    # Of course we don't want this example to run forever,
    # so we still add a stop condition:
    if len(spider2.visited) > 2:
        break
        
# If you create a spider without a domains restriction, it is free to roam the entire web.
# You can use crawl() with an optional method parameter.
# When set to DEPTH, it prefers to visit links in the same domain.
# When set to BREADTH, it prefers to visit links to other domains.
# Observe the difference between spider3 and spider4,
# which use DEPTH and BREADTH respectively.

spider3 = SimpleSpider1(links=["http://www.clips.ua.ac.be/pages/pattern/"], delay=0.0)

print
print "SPIDER 3 " + "-" * 50
while len(spider3.visited) < 3:
    spider3.crawl(method=DEPTH)
    
spider4 = SimpleSpider1(links=["http://www.clips.ua.ac.be/pages/pattern/"], delay=0.0)

print
print "SPIDER 4 " + "-" * 50
while len(spider4.visited) < 3:
    spider4.crawl(method=BREADTH)
    
# With method=DEPTH and a delay,
# it will have to wait a while between requests to the same domain.
# In the meantime, it will visit other links.
# Usually this means that it will alternate between a couple of domains:

spider5 = SimpleSpider1(links=["http://www.clips.ua.ac.be/pages/pattern/"], delay=0.1)

print
print "SPIDER 5 " + "-" * 50
while len(spider5.visited) < 4:
    spider5.crawl(method=DEPTH)

# A BREADTH-spider in an endless crawl loop will eventually queue the entire web for a visit.
# But this is not possible of course: we can't keep the entire web in memory.
# When the number of queued links exceeds Spider.QUEUE (10,000 by default),
# less relevant queued links will start to be thrown away.
# "Less relevant" depends on two settings.
# 1) First, there is the Spider.priority() method that returns a number between 0.0-1.0.
#    Links with a higher priority are more relevant and will be visited sooner.
# 2) Links with an equal priority are queued either FIFO or LIFO.
#    FIFO means first-in-first-out: the earliest queued links will be visited sooner.
#    LIFO means last-in-first-out: more recently queued links will be visited sooner.

class SimpleSpider2(Spider):
    
    def visit(self, link, source=None):
        print "visiting:", link.url, "from:", link.referrer
    
    def priority(self, link, method=DEPTH):
        if "?" in link.url:
            # This ignores links with a querystring.
            return 0.0
        else:
            # Otherwise use the default priority ranker,
            # i.e. the priority depends on DEPTH or BREADTH crawl mode.
            return Spider.priority(self, link, method)

# Note the LIFO sort order. 
# This will make more recently queued links more relevant.
# If you go and observe the page in a browser,
# you'll notice that the last external link at the bottom of the page is now visited first.
spider6 = SimpleSpider2(links=["http://www.clips.ua.ac.be/pages/pattern/"], delay=0.1, sort=LIFO)

print
print "SPIDER 6 " + "-" * 50
while len(spider6.visited) < 4:
    spider6.crawl(method=BREADTH)
    
# In the long run, the Spider.visited dictionary will start filling up memory too.
# If you want a single spider that runs forever, you should empty the dictionary now and then,
# and instead use a strategy with a persistent database of visited links
# in combination with Spider.follow().
# Another strategy would be to use different DEPTH-spiders for different domains,
# and delete them when they are done.