#### PATTERN | WEB #################################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Python API interface for various web services (Google, Twitter, Wikipedia, ...)

# smgllib.py is removed from Python 3, a warning is issued in Python 2.6+. Ignore for now.
import warnings; warnings.filterwarnings(action='ignore', category=DeprecationWarning, module="sgmllib")

import threading
import time
import os
import socket, urlparse, urllib, urllib2
import base64
import htmlentitydefs
import sgmllib
import re
import xml.dom.minidom
import StringIO
import bisect

import api
import feed
import oauth
import json
import locale

from feed import feedparser
from soup import BeautifulSoup

try:
    # Import persistent Cache.
    # If this module is used separately, a dict is used (i.e. for this Python session only).
    from cache import Cache, cache, TMP
except:
    cache = {}

try:
    from imap import Mail, MailFolder, Message, GMAIL
    from imap import MailError, MailServiceError, MailLoginError, MailNotLoggedIn
    from imap import FROM, SUBJECT, DATE, BODY, ATTACHMENTS
except:
    pass
    
try:
    MODULE = os.path.dirname(os.path.abspath(__file__))
except:
    MODULE = ""

#### UNICODE #######################################################################################

def decode_utf8(string):
    """ Returns the given string as a unicode string (if possible).
    """
    if isinstance(string, str):
        for encoding in (("utf-8",), ("windows-1252",), ("utf-8", "ignore")):
            try: 
                return string.decode(*encoding)
            except:
                pass
        return string
    return unicode(string)
    
def encode_utf8(string):
    """ Returns the given string as a Python byte string (if possible).
    """
    if isinstance(string, unicode):
        try: 
            return string.encode("utf-8")
        except:
            return string
    return str(string)

u = decode_utf8
s = encode_utf8

# For clearer source code:
bytestring = s

#### ASYNCHRONOUS REQUEST ##########################################################################

class AsynchronousRequest:
    
    def __init__(self, function, *args, **kwargs):
        """ Executes the function in the background.
            AsynchronousRequest.done is False as long as it is busy, but the program will not halt in the meantime.
            AsynchronousRequest.value contains the function's return value once done.
            AsynchronousRequest.error contains the Exception raised by an erronous function.
            For example, this is useful for running live web requests while keeping an animation running.
            For good reasons, there is no way to interrupt a background process (i.e. Python thread).
            You are responsible for ensuring that the given function doesn't hang.
        """
        self._response = None # The return value of the given function.
        self._error    = None # The exception (if any) raised by the function.
        self._time     = time.time()
        self._function = function
        self._thread   = threading.Thread(target=self._fetch, args=(function,)+args, kwargs=kwargs)
        self._thread.start()
        
    def _fetch(self, function, *args, **kwargs):
        """ Executes the function and sets AsynchronousRequest.response.
        """
        try: 
            self._response = function(*args, **kwargs)
        except Exception, e:
            self._error = e

    def now(self):
        """ Waits for the function to finish and yields its return value.
        """
        self._thread.join(); return self._response

    @property
    def elapsed(self):
        return time.time() - self._time
    @property
    def done(self):
        return not self._thread.isAlive()
    @property
    def value(self):
        return self._response
    @property
    def error(self):
        return self._error
        
    def __repr__(self):
        return "AsynchronousRequest(function='%s')" % self._function.__name__

def asynchronous(function, *args, **kwargs):
    """ Returns an AsynchronousRequest object for the given function.
    """
    return AsynchronousRequest(function, *args, **kwargs)
    
send = asynchronous

#### URL ###########################################################################################

# User agent and referrer.
# Used to identify the application accessing the web.
USER_AGENT = "Pattern/2.3 +http://www.clips.ua.ac.be/pages/pattern"
REFERRER   = "http://www.clips.ua.ac.be/pages/pattern"

# Mozilla user agent.
# Websites can include code to block out any application except browsers.
MOZILLA = "Mozilla/5.0"

# HTTP request method.
GET  = "get"  # Data is encoded in the URL.
POST = "post" # Data is encoded in the message body.

# URL parts.
# protocol://username:password@domain:port/path/page?query_string#anchor
PROTOCOL, USERNAME, PASSWORD, DOMAIN, PORT, PATH, PAGE, QUERY, ANCHOR = \
    "protocol", "username", "password", "domain", "port", "path", "page", "query", "anchor"

# MIME type.
MIMETYPE_WEBPAGE    = ["text/html"]
MIMETYPE_STYLESHEET = ["text/css"]
MIMETYPE_PLAINTEXT  = ["text/plain"]
MIMETYPE_PDF        = ["application/pdf"]
MIMETYPE_NEWSFEED   = ["application/rss+xml", "application/atom+xml"]
MIMETYPE_IMAGE      = ["image/gif", "image/jpeg", "image/png", "image/tiff"]
MIMETYPE_AUDIO      = ["audio/mpeg", "audio/mp4", "audio/x-aiff", "audio/x-wav"]
MIMETYPE_VIDEO      = ["video/mpeg", "video/mp4", "video/quicktime"]
MIMETYPE_ARCHIVE    = ["application/x-stuffit", "application/x-tar", "application/zip"]
MIMETYPE_SCRIPT     = ["application/javascript", "application/ecmascript"]

def extension(filename):
    """ Returns the extension in the given filename: "cat.jpg" => ".jpg".
    """
    return os.path.splitext(filename)[1]

def urldecode(query):
    """ Inverse operation of urllib.urlencode.
        Returns a dictionary of (name, value)-items from a URL query string.
    """
    def _format(s):
        if s == "None":
             return None
        if s.isdigit(): 
             return int(s)
        try: return float(s)
        except:
             return s
    query = [(kv.split("=")+[None])[:2] for kv in query.lstrip("?").split("&")]
    query = [(urllib.unquote_plus(bytestring(k)), urllib.unquote_plus(bytestring(v))) for k, v in query]
    query = [(u(k), u(v)) for k, v in query]
    query = [(k, _format(v) or None) for k, v in query]
    query = dict([(k,v) for k, v in query if k != ""])
    return query
    
url_decode = urldecode

def proxy(host, protocol="https"):
    """ Returns the value for the URL.open() proxy parameter.
        - host: host address of the proxy server.
    """
    return (host, protocol)

class URLError(Exception):
    pass # URL contains errors (e.g. a missing t in htp://).
class URLTimeout(URLError):
    pass # URL takes to long to load.
class HTTPError(URLError):
    pass # URL causes an error on the contacted server.
class HTTP301Redirect(HTTPError):
    pass # Too many redirects.
         # The site may be trying to set a cookie and waiting for you to return it,
         # or taking other measures to discern a browser from a script.
         # For specific purposes you should build your own urllib2.HTTPRedirectHandler
         # and pass it to urllib2.build_opener() in URL.open()
class HTTP400BadRequest(HTTPError):
    pass # URL contains an invalid request.
class HTTP401Authentication(HTTPError):
    pass # URL requires a login and password.
class HTTP403Forbidden(HTTPError):
    pass # URL is not accessible (user-agent?)
class HTTP404NotFound(HTTPError):
    pass # URL doesn't exist on the internet.
class HTTP420Error(HTTPError):
    pass # Used by Twitter for rate limiting.
class HTTP500InternalServerError(HTTPError):
    pass # Generic server error.
    
class URL:
    
    def __init__(self, string=u"", method=GET, query={}):
        """ URL object with the individual parts available as attributes:
            For protocol://username:password@domain:port/path/page?query_string#anchor:
            - URL.protocol: http, https, ftp, ...
            - URL.username: username for restricted domains.
            - URL.password: password for restricted domains.
            - URL.domain  : the domain name, e.g. nodebox.net.
            - URL.port    : the server port to connect to.
            - URL.path    : the server path of folders, as a list, e.g. ['news', '2010']
            - URL.page    : the page name, e.g. page.html.
            - URL.query   : the query string as a dictionary of (name, value)-items.
            - URL.anchor  : the page anchor.
            If method is POST, the query string is sent with HTTP POST.
        """
        self.__dict__["method"]    = method # Use __dict__ directly since __setattr__ is overridden.
        self.__dict__["_string"]   = u(string)
        self.__dict__["_parts"]    = None
        self.__dict__["_headers"]  = None
        self.__dict__["_redirect"] = None
        if isinstance(string, URL):
            self.__dict__["method"] = string.method
            self.query.update(string.query)
        if len(query) > 0:
            # Requires that we parse the string first (see URL.__setattr__).
            self.query.update(query)
        
    def _parse(self):
        """ Parses all the parts of the URL string to a dictionary.
            URL format: protocal://username:password@domain:port/path/page?querystring#anchor
            For example: http://user:pass@example.com:992/animal/bird?species=seagull&q#wings
            This is a cached method that is only invoked when necessary, and only once.
        """
        p = urlparse.urlsplit(self._string)
        P = {PROTOCOL: p[0],            # http
             USERNAME: u"",             # user
             PASSWORD: u"",             # pass
               DOMAIN: p[1],            # example.com
                 PORT: u"",             # 992
                 PATH: p[2],            # [animal]
                 PAGE: u"",             # bird
                QUERY: urldecode(p[3]), # {"species": "seagull", "q": None}
               ANCHOR: p[4]             # wings
        }
        # Split the username and password from the domain.
        if "@" in P[DOMAIN]:
            P[USERNAME], \
            P[PASSWORD] = (p[1].split("@")[0].split(":")+[u""])[:2]
            P[DOMAIN]   =  p[1].split("@")[1]
        # Split the port number from the domain.
        if ":" in P[DOMAIN]:
            P[DOMAIN], \
            P[PORT] = P[DOMAIN].split(":")
            P[PORT] = int(P[PORT])
        # Split the base page from the path.
        if "/" in P[PATH]:
            P[PAGE] = p[2].split("/")[-1]
            P[PATH] = p[2][:len(p[2])-len(P[PAGE])].strip("/").split("/")
            P[PATH] = filter(lambda v: v != "", P[PATH])
        else:
            P[PAGE] = p[2].strip("/")
            P[PATH] = []
        self.__dict__["_parts"] = P
    
    # URL.string yields unicode(URL) by joining the different parts,
    # if the URL parts have been modified.
    def _get_string(self): return unicode(self)
    def _set_string(self, v):
        self.__dict__["_string"] = u(v)
        self.__dict__["_parts"]  = None
        
    string = property(_get_string, _set_string)
    
    @property
    def parts(self):
        """ Yields a dictionary with the URL parts.
        """
        if not self._parts: self._parse()
        return self._parts
    
    @property
    def querystring(self):
        """ Yields the URL querystring: "www.example.com?page=1" => "page=1"
        """
        s = dict((bytestring(k), bytestring(v or "")) for k, v in self.parts[QUERY].items())
        s = urllib.urlencode(s)
        return s
    
    def __getattr__(self, k):
        if k in self.__dict__ : return self.__dict__[k]
        if k in self.parts    : return self.__dict__["_parts"][k]
        raise AttributeError, "'URL' object has no attribute '%s'" % k
    
    def __setattr__(self, k, v):
        if k in self.__dict__ : self.__dict__[k] = u(v); return
        if k == "string"      : self._set_string(v); return
        if k == "query"       : self.parts[k] = v; return
        if k in self.parts    : self.__dict__["_parts"][k] = u(v); return
        raise AttributeError, "'URL' object has no attribute '%s'" % k
        
    def open(self, timeout=10, proxy=None, user_agent=USER_AGENT, referrer=REFERRER, authentication=None):
        """ Returns a connection to the url from which data can be retrieved with connection.read().
            When the timeout amount of seconds is exceeded, raises a URLTimeout.
            When an error occurs, raises a URLError (e.g. HTTP404NotFound).
        """
        url = self.string
        # Use basic urllib.urlopen() instead of urllib2.urlopen() for local files.
        if os.path.exists(url):
            return urllib.urlopen(url)
        # Get the query string as a separate parameter if method=POST.          
        post = self.method == POST and self.querystring or None
        socket.setdefaulttimeout(timeout)
        if proxy:
            proxy = urllib2.ProxyHandler({proxy[1]: proxy[0]})
            proxy = urllib2.build_opener(proxy, urllib2.HTTPHandler)
            urllib2.install_opener(proxy)
        try:
            request = urllib2.Request(bytestring(url), post, {
                        "User-Agent": user_agent, 
                           "Referer": referrer
                         })
            # Basic authentication is established with authentication=(username, password).
            if authentication is not None:
                request.add_header("Authorization", "Basic %s" % 
                    base64.encodestring('%s:%s' % authentication))
            return urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if e.code == 301: raise HTTP301Redirect
            if e.code == 400: raise HTTP400BadRequest
            if e.code == 401: raise HTTP401Authentication
            if e.code == 403: raise HTTP403Forbidden
            if e.code == 404: raise HTTP404NotFound
            if e.code == 420: raise HTTP420Error
            if e.code == 500: raise HTTP500InternalServerError
            raise HTTPError
        except socket.timeout:
            raise URLTimeout
        except urllib2.URLError, e:
            if e.reason == "timed out" \
            or e.reason[0] in (36, "timed out"): 
                raise URLTimeout
            raise URLError, e.reason
        except ValueError, e:
            raise URLError, e
            
    def download(self, timeout=10, cached=True, throttle=0, proxy=None, user_agent=USER_AGENT, referrer=REFERRER, authentication=None, unicode=False):
        """ Downloads the content at the given URL (by default it will be cached locally).
            Unless unicode=False, the content is returned as a unicode string.
        """
        # Filter OAuth parameters from cache id (they will be unique for each request).
        if self._parts is None and self.method == GET and "oauth_" not in self._string:
            id = self._string
        else: 
            id = repr(self.parts)
            id = re.sub("u{0,1}'oauth_.*?': u{0,1}'.*?', ", "", id)
        # Keep a separate cache of unicode and raw download for same URL.
        if unicode is True:
            id = "u" + id
        if cached and id in cache:
            if unicode is True:
                return cache[id]
            if unicode is False:
                return cache.get(id, unicode=False)
        t = time.time()
        # Open a connection with the given settings, read it and (by default) cache the data.
        data = self.open(timeout, proxy, user_agent, referrer, authentication).read()
        if unicode is True:
            data = u(data)
        if cached:
            cache[id] = data
        if throttle:
            time.sleep(max(throttle-(time.time()-t), 0))
        return data
    
    def read(self, *args):
        return self.open().read(*args)
            
    @property
    def exists(self, timeout=10):
        """ Yields False if the URL generates a HTTP404NotFound error.
        """
        try: self.open(timeout)
        except HTTP404NotFound:
            return False
        except HTTPError, URLTimeoutError:
            return True
        except URLError:
            return False
        except:
            return True
        return True
    
    @property
    def mimetype(self, timeout=10):
        """ Yields the MIME-type of the document at the URL, or None.
            MIME is more reliable than simply checking the document extension.
            You can then do: URL.mimetype in MIMETYPE_IMAGE.
        """
        try: 
            return self.headers["content-type"].split(";")[0]
        except KeyError:
            return None
            
    @property
    def headers(self, timeout=10):
        """ Yields a dictionary with the HTTP response headers.
        """
        if self.__dict__["_headers"] is None:
            try:
                h = dict(self.open(timeout).info())
            except URLError:
                h = {}
            self.__dict__["_headers"] = h
        return self.__dict__["_headers"]
            
    @property
    def redirect(self, timeout=10):
        """ Yields the redirected URL, or None.
        """
        if self.__dict__["_redirect"] is None:
            try:
                r = self.open(timeout).geturl()
            except URLError:
                r = None
            self.__dict__["_redirect"] = r != self.string and r or ""
        return self.__dict__["_redirect"] or None

    def __str__(self):
        return bytestring(self.string)
            
    def __unicode__(self):
        # The string representation includes the query attributes with HTTP GET.
        # This gives us the advantage of not having to parse the URL
        # when no separate query attributes were given (e.g. all info is in URL._string):
        if self._parts is None and self.method == GET: 
            return self._string
        P = self._parts 
        u = []
        if P[PROTOCOL]: u.append("%s://" % P[PROTOCOL])
        if P[USERNAME]: u.append("%s:%s@" % (P[USERNAME], P[PASSWORD]))
        if P[DOMAIN]  : u.append(P[DOMAIN])
        if P[PORT]    : u.append(":%s" % P[PORT])
        if P[PATH]    : u.append("/%s/" % "/".join(P[PATH]))
        if P[PAGE]    : u.append("/%s" % P[PAGE]); u[-2]=u[-2].rstrip("/")
        if self.method == GET: u.append("?%s" % self.querystring)
        if P[ANCHOR]  : u.append("#%s" % P[ANCHOR])
        return u"".join(u)

    def __repr__(self):
        return "URL('%s', method='%s')" % (str(self), str(self.method))

    def copy(self):
        return URL(self.string, self.method, self.query)

#url = URL("http://user:pass@example.com:992/animal/bird?species#wings")
#print url.parts
#print url.query
#print url.string

#--- FIND URLs -------------------------------------------------------------------------------------

RE_URL_PUNCTUATION = ("\"'{(>", "\"'.,;)}")
RE_URL_HEAD = r"[%s|\[|\s]" % "|".join(RE_URL_PUNCTUATION[0])      # Preceded by space, parenthesis or HTML tag.
RE_URL_TAIL = r"[%s|\]]*[\s|\<]" % "|".join(RE_URL_PUNCTUATION[1]) # Followed by space, punctuation or HTML tag.
RE_URL1 = r"(https?://.*?)" + RE_URL_TAIL                          # Starts with http:// or https://
RE_URL2 = RE_URL_HEAD + r"(www\..*?\..*?)" + RE_URL_TAIL           # Starts with www.
RE_URL3 = RE_URL_HEAD + r"([\w|-]*?\.(com|net|org))" + RE_URL_TAIL # Ends with .com, .net, .org

RE_URL1, RE_URL2, RE_URL3 = (
    re.compile(RE_URL1, re.I), 
    re.compile(RE_URL2, re.I), 
    re.compile(RE_URL3, re.I))

def find_urls(string, unique=True):
    """ Returns a list of URLs parsed from the string.
        Works on http://, https://, www. links or domain names ending in .com, .org, .net.
        Links can be preceded by leading punctuation (open parens)
        and followed by trailing punctuation (period, comma, close parens).
    """
    string = u(string)
    string = string.replace(u"\u2024", ".")
    string = string.replace(" ", "  ")
    matches = []
    for p in (RE_URL1, RE_URL2, RE_URL3):
        for m in p.finditer(" %s " % string):
            s = m.group(1)
            s = s.split("\">")[0].split("'>")[0] # google.com">Google => google.com
            if not unique or s not in matches:
                matches.append(s)
    return matches
    
links = find_urls

RE_EMAIL = re.compile(r"[\w\-\.\+]+@(\w[\w\-]+\.)+[\w\-]+") # tom.de+smedt@clips.ua.ac.be

def find_email(string, unique=True):
    """ Returns a list of e-mail addresses parsed from the string.
    """
    string = u(string).replace(u"\u2024", ".")
    matches = []
    for m in RE_EMAIL.finditer(string):
        s = m.group(0)
        if not unique or s not in matches:
            matches.append(s)
    return matches
    
def find_between(a, b, string):
    """ Returns a list of substrings between a and b in the given string.
    """
    p = "%s(.*?)%s" % (a, b)
    p = re.compile(p, re.DOTALL | re.I)
    return [m for m in p.findall(string)]

#### PLAIN TEXT ####################################################################################

BLOCK = [
    "title", "h1", "h2", "h3", "h4", "h5", "h6", "p", 
    "center", "blockquote", "div", "table", "ul", "ol", "pre", "code", "form"
]

SELF_CLOSING = ["br", "hr", "img"]

# Element tag replacements for a stripped version of HTML source with strip_tags().
# Block-level elements are followed by linebreaks,
# list items are preceded by an asterisk ("*").
LIST_ITEM = "*"
blocks = dict.fromkeys(BLOCK+["br", "tr", "td"], ("", "\n\n"))
blocks.update({
    "li": ("%s " % LIST_ITEM, "\n"),
   "img": ("", ""),
    "br": ("", "\n"),
    "th": ("", "\n"),
    "tr": ("", "\n"),
    "td": ("", "\t"),
})

class HTMLParser(sgmllib.SGMLParser):
    
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
    
    def handle_starttag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        pass
    
    def unknown_starttag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
    
    def unknown_endtag(self, tag):
        self.handle_endtag(tag)
    
    def clean(self, html):
        html = decode_utf8(html)
        html = html.replace("/>", " />")
        html = html.replace("  />", " />")
        html = html.replace("<!", "&lt;!")
        html = html.replace("&lt;!DOCTYPE", "<!DOCTYPE")
        html = html.replace("&lt;!doctype", "<!doctype")
        html = html.replace("&lt;!--", "<!--")
        return html

        
    def parse_declaration(self, i):
        # We can live without sgmllib's parse_declaration().
        try: 
            return sgmllib.SGMLParser.parse_declaration(self, i)
        except sgmllib.SGMLParseError:
            return i + 1
        
    def convert_charref(self, name):
        # This fixes a bug in older versions of sgmllib when working with Unicode.
        # Fix: ASCII ends at 127, not 255
        try:
            n = int(name)
        except ValueError:
            return
        if not 0 <= n <= 127:
            return
        return chr(n)

class HTMLTagstripper(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)

    def strip(self, html, exclude=[], replace=blocks):
        """ Returns the HTML string with all element tags (e.g. <p>) removed.
            - exclude    : a list of tags to keep. Element attributes are stripped.
                           To preserve attributes a dict of (tag name, [attribute])-items can be given.
            - replace    : a dictionary of (tag name, (replace_before, replace_after))-items.
                           By default, block-level elements are separated with linebreaks.
        """
        if html is None:
            return None
        self._exclude = isinstance(exclude, dict) and exclude or dict.fromkeys(exclude, [])
        self._replace = replace
        self._data    = []
        self.feed(self.clean(html))
        self.close()
        self.reset()
        return "".join(self._data)
    
    def handle_starttag(self, tag, attributes):
        if tag in self._exclude:
            # Create the tag attribute string, 
            # including attributes defined in the HTMLTagStripper._exclude dict.
            a = len(self._exclude[tag]) > 0 and attributes or []
            a = ["%s=\"%s\"" % (k,v) for k, v in a if k in self._exclude[tag]]
            a = (" "+" ".join(a)).rstrip()
            self._data.append("<%s%s>" % (tag, a))
        if tag in self._replace: 
            self._data.append(self._replace[tag][0])
        if tag in self._replace and tag in SELF_CLOSING:
            self._data.append(self._replace[tag][1])
            
    def handle_endtag(self, tag):
        if tag in self._exclude and self._data and self._data[-1].startswith("<"+tag):
            # Never keep empty elements (e.g. <a></a>).
            self._data.pop(-1); return
        if tag in self._exclude:
            self._data.append("</%s>" % tag)
        if tag in self._replace: 
            self._data.append(self._replace[tag][1])

    def handle_data(self, data):
	    self._data.append(data.strip("\n\t"))
    def handle_entityref(self, ref):
        self._data.append("&%s;" % ref)
    def handle_charref(self, ref):
        self._data.append("&%s;" % ref)
        
    def handle_comment(self, comment):
        if "comment" in self._exclude or \
               "!--" in self._exclude:
            self._data.append("<!--%s-->" % comment)

# As a function:
strip_tags = HTMLTagstripper().strip

def strip_element(string, tag, attributes=""):
    """ Removes all elements with the given tagname and attributes from the string.
        Open and close tags are kept in balance.
        No HTML parser is used: strip_element(s, "a", "href='foo' class='bar'")
        matches "<a href='foo' class='bar'" but not "<a class='bar' href='foo'".
    """
    s = string.lower() # Case-insensitive.
    t = tag.strip("</>")
    a = (" " + attributes.lower().strip()).rstrip()
    i = 0
    j = 0
    while j >= 0:
        i = s.find("<%s%s" % (t, a), i)
        j = s.find("</%s>" % t, i+1)
        opened, closed = s[i:j].count("<%s" % t), 1
        while opened > closed and j >= 0:
            k = s.find("</%s>" % t, j+1)
            opened += s[j:k].count("<%s" % t)
            closed += 1
            j = k
        if i < 0: return string
        if j < 0: return string[:i]
        string = string[:i] + string[j+len(t)+3:]; s=string.lower()
    return string

def strip_between(a, b, string):
    """ Removes anything between (and including) string a and b inside the given string.
    """
    p = "%s.*?%s" % (a, b)
    p = re.compile(p, re.DOTALL | re.I)
    return re.sub(p, "", string)
    
def strip_javascript(html): 
    return strip_between("<script.*?>", "</script>", html)
def strip_inline_css(html): 
    return strip_between("<style.*?>", "</style>", html)
def strip_comments(html): 
    return strip_between("<!--", "-->", html)
def strip_forms(html): 
    return strip_between("<form.*?>", "</form>", html)

RE_AMPERSAND = re.compile("\&(?!\#)")           # & not followed by #
RE_UNICODE   = re.compile(r'&(#?)(x|X?)(\w+);') # &#201;

def encode_entities(string):
    """ Encodes HTML entities in the given string ("<" => "&lt;").
        For example, to display "<em>hello</em>" in a browser,
        we need to pass "&lt;em&gt;hello&lt;/em&gt;" (otherwise "hello" in italic is displayed).
    """
    if isinstance(string, (str, unicode)):
        string = RE_AMPERSAND.sub("&amp;", string)
        string = string.replace("<", "&lt;")
        string = string.replace(">", "&gt;")
        string = string.replace('"', "&quot;")
        string = string.replace("'", "&#39;")
    return string

def decode_entities(string):
    """ Decodes HTML entities in the given string ("&lt;" => "<").
    """
    # http://snippets.dzone.com/posts/show/4569
    def replace_entity(match):
        hash, hex, name = match.group(1), match.group(2), match.group(3)
        if hash == "#" or name.isdigit():
            if hex == '' : 
                return unichr(int(name))                 # "&#38;" => "&"
            if hex in ("x","X"):
                return unichr(int('0x'+name, 16))        # "&#x0026;" = > "&"
        else:
            cp = htmlentitydefs.name2codepoint.get(name) # "&amp;" => "&"
            return cp and unichr(cp) or match.group()    # "&foo;" => "&foo;"
    if isinstance(string, (str, unicode)):
        return RE_UNICODE.subn(replace_entity, string)[0]
    return string

def decode_url(string):
    return urllib.quote_plus(string)
def encode_url(string):
    return urllib.unquote_plus(string) # "black/white" => "black%2Fwhite".

RE_SPACES = re.compile("( |\xa0)+", re.M) # Matches one or more spaces.
RE_TABS   = re.compile(r"\t+", re.M)      # Matches one or more tabs.

def collapse_spaces(string, indentation=False, replace=" "):
    """ Returns a string with consecutive spaces collapsed to a single space.
        Whitespace on empty lines and at the end of each line is removed.
        With indentation=True, retains leading whitespace on each line.
    """
    p = []
    for x in string.splitlines():
        n = indentation and len(x) - len(x.lstrip()) or 0
        p.append(x[:n] + RE_SPACES.sub(replace, x[n:]).strip())
    return "\n".join(p)

def collapse_tabs(string, indentation=False, replace=" "):
    """ Returns a string with (consecutive) tabs replaced by a single space.
        Whitespace on empty lines and at the end of each line is removed.
        With indentation=True, retains leading whitespace on each line.
    """
    p = []
    for x in string.splitlines():
        n = indentation and len(x) - len(x.lstrip()) or 0
        p.append(x[:n] + RE_TABS.sub(replace, x[n:]).strip())
    return "\n".join(p)

def collapse_linebreaks(string, threshold=1):
    """ Returns a string with consecutive linebreaks collapsed to at most the given threshold.
        Whitespace on empty lines and at the end of each line is removed.
    """
    n = "\n" * threshold
    p = [s.rstrip() for s in string.splitlines()]
    string = "\n".join(p)
    string = re.sub(n+r"+", n, string)
    return string

def plaintext(html, keep=[], replace=blocks, linebreaks=2, indentation=False):
    """ Returns a string with all HTML tags removed.
        Content inside HTML comments, the <style> tag and the <script> tags is removed.
        - keep        : a list of tags to keep. Element attributes are stripped.
                        To preserve attributes a dict of (tag name, [attribute])-items can be given.
        - replace     : a dictionary of (tag name, (replace_before, replace_after))-items.
                        By default, block-level elements are followed by linebreaks.
        - linebreaks  : the maximum amount of consecutive linebreaks,
        - indentation : keep left line indentation (tabs and spaces)?
    """
    if not keep.__contains__("script"):
        html = strip_javascript(html)
    if not keep.__contains__("style"):
        html = strip_inline_css(html)
    if not keep.__contains__("form"):
        html = strip_forms(html)
    if not keep.__contains__("comment") and \
       not keep.__contains__("!--"):
        html = strip_comments(html)
    html = html.replace("\r", "\n")
    html = strip_tags(html, exclude=keep, replace=replace)
    html = decode_entities(html)
    html = collapse_spaces(html, indentation)
    html = collapse_tabs(html, indentation)
    html = collapse_linebreaks(html, linebreaks)
    html = html.strip()
    return html

#### SEARCH ENGINE #################################################################################

SEARCH    = "search"    # Query for pages (i.e. links to websites).
IMAGE     = "image"     # Query for images.
NEWS      = "news"      # Query for news items.

TINY      = "tiny"      # Image size around 100x100.
SMALL     = "small"     # Image size around 200x200.
MEDIUM    = "medium"    # Image size around 500x500.
LARGE     = "large"     # Image size around 1000x1000.

RELEVANCY = "relevancy" # Sort results by most relevant.
LATEST    = "latest"    # Sort results by most recent.

class Result(dict):
    
    def __init__(self, url):
        """ An item in a list of results returned by SearchEngine.search().
            All dictionary entries are available as unicode string attributes.
            - url        : the URL of the referred web content,
            - title      : the title of the content at the URL,
            - description: the content description,
            - language   : the content language,
            - author     : for news items and images, the author,
            - date       : for news items, the publication date.
        """
        dict.__init__(self)
        self.url   = url

    def download(self, *args, **kwargs):
        """ Download the content at the given URL. 
            By default it will be cached - see URL.download().
        """
        return URL(self.url).download(*args, **kwargs)

    def __getattr__(self, k):
        return self.get(k, u"")
    def __getitem__(self, k):
        return self.get(k, u"")
    def __setattr__(self, k, v):
        dict.__setitem__(self, u(k), v is not None and u(v) or u"") # Store strings as unicode.
    def __setitem__(self, k, v):
        dict.__setitem__(self, u(k), v is not None and u(v) or u"")
        
    def setdefault(self, k, v):
        dict.setdefault(self, u(k), u(v))
    def update(self, *args, **kwargs):
        map = dict()
        map.update(*args, **kwargs)
        dict.update(self, [(u(k), u(v)) for k, v in map.items()])

    def __repr__(self):
        return "Result(url=%s)" % repr(self.url)

class Results(list):
    
    def __init__(self, source=None, query=None, type=SEARCH, total=0):
        """ A list of results returned from SearchEngine.search().
            - source: the service that yields the results (e.g. GOOGLE, TWITTER).
            - query : the query that yields the results.
            - type  : the query type (SEARCH, IMAGE, NEWS).
            - total : the total result count.
                      This is not the length of the list, but the total number of matches for the given query.
        """
        self.source = source
        self.query  = query
        self.type   = type
        self.total  = total

class SearchEngine:
    
    def __init__(self, license=None, throttle=1.0, language=None):
        """ A base class for a web service.
            - license  : license key for the API,
            - throttle : delay between requests (avoid hammering the server).
            Inherited by: Google, Yahoo, Bing, Twitter, Wikipedia, Flickr.
        """
        self.license  = license
        self.throttle = throttle    # Amount of sleep time after executing a query.
        self.language = language    # Result.language restriction (e.g., "en").
        self.format   = lambda x: x # Formatter applied to each attribute of each Result.
    
    def search(self, query, type=SEARCH, start=1, count=10, sort=RELEVANCY, size=None, cached=True, **kwargs):
        return Results(source=None, query=query, type=type)

class SearchEngineError(HTTPError):
    pass
class SearchEngineTypeError(SearchEngineError):
    pass # Raised when an unknown type is passed to SearchEngine.search().
class SearchEngineLimitError(SearchEngineError):
    pass # Raised when the query limit for a license is reached.

#--- GOOGLE ----------------------------------------------------------------------------------------
# Google Custom Search is a paid service.
# https://code.google.com/apis/console/
# http://code.google.com/apis/customsearch/v1/overview.html

GOOGLE = "https://www.googleapis.com/customsearch/v1?"
GOOGLE_LICENSE = api.license["Google"]
GOOGLE_CUSTOM_SEARCH_ENGINE = "000579440470800426354:_4qo2s0ijsi"

# Search result descriptions can start with: "Jul 29, 2007 ...",
# which is the date of the page parsed by Google from the content.
RE_GOOGLE_DATE = re.compile("^([A-Z][a-z]{2} [0-9]{1,2}, [0-9]{4}) {0,1}...")

class Google(SearchEngine):
    
    def __init__(self, license=None, throttle=0.5, language=None):
        SearchEngine.__init__(self, license or GOOGLE_LICENSE, throttle, language)
    
    def search(self, query, type=SEARCH, start=1, count=10, sort=RELEVANCY, size=None, cached=True, **kwargs):
        """ Returns a list of results from Google for the given query.
            - type : SEARCH,
            - start: maximum 100 results => start 1-10 with count=10,
            - count: maximum 10,
            There is a daily limit of 10,000 queries. Google Custom Search is a paid service.
        """
        if type != SEARCH:
            raise SearchEngineTypeError
        if not query or count < 1 or start < 1 or start > (100 / count): 
            return Results(GOOGLE, query, type)
        # 1) Create request URL.
        url = URL(GOOGLE, query={
              "key": self.license or GOOGLE_LICENSE,
               "cx": GOOGLE_CUSTOM_SEARCH_ENGINE,
                "q": query,
            "start": 1 + (start-1) * count,
              "num": min(count, 10),
              "alt": "json"
        })
        # 2) Restrict language.
        if self.language is not None:
            url.query["lr"] = "lang_" + self.language
        # 3) Parse JSON response.
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        data = url.download(cached=cached, **kwargs)
        data = json.loads(data)
        if data.get("error", {}).get("code") == 403:
            raise SearchEngineLimitError
        results = Results(GOOGLE, query, type)
        results.total = int(data.get("queries", {}).get("request", [{}])[0].get("totalResults") or 0)
        for x in data.get("items", []):
            r = Result(url=None)
            r.url         = self.format(x.get("link"))
            r.title       = self.format(x.get("title"))
            r.description = self.format(x.get("htmlSnippet").replace("<br>  ","").replace("<b>...</b>", "..."))
            r.language    = self.language or ""
            r.date        = ""
            if not r.date:
                # Google Search descriptions can start with a date (parsed from the content):
                m = RE_GOOGLE_DATE.match(r.description)
                if m: 
                    r.date = m.group(1)
                    r.description = "..." + r.description[len(m.group(0)):]
            results.append(r)
        return results
        
    def translate(self, string, input="en", output="fr", **kwargs):
        """ Returns the translation of the given string in the desired output language.
            Google Translate is a paid service, license without billing raises HTTP401Authentication.
        """
        url = URL("https://www.googleapis.com/language/translate/v2?", method=GET, query={
               "key": GOOGLE_LICENSE,
                 "q": string,
            "source": input,
            "target": output
        })
        kwargs.setdefault("cached", False)
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        try:
            data = url.download(**kwargs)
        except HTTP403Forbidden:
            raise HTTP401Authentication, "Google translate API is a paid service"
        data = json.loads(data)
        data = data.get("data", {}).get("translations", [{}])[0].get("translatedText", "")
        data = decode_entities(data)
        return u(data)
        
    def identify(self, string, **kwargs):
        """ Returns a (language, confidence)-tuple for the given string.
            Google Translate is a paid service, license without billing raises HTTP401Authentication.
        """
        url = URL("https://www.googleapis.com/language/translate/v2/detect?", method=GET, query={
               "key": GOOGLE_LICENSE,
                 "q": string[:1000]
        })
        kwargs.setdefault("cached", False)
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        try:
            data = url.download(**kwargs)
        except HTTP403Forbidden:
            raise HTTP401Authentication, "Google translate API is a paid service"
        data = json.loads(data)
        data = data.get("data", {}).get("detections", [[{}]])[0][0]
        data = u(data.get("language")), float(data.get("confidence"))
        return data

#--- YAHOO -----------------------------------------------------------------------------------------
# Yahoo BOSS is a paid service.
# http://developer.yahoo.com/search/

YAHOO = "http://yboss.yahooapis.com/ysearch/"
YAHOO_LICENSE = api.license["Yahoo"] 

class Yahoo(SearchEngine):

    def __init__(self, license=None, throttle=0.5, language=None):
        SearchEngine.__init__(self, license or YAHOO_LICENSE, throttle, language)

    def search(self, query, type=SEARCH, start=1, count=10, sort=RELEVANCY, size=None, cached=True, **kwargs):
        """ Returns a list of results from Yahoo for the given query.
            - type : SEARCH, IMAGE or NEWS,
            - start: maximum 1000 results => start 1-100 with count=10, 1000/count,
            - count: maximum 50, or 35 for images.
            There is no daily limit, however Yahoo BOSS is a paid service.
        """
        if type not in (SEARCH, IMAGE, NEWS):
            raise SearchEngineTypeError
        if type == SEARCH: 
            url = YAHOO + "web"
        if type == IMAGE: 
            url = YAHOO + "images"
        if type == NEWS: 
            url = YAHOO + "news"
        if not query or count < 1 or start < 1 or start > 1000/count: 
            return Results(YAHOO, query, type)
        # 1) Create request URL.
        url = URL(url, method=GET, query={
                 "q": oauth.normalize(query.replace(" ", "_")),
             "start": 1 + (start-1) * count,
             "count": min(count, type==IMAGE and 35 or 50),
            "format": "json"
        })
        # 2) Restrict language.
        if self.language is not None:
            market = locale.market(self.language)
            if market:
                url.query["market"] = market.lower()
        # 3) BOSS OAuth authentication.
        url.query.update({ 
            "oauth_version": "1.0",
            "oauth_nonce": oauth.nonce(),
            "oauth_timestamp": oauth.timestamp(),
            "oauth_consumer_key": self.license[0],
            "oauth_signature_method": "HMAC-SHA1"         
        })
        url.query["oauth_signature"] = oauth.sign(url.string.split("?")[0], url.query, method=GET, secret=self.license[1])
        # 3) Parse JSON response.
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        try: 
            data = url.download(cached=cached, **kwargs)
        except HTTP401Authentication:
            raise HTTP401Authentication, "Yahoo %s API is a paid service" % type
        except HTTP403Forbidden:
            raise SearchEngineLimitError
        data = json.loads(data)
        data = data.get("bossresponse") or {}
        data = data.get({SEARCH:"web", IMAGE:"images", NEWS:"news"}[type], {})
        results = Results(YAHOO, query, type)
        results.total = int(data.get("totalresults") or 0)
        for x in data.get("results", []):
            r = Result(url=None)
            r.url         = self.format(x.get("url", x.get("clickurl")))
            r.title       = self.format(x.get("title"))
            r.description = self.format(x.get("abstract"))
            r.date        = self.format(x.get("date"))
            r.author      = self.format(x.get("source"))
            r.language    = self.format(x.get("language") and \
                                        x.get("language").split(" ")[0] or self.language or "")
            results.append(r)
        return results

#--- BING ------------------------------------------------------------------------------------------
# https://datamarket.azure.com/dataset/5BA839F1-12CE-4CCE-BF57-A49D98D29A44
# https://datamarket.azure.com/account/info

BING = "https://api.datamarket.azure.com/Bing/Search/"
BING_LICENSE = api.license["Bing"] 

class Bing(SearchEngine):

    def __init__(self, license=None, throttle=0.5, language=None):
        SearchEngine.__init__(self, license or BING_LICENSE, throttle, language)

    def search(self, query, type=SEARCH, start=1, count=10, sort=RELEVANCY, size=None, cached=True, **kwargs):
        """" Returns a list of results from Bing for the given query.
            - type : SEARCH, IMAGE or NEWS,
            - start: maximum 1000 results => start 1-100 with count=10, 1000/count,
            - count: maximum 50, or 15 for news,
            - size : for images, either SMALL, MEDIUM or LARGE.
            There is no daily query limit.
        """
        if type not in (SEARCH, IMAGE, NEWS):
            raise SearchEngineTypeError
        if type == SEARCH: 
            src = "Web"
        if type == IMAGE: 
            src = "Image"
        if type == NEWS:
            src = "News"
        if not query or count < 1 or start < 1 or start > 1000/count: 
            return Results(BING + src + "?", query, type)
        # 1) Construct request URL.
        url = URL(BING + "Composite", method=GET, query={
               "Sources": "'" + src.lower() + "'",
                 "Query": "'" + query + "'",
                 "$skip": 1 + (start-1) * count,
                  "$top": min(count, type==NEWS and 15 or 50),
               "$format": "json",
        })
        # 2) Restrict image size.
        if size in (TINY, SMALL, MEDIUM, LARGE):
            url.query["ImageFilters"] = {
                    TINY: "'Size:Small'", 
                   SMALL: "'Size:Small'", 
                  MEDIUM: "'Size:Medium'", 
                   LARGE: "'Size:Large'" }[size]
        # 3) Restrict language.
        if type in (SEARCH, IMAGE) and self.language is not None:
            url.query["Query"] = url.query["Query"][:-1] + " language: %s'" % self.language
        #if self.language is not None:
        #    market = locale.market(self.language)
        #    if market:
        #        url.query["market"] = market
        # 4) Parse JSON response.
        kwargs["authentication"] = ("", self.license)
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        try: 
            data = url.download(cached=cached, **kwargs)
        except HTTP401Authentication:
            raise HTTP401Authentication, "Bing %s API is a paid service" % type
        data = json.loads(data)
        data = data.get("d", {})
        data = data.get("results", [{}])[0]
        results = Results(BING, query, type)
        results.total = int(data.get(src+"Total", 0))
        for x in data.get(src, []):
            r = Result(url=None)
            r.url         = self.format(x.get("MediaUrl", x.get("Url")))
            r.title       = self.format(x.get("Title"))
            r.description = self.format(x.get("Description", x.get("Snippet")))
            r.language    = self.language or ""
            r.date        = self.format(x.get("DateTime", x.get("Date")))
            r.author      = self.format(x.get("Source"))
            results.append(r)
        return results

#--- TWITTER ---------------------------------------------------------------------------------------
# http://apiwiki.twitter.com/

TWITTER = "http://search.twitter.com/"
TWITTER_LICENSE = api.license["Twitter"] 

# Hashtag = word starting with #, for example: #OccupyWallstreet
# Retweet = word starting with @ preceded by RT: RT @nathan
TWITTER_SOURCE  = re.compile(r"href=&quot;(.*?)&quot;")
TWITTER_HASHTAG = re.compile(r"(\s|^)(#[a-z0-9_\-]+)", re.I)
TWITTER_RETWEET = re.compile(r"(\s|^RT )(@[a-z0-9_\-]+)", re.I)

class Twitter(SearchEngine):
    
    def __init__(self, license=None, throttle=0.5, language=None):
        SearchEngine.__init__(self, license or TWITTER_LICENSE, throttle, language)

    def search(self, query, type=SEARCH, start=1, count=10, sort=RELEVANCY, size=None, cached=False, **kwargs):
        """ Returns a list of results from Twitter for the given query.
            - type : SEARCH or TRENDS,
            - start: maximum 1500 results (10 for trends) => start 1-15 with count=100, 1500/count,
            - count: maximum 100, or 10 for trends.
            There is an hourly limit of 150+ queries (actual amount undisclosed).
        """
        if type != SEARCH:
            raise SearchEngineTypeError
        if not query or count < 1 or start < 1 or start > 1500/count: 
            return Results(TWITTER, query, type)
        # 1) Construct request URL.
        url = URL(TWITTER + "search.json?", method=GET)
        url.query = {
               "q": query,
            "page": start,
             "rpp": min(count, 100) 
        }
        if "geo" in kwargs:
            # Filter by location with geo=(latitude, longitude, radius).
            # It can also be a (latitude, longitude)-tuple with default radius "10km".
            url.query["geocode"] = ",".join((map(str, kwargs.pop("geo")) + ["10km"])[:3])
        # 2) Restrict language.
        url.query["lang"] = self.language or ""
        # 3) Parse JSON response.
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        try: 
            data = URL(url).download(cached=cached, **kwargs)
        except HTTP420Error:
            raise SearchEngineLimitError
        data = json.loads(data)
        results = Results(TWITTER, query, type)
        results.total = None
        for x in data.get("results", data.get("trends", [])):
            r = Result(url=None)
            r.url         = self.format("https://twitter.com/%s/status/%s" % (x.get("from_user"), x.get("id_str")))
            r.description = self.format(x.get("text"))
            r.date        = self.format(x.get("created_at", data.get("as_of")))
            r.author      = self.format(x.get("from_user"))
            r.profile     = self.format(x.get("profile_image_url")) # Profile picture URL.
            r.language    = self.format(x.get("iso_language_code"))
            results.append(r)
        return results
        
    def trends(self, **kwargs):
        """ Returns a list with 10 trending topics on Twitter.
        """
        url = URL("https://api.twitter.com/1/trends/1.json")
        kwargs.setdefault("cached", False)
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        data = url.download(**kwargs)
        data = json.loads(data)
        return [u(x.get("name")) for x in data[0].get("trends", [])]

def author(name):
    """ Returns a Twitter query-by-author-name that can be passed to Twitter.search().
        For example: Twitter().search(author("tom_de_smedt"))
    """
    return "from:%s" % name

def hashtags(string):
    """ Returns a list of hashtags (words starting with a #hash) from a tweet.
    """
    return [b for a, b in TWITTER_HASHTAG.findall(string)]
    
def retweets(string):
    """ Returns a list of retweets (words starting with a RT @author) from a tweet.
    """
    return [b for a, b in TWITTER_RETWEET.findall(string)]

#--- WIKIPEDIA -------------------------------------------------------------------------------------
# http://en.wikipedia.org/w/api.php

WIKIPEDIA = "http://en.wikipedia.org/w/api.php"
WIKIPEDIA_LICENSE = api.license["Wikipedia"] 

# Pattern for meta links (e.g. Special:RecentChanges).
# http://en.wikipedia.org/wiki/Main_namespace
WIKIPEDIA_NAMESPACE  = ["Main", "User", "Wikipedia", "File", "MediaWiki", "Template", "Help", "Category", "Portal", "Book"]
WIKIPEDIA_NAMESPACE += [s+" talk" for s in WIKIPEDIA_NAMESPACE] + ["Talk", "Special", "Media"]
WIKIPEDIA_NAMESPACE += ["WP", "WT", "MOS", "C", "CAT", "Cat", "P", "T", "H", "MP", "MoS", "Mos"]
_wikipedia_namespace = re.compile(r"^"+"|".join(WIKIPEDIA_NAMESPACE)+":", re.I)

# Pattern to identify disambiguation pages.
WIKIPEDIA_DISAMBIGUATION = "<a href=\"/wiki/Help:Disambiguation\" title=\"Help:Disambiguation\">disambiguation</a> page"

# Pattern to identify references, e.g. [12]
WIKIPEDIA_REFERENCE = r"\s*\[[0-9]{1,3}\]"

class Wikipedia(SearchEngine):
    
    def __init__(self, license=None, throttle=5.0, language="en"):
        SearchEngine.__init__(self, license or WIKIPEDIA_LICENSE, throttle, language)

    def search(self, query, type=SEARCH, start=1, count=1, sort=RELEVANCY, size=None, cached=True, **kwargs):
        """ Returns a WikipediaArticle for the given query.
            The query is case-sensitive: 
            - "tiger" = Panthera tigris,
            - "TIGER" = Topologically Integrated Geographic Encoding and Referencing.
        """
        if type != SEARCH:
            raise SearchEngineTypeError
        if count < 1:
            return None
        # 1) Construct request URL for the Wikipedia in the given language.
        url = WIKIPEDIA.replace("en.", "%s." % self.language) + "?"
        url = URL(url, method=GET, query={
            "action": "parse",
              "page": query.replace(" ","_"),
         "redirects": 1,
            "format": "json"
        })
        # 2) Parse JSON response.
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("timeout", 30) # Parsing the article takes some time.
        kwargs.setdefault("throttle", self.throttle)
        data = url.download(cached=cached, **kwargs)
        data = json.loads(data)
        data = data.get("parse", {})
        a = self._parse_article(data, query=query)
        a = self._parse_article_sections(a, data)
        a = self._parse_article_section_structure(a)
        if not a.html or "id=\"noarticletext\"" in a.html:
            return None
        return a
    
    def _parse_article(self, data, **kwargs):
        return WikipediaArticle(
                  title = plaintext(data.get("displaytitle", "")),
                 source = data.get("text", {}).get("*", ""),
         disambiguation = data.get("text", {}).get("*", "").find(WIKIPEDIA_DISAMBIGUATION) >= 0,
                  links = [x["*"] for x in data.get("links", []) if not _wikipedia_namespace.match(x["*"])],
             categories = [x["*"] for x in data.get("categories", [])],
               external = [x for x in data.get("externallinks", [])],
                  media = [x for x in data.get("images", [])],
              languages = dict([(x["lang"], x["*"]) for x in data.get("langlinks", [])]),
              language  = self.language, **kwargs)
    
    def _parse_article_sections(self, article, data):
        # If "References" is a section in the article,
        # the HTML will contain a marker <h*><span class="mw-headline" id="References">.
        # http://en.wikipedia.org/wiki/Section_editing
        t = article.title
        d = 0
        i = 0
        for x in data.get("sections", {}):
            a = x.get("anchor")
            if a:
                p = r"<h.>\s*.*?\s*<span class=\"mw-headline\" id=\"%s\">" % a
                p = re.compile(p)
                m = p.search(article.source, i)
                if m:
                    j = m.start()
                    article.sections.append(WikipediaSection(article, 
                        title = t,
                        start = i, 
                         stop = j,
                        level = d))
                    t = x.get("line", "")
                    d = int(x.get("level", 2)) - 1
                    i = j
        return article
    
    def _parse_article_section_structure(self, article):
        # Sections with higher level are children of previous sections with lower level.
        for i, s2 in enumerate(article.sections):
            for s1 in reversed(article.sections[:i]):
                if s1.level < s2.level:
                    s2.parent = s1
                    s1.children.append(s2)
                    break
        return article

class WikipediaArticle:
    
    def __init__(self, title=u"", source=u"", links=[], categories=[], languages={}, disambiguation=False, **kwargs):
        """ An article on Wikipedia returned from Wikipedia.search().
            WikipediaArticle.string contains the HTML content.
        """
        self.title          = title          # Article title.
        self.source         = source         # Article HTML content.
        self.sections       = []             # Article sections.
        self.links          = links          # List of titles of linked articles.
        self.categories     = categories     # List of categories. As links, prepend "Category:".
        self.external       = []             # List of external links.
        self.media          = []             # List of linked media (images, sounds, ...)
        self.languages      = languages      # Dictionary of (language, article)-items, e.g. Cat => ("nl", "Kat")
        self.language       = kwargs.get("language", "en")
        self.disambiguation = disambiguation # True when the article is a disambiguation page.
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def download(self, media, **kwargs):
        """ Downloads an item from WikipediaArticle.media and returns the content.
            Note: images on Wikipedia can be quite large, and this method uses screen-scraping,
                  so Wikipedia might not like it that you download media in this way.
            To save the media in a file: 
            data = article.download(media)
            open(filename+extension(media),"w").write(data)
        """
        url = "http://%s.wikipedia.org/wiki/File:%s" % (self.__dict__.get("language", "en"), media)
        if url not in cache:
            time.sleep(1)
        data = URL(url).download(**kwargs)
        data = re.search(r"http://upload.wikimedia.org/.*?/%s" % media, data)
        data = data and URL(data.group(0)).download(**kwargs) or None
        return data
    
    def _plaintext(self, string, **kwargs):
        """ Strips HTML tags, whitespace and Wikipedia markup from the HTML source, including:
            metadata, info box, table of contents, annotations, thumbnails, disambiguation link.
            This is called internally from WikipediaArticle.string.
        """
        s = string
        s = strip_between("<table class=\"metadata", "</table>", s)   # Metadata.
        s = strip_between("<table id=\"toc", "</table>", s)           # Table of contents.
        s = strip_between("<table class=\"infobox", "</table>", s)    # Infobox.
        s = strip_between("<table class=\"wikitable", "</table>", s)  # Table.
        s = strip_element(s, "table", "class=\"navbox")               # Navbox.
        s = strip_between("<div id=\"annotation", "</div>", s)        # Annotations.
        s = strip_between("<div class=\"dablink", "</div>", s)        # Disambiguation message.
        s = strip_between("<div class=\"magnify", "</div>", s)        # Thumbnails.
        s = strip_between("<div class=\"thumbcaption", "</div>", s)   # Thumbnail captions.
        s = re.sub(r"<img class=\"tex\".*?/>", "[math]", s)           # LaTex math images.
        s = plaintext(s, **kwargs)
        s = re.sub(r"\[edit\]\s*", "", s) # [edit] is language dependent (e.g. nl => "[bewerken]")
        s = s.replace("[", " [").replace("  [", " [") # Space before inline references.
        #s = re.sub(WIKIPEDIA_REFERENCE, " ", s)      # Remove inline references.
        return s
        
    def plaintext(self, **kwargs):
        return self._plaintext(self.source, **kwargs)
    
    @property
    def html(self):
        return self.source
        
    @property
    def string(self):
        return self.plaintext()
        
    def __repr__(self):
        return "WikipediaArticle(title=%s)" % repr(self.title)

class WikipediaSection:
    
    def __init__(self, article, title=u"", start=0, stop=0, level=1):
        """ A (nested) section in the content of a WikipediaArticle.
        """
        self.article  = article # WikipediaArticle the section is part of.
        self.parent   = None    # WikipediaSection the section is part of.
        self.children = []      # WikipediaSections belonging to this section.
        self.title    = title   # Section title.
        self._start   = start   # Section start index in WikipediaArticle.string.
        self._stop    = stop    # Section stop index in WikipediaArticle.string.
        self._level   = level   # Section depth (main title + intro = level 0).
        self._tables  = None

    def plaintext(self, **kwargs):
        return self.article._plaintext(self.source, **kwargs)

    @property
    def source(self):
        return self.article.source[self._start:self._stop]
        
    @property
    def html(self):
        return self.source
        
    @property
    def string(self):
        return self.plaintext()
        
    @property
    def content(self):
        # ArticleSection.string, minus the title.
        s = self.plaintext()
        if s == self.title or s.startswith(self.title+"\n"):
            return s[len(self.title):].lstrip()
        return s
    
    @property
    def tables(self):
        """ Yields a list of WikipediaTable objects in the section.
        """
        if self._tables is None:
            self._tables = []
            b = "<table class=\"wikitable\"", "</table>"
            p = self.article._plaintext
            f = find_between
            for s in f(b[0], b[1], self.source):
                t = WikipediaTable(self,
                     title = p((f(r"<caption.*?>", "</caption>", s) + [""])[0]),
                    source = b[0] + s + b[1]
                )
                for i, row in enumerate(f(r"<tr", "</tr>", s)):
                    # 1) Parse <td> and <th> content and format it as plain text.
                    # 2) Parse <td colspan=""> attribute, duplicate spanning cells.
                    # 3) For <th> in the first row, update WikipediaTable.headers.
                    r1 = f(r"<t[d|h]", r"</t[d|h]>", row)
                    r1 = (((f(r'colspan="', r'"', v)+[1])[0], v[v.find(">")+1:]) for v in r1)
                    r1 = ((int(n), v) for n, v in r1)
                    r2 = []; [[r2.append(p(v)) for j in range(n)] for n, v in r1]
                    if i == 0 and "</th>" in row:
                        t.headers = r2
                    else:
                        t.rows.append(r2)
                self._tables.append(t)
        return self._tables

    @property
    def level(self):
        return self._level
        
    depth = level

    def __repr__(self):
        return "WikipediaSection(title='%s')" % bytestring(self.title)

class WikipediaTable:
    
    def __init__(self, section, title=u"", headers=[], rows=[], source=u""):
        """ A <table class="wikitable> in a WikipediaSection.
        """
        self.section = section # WikipediaSection the table is part of.
        self.source  = source  # Table HTML.
        self.title   = title   # Table title.
        self.headers = headers # List of table headers.
        self.rows    = rows    # List of table rows, each a list of cells.
        
    @property
    def html(self):
        return self.source
        
    def __repr__(self):
        return "WikipediaTable(title='%s')" % bytestring(self.title)

#article = Wikipedia().search("nodebox")
#for section in article.sections:
#    print "  "*(section.level-1) + section.title
#if article.media:
#    data = article.download(article.media[0])
#    f = open(article.media[0], "w")
#    f.write(data)
#    f.close()
#    
#article = Wikipedia(language="nl").search("borrelnootje")
#print article.string

#--- FLICKR ----------------------------------------------------------------------------------------
# http://www.flickr.com/services/api/

FLICKR = "http://api.flickr.com/services/rest/"
FLICKR_LICENSE = api.license["Flickr"] 

INTERESTING = "interesting"

class Flickr(SearchEngine):
    
    def __init__(self, license=None, throttle=5.0, language=None):
        SearchEngine.__init__(self, license or FLICKR_LICENSE, throttle, language)

    def search(self, query, type=IMAGE, start=1, count=10, sort=RELEVANCY, size=None, cached=True, **kwargs):
        """ Returns a list of results from Flickr for the given query.
            Retrieving the URL of a result (i.e. image) requires an additional query.
            - type : SEARCH, IMAGE,
            - start: maximum undefined,
            - count: maximum 500,
            - sort : RELEVANCY, LATEST or INTERESTING.
            There is no daily limit.
        """
        if type not in (SEARCH, IMAGE):
            raise SearchEngineTypeError
        if not query or count < 1 or start < 1 or start > 500/count:
            return Results(FLICKR, query, IMAGE)
        # 1) Construct request URL.
        url = FLICKR+"?"
        url = URL(url, method=GET, query={        
           "api_key": self.license or "",
            "method": "flickr.photos.search",
              "text": query.replace(" ", "_"),
              "page": start,
          "per_page": min(count, 500),
              "sort": { RELEVANCY: "relevance", 
                           LATEST: "date-posted-desc", 
                      INTERESTING: "interestingness-desc" }.get(sort)
        })
        if kwargs.get("copyright", True) is False:
            # With copyright=False, only returns Public Domain and Creative Commons images.
            # http://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html
            # 5: "Attribution-ShareAlike License"
            # 7: "No known copyright restriction"
            url.query["license"] = "5,7"
        # 2) Parse XML response.
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        data = url.download(cached=cached, **kwargs)
        data = xml.dom.minidom.parseString(bytestring(data))
        results = Results(FLICKR, query, IMAGE)
        results.total = int(data.getElementsByTagName("photos")[0].getAttribute("total"))
        for x in data.getElementsByTagName("photo"):
            r = FlickrResult(url=None)
            r.__dict__["_id"]       = x.getAttribute("id")
            r.__dict__["_size"]     = size
            r.__dict__["_license"]  = self.license
            r.__dict__["_throttle"] = self.throttle
            r.description = self.format(x.getAttribute("title"))
            r.author      = self.format(x.getAttribute("owner"))
            results.append(r)
        return results
        
class FlickrResult(Result):
    
    @property
    def url(self):
        # Retrieving the url of a FlickrResult (i.e. image location) requires another query.
        # Note: the "Original" size no longer appears in the response,
        # so Flickr might not like it if we download it.
        url = FLICKR + "?method=flickr.photos.getSizes&photo_id=%s&api_key=%s" % (self._id, self._license)
        data = URL(url).download(throttle=self._throttle, unicode=True)
        data = xml.dom.minidom.parseString(bytestring(data))
        size = { TINY: "Thumbnail", 
                SMALL: "Small", 
               MEDIUM: "Medium", 
                LARGE: "Original" }.get(self._size, "Medium")
        for x in data.getElementsByTagName("size"):
            if size == x.getAttribute("label"):
                return x.getAttribute("source")
            if size == "Original":
                url = x.getAttribute("source")
                url = url[:-len(extension(url))-2] + "_o" + extension(url)
                return u(url)

#images = Flickr().search("kitten", count=10, size=SMALL)
#for img in images:
#    print bytestring(img.description)
#    print img.url
#
#data = img.download()
#f = open("kitten"+extension(img.url), "w")
#f.write(data)
#f.close()

#--- FACEBOOK --------------------------------------------------------------------------------------
# Facebook public status updates.
# Author: Rajesh Nair, 2012.
# https://developers.facebook.com/docs/reference/api/

FACEBOOK = "https://graph.facebook.com/"
FACEBOOK_LICENSE = api.license["Facebook"] 

class Facebook(SearchEngine):

    def __init__(self, license=None, throttle=1.0, language=None):
        SearchEngine.__init__(self, license, throttle, language)
        
    def search(self, query, type=SEARCH, start=1, count=10, cached=False, **kwargs):
        """ Returns a list of results from Facebook public status updates for the given query.
            - type : SEARCH,
            - start: 1,
            - count: maximum 100.
            There is an hourly limit of +-600 queries (actual amount undisclosed).
        """
        if type != SEARCH:
            raise SearchEngineTypeError
        if not query or start < 1 or count < 1: 
            return Results(FACEBOOK, query, SEARCH)
        # 1) Construct request URL.
        url = FACEBOOK + "search?"
        url = URL(url, method=GET, query={
                 "q": query,
              "type": "post",
             "limit": min(count, 100),
            "fields": "link,message,from"
        })
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        data = URL(url).download(cached=cached, **kwargs)
        data = json.loads(data)
        results = Results(FACEBOOK, query, SEARCH)
        results.total = None
        for x in data.get("data", []):
            r = Result(url=None)
            r.url          = self.format(x.get("link"))
            r.description  = self.format(x.get("message"))
            r.date         = self.format(x.get("created_time"))
            r.author       = self.format(x.get("from", {}).get("name"))
            results.append(r)
        return results

#--- PRODUCT REVIEWS -------------------------------------------------------------------------------

PRODUCTWIKI = "http://api.productwiki.com/connect/api.aspx"
PRODUCTWIKI_LICENSE = api.license["Products"] 

class Products(SearchEngine):
    
    def __init__(self, license=None, throttle=5.0, language=None):
        SearchEngine.__init__(self, license or PRODUCTWIKI_LICENSE, throttle, language)
    
    def search(self, query, type=SEARCH, start=1, count=10, sort=RELEVANCY, size=None, cached=True, **kwargs):
        """ Returns a list of results from Productwiki for the given query.
            Each Result.reviews is a list of (review, score)-items.
            - type : SEARCH,
            - start: maximum undefined,
            - count: 20,
            - sort : RELEVANCY.
            There is no daily limit.
        """ 
        if type != SEARCH:
            raise SearchEngineTypeError
        if not query or start < 1 or count < 1: 
            return Results(PRODUCTWIKI, query, type)
        # 1) Construct request URL.
        url = PRODUCTWIKI+"?"
        url = URL(url, method=GET, query={ 
               "key": self.license or "",
                 "q": query,
             "page" : start,
                "op": "search",
            "fields": "proscons", # "description,proscons" is heavy.
            "format": "json"
        })
        # 2) Parse JSON response.
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        data = URL(url).download(cached=cached, **kwargs)
        data = json.loads(data)
        results = Results(PRODUCTWIKI, query, type)
        results.total = None
        for x in data.get("products", [])[:count]:
            r = Result(url=None)
            r.__dict__["title"]       = u(x.get("title"))
            r.__dict__["description"] = u(x.get("description"))
            r.__dict__["reviews"]     = []
            reviews = x.get("community_review") or {}
            for p in reviews.get("pros", []):
                r.reviews.append((p.get("text", ""), int(p.get("score")) or +1))
            for p in reviews.get("cons", []):
                r.reviews.append((p.get("text", ""), int(p.get("score")) or -1))
            r.__dict__["score"] = int(sum(score for review, score in r.reviews))
            results.append(r)
        # Highest score first.
        results.sort(key=lambda r: r.score, reverse=True)
        return results  

#for r in Products().search("computer"):
#    print r.title
#    print r.score
#    print r.reviews
#    print

#--- NEWS FEED -------------------------------------------------------------------------------------
# Based on the Universal Feed Parser by Mark Pilgrim:
# http://www.feedparser.org/

class Newsfeed(SearchEngine):
    
    def __init__(self, license=None, throttle=1.0, language=None):
        SearchEngine.__init__(self, license, throttle, language)
    
    def search(self, query, type=NEWS, start=1, count=10, sort=LATEST, size=SMALL, cached=True, **kwargs):
        """ Returns a list of results from the given RSS or Atom newsfeed URL.
        """ 
        if type != NEWS:
            raise SearchEngineTypeError
        if not query or start < 1 or count < 1:
            return Results(query, query, NEWS)
        # 1) Construct request URL.
        # 2) Parse RSS/Atom response.
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        tags = kwargs.pop("tags", [])
        data = URL(query).download(cached=cached, **kwargs)
        data = feedparser.parse(bytestring(data))
        results = Results(query, query, NEWS)
        results.total = None
        for x in data["entries"][:count]:
            s = "\n\n".join([v.get("value") for v in x.get("content", [])]) or x.get("summary")
            r = Result(url=None)
            r.id          = self.format(x.get("id"))
            r.url         = self.format(x.get("link"))
            r.title       = self.format(x.get("title"))
            r.description = self.format(s)
            r.date        = self.format(x.get("updated"))
            r.author      = self.format(x.get("author"))
            r.language    = self.format(x.get("content") and \
                                x.get("content")[0].get("language") or \
                                               data.get("language"))
            for tag in tags:
                # Parse custom tags.
                # Newsfeed.search(tags=["dc:identifier"]) => Result.dc_identifier.
                tag = tag.replace(":", "_")
                r[tag] = self.format(x.get(tag))
            results.append(r) 
        return results           

feeds = {
          "Nature": "http://feeds.nature.com/nature/rss/current",
         "Science": "http://www.sciencemag.org/rss/podcast.xml",
  "Herald Tribune": "http://www.iht.com/rss/frontpage.xml",
            "TIME": "http://feeds.feedburner.com/time/topstories",
             "CNN": "http://rss.cnn.com/rss/edition.rss",
}

#for r in Newsfeed().search(feeds["Nature"]):
#    print r.title
#    print r.author
#    print r.url
#    print plaintext(r.description)
#    print

#--- WEB SORT --------------------------------------------------------------------------------------

SERVICES = {
    GOOGLE    : Google,
    YAHOO     : Yahoo,
    BING      : Bing,
    TWITTER   : Twitter,
    WIKIPEDIA : Wikipedia,
    FLICKR    : Flickr,
    FACEBOOK  : Facebook
}

def sort(terms=[], context="", service=GOOGLE, license=None, strict=True, reverse=False, **kwargs):
    """ Returns a list of (percentage, term)-tuples for the given list of terms.
        Sorts the terms in the list according to search result count.
        When a context is defined, sorts according to relevancy to the context, e.g.:
        sort(terms=["black", "green", "red"], context="Darth Vader") =>
        yields "black" as the best candidate, because "black Darth Vader" is more common in search results.
        - terms   : list of search terms,
        - context : term used for sorting,
        - service : web service name (GOOGLE, YAHOO, BING),
        - license : web service license id,
        - strict  : when True the query constructed from term + context is wrapped in quotes.
    """
    service = SERVICES.get(service, SearchEngine)(license, language=kwargs.pop("language", None))
    R = []
    for word in terms:
        q = reverse and context+" "+word or word+" "+context
        q.strip()
        q = strict and "\"%s\"" % q or q
        r = service.search(q, count=1, **kwargs)
        R.append(r)        
    s = float(sum([r.total or 1 for r in R])) or 1.0
    R = [((r.total or 1)/s, r.query) for r in R]
    R = sorted(R, reverse=True)    
    return R

#print sort(["black", "happy"], "darth vader", GOOGLE)

#### DOCUMENT OBJECT MODEL #########################################################################
# Tree traversal of HTML source code.
# The Document Object Model (DOM) is a cross-platform and language-independent convention 
# for representing and interacting with objects in HTML, XHTML and XML documents.
# BeautifulSoup is wrapped in Document, Element and Text classes that resemble the Javascript DOM.
# BeautifulSoup can of course be used directly since it is imported here.
# http://www.crummy.com/software/BeautifulSoup/

SOUP = (
    BeautifulSoup.BeautifulSoup,
    BeautifulSoup.Tag, 
    BeautifulSoup.NavigableString,
    BeautifulSoup.Comment
)

NODE, TEXT, COMMENT, ELEMENT, DOCUMENT = \
    "node", "text", "comment", "element", "document"

#--- NODE ------------------------------------------------------------------------------------------

class Node:
    
    def __init__(self, html, type=NODE, **kwargs):
        """ The base class for Text, Comment and Element.
            All DOM nodes can be navigated in the same way (e.g. Node.parent, Node.children, ...)
        """
        self.type = type
        self._p = not isinstance(html, SOUP) and BeautifulSoup.BeautifulSoup(u(html), **kwargs) or html

    @property
    def _beautifulSoup(self):
        # If you must, access the BeautifulSoup object with Node._beautifulSoup.
        return self._p

    def __eq__(self, other):
        # Two Node objects containing the same BeautifulSoup object, are the same.
        return isinstance(other, Node) and hash(self._p) == hash(other._p)
    
    def _wrap(self, x):
        # Navigating to other nodes yields either Text, Element or None.
        if isinstance(x, BeautifulSoup.Comment):
            return Comment(x)
        if isinstance(x, BeautifulSoup.Declaration):
            return Text(x)
        if isinstance(x, BeautifulSoup.NavigableString):
            return Text(x)
        if isinstance(x, BeautifulSoup.Tag):
            return Element(x)
    
    @property
    def parent(self):
        return self._wrap(self._p.parent)
    @property
    def children(self):
        return hasattr(self._p, "contents") and [self._wrap(x) for x in self._p.contents] or []
    @property
    def html(self):
        return self.__unicode__()
    @property
    def source(self):
        return self.__unicode__()
    @property
    def next_sibling(self):
        return self._wrap(self._p.nextSibling)
    @property
    def previous_sibling(self):
        return self._wrap(self._p.previousSibling)
    next, previous = next_sibling, previous_sibling

    def traverse(self, visit=lambda node: None):
        """ Executes the visit function on this node and each of its child nodes.
        """
        visit(self); [node.traverse(visit) for node in self.children]
        
    def __len__(self):
        return len(self.children)
    def __iter__(self):
        return iter(self.children)
    def __getitem__(self, index):
        return self.children[index]

    def __repr__(self):
        return "Node(type=%s)" % repr(self.type)
    def __str__(self):
        return bytestring(self.__unicode__())
    def __unicode__(self):
        return u(self._p)

#--- TEXT ------------------------------------------------------------------------------------------

class Text(Node):
    """ Text represents a chunk of text without formatting in a HTML document.
        For example: "the <b>cat</b>" is parsed to [Text("the"), Element("cat")].
    """    
    def __init__(self, string):
        Node.__init__(self, string, type=TEXT)
    def __repr__(self):
        return "Text(%s)" % repr(self._p)
    
class Comment(Text):
    """ Comment represents a comment in the HTML source code.
        For example: "<!-- comment -->".
    """
    def __init__(self, string):
        Node.__init__(self, string, type=COMMENT)
    def __repr__(self):
        return "Comment(%s)" % repr(self._p)

#--- ELEMENT ---------------------------------------------------------------------------------------

class Element(Node):
    
    def __init__(self, html):
        """ Element represents an element or tag in the HTML source code.
            For example: "<b>hello</b>" is a "b"-Element containing a child Text("hello").
        """
        Node.__init__(self, html, type=ELEMENT)

    @property
    def tagname(self):
        return self._p.name
    tag = tagName = tagname
    
    @property
    def attributes(self):
        return self._p._getAttrMap()

    @property
    def id(self):
        return self.attributes.get("id")
        
    def get_elements_by_tagname(self, v):
        """ Returns a list of nested Elements with the given tag name.
            The tag name can include a class (e.g. div.header) or an id (e.g. div#content).
        """
        if isinstance(v, basestring) and "#" in v:
            v1, v2 = v.split("#")
            v1 = v1 in ("*","") or v1.lower()
            return [Element(x) for x in self._p.findAll(v1, id=v2)]
        if isinstance(v, basestring) and "." in v:
            v1, v2 = v.split(".")
            v1 = v1 in ("*","") or v1.lower()
            return [Element(x) for x in self._p.findAll(v1, v2)]
        return [Element(x) for x in self._p.findAll(v in ("*","") or v.lower())]
    by_tag = getElementsByTagname = get_elements_by_tagname

    def get_element_by_id(self, v):
        """ Returns the first nested Element with the given id attribute value.
        """
        return ([Element(x) for x in self._p.findAll(id=v, limit=1) or []]+[None])[0]
    by_id = getElementById = get_element_by_id
    
    def get_elements_by_classname(self, v):
        """ Returns a list of nested Elements with the given class attribute value.
        """
        return [Element(x) for x in (self._p.findAll(True, v))]
    by_class = getElementsByClassname = get_elements_by_classname

    def get_elements_by_attribute(self, **kwargs):
        """ Returns a list of nested Elements with the given attribute value.
        """
        return [Element(x) for x in (self._p.findAll(True, attrs=kwargs))]
    by_attribute = getElementsByAttribute = get_elements_by_attribute
    
    @property
    def content(self):
        """ Yields the element content as a unicode string.
        """
        return u"".join([u(x) for x in self._p.contents])
    
    @property
    def source(self):
        """ Yields the HTML source as a unicode string (tag + content).
        """
        return u(self._p)
    html = source

    def __repr__(self):
        return "Element(tag='%s')" % bytestring(self.tagname)

#--- DOCUMENT --------------------------------------------------------------------------------------

class Document(Element):
    
    def __init__(self, html, **kwargs):
        """ Document is the top-level element in the Document Object Model.
            It contains nested Element, Text and Comment nodes.
        """
        # Aliases for BeautifulSoup optional parameters: 
        kwargs["selfClosingTags"] = kwargs.pop("self_closing", kwargs.get("selfClosingTags"))
        Node.__init__(self, u(html).strip(), type=DOCUMENT, **kwargs)

    @property
    def declaration(self):
        """ Yields the <!doctype> declaration, as a TEXT Node or None.
        """
        for child in self.children:
            if isinstance(child._p, BeautifulSoup.Declaration):
                return child
    
    @property
    def head(self):
        return self._wrap(self._p.head)
    @property
    def body(self):
        return self._wrap(self._p.body)
    @property
    def tagname(self):
        return None
    tag = tagname
    
    def __repr__(self):
        return "Document()"

DOM = Document

#article = Wikipedia().search("Document Object Model")
#dom = DOM(article.html)
#print dom.get_element_by_id("References").source
#print [element.attributes["href"] for element in dom.get_elements_by_tagname("a")]
#print dom.get_elements_by_tagname("p")[0].next.previous.children[0].parent.__class__
#print

#### WEB CRAWLER ###################################################################################
# Tested with a crawl across 1,000 domain so far.

class Link:
    
    def __init__(self, url, description="", relation="", referrer=""):
        """ A hyperlink parsed from a HTML document, in the form:
            <a href="url"", title="description", rel="relation">xxx</a>.
        """
        self.url, self.description, self.relation, self.referrer = \
            u(url), u(description), u(relation), u(referrer), 
    
    def __repr__(self):
        return "Link(url=%s)" % repr(self.url)

    # Used for sorting in Spider.links:
    def __eq__(self, link):
        return self.url == link.url
    def __ne__(self, link):
        return self.url != link.url
    def __lt__(self, link):
        return self.url < link.url
    def __gt__(self, link):
        return self.url > link.url

class HTMLLinkParser(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)

    def parse(self, html, url=""):
        """ Returns a list of Links parsed from the given HTML string.
        """
        if html is None:
            return None
        self._url  = url
        self._data = []
        self.feed(self.clean(html))
        self.close()
        self.reset()
        return self._data
    
    def handle_starttag(self, tag, attributes):
        if tag == "a":
            attributes = dict(attributes)
            if "href" in attributes:
                link = Link(url = attributes.get("href"),
                    description = attributes.get("title"),
                       relation = attributes.get("rel", ""),
                       referrer = self._url)
                self._data.append(link)

def base(url):
    """ Returns the URL domain name: 
        http://en.wikipedia.org/wiki/Web_crawler => en.wikipedia.org
    """
    return urlparse.urlparse(url).netloc

def abs(url, base=None):
    """ Returns the absolute URL:
        ../media + http://en.wikipedia.org/wiki/ => http://en.wikipedia.org/media
    """
    if url.startswith("#") and not base is None and not base.endswith("/"):
        if not re.search("[^/]/[^/]", base):
            base += "/"
    return urlparse.urljoin(base, url)

DEPTH   = "depth"
BREADTH = "breadth"

FIFO = "fifo" # First In, First Out.
FILO = "filo" # First In, Last Out.
LIFO = "lifo" # Last In, First Out (= FILO).

class Spider:
    
    def __init__(self, links=[], domains=[], delay=20.0, parser=HTMLLinkParser().parse, sort=FIFO):
        """ A spider can be used to browse the web in an automated manner.
            It visits the list of starting URLs, parses links from their content, visits those, etc.
            - Links can be prioritized by overriding Spider.priority().
            - Links can be ignored by overriding Spider.follow().
            - Each visited link is passed to Spider.visit(), which can be overridden.
        """
        self.parse    = parser
        self.delay    = delay   # Delay between visits to the same (sub)domain.
        self.domains  = domains # Domains the spider is allowed to visit.
        self.history  = {}      # Domain name => time last visited.
        self.visited  = {}      # URLs visited.
        self._queue   = []      # URLs scheduled for a visit: (priority, time, Link).
        self._queued  = {}      # URLs scheduled so far, lookup dictionary.
        self.QUEUE    = 10000   # Increase or decrease according to available memory.
        self.sort     = sort
        # Queue given links:
        for link in links:
            if not isinstance(link, Link):
                link = Link(url=link)
            self._queue.append((0.0, 0.0, link)) # 0.0, 0.0 = highest priority.

    @property
    def done(self):
        return len(self._queue) == 0

    @property
    def next(self):
        return self._pop_queue()

    def _pop_queue(self):
        """ Returns the next Link queued to visit.
            Links on a recently visited (sub)domain are skipped until Spider.delay has elapsed.
        """
        now = time.time()
        for i, (priority, dt, link) in enumerate(self._queue):
            if self.delay <= now - self.history.get(base(link.url), 0):
                self._queue.pop(i)
                self._queued.pop(link.url, None)
                return link
    
    def crawl(self, method=DEPTH, **kwargs):
        """ Visits the next link in Spider._queue.
            If the link is on a domain recently visited (< Spider.delay) it is skipped.
            Parses the content at the link for new links and adds them to the queue,
            according to their Spider.priority().
            Visited links (and content) are passed to Spider.visit().
        """
        link = self._pop_queue()
        if link is None:
            return False
        if link.url not in self.visited:
            t = time.time()
            url = URL(link.url)
            if url.mimetype == "text/html":
                try:
                    kwargs.setdefault("unicode", True)
                    html = url.download(**kwargs)
                    for new in self.parse(html, url=link.url):
                        new.url = abs(new.url, base=url.redirect or link.url)
                        new.url = self.normalize(new.url)
                        # 1) Parse new links from HTML web pages.
                        # 2) Schedule unknown links for a visit.
                        # 3) Only links that are not already queued are queued.
                        # 4) Only links for which Spider.follow() is True are queued.
                        # 5) Only links on Spider.domains are queued.
                        if new.url in self.visited:
                            continue
                        if new.url in self._queued:
                            continue
                        if self.follow(new) is False:
                            continue
                        if self.domains and not base(new.url).endswith(tuple(self.domains)):
                            continue
                        # 6) Limit the queue (remove tail), unless you are Google.
                        if self.QUEUE is not None and \
                           self.QUEUE * 1.25 < len(self._queue):
                            self._queue = self._queue[:self.QUEUE]
                            self._queued.clear()
                            self._queued.update(dict((q[2].url, True) for q in self._queue))
                        # 7) Position in the queue is determined by Spider.priority().
                        # 8) Equal ranks are sorted FIFO or FILO.
                        dt = self.sort == FIFO and time.time() or 1/time.time()
                        bisect.insort(self._queue, 
                            (1 - self.priority(new, method=method), dt, new))
                        self._queued[new.url] = True
                    self.visit(link, source=html)
                except URLError:
                    # URL can not be reached (HTTP404NotFound, URLTimeout).
                    self.fail(link)
            else:
                # URL MIME-type is not HTML, don't know how to handle.
                self.fail(link)
            # Log the current time visited for the domain (see Spider._pop_queue()).
            # Log the URL as visited.
            self.history[base(link.url)] = time.time()
            self.visited[link.url] = True
            return True
        # Nothing happened, we already visited this link.
        return False

    def normalize(self, url):
        """ Called from Spider.crawl() to normalize URLs.
            For example: return url.split("?")[0]
        """
        # All links pass through here (visited or not).
        # This can be a place to count backlinks.
        return url

    def follow(self, link):
        """ Called from Spider.crawl() to determine if it should follow this link.
            For example: return "nofollow" not in link.relation
        """
        return True

    def priority(self, link, method=DEPTH):
        """ Called from Spider.crawl() to determine the priority of this link,
            as a number between 0.0-1.0. Links with higher priority are visited first.
        """
        # Depth-first search dislikes external links to other (sub)domains.
        external = base(link.url) != base(link.referrer)
        if external is True:
            if method == DEPTH: 
                return 0.75
            if method == BREADTH:
                return 0.85
        return 0.80

    def visit(self, link, source=None):
        """ Called from Spider.crawl() when the link is crawled.
            When source=None, the link is not a web page (and was not parsed),
            or possibly a URLTimeout occured (content size too big).
        """
        pass
        
    def fail(self, link):
        """ Called from Spider.crawl() for link whose MIME-type could not be determined,
            or which raised a URLError on download.
        """
        pass

#class Spiderling(Spider):
#    def visit(self, link, source=None):
#        print "visited:", link.url, "from:", link.referrer
#    def fail(self, link):
#        print "failed:", link.url
#
#s = Spiderling(links=["http://nodebox.net/"], domains=["nodebox.net"], delay=5)
#while not s.done:
#    s.crawl(method=DEPTH, cached=True, throttle=5)

#### PDF PARSER ####################################################################################
#  Yusuke Shinyama, PDFMiner, http://www.unixuser.org/~euske/python/pdfminer/

class PDFParseError(Exception):
    pass

class PDF:
    
    def __init__(self, data, format=None):
        """ Plaintext parsed from the given PDF data.
        """
        self.content = self._parse(data, format)
    
    @property
    def string(self):
        return self.content
    def __unicode__(self):
        return self.content
        
    def _parse(self, data, format=None):
        # The output will be ugly: it may be useful for mining but probably not for displaying.
        # You can also try PDF(data, format="html") to preserve some layout information.
        from pdf.pdfinterp import PDFResourceManager, process_pdf
        from pdf.converter import TextConverter, HTMLConverter
        from pdf.layout    import LAParams
        s = ""
        m = PDFResourceManager()
        try:
            # Given data is a PDF file path.
            data = os.path.exists(data) and open(data) or StringIO.StringIO(data)
        except TypeError:
            # Given data is a PDF string.
            data = StringIO.StringIO(data)
        try:
            stream = StringIO.StringIO()
            parser = format=="html" and HTMLConverter or TextConverter
            parser = parser(m, stream, codec="utf-8", laparams=LAParams())
            process_pdf(m, parser, data, set(), maxpages=0, password="")
        except Exception, e:
            raise PDFParseError, str(e)
        s = stream.getvalue()
        s = decode_utf8(s)
        s = s.strip()
        s = re.sub(r"([a-z])\-\n", "\\1", s)        # Join hyphenated words.
        s = s.replace("\n\n", "<!-- paragraph -->") # Preserve paragraph spacing.
        s = s.replace("\n", " ")
        s = s.replace("<!-- paragraph -->", "\n\n")
        s = collapse_spaces(s)
        return s

####################################################################################################

def test():
    # A shallow test to see if all the services can be reached.
    p = cache.path
    cache.path = TMP
    cache.clear()
    for engine in (Google, Yahoo, Bing, Twitter, Wikipedia, Flickr):
        try: 
            engine().search("tiger")
            print engine.__name__, "ok."
        except:
            print engine.__name__, "error."
    cache.path = p
    
#test()
