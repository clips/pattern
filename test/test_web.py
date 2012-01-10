# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest
import time

from pattern import web

#-----------------------------------------------------------------------------------------------------

class TestUnicode(unittest.TestCase):
    
    def setUp(self):
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
        v = web.strip_element(" <p><p></p>text</p> <b><P></P></b>", "p")
        self.assertEqual(v, "  <b></b>")
        
    def test_strip_between(self):
        v = web.strip_between("<p", "</p>", " <p><p></p>text</p> <b><P></P></b>")
        self.assertEqual(v, " text</p> <b></b>")
        
    def test_strip_javascript(self):
        v = web.strip_javascript(" <script type=\"text/javascript\">text</script> ")
        self.assertEqual(v, "  ")

    def test_strip_inline_css(self):
        v = web.strip_inline_css(" <style type=\"text/css\">text</style> ")
        self.assertEqual(v, "  ")
        
    def test_strip_comments(self):
        v = web.strip_comments(" <!-- text --> ")
        self.assertEqual(v, "  ")

    def test_strip_forms(self):
        v = web.strip_forms(" <form method=\"get\">text</form> ")
        self.assertEqual(v, "  ")
        
    def test_encode_entities(self):
        for a, b in (
          ("&#201;", "&#201;"), 
          ("&", "&amp;"), 
          ("<", "&lt;"), 
          (">", "&gt;"), 
          ('"', "&quot;"),
          ("'", "&#39;")):
            self.assertEqual(web.encode_entities(a), b)
            
    def test_decode_entities(self):
        for a, b in (
          ("&#38;", "&"),
          ("&amp;", "&"),
          ("&#x0026;", "&"),
          ("&foo;", "&foo;")):
            self.assertEqual(web.decode_entities(a), b)
            
    def test_collapse_spaces(self):
        for a, b in (
          ("    ", ""),
          (" .. ", ".."),
          (".  .", ". ."),
          (". \n", ".")):
            self.assertEqual(web.collapse_spaces(a), b)
        # Assert preserve indendation.
        self.assertEqual(web.collapse_spaces("  . \n", indentation=True), "  .")
        
    def test_collapse_tabs(self):
        for a, b in (
          ("\t\t\t", ""),
          ("\t..\t", ".."),
          (".\t\t.", ". ."),
          (".\t\n", ".")):
            self.assertEqual(web.collapse_tabs(a), b)
        # Assert preserve indendation.
        self.assertEqual(web.collapse_tabs("\t\t .\t\n", indentation=True), "\t\t .")
        
    def collapse_linebreaks(self):
        for a, b in (
          ("\n\n\n", "\n"),
          (".\n\n.", ".\n."),
          (".\r\n.", ".\n."),
          (".\n  .", ".\n.")):
            self.assertEqual(web.collapse_linebreaks(a), b)
    
        

#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUnicode))
    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestURL))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPlaintext))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())