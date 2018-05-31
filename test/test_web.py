# -*- coding: utf-8 -*-
# These tests require a working internet connection.

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range, next

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
import time
import warnings

from pattern import web

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------


class TestCache(unittest.TestCase):

    def setUp(self):
        pass

    def test_cache(self):
        # Assert cache unicode.
        k, v = "test", "ünîcødé"
        web.cache[k] = v
        self.assertTrue(isinstance(web.cache[k], str))
        self.assertEqual(web.cache[k], v)
        self.assertEqual(web.cache.age(k), 0)
        del web.cache[k]
        print("pattern.web.Cache")

#---------------------------------------------------------------------------------------------------


class TestUnicode(unittest.TestCase):

    def setUp(self):
        # Test data with different (or wrong) encodings.
        self.strings = (
            "ünîcøde",
            "ünîcøde".encode("utf-16"),
            "ünîcøde".encode("latin-1"),
            "ünîcøde".encode("windows-1252"),
             "ünîcøde",
            "אוניקאָד"
        )

    def test_decode_utf8(self):
        # Assert unicode.
        for s in self.strings:
            self.assertTrue(isinstance(web.decode_utf8(s), str))
        print("pattern.web.decode_utf8()")

    def test_encode_utf8(self):
        # Assert Python bytestring.
        for s in self.strings:
            self.assertTrue(isinstance(web.encode_utf8(s), bytes))
        print("pattern.web.encode_utf8()")

    def test_fix(self):
        # Assert fix for common Unicode mistakes.
        self.assertEqual(web.fix("clichÃ©"), "cliché")
        self.assertEqual(web.fix("clichÃ©"), "cliché")
        self.assertEqual(web.fix("cliché"), "cliché")
        self.assertEqual(web.fix("â€“"), "–")

#---------------------------------------------------------------------------------------------------


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
        print("pattern.web.asynchronous()")

    def test_extension(self):
        # Assert filename extension.
        v = web.extension(os.path.join("pattern", "test", "test-web.py.zip"))
        self.assertEqual(v, ".zip")
        print("pattern.web.extension()")

    def test_urldecode(self):
        # Assert URL decode (inverse of urllib.urlencode).
        v = web.urldecode("?user=me&page=1&q=&")
        self.assertEqual(v, {"user": "me", "page": 1, "q": None})
        print("pattern.web.urldecode()")

    def test_proxy(self):
        # Assert URL proxy.
        v = web.proxy("www.proxy.com", "https")
        self.assertEqual(v, ("www.proxy.com", "https"))
        print("pattern.web.proxy()")

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
        print("pattern.web.URL.parts")

    def test_url_query(self):
        # Assert URL.query and URL.querystring.
        v = web.URL(self.url)
        v.query["page"] = 10
        v.query["user"] = None
        self.assertEqual(v.query, {"q": 1, "page": 10, "user": None})
        self.assertEqual(v.querystring, "q=1&page=10&user=")
        # Assert URL.querystring encodes unicode arguments.
        q = ({"ünîcødé": 1.5}, "%C3%BCn%C3%AEc%C3%B8d%C3%A9=1.5")
        v.query = q[0]
        self.assertEqual(v.querystring, q[1])
        # Assert URL.query decodes unicode arguments.
        v = web.URL("http://domain.com?" + q[1])
        self.assertEqual(v.query, q[0])
        print("pattern.web.URL.query")
        print("pattern.web.URL.querystring")

    def test_url_string(self):
        # Assert URL._set_string().
        v = web.URL("")
        v.string = "https://domain.com"
        self.assertEqual(v.parts[web.PROTOCOL], "https")
        self.assertEqual(v.parts[web.DOMAIN], "domain.com")
        self.assertEqual(v.parts[web.PATH], [])
        print("pattern.web.URL.string")

    def test_url(self):
        # Assert URL.copy().
        v = web.URL(self.url)
        v = v.copy()
        # Assert URL.__setattr__().
        v.username = "new-username"
        v.password = "new-password"
        # Assert URL.__getattr__().
        self.assertEqual(v.method, web.GET)
        self.assertEqual(v.protocol, self.parts["protocol"])
        self.assertEqual(v.username, "new-username")
        self.assertEqual(v.password, "new-password")
        self.assertEqual(v.domain, self.parts["domain"])
        self.assertEqual(v.port, self.parts["port"])
        self.assertEqual(v.path, self.parts["path"])
        self.assertEqual(v.page, self.parts["page"])
        self.assertEqual(v.query, self.parts["query"])
        self.assertEqual(v.anchor, self.parts["anchor"])
        print("pattern.web.URL")

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
        self.assertTrue(v.open() is not None)
        self.assertEqual(v.exists, True)
        # Assert user-agent and referer.
        self.assertTrue(v.open(user_agent=web.MOZILLA, referrer=web.REFERRER) is not None)
        print("pattern.web.URL.exists")
        print("pattern.web.URL.open()")

    def test_url_download(self):
        t = time.time()
        v = web.URL(self.live).download(cached=False, throttle=0.25, unicode=True)
        t = time.time() - t
        # Assert unicode content.
        self.assertTrue(isinstance(v, str))
        # Assert download rate limiting.
        self.assertTrue(t >= 0.25)
        print("pattern.web.URL.download()")

    def test_url_mimetype(self):
        # Assert URL MIME-type.
        v = web.URL(self.live).mimetype
        self.assertTrue(v in web.MIMETYPE_WEBPAGE)
        print("pattern.web.URL.mimetype")

    def test_url_headers(self):
        # Assert URL headers.
        v = web.URL(self.live).headers["content-type"].split(";")[0]
        self.assertEqual(v, "text/html")
        print("pattern.web.URL.headers")

    def test_url_redirect(self):
        # Assert URL redirected URL (this depends on where you are).
        # In Belgium, it yields "http://www.google.be/".
        v = web.URL(self.live).redirect
        print("pattern.web.URL.redirect: " + self.live + " => " + str(v))

    def test_abs(self):
        # Assert absolute URL (special attention for anchors).
        for a, b in (
          ("../page.html", "http://domain.com/path/"),
          (   "page.html", "http://domain.com/home.html")):
            v = web.abs(a, base=b)
            self.assertEqual(v, "http://domain.com/page.html")
        for a, b, c in (
          (     "#anchor", "http://domain.com", "/"),
          (     "#anchor", "http://domain.com/", ""),
          (     "#anchor", "http://domain.com/page", "")):
            v = web.abs(a, base=b)
            self.assertEqual(v, b + c + a) # http://domain.com/#anchor
        print("pattern.web.abs()")

    def test_base(self):
        # Assert base URL domain name.
        self.assertEqual(web.base("http://domain.com/home.html"), "domain.com")
        print("pattern.web.base()")

    def test_oauth(self):
        # Assert OAuth algorithm.
        data = {
            "q": '"cåts, døgs & chîckéns = fün+"',
            "oauth_version": "1.0",
            "oauth_nonce": "0",
            "oauth_timestamp": 0,
            "oauth_consumer_key": "key",
            "oauth_signature_method": "HMAC-SHA1"
        }
        v = web.oauth.sign("http://yboss.yahooapis.com/ysearch/web", data, secret="secret")
        self.assertEqual(v, "RtTu8dxSp3uBzSbsuLAXIWOKfyI=")
        print("pattern.web.oauth.sign()")

#---------------------------------------------------------------------------------------------------


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
            self.assertEqual(web.find_urls("(" + url + ".")[0], url)
        # Assert case-insensitive, punctuation and <a href="">.
        # Assert several matches in string.
        self.assertEqual(web.find_urls("HTTP://domain.net")[0], "HTTP://domain.net")
        self.assertEqual(web.find_urls("http://domain.net),};")[0], "http://domain.net")
        self.assertEqual(web.find_urls("http://domain.net\">domain")[0], "http://domain.net")
        self.assertEqual(web.find_urls("domain.com, domain.net"), ["domain.com", "domain.net"])
        print("pattern.web.find_urls()")

    def test_find_email(self):
        # Assert e-mail finder with common e-mail notations.
        s = "firstname.last+name@domain.ac.co.uk"
        v = web.find_email("(" + s + ".")
        self.assertEqual(v[0], s)
        # Assert several matches in string.
        s = ["me@site1.com", "me@site2.com"]
        v = web.find_email("(" + ",".join(s) + ")")
        self.assertEqual(v, s)
        print("pattern.web.find_email()")

    def test_find_between(self):
        # Assert search between open tag and close tag.
        s = "<script type='text/javascript'>alert(0);</script>"
        v = web.find_between("<script", "</script>", s)
        self.assertEqual(v[0], " type='text/javascript'>alert(0);")
        # Assert several matches in string.
        s = "a0ba1b"
        v = web.find_between("a", "b", s)
        self.assertEqual(v, ["0", "1"])
        print("pattern.web.find_between()")

    def test_strip_tags(self):
        # Assert HTML parser and tag stripper.
        for html, plain in (
          ("<b>ünîcøde</b>", "ünîcøde"),
          ("<img src=""/>", ""),
          ("<p>text</p>", "text\n\n"),
          ("<li>text</li>", "* text\n"),
          ("<td>text</td>", "text\t"),
          ("<br>", "\n"),
          ("<br/>", "\n\n"),
          ("<br /><br/><br>", "\n\n\n\n\n")):
            self.assertEqual(web.strip_tags(html), plain)
        # Assert exclude tags and attributes
        v = web.strip_tags("<a href=\"\" onclick=\"\">text</a>", exclude={"a": ["href"]})
        self.assertEqual(v, "<a href=\"\">text</a>")
        print("pattern.web.strip_tags()")

    def test_strip_element(self):
        # Assert strip <p> elements.
        v = web.strip_element(" <p><p></p>text</p> <b><P></P></b>", "p")
        self.assertEqual(v, "  <b></b>")
        print("pattern.web.strip_element()")

    def test_strip_between(self):
        # Assert strip <p> elements.
        v = web.strip_between("<p", "</p>", " <p><p></p>text</p> <b><P></P></b>")
        self.assertEqual(v, " text</p> <b></b>")
        print("pattern.web.strip_between()")

    def test_strip_javascript(self):
        # Assert strip <script> elements.
        v = web.strip_javascript(" <script type=\"text/javascript\">text</script> ")
        self.assertEqual(v, "  ")
        print("pattern.web.strip_javascript()")

    def test_strip_inline_css(self):
        # Assert strip <style> elements.
        v = web.strip_inline_css(" <style type=\"text/css\">text</style> ")
        self.assertEqual(v, "  ")
        print("pattern.web.strip_inline_css()")

    def test_strip_comments(self):
        # Assert strip <!-- --> elements.
        v = web.strip_comments(" <!-- text --> ")
        self.assertEqual(v, "  ")
        print("pattern.web.strip_comments()")

    def test_strip_forms(self):
        # Assert strip <form> elements.
        v = web.strip_forms(" <form method=\"get\">text</form> ")
        self.assertEqual(v, "  ")
        print("pattern.web.strip_forms()")

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
        print("pattern.web.encode_entities()")

    def test_decode_entities(self):
        # Assert HMTL entity decoder (e.g., "&amp;" => "&")
        for a, b in (
          ("&#38;", "&"),
          ("&amp;", "&"),
          ("&#x0026;", "&"),
          ("&#160;", "\xa0"),
          ("&foo;", "&foo;")):
            self.assertEqual(web.decode_entities(a), b)
        print("pattern.web.decode_entities()")

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
        print("pattern.web.collapse_spaces()")

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
        print("pattern.web.collapse_tabs()")

    def test_collapse_linebreaks(self):
        # Assert collapse multiple linebreaks.
        for a, b in (
          ("\n\n\n", "\n"),
          (".\n\n.", ".\n."),
          (".\r\n.", ".\n."),
          (".\n  .", ".\n  ."),
          (" \n  .", "\n  .")):
            self.assertEqual(web.collapse_linebreaks(a), b)
        print("pattern.web.collapse_linebreaks()")

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
            "tags & things\n\ntitle1\n\ntitle2\n\nparagraph1\n\nparagraph2 " + \
            "<a href=\"http://www.domain.com\">link</a>\n\n* item1 xxx\n* item2")
        print("pattern.web.plaintext()")

#---------------------------------------------------------------------------------------------------


class TestSearchEngine(unittest.TestCase):

    def setUp(self):
        # Test data for all search engines:
        # {api: (source, license, Engine)}.
        self.api = {
            "Google": (web.GOOGLE,      web.GOOGLE_LICENSE,      web.Google),
             "Yahoo": (web.YAHOO,       web.YAHOO_LICENSE,       web.Yahoo),
              "Bing": (web.BING,        web.BING_LICENSE,        web.Bing),
           "Twitter": (web.TWITTER,     web.TWITTER_LICENSE,     web.Twitter),
         "Wikipedia": (web.MEDIAWIKI,   web.WIKIPEDIA_LICENSE,   web.Wikipedia),
             "Wikia": (web.MEDIAWIKI,   web.MEDIAWIKI_LICENSE,   web.Wikia),
            "Flickr": (web.FLICKR,      web.FLICKR_LICENSE,      web.Flickr),
          "Facebook": (web.FACEBOOK,    web.FACEBOOK_LICENSE,    web.Facebook),
       "ProductWiki": (web.PRODUCTWIKI, web.PRODUCTWIKI_LICENSE, web.ProductWiki)
        }

    def _test_search_engine(self, api, source, license, Engine, query="today", type=web.SEARCH):
        # Assert SearchEngine standard interface for any api:
        # Google, Yahoo, Bing, Twitter, Wikipedia, Flickr, Facebook, ProductWiki, Newsfeed.
        # SearchEngine.search() returns a list of Result objects with unicode fields,
        # except Wikipedia which returns a WikipediaArticle (MediaWikiArticle subclass).
        if api == "Yahoo" and license == ("", ""):
            return
        t = time.time()
        e = Engine(license=license, throttle=0.25, language="en")
        v = e.search(query, type, start=1, count=1, cached=False)
        t = time.time() - t
        self.assertTrue(t >= 0.25)
        self.assertEqual(e.license, license)
        self.assertEqual(e.throttle, 0.25)
        self.assertEqual(e.language, "en")
        self.assertEqual(v.query, query)
        if source != web.MEDIAWIKI:
            self.assertEqual(v.source, source)
            self.assertEqual(v.type, type)
            self.assertEqual(len(v), 1)
            self.assertTrue(isinstance(v[0], web.Result))
            self.assertTrue(isinstance(v[0].url, str))
            self.assertTrue(isinstance(v[0].title, str))
            self.assertTrue(isinstance(v[0].description, str))
            self.assertTrue(isinstance(v[0].language, str))
            self.assertTrue(isinstance(v[0].author, (str, tuple)))
            self.assertTrue(isinstance(v[0].date, str))
        else:
            self.assertTrue(isinstance(v, web.MediaWikiArticle))
        # Assert zero results for start < 1 and count < 1.
        v1 = e.search(query, start=0)
        v2 = e.search(query, count=0)
        if source != web.MEDIAWIKI:
            self.assertEqual(len(v1), 0)
            self.assertEqual(len(v2), 0)
        else:
            self.assertTrue(isinstance(v1, web.MediaWikiArticle))
            self.assertEqual(v2, None)
        # Assert SearchEngineTypeError for unknown type.
        self.assertRaises(web.SearchEngineTypeError, e.search, query, type="crystall-ball")
        print("pattern.web.%s.search()" % api)

    def test_search_google(self):
        self._test_search_engine("Google", *self.api["Google"])

    def test_search_yahoo(self):
        self._test_search_engine("Yahoo", *self.api["Yahoo"])

    @unittest.skip('Bing Search API has no free quota')
    def test_search_bing(self):
        self._test_search_engine("Bing", *self.api["Bing"])

    def test_search_twitter(self):
        self._test_search_engine("Twitter", *self.api["Twitter"])

    @unittest.skip('Mediawiki/Wikipedia API or appearance changed')
    def test_search_wikipedia(self):
        self._test_search_engine("Wikipedia", *self.api["Wikipedia"])

    @unittest.skip('Mediawiki API or appearance changed')
    def test_search_wikia(self):
        self._test_search_engine("Wikia", *self.api["Wikia"], **{"query": "games"})

    def test_search_flickr(self):
        self._test_search_engine("Flickr", *self.api["Flickr"], **{"type": web.IMAGE})

    @unittest.skip('Facebook API changed')
    def test_search_facebook(self):
        self._test_search_engine("Facebook", *self.api["Facebook"])

    @unittest.skip('ProductWiki is deprecated')
    def test_search_productwiki(self):
        self._test_search_engine("ProductWiki", *self.api["ProductWiki"], **{"query": "computer"})

    def test_search_newsfeed(self):
        for feed, url in web.feeds.items():
            self._test_search_engine("Newsfeed", url, None, web.Newsfeed, query=url, type=web.NEWS)

    def _test_results(self, api, source, license, Engine, type=web.SEARCH, query="today", baseline=[6, 6, 6, 0]):
        # Assert SearchEngine result content.
        # We expect to find http:// URL's and descriptions containing the search query.
        if api == "Yahoo" and license == ("", ""):
            return
        i1 = 0
        i2 = 0
        i3 = 0
        i4 = 0
        e = Engine(license=license, language="en", throttle=0.25)
        for result in e.search(query, type, count=10, cached=False):
            i1 += int(result.url.startswith("http"))
            i2 += int(query in result.url.lower())
            i2 += int(query in result.title.lower())
            i2 += int(query in result.description.lower())
            i3 += int(result.language == "en")
            i4 += int(result.url.endswith(("jpg", "png", "gif")))
            #print(result.url)
            #print(result.title)
            #print(result.description)
        #print(i1, i2, i3, i4)
        self.assertTrue(i1 >= baseline[0]) # url's starting with "http"
        self.assertTrue(i2 >= baseline[1]) # query in url + title + description
        self.assertTrue(i3 >= baseline[2]) # language "en"
        self.assertTrue(i4 >= baseline[3]) # url's ending with "jpg", "png" or "gif"
        print("pattern.web.%s.Result(type=%s)" % (api, type.upper()))

    def test_results_google(self):
        self._test_results("Google", *self.api["Google"])

    def test_results_yahoo(self):
        self._test_results("Yahoo", *self.api["Yahoo"])

    def test_results_yahoo_images(self):
        self._test_results("Yahoo", *self.api["Yahoo"], **{"type": web.IMAGE, "baseline": [6, 6, 0, 6]})

    def test_results_yahoo_news(self):
        self._test_results("Yahoo", *self.api["Yahoo"], **{"type": web.NEWS})

    @unittest.skip('Bing API changed')
    def test_results_bing(self):
        self._test_results("Bing", *self.api["Bing"])

    @unittest.skip('Bing API changed')
    def test_results_bing_images(self):
        self._test_results("Bing", *self.api["Bing"], **{"type": web.IMAGE, "baseline": [6, 6, 0, 6]})

    @unittest.skip('Bing API changed')
    def test_results_bing_news(self):
        self._test_results("Bing", *self.api["Bing"], **{"type": web.NEWS})

    def test_results_twitter(self):
        self._test_results("Twitter", *self.api["Twitter"])

    def test_results_flickr(self):
        self._test_results("Flickr", *self.api["Flickr"], **{"baseline": [6, 6, 0, 6]})

    @unittest.skip('Facebook API changed')
    def test_results_facebook(self):
        self._test_results("Facebook", *self.api["Facebook"], **{"baseline": [0, 1, 0, 0]})

    def test_google_translate(self):
        try:
            # Assert Google Translate API.
            # Requires license with billing enabled.
            source, license, Engine = self.api["Google"]
            v = Engine(license, throttle=0.25).translate("thé", input="fr", output="en", cached=False)
            self.assertEqual(v, "tea")
            print("pattern.web.Google.translate()")
        except web.HTTP401Authentication:
            pass

    def test_google_identify(self):
        try:
            # Assert Google Translate API (language detection).
            # Requires license with billing enabled.
            source, license, Engine = self.api["Google"]
            v = Engine(license, throttle=0.25).identify("L'essence des mathématiques, c'est la liberté!", cached=False)
            self.assertEqual(v[0], "fr")
            print("pattern.web.Google.identify()")
        except web.HTTP401Authentication:
            pass

    def test_twitter_author(self):
        self.assertEqual(web.author("me"), "from:me")
        print("pattern.web.author()")

    def test_twitter_hashtags(self):
        self.assertEqual(web.hashtags("#cat #dog"), ["#cat", "#dog"])
        print("pattern.web.hashtags()")

    def test_twitter_retweets(self):
        self.assertEqual(web.retweets("RT @me: blah"), ["@me"])
        print("pattern.web.retweets()")

    def _test_search_image_size(self, api, source, license, Engine):
        # Assert image URL's for different sizes actually exist.
        if api == "Yahoo" and license == ("", ""):
            return
        e = Engine(license, throttle=0.25)
        for size in (web.TINY, web.SMALL, web.MEDIUM, web.LARGE):
            v = e.search("cats", type=web.IMAGE, count=1, size=size, cached=False)
            self.assertEqual(web.URL(v[0].url).exists, True)
            print("pattern.web.%s.search(type=IMAGE, size=%s)" % (api, size.upper()))

    def test_yahoo_image_size(self):
        self._test_search_image_size("Yahoo", *self.api["Yahoo"])

    @unittest.skip('Bing Search API has no free quota')
    def test_bing_image_size(self):
        self._test_search_image_size("Bing", *self.api["Bing"])

    def test_flickr_image_size(self):
        self._test_search_image_size("Flickr", *self.api["Flickr"])

    @unittest.skip('Mediawiki/Wikipedia API or appearance changed')
    def test_wikipedia_list(self):
        # Assert WikipediaArticle.list(), an iterator over all article titles.
        source, license, Engine = self.api["Wikipedia"]
        v = Engine(license).list(start="a", count=1)
        v = [next(v) for i in range(2)]
        self.assertTrue(len(v) == 2)
        self.assertTrue(v[0].lower().startswith("a"))
        self.assertTrue(v[1].lower().startswith("a"))
        print("pattern.web.Wikipedia.list()")

    def test_wikipedia_all(self):
        # Assert WikipediaArticle.all(), an iterator over WikipediaArticle objects.
        source, license, Engine = self.api["Wikipedia"]
        v = Engine(license).all(start="a", count=1)
        v = [next(v) for i in range(1)]
        self.assertTrue(len(v) == 1)
        self.assertTrue(isinstance(v[0], web.WikipediaArticle))
        self.assertTrue(v[0].title.lower().startswith("a"))
        print("pattern.web.Wikipedia.all()")

    @unittest.skip('Mediawiki/Wikipedia API or appearance changed')
    def test_wikipedia_article(self):
        source, license, Engine = self.api["Wikipedia"]
        v = Engine(license).search("cat", cached=False)
        # Assert WikipediaArticle properties.
        self.assertTrue(isinstance(v.title, str))
        self.assertTrue(isinstance(v.string, str))
        self.assertTrue(isinstance(v.links, list))
        self.assertTrue(isinstance(v.categories, list))
        self.assertTrue(isinstance(v.external, list))
        self.assertTrue(isinstance(v.media, list))
        self.assertTrue(isinstance(v.languages, dict))
        # Assert WikipediaArticle properties content.
        self.assertTrue(v.string == v.plaintext())
        self.assertTrue(v.html == v.source)
        self.assertTrue("</div>"  in v.source)
        self.assertTrue("cat"     in v.title.lower())
        self.assertTrue("Felis"   in v.links)
        self.assertTrue("Felines" in v.categories)
        self.assertTrue("en" == v.language)
        self.assertTrue("fr"      in v.languages)
        self.assertTrue("chat"    in v.languages["fr"].lower())
        self.assertTrue(v.external[0].startswith("http"))
        self.assertTrue(v.media[0].endswith(("jpg", "png", "gif", "svg")))
        print("pattern.web.WikipediaArticle")

    @unittest.skip('Mediawiki/Wikipedia API or appearance changed')
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
        print("pattern.web.WikipediaSection")

    @unittest.skip('ProductWiki is deprecated')
    def test_productwiki(self):
        # Assert product reviews and score.
        source, license, Engine = self.api["ProductWiki"]
        v = Engine(license).search("computer", cached=False)
        self.assertTrue(isinstance(v[0].reviews, list))
        self.assertTrue(isinstance(v[0].score, int))
        print("pattern.web.ProductWiki.Result.reviews")
        print("pattern.web.ProductWiki.Result.score")

#---------------------------------------------------------------------------------------------------


class TestDOM(unittest.TestCase):

    def setUp(self):
        # Test HTML document.
        self.html = """
            <!doctype html>
            <html lang="en">
            <head>
                <title>title</title>
                <meta charset="utf-8" />
            </head>
            <body id="front" class="comments">
                <script type="text/javascript">alert(0);</script>
                <div id="navigation">
                    <a href="nav1.html">nav1</a> | 
                    <a href="nav2.html">nav2</a> | 
                    <a href="nav3.html">nav3</a>
                </div>
                <div id="content">
                    <P class="comment">
                        <span class="date">today</span>
                        <span class="author">me</span>
                        Blah blah
                    </P>
                    <P class="class1 class2">
                        Blah blah
                    </P>
                    <p>Read more</p>
                </div>
            </body>
            </html>
        """

    def test_node_document(self):
        # Assert Node properties.
        v1 = web.Document(self.html)
        self.assertEqual(v1.type, web.DOCUMENT)
        self.assertEqual(v1.source[:10], "<!DOCTYPE ") # Note: BeautifulSoup strips whitespace.
        self.assertEqual(v1.parent, None)
        # Assert Node traversal.
        v2 = v1.children[0].next
        self.assertEqual(v2.type, web.ELEMENT)
        self.assertEqual(v2.previous, v1.children[0])
        # Assert Document properties.
        v3 = v1.declaration
        self.assertEqual(v3, v1.children[0])
        self.assertEqual(v3.parent, v1)
        self.assertEqual(v3.source, "html")
        self.assertEqual(v1.head.type, web.ELEMENT)
        self.assertEqual(v1.body.type, web.ELEMENT)
        self.assertTrue(v1.head.source.startswith("<head"))
        self.assertTrue(v1.body.source.startswith("<body"))
        print("pattern.web.Node")
        print("pattern.web.DOM")

    def test_node_traverse(self):
        # Assert Node.traverse() (must visit all child nodes recursively).
        self.b = False

        def visit(node):
            if node.type == web.ELEMENT and node.tag == "span":
                self.b = True
        v = web.DOM(self.html)
        v.traverse(visit)
        self.assertEqual(self.b, True)
        print("pattern.web.Node.traverse()")

    def test_element(self):
        # Assert Element properties (test <body>).
        v = web.DOM(self.html).body
        self.assertEqual(v.tag, "body")
        self.assertEqual(v.attributes["id"], "front")
        self.assertEqual(v.attributes["class"], ["comments"])
        self.assertTrue(v.content.startswith("\n<script"))
        # Assert Element.getElementsByTagname() (test navigation links).
        a = v.by_tag("a")
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0].content, "nav1")
        self.assertEqual(a[1].content, "nav2")
        self.assertEqual(a[2].content, "nav3")
        # Assert Element.getElementsByClassname() (test <p class="comment">).
        a = v.by_class("comment")
        self.assertEqual(a[0].tag, "p")
        self.assertEqual(a[0].by_tag("span")[0].attributes["class"], ["date"])
        self.assertEqual(a[0].by_tag("span")[1].attributes["class"], ["author"])
        for selector in (".comment", "p.comment", "*.comment"):
            self.assertEqual(v.by_tag(selector)[0], a[0])
        # Assert Element.getElementById() (test <div id="content">).
        e = v.by_id("content")
        self.assertEqual(e.tag, "div")
        self.assertEqual(e, a[0].parent)
        for selector in ("#content", "div#content", "*#content"):
            self.assertEqual(v.by_tag(selector)[0], e)
        # Assert Element.getElementByAttribute() (test on <a href="">).
        a = v.by_attribute(href="nav1.html")
        self.assertEqual(a[0].content, "nav1")
        print("pattern.web.Element")
        print("pattern.web.Element.by_tag()")
        print("pattern.web.Element.by_class()")
        print("pattern.web.Element.by_id()")
        print("pattern.web.Element.by_attribute()")

    def test_selector(self):
        # Assert DOM CSS selectors with multiple classes.
        v = web.DOM(self.html).body
        p = v("p.class1")
        self.assertEqual(len(p), 1)
        self.assertTrue("class1" in p[0].attributes["class"])
        p = v("p.class2")
        self.assertEqual(len(p), 1)
        self.assertTrue("class2" in p[0].attributes["class"])
        p = v("p.class1.class2")
        self.assertEqual(len(p), 1)
        self.assertTrue("class1" in p[0].attributes["class"])
        self.assertTrue("class2" in p[0].attributes["class"])
        e = p[0]
        self.assertEqual(e, v("p[class='class1 class2']")[0])
        self.assertEqual(e, v("p[class^='class1']")[0])
        self.assertEqual(e, v("p[class$='class2']")[0])
        self.assertEqual(e, v("p[class*='class']")[0])
        self.assertEqual(e, v("p:contains('blah')")[1])
        self.assertTrue(web.Selector("p[class='class1 class2']").match(e))
        print("pattern.web.Selector()")

#---------------------------------------------------------------------------------------------------


class TestDocumentParser(unittest.TestCase):

    def setUp(self):
        pass

    def test_pdf(self):
        # Assert PDF to string parser.
        s = web.parsedoc(os.path.join(PATH, "corpora", "carroll-wonderland.pdf"))
        self.assertTrue("Curiouser and curiouser!" in s)
        self.assertTrue(isinstance(s, str))
        print("pattern.web.parsepdf()")

    def test_docx(self):
        # Assert PDF to string parser.
        s = web.parsedoc(os.path.join(PATH, "corpora", "carroll-lookingglass.docx"))
        self.assertTrue("'Twas brillig, and the slithy toves" in s)
        self.assertTrue(isinstance(s, str))
        print("pattern.web.parsedocx()")

#---------------------------------------------------------------------------------------------------


class TestLocale(unittest.TestCase):

    def setUp(self):
        pass

    def test_encode_language(self):
        # Assert "Dutch" => "nl".
        self.assertEqual(web.locale.encode_language("dutch"), "nl")
        self.assertEqual(web.locale.encode_language("?????"), None)
        print("pattern.web.locale.encode_language()")

    def test_decode_language(self):
        # Assert "nl" => "Dutch".
        self.assertEqual(web.locale.decode_language("nl"), "Dutch")
        self.assertEqual(web.locale.decode_language("NL"), "Dutch")
        self.assertEqual(web.locale.decode_language("??"), None)
        print("pattern.web.locale.decode_language()")

    def test_encode_region(self):
        # Assert "Belgium" => "BE".
        self.assertEqual(web.locale.encode_region("belgium"), "BE")
        self.assertEqual(web.locale.encode_region("???????"), None)
        print("pattern.web.locale.encode_region()")

    def test_decode_region(self):
        # Assert "BE" => "Belgium".
        self.assertEqual(web.locale.decode_region("be"), "Belgium")
        self.assertEqual(web.locale.decode_region("BE"), "Belgium")
        self.assertEqual(web.locale.decode_region("??"), None)
        print("pattern.web.locale.decode_region()")

    def test_languages(self):
        # Assert "BE" => "fr" + "nl".
        self.assertEqual(web.locale.languages("be"), ["fr", "nl"])
        print("pattern.web.locale.languages()")

    def test_regions(self):
        # Assert "nl" => "NL" + "BE".
        self.assertEqual(web.locale.regions("nl"), ["NL", "BE"])
        print("pattern.web.locale.regions()")

    def test_regionalize(self):
        # Assert "nl" => "nl-NL" + "nl-BE".
        self.assertEqual(web.locale.regionalize("nl"), ["nl-NL", "nl-BE"])
        print("pattern.web.locale.regionalize()")

    def test_geocode(self):
        # Assert region geocode.
        v = web.locale.geocode("brussels")
        self.assertAlmostEqual(v[0], 50.83, places=2)
        self.assertAlmostEqual(v[1], 4.33, places=2)
        self.assertEqual(v[2], "nl")
        self.assertEqual(v[3], "Belgium")
        print("pattern.web.locale.geocode()")

    def test_correlation(self):
        # Test the correlation between locale.LANGUAGE_REGION and locale.GEOCODE.
        # It should increase as new languages and locations are added.
        i = 0
        n = len(web.locale.GEOCODE)
        for city, (latitude, longitude, language, region) in web.locale.GEOCODE.items():
            if web.locale.encode_region(region) is not None:
                i += 1
        self.assertTrue(float(i) / n > 0.60)

#---------------------------------------------------------------------------------------------------
# You need to define a username, password and mailbox to test on.


class TestMail(unittest.TestCase):

    def setUp(self):
        self.username = ""
        self.password = ""
        self.service = web.GMAIL
        self.port = 993
        self.SSL = True
        self.query1 = "google" # FROM-field query in Inbox.
        self.query2 = "viagra" # SUBJECT-field query in Spam.

    def test_mail(self):
        if not self.username or not self.password:
            return
        # Assert web.imap.Mail.
        m = web.Mail(self.username, self.password, service=self.service, port=self.port, secure=self.SSL)
        # Assert web.imap.MailFolder (assuming GMail folders).
        print(m.folders)
        self.assertTrue(len(m.folders) > 0)
        self.assertTrue(len(m.inbox) > 0)
        print("pattern.web.Mail")

    def test_mail_message1(self):
        if not self.username or not self.password or not self.query1:
            return
        # Assert web.imap.Mailfolder.search().
        m = web.Mail(self.username, self.password, service=self.service, port=self.port, secure=self.SSL)
        a = m.inbox.search(self.query1, field=web.FROM)
        self.assertTrue(isinstance(a[0], int))
        # Assert web.imap.Mailfolder.read().
        e = m.inbox.read(a[0], attachments=False, cached=False)
        # Assert web.imap.Message.
        self.assertTrue(isinstance(e, web.imap.Message))
        self.assertTrue(isinstance(e.author, str))
        self.assertTrue(isinstance(e.email_address, str))
        self.assertTrue(isinstance(e.date, str))
        self.assertTrue(isinstance(e.subject, str))
        self.assertTrue(isinstance(e.body, str))
        self.assertTrue(self.query1 in e.author.lower())
        self.assertTrue("@" in e.email_address)
        print("pattern.web.Mail.search(field=FROM)")
        print("pattern.web.Mail.read()")

    def test_mail_message2(self):
        if not self.username or not self.password or not self.query2:
            return
        # Test if we can download some mail attachments.
        # Set query2 to a mail subject of a spam e-mail you know contains an attachment.
        m = web.Mail(self.username, self.password, service=self.service, port=self.port, secure=self.SSL)
        if "spam" in m.folders:
            for id in m.spam.search(self.query2, field=web.SUBJECT):
                e = m.spam.read(id, attachments=True, cached=False)
                if len(e.attachments) > 0:
                    self.assertTrue(isinstance(e.attachments[0][1], bytes))
                    self.assertTrue(len(e.attachments[0][1]) > 0)
                    print("pattern.web.Message.attachments (MIME-type: %s)" % e.attachments[0][0])
        print("pattern.web.Mail.search(field=SUBJECT)")
        print("pattern.web.Mail.read()")

#---------------------------------------------------------------------------------------------------


class TestCrawler(unittest.TestCase):

    def setUp(self):
        pass

    def test_link(self):
        # Assert web.Link parser and properties.
        v = web.HTMLLinkParser().parse("""
            <html>
            <head>
                <title>title</title>
            </head>
            <body>
                <div id="navigation">
                    <a href="http://www.domain1.com/?p=1" title="1" rel="a">nav1</a>
                    <a href="http://www.domain2.com/?p=2" title="2" rel="b">nav1</a>
                </div>
            </body>
            </html>
        """, "http://www.domain.com/")
        self.assertTrue(v[0].url, "http://www.domain1.com/?p=1")
        self.assertTrue(v[1].url, "http://www.domain1.com/?p=2")
        self.assertTrue(v[0].description, "1")
        self.assertTrue(v[1].description, "2")
        self.assertTrue(v[0].relation, "a")
        self.assertTrue(v[1].relation, "b")
        self.assertTrue(v[0].referrer, "http://www.domain.com/")
        self.assertTrue(v[1].referrer, "http://www.domain.com/")
        self.assertTrue(v[0] < v[1])
        print("pattern.web.HTMLLinkParser")

    def test_crawler_crawl(self):
        # Assert domain filter.
        v = web.Crawler(links=["http://nodebox.net/"], domains=["nodebox.net"], delay=0.5)
        while len(v.visited) < 4:
            v.crawl(throttle=0.1, cached=False)
        for url in v.visited:
            self.assertTrue("nodebox.net" in url)
        self.assertTrue(len(v.history) == 2)
        print("pattern.web.Crawler.crawl()")

    def test_crawler_delay(self):
        # Assert delay for several crawls to a single domain.
        v = web.Crawler(links=["http://nodebox.net/"], domains=["nodebox.net"], delay=1.2)
        v.crawl()
        t = time.time()
        while not v.crawl(throttle=0.1, cached=False):
            pass
        t = time.time() - t
        self.assertTrue(t > 1.0)
        print("pattern.web.Crawler.delay")

    def test_crawler_breadth(self):
        # Assert BREADTH cross-domain preference.
        v = web.Crawler(links=["http://nodebox.net/"], delay=10)
        while len(v.visited) < 4:
            v.crawl(throttle=0.1, cached=False, method=web.BREADTH)
        self.assertTrue(list(v.history.keys())[0] != list(v.history.keys())[1])
        self.assertTrue(list(v.history.keys())[0] != list(v.history.keys())[2])
        self.assertTrue(list(v.history.keys())[1] != list(v.history.keys())[2])
        print("pattern.web.Crawler.crawl(method=BREADTH)")

#---------------------------------------------------------------------------------------------------


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestCache))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUnicode))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestURL))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPlaintext))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSearchEngine))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDOM))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDocumentParser))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestLocale))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMail))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestCrawler))
    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
