# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import unittest
import time

from pattern import web

#-----------------------------------------------------------------------------------------------------

class TestURL(unittest.TestCase):
    
    def setUp(self):
        # Set up a URL with fast response time for live testing.
        self.live = "http://www.google.com/"
        # Set up a (fake) URL with all the different parts for testing the URL parser.
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

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestURL))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())