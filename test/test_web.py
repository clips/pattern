# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest
import time
import warnings

from pattern import web

#-----------------------------------------------------------------------------------------------------

class TestUnicode(unittest.TestCase):
    
    def setUp(self):
        # Test data with different (or wrong) encodings.
        self.strings = (
            u"ünîcøde",
            u"ünîcøde".encode("utf-16"),
            u"ünîcøde".encode("latin-1"),
            u"ünîcøde".encode("windows-1252"),
             "ünîcøde",
            u"אוניקאָד"
        )
        
    def test_decode_utf8(self):
        # Assert unicode.
        for s in self.strings:
            self.assertTrue(isinstance(web.decode_utf8(s), unicode))
        print "pattern.web.decode_utf8()"

    def test_encode_utf8(self):
        # Assert Python bytestring.
        for s in self.strings:
            self.assertTrue(isinstance(web.encode_utf8(s), str))
        print "pattern.web.encode_utf8()"

#-----------------------------------------------------------------------------------------------------

class TestURL(unittest.TestCase):
    
    def setUp(self):
        # Test a live URL that has fast response time
        self.live = "http://www.google.com/"
        # Test a fake URL with the URL parser.
        self.url = "https://username:password@www.domain.com:8080/path/path/page.html?q=1#anchor"
        self.parts = {
            "protocol": "https",
            "username": "username",
            "password": "password",
              "domain": "www.domain.com",
                "port": 8080,
                "path": ["path", "path"],
                "page": "page.html",
               "query": {"q": 1},
              "anchor": "anchor"
        }
    
    def test_asynchrous(self):
        # Assert asynchronous function call (returns 1).
        v = web.asynchronous(lambda t: time.sleep(t) or 1, 0.2)
        while not v.done:
            time.sleep(0.1)
        self.assertEqual(v.value, 1)
        print "pattern.web.asynchronous()"
    
    def test_extension(self):
        # Assert filename extension.
        v = web.extension(os.path.join("pattern", "test", "test-web.py.zip"))
        self.assertEqual(v, ".zip")
        print "pattern.web.extension()"
        
    def test_urldecode(self):
        # Assert URL decode (inverse of urllib.urlencode).
        v = web.urldecode("?user=me&page=1&q=&")
        self.assertEqual(v, {"user": "me", "page": 1, "q": None})
        print "pattern.web.urldecode()"
        
    def test_proxy(self):
        # Assert URL proxy.
        v = web.proxy("www.proxy.com", "https")
        self.assertEqual(v, ("www.proxy.com", "https"))
        print "pattern.web.proxy()"
        
    def test_url_parts(self):
        # Assert URL._parse and URL.parts{}.
        v = web.URL(self.url)
        for a, b in (
          (web.PROTOCOL, self.parts["protocol"]),
          (web.USERNAME, self.parts["username"]),
          (web.PASSWORD, self.parts["password"]),
          (web.DOMAIN,   self.parts["domain"]),
          (web.PORT,     self.parts["port"]),
          (web.PATH,     self.parts["path"]),
          (web.PAGE,     self.parts["page"]),
          (web.QUERY,    self.parts["query"]),
          (web.ANCHOR,   self.parts["anchor"])):
            self.assertEqual(v.parts[a], b)
        print "pattern.web.URL.parts"
    
    def test_url_query(self):
        # Assert URL.query and URL.querystring.
        v = web.URL(self.url)
        v.query["page"] = 10
        v.query["user"] = None
        self.assertEqual(v.query, {"q": 1, "page": 10, "user": None})
        self.assertEqual(v.querystring, "q=1&page=10&user=")
        # Assert URL.querystring encodes unicode arguments.
        q = ({u"ünîcødé": 1.5}, "%C3%BCn%C3%AEc%C3%B8d%C3%A9=1.5")
        v.query = q[0]
        self.assertEqual(v.querystring, q[1])
        # Assert URL.query decodes unicode arguments.
        v = web.URL("http://domain.com?" + q[1])
        self.assertEqual(v.query, q[0])
        print "pattern.web.URL.query"
        print "pattern.web.URL.querystring"
    
    def test_url_string(self):
        # Assert URL._set_string().
        v = web.URL("")
        v.string = "https://domain.com"
        self.assertEqual(v.parts[web.PROTOCOL], "https")
        self.assertEqual(v.parts[web.DOMAIN],   "domain.com")
        self.assertEqual(v.parts[web.PATH],     [])
        print "pattern.web.URL.string"
        
    def test_url(self):
        # Assert URL.copy().
        v = web.URL(self.url)
        v = v.copy()
        # Assert URL.__setattr__().
        v.username = "new-username"
        v.password = "new-password"
        # Assert URL.__getattr__().
        self.assertEqual(v.method,   web.GET)
        self.assertEqual(v.protocol, self.parts["protocol"])
        self.assertEqual(v.username, "new-username")
        self.assertEqual(v.password, "new-password")
        self.assertEqual(v.domain,   self.parts["domain"])
        self.assertEqual(v.port,     self.parts["port"])
        self.assertEqual(v.path,     self.parts["path"])
        self.assertEqual(v.page,     self.parts["page"])
        self.assertEqual(v.query,    self.parts["query"])
        self.assertEqual(v.anchor,   self.parts["anchor"])
        print "pattern.web.URL"
        
    def test_url_open(self):
        # Assert URLError.
        v = web.URL(self.live.replace("http://", "htp://"))
        self.assertRaises(web.URLError, v.open)
        self.assertEqual(v.exists, False)
        # Assert HTTPError.
        v = web.URL(self.live + "iphone/android.html")
        self.assertRaises(web.HTTPError, v.open)
        self.assertRaises(web.HTTP404NotFound, v.open)
        self.assertEqual(v.exists, False)
        # Assert socket connection.
        v = web.URL(self.live)
        self.assertTrue(v.open() != None)
        self.assertEqual(v.exists, True)
        # Assert user-agent and referer.
        self.assertTrue(v.open(user_agent=web.MOZILLA, referrer=web.REFERRER) != None)
        print "pattern.web.URL.exists"
        print "pattern.web.URL.open()"
        
    def test_url_download(self):
        t = time.time()
        v = web.URL(self.live).download(cached=False, throttle=0.25)
        t = time.time() - t
        # Assert unicode content.
        self.assertTrue(isinstance(v, unicode))
        # Assert download rate limiting.
        self.assertTrue(t >= 0.25)
        print "pattern.web.URL.download()"
        
    def test_url_mimetype(self):
        # Assert URL MIME-type.
        v = web.URL(self.live).mimetype
        self.assertTrue(v in web.MIMETYPE_WEBPAGE)
        print "pattern.web.URL.mimetype"
        
    def test_url_headers(self):
        # Assert URL headers.
        v = web.URL(self.live).headers["content-type"].split(";")[0]
        self.assertEqual(v, "text/html")
        print "pattern.web.URL.headers"
        
    def test_url_redirect(self):
        # Assert URL redirected URL (this depends on where you are).
        # In Belgium, it yields "http://www.google.be/".
        v = web.URL(self.live).redirect
        print "pattern.web.URL.redirect: " + self.live + " => " + v

#-----------------------------------------------------------------------------------------------------

class TestPlaintext(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_find_urls(self):
        # Assert URL finder with common URL notations.
        for url in (
          "http://domain.co.uk",
          "https://domain.co.uk",
          "www.domain.cu.uk",
          "domain.com",
          "domain.org",
          "domain.net"):
            self.assertEqual(web.find_urls("("+url+".")[0], url)
        # Assert case-insensitive and <a href="">.
        # Assert several matches in string.
        self.assertEqual(web.find_urls("<a href=\"HTTP://domain.net\">")[0], "HTTP://domain.net")
        self.assertEqual(web.find_urls("domain.com, domain.net"), ["domain.com", "domain.net"])
        print "pattern.web.find_urls()"
        
    def test_find_email(self):
        # Assert e-mail finder with common e-mail notations.
        s = "firstname.last+name@domain.ac.co.uk"
        v = web.find_email("("+s+".")
        self.assertEqual(v[0], s)
        # Assert several matches in string.
        s = ["me@site1.com", "me@site2.com"]
        v = web.find_email("("+",".join(s)+")")
        self.assertEqual(v, s)
        print "pattern.web.find_email()"
        
    def test_find_between(self):
        # Assert search between open tag and close tag.
        s = "<script type='text/javascript'>alert(0);</script>"
        v = web.find_between("<script","</script>", s)
        self.assertEqual(v[0], " type='text/javascript'>alert(0);")
        # Assert several matches in string.
        s = "a0ba1b"
        v = web.find_between("a", "b", s)
        self.assertEqual(v, ["0", "1"])
        print "pattern.web.find_between()"
        
    def test_strip_tags(self):
        # Assert HTML parser and tag stripper.
        for html, plain in (
          (u"<b>ünîcøde</b>", u"ünîcøde"),
          ( "<img src=""/>",   ""),
          ( "<p>text</p>",     "text\n\n"),
          ( "<li>text</li>",   "* text\n"),
          ( "<td>text</td>",   "text\t"),
          ( "<br /><br/><br>", "\n\n\n")):
            self.assertEqual(web.strip_tags(html), plain)
        # Assert exclude tags and attributes
        v = web.strip_tags("<a href=\"\" onclick=\"\">text</a>", exclude={"a": ["href"]})
        self.assertEqual(v, "<a href=\"\">text</a>")
        print "pattern.web.strip_tags()"
    
    def test_strip_element(self):
        # Assert strip <p> elements.
        v = web.strip_element(" <p><p></p>text</p> <b><P></P></b>", "p")
        self.assertEqual(v, "  <b></b>")
        print "pattern.web.strip_element()"
        
    def test_strip_between(self):
        # Assert strip <p> elements.
        v = web.strip_between("<p", "</p>", " <p><p></p>text</p> <b><P></P></b>")
        self.assertEqual(v, " text</p> <b></b>")
        print "pattern.web.strip_between()"
        
    def test_strip_javascript(self):
        # Assert strip <script> elements.
        v = web.strip_javascript(" <script type=\"text/javascript\">text</script> ")
        self.assertEqual(v, "  ")
        print "pattern.web.strip_javascript()"

    def test_strip_inline_css(self):
        # Assert strip <style> elements.
        v = web.strip_inline_css(" <style type=\"text/css\">text</style> ")
        self.assertEqual(v, "  ")
        print "pattern.web.strip_inline_css()"
        
    def test_strip_comments(self):
        # Assert strip <!-- --> elements.
        v = web.strip_comments(" <!-- text --> ")
        self.assertEqual(v, "  ")
        print "pattern.web.strip_comments()"

    def test_strip_forms(self):
        # Assert strip <form> elements.
        v = web.strip_forms(" <form method=\"get\">text</form> ")
        self.assertEqual(v, "  ")
        print "pattern.web.strip_forms()"
        
    def test_encode_entities(self):
        # Assert HTML entity encoder (e.g., "&" => "&&amp;")
        for a, b in (
          ("&#201;", "&#201;"), 
          ("&", "&amp;"), 
          ("<", "&lt;"), 
          (">", "&gt;"), 
          ('"', "&quot;"),
          ("'", "&#39;")):
            self.assertEqual(web.encode_entities(a), b)
        print "pattern.web.encode_entities()"
            
    def test_decode_entities(self):
        # Assert HMTL entity decoder (e.g., "&amp;" => "&")
        for a, b in (
          ("&#38;", "&"),
          ("&amp;", "&"),
          ("&#x0026;", "&"),
          ("&#160;", u"\xa0"),
          ("&foo;", "&foo;")):
            self.assertEqual(web.decode_entities(a), b)
        print "pattern.web.decode_entities()"
            
    def test_collapse_spaces(self):
        # Assert collapse multiple spaces.
        for a, b in (
          ("    ", ""),
          (" .. ", ".."),
          (".  .", ". ."),
          (". \n", "."),
          ("\xa0", "")):
            self.assertEqual(web.collapse_spaces(a), b)
        # Assert preserve indendation.
        self.assertEqual(web.collapse_spaces("  . \n", indentation=True), "  .")
        print "pattern.web.collapse_spaces()"
        
    def test_collapse_tabs(self):
        # Assert collapse multiple tabs to 1 space.
        for a, b in (
          ("\t\t\t", ""),
          ("\t..\t", ".."),
          (".\t\t.", ". ."),
          (".\t\n", ".")):
            self.assertEqual(web.collapse_tabs(a), b)
        # Assert preserve indendation.
        self.assertEqual(web.collapse_tabs("\t\t .\t\n", indentation=True), "\t\t .")
        print "pattern.web.collapse_tabs()"
        
    def test_collapse_linebreaks(self):
        # Assert collapse multiple linebreaks.
        for a, b in (
          ("\n\n\n", "\n"),
          (".\n\n.", ".\n."),
          (".\r\n.", ".\n."),
          (".\n  .", ".\n  ."),
          (" \n  .", "\n  .")):
            self.assertEqual(web.collapse_linebreaks(a), b)
        print "pattern.web.collapse_linebreaks()"
    
    def test_plaintext(self):
        # Assert plaintext: 
        # - strip <script>, <style>, <form>, <!-- --> elements,
        # - strip tags,
        # - decode entities,
        # - collapse whitespace,
        html = """
            <html>
            <head>
                <title>tags &amp; things</title>
            </head>
            <body>
                <div id="content">       \n\n\n\
                    <!-- main content -->
                    <script type="text/javascript>"alert(0);</script>
                    <h1>title1</h1>
                    <h2>title2</h2>
                    <p>paragraph1</p>
                    <p>paragraph2 <a href="http://www.domain.com" onclick="alert(0);">link</a></p>
                    <ul>
                        <li>item1&nbsp;&nbsp;&nbsp;xxx</li>
                        <li>item2</li>
                    <ul>
                </div>
                <br />
                <br />
            </body>
            </html>
        """
        self.assertEqual(web.plaintext(html, keep={"a": "href"}),
            u"tags & things\n\ntitle1\n\ntitle2\n\nparagraph1\n\nparagraph2 " + \
            u"<a href=\"http://www.domain.com\">link</a>\n\n* item1 xxx\n* item2")
        print "pattern.web.plaintext()"

#-----------------------------------------------------------------------------------------------------

class TestSearchEngine(unittest.TestCase):
    
    def setUp(self):
        # Test data for all search engines: 
        # {api: (source, license, Engine)}.
        self.api = {
            "Google": (web.GOOGLE,      web.GOOGLE_LICENSE,      web.Google),
             "Yahoo": (web.YAHOO,       web.YAHOO_LICENSE,       web.Yahoo),
              "Bing": (web.BING,        web.BING_LICENSE,        web.Bing),
           "Twitter": (web.TWITTER,     web.TWITTER_LICENSE,     web.Twitter),
         "Wikipedia": (web.WIKIPEDIA,   web.WIKIPEDIA_LICENSE,   web.Wikipedia),
            "Flickr": (web.FLICKR,      web.FLICKR_LICENSE,      web.Flickr),
          "Facebook": (web.FACEBOOK,    web.FACEBOOK_LICENSE,    web.Facebook),
          "Products": (web.PRODUCTWIKI, web.PRODUCTWIKI_LICENSE, web.Products)
        }

    def _test_search_engine(self, api, source, license, Engine, query="today", type=web.SEARCH):
        # Assert SearchEngine standard interface for any api:
        # Google, Yahoo, Bing, Twitter, Wikipedia, Flickr, Facebook, Products, Newsfeed.
        # SearchEngine.search() returns a list of Result objects with unicode fields, 
        # except Wikipedia which returns a WikipediaArticle.
        if api == web.YAHOO and license == ("",""): 
            return
        t = time.time()
        e = Engine(license, throttle=0.25, language="en")
        v = e.search(query, type, start=1, count=1, cached=False)
        t = time.time() - t
        self.assertTrue(t >= 0.25)
        self.assertEqual(e.license, license)
        self.assertEqual(e.throttle, 0.25)
        self.assertEqual(e.language, "en")
        self.assertEqual(v.query, query)
        if source != web.WIKIPEDIA:
            self.assertEqual(v.source, source)
            self.assertEqual(v.type, type)
            self.assertEqual(len(v), 1)
            self.assertTrue(isinstance(v[0], web.Result))
            self.assertTrue(isinstance(v[0].url, unicode))
            self.assertTrue(isinstance(v[0].title, unicode))
            self.assertTrue(isinstance(v[0].description, unicode))
            self.assertTrue(isinstance(v[0].language, unicode))
            self.assertTrue(isinstance(v[0].author, unicode))
            self.assertTrue(isinstance(v[0].date, unicode))
        else:
            self.assertTrue(isinstance(v, web.WikipediaArticle))
        # Assert zero results for start < 1 and count < 1.
        v1 = e.search(query, start=0)
        v2 = e.search(query, count=0)
        if source != web.WIKIPEDIA:
            self.assertEqual(len(v1), 0)
            self.assertEqual(len(v2), 0)
        else:
            self.assertTrue(isinstance(v1, web.WikipediaArticle))
            self.assertEqual(v2, None)
        # Assert SearchEngineTypeError for unknown type.
        self.assertRaises(web.SearchEngineTypeError, e.search, query, type="crystall-ball")
        print "pattern.web.%s.search()" % api
    
    def test_search_google(self):
        self._test_search_engine("Google",    *self.api["Google"])
    def test_search_yahoo(self):
        self._test_search_engine("Yahoo",     *self.api["Yahoo"])
    def test_search_bing(self):
        self._test_search_engine("Bing",      *self.api["Bing"])
    def test_search_twitter(self):
        self._test_search_engine("Twitter",   *self.api["Twitter"])
    def test_search_wikipedia(self):
        self._test_search_engine("Wikipedia", *self.api["Wikipedia"])
    def test_search_flickr(self):
        self._test_search_engine("Flickr",    *self.api["Flickr"], **{"type": web.IMAGE})
    def test_search_facebook(self):
        self._test_search_engine("Facebook",  *self.api["Facebook"])
    def test_search_products(self):
        self._test_search_engine("Products",  *self.api["Products"])
    def test_search_newsfeed(self):
        for feed, url in web.feeds.items():
            self._test_search_engine("Newsfeed", url, None, web.Newsfeed, query=url, type=web.NEWS)
    
    def _test_results(self, api, source, license, Engine, type=web.SEARCH, query="today", baseline=[6,6,6,0]):
        # Assert SearchEngine result content.
        # We expect to find http:// URL's and descriptions containing the search query.
        if api == web.YAHOO and license == ("",""): 
            return
        i1 = 0
        i2 = 0
        i3 = 0
        i4 = 0
        e = Engine(license, language="en", throttle=0.25)
        for result in e.search(query, type, count=10, cached=False):
            i1 += int(result.url.startswith("http"))
            i2 += int(query in result.url.lower())
            i2 += int(query in result.title.lower())
            i2 += int(query in result.description.lower())
            i3 += int(result.language == "en")
            i4 += int(result.url.endswith(("jpg","png","gif")))
            #print result.url
            #print result.title
            #print result.description
        #print i1, i2, i3, i4
        self.assertTrue(i1 >= baseline[0]) # url's starting with "http"
        self.assertTrue(i2 >= baseline[1]) # query in url + title + description
        self.assertTrue(i3 >= baseline[2]) # language "en"
        self.assertTrue(i4 >= baseline[3]) # url's ending with "jpg", "png" or "gif"
        print "pattern.web.%s.Result(type=%s)" % (api, type.upper())
    
    def test_results_google(self):
        self._test_results("Google",   *self.api["Google"])
    def test_results_yahoo(self):
        self._test_results("Yahoo",    *self.api["Yahoo"])
    def test_results_yahoo_images(self):
        self._test_results("Yahoo",    *self.api["Yahoo"], **{"type": web.IMAGE, "baseline": [6,6,0,6]})
    def test_results_yahoo_news(self):
        self._test_results("Yahoo",    *self.api["Yahoo"], **{"type": web.NEWS})
    def test_results_bing(self):
        self._test_results("Bing",     *self.api["Bing"])
    def test_results_bing_images(self):
        self._test_results("Bing",     *self.api["Bing"], **{"type": web.IMAGE, "baseline": [6,6,0,6]})
    def test_results_bing_news(self):
        self._test_results("Bing",     *self.api["Bing"], **{"type": web.NEWS})
    def test_results_twitter(self):
        self._test_results("Twitter",  *self.api["Twitter"])
    def test_results_flickr(self):
        self._test_results("Flickr", *self.api["Flickr"], **{"baseline": [6,6,0,6]})
    def test_results_facebook(self):
        self._test_results("Facebook", *self.api["Facebook"], **{"baseline": [0,1,0,0]})

    def test_google_translate(self):
        try:
            # Assert Google Translate API.
            # Requires license with billing enabled.
            source, license, Engine = self.api["Google"]
            v = Engine(license, throttle=0.25).translate(u"thé", input="fr", output="en", cached=False)
            self.assertEqual(v, "tea")
            print "pattern.web.Google.translate()"
        except web.HTTP401Authentication:
            pass
            
    def test_google_identify(self):
        try:
            # Assert Google Translate API (language detection).
            # Requires license with billing enabled.
            source, license, Engine = self.api["Google"]
            v = Engine(license, throttle=0.25).identify(u"L'essence des mathématiques, c'est la liberté!", cached=False)
            self.assertEqual(v[0], "fr")
            print "pattern.web.Google.identify()"
        except web.HTTP401Authentication:
            pass
    
    def test_twitter_author(self):
        self.assertEqual(web.author("me"), "from:me")
        print "pattern.web.author()"
    def test_twitter_hashtags(self):
        self.assertEqual(web.hashtags("#cat #dog"), ["#cat", "#dog"])
        print "pattern.web.hashtags()"
    def test_twitter_retweets(self):
        self.assertEqual(web.retweets("RT @me: blah"), ["@me"])
        print "pattern.web.retweets()"
        
    def _test_search_image_size(self, api, source, license, Engine):
        # Assert image URL's for different sizes actually exist.
        if api == web.YAHOO and license == ("",""): 
            return
        e = Engine(license, throttle=0.25)
        for size in (web.TINY, web.SMALL, web.MEDIUM, web.LARGE):
            v = e.search("cat", type=web.IMAGE, count=1, size=size, cached=False)
            self.assertEqual(web.URL(v[0].url).exists, True)
            print "pattern.web.%s.search(type=IMAGE, size=%s)" % (api, size.upper())

    def test_yahoo_image_size(self):
        self._test_search_image_size("Yahoo",  *self.api["Yahoo"])
    def test_bing_image_size(self):
        self._test_search_image_size("Bing",   *self.api["Bing"])
    def test_flickr_image_size(self):
        self._test_search_image_size("Flickr", *self.api["Flickr"])
    
    def test_wikipedia_article(self):
        source, license, Engine = self.api["Wikipedia"]
        v = Engine(license).search("cat", cached=False)
        # Assert WikipediaArticle properties.
        self.assertTrue(isinstance(v.title,      unicode))
        self.assertTrue(isinstance(v.string,     unicode))
        self.assertTrue(isinstance(v.links,      list))
        self.assertTrue(isinstance(v.categories, list))
        self.assertTrue(isinstance(v.external,   list))
        self.assertTrue(isinstance(v.media,      list))
        self.assertTrue(isinstance(v.languages,  dict))
        # Assert WikipediaArticle properties content.
        self.assertTrue(v.string  == v.plaintext())
        self.assertTrue(v.html    == v.source)
        self.assertTrue("</div>"  in v.source)
        self.assertTrue("cat"     in v.title.lower())
        self.assertTrue("Felis"   in v.links)
        self.assertTrue("Felines" in v.categories)
        self.assertTrue("en"      == v.language)
        self.assertTrue("fr"      in v.languages)
        self.assertTrue("chat"    in v.languages["fr"].lower())
        self.assertTrue(v.external[0].startswith("http"))
        self.assertTrue(v.media[0].endswith(("jpg","png","gif","svg")))
        print "pattern.web.WikipediaArticle"
        
    def test_wikipedia_article_sections(self):
        # Assert WikipediaArticle.sections structure.
        # The test may need to be modified if the Wikipedia "Cat" article changes.
        source, license, Engine = self.api["Wikipedia"]
        v = Engine(license).search("cat", cached=False)
        s1 = s2 = s3 = None
        for section in v.sections:
            if section.title == "Behavior":
                s1 = section
            if section.title == "Grooming":
                s2 = section
            if section.title == "Play":
                s3 = section
            self.assertTrue(section.article == v)
            self.assertTrue(section.level == 0 or section.string.startswith(section.title))
        # Test section depth.
        self.assertTrue(s1.level == 1)
        self.assertTrue(s2.level == 2)
        self.assertTrue(s2.level == 2)
        # Test section parent-child structure.
        self.assertTrue(s2 in s1.children) # Behavior => Grooming
        self.assertTrue(s3 in s1.children) # Behavior => Play
        self.assertTrue(s2.parent == s1)
        self.assertTrue(s3.parent == s1)
        # Test section content.
        self.assertTrue("hairballs" in s2.content)
        self.assertTrue("laser pointer" in s3.content)
        # Test section tables.
        # XXX should test <td colspan="x"> more thoroughly.
        self.assertTrue(len(v.sections[1].tables) > 0)
        print "pattern.web.WikipediaSection"

    def test_products(self):
        # Assert product reviews and score.
        source, license, Engine = self.api["Products"]
        v = Engine(license).search("computer", cached=False)
        self.assertTrue(isinstance(v[0].reviews, list))
        self.assertTrue(isinstance(v[0].score, int))
        print "pattern.web.Products.Result.reviews"
        print "pattern.web.Products.Result.score"
            
#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUnicode))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestURL))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPlaintext))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSearchEngine))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())