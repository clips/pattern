#### PATTERN | SERVER ##############################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2014 University of Antwerp, Belgium
# Copyright (c) 2014 St. Lucas University College of Art & Design, Antwerp.
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).

####################################################################################################

from __future__ import with_statement

import __main__
import sys
import os
import re
import time; _time=time
import atexit
import urllib
import hashlib
import base64
import random
import string
import cStringIO
import cPickle
import textwrap
import types
import inspect
import threading
import itertools
import collections
import sqlite3 as sqlite

try:
    # Folder that contains pattern.server.
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""
    
try:
    # Folder that contains the script that (indirectly) imports pattern.server.
    # This is used as the default App.path.
    f = inspect.currentframe()
    f = inspect.getouterframes(f)[-1][0]
    f = f.f_globals["__file__"]
    SCRIPT = os.path.dirname(os.path.abspath(f))
except:
    SCRIPT = os.getcwd()

try:
    # Import from python2.x/site-packages/cherrypy
    import cherrypy; cp=cherrypy
except:
    # Import from pattern/server/cherrypy/cherrypy
    # Bundled package is "hidden" in a non-package folder,
    # otherwise it conflicts with site-packages/cherrypy.
    sys.path.insert(0, os.path.join(MODULE, "cherrypy"))
    import cherrypy; cp=cherrypy

try: import json # Python 2.6+
except:
    try: from pattern.web import json # simplejson
    except:
        json = None

#### STRING FUNCTIONS ##############################################################################

RE_AMPERSAND = re.compile("\&(?!\#)")           # & not followed by #
RE_UNICODE   = re.compile(r'&(#?)(x|X?)(\w+);') # &#201;

def encode_entities(string):
    """ Encodes HTML entities in the given string ("<" => "&lt;").
        For example, to display "<em>hello</em>" in a browser,
        we need to pass "&lt;em&gt;hello&lt;/em&gt;" (otherwise "hello" in italic is displayed).
    """
    if isinstance(string, basestring):
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
            if hex == "":
                return unichr(int(name))                 # "&#38;" => "&"
            if hex.lower() == "x":
                return unichr(int("0x" + name, 16))      # "&#x0026;" = > "&"
        else:
            cp = htmlentitydefs.name2codepoint.get(name) # "&amp;" => "&"
            return unichr(cp) if cp else match.group()   # "&foo;" => "&foo;"
    if isinstance(string, basestring):
        return RE_UNICODE.subn(replace_entity, string)[0]
    return string

def encode_url(string):
    return urllib.quote_plus(bytestring(string)) # "black/white" => "black%2Fwhite".
    
def decode_url(string):
    return urllib.unquote_plus(string)

#### INTROSPECTION #################################################################################
# URL paths are routed to handler functions, whose arguments represent URL path & query parameters.
# So we need to know what the arguments and keywords arguments are at runtime.

def define(f):
    """ Returns (name, type, tuple, dict) for the given function,
        with a tuple of argument names and a dict of keyword arguments.
        If the given function has *args, returns True instead of tuple.
        If the given function has **kwargs, returns True instead of dict.
    """
    def undecorate(f): # "__closure__" in Py3.
        while getattr(f, "func_closure", None):
            f = [v.cell_contents for v in getattr(f, "func_closure")]
            f = [v for v in f if callable(v)]
            f = f[0]   # We need guess (arg could also be a function).
        return f
    f = undecorate(f)
    a = inspect.getargspec(f) # (names, *args, **kwargs, values)
    i = len(a[0]) - len(a[3] or [])
    x = tuple(a[0][:i])
    y = dict(zip(a[0][i:], a[3] or []))
    x = x if not a[1] else True
    y = y if not a[2] else True
    return (f.__name__, type(f), x, y)

#### DATABASE ######################################################################################

#--- DATABASE --------------------------------------------------------------------------------------
# A simple wrapper for SQLite and MySQL databases.

# Database type:
SQLITE, MYSQL = "sqlite", "mysql"

# Database host:
LOCALHOST = "127.0.0.1"

class Row(dict):
    
    def __init__(self, cursor, row):
        """ Row as dictionary.
        """
        d = cursor.description
        dict.__init__(self, ((d[i][0], v) for i, v in enumerate(row)))
        
    def __getattr__(self, k):
        return self[k] # Row.[field]
        
class DatabaseError(Exception):
    pass
        
class Database(object):
    
    def __init__(self, name, **kwargs):
        """ Creates and opens the SQLite database with the given name.
        """
        k = kwargs.get
        self._name    = name
        self._type    = k("type", SQLITE)
        self._host    = k("host", LOCALHOST)
        self._port    = k("port", 3306)
        self._user    = k("user", (k("username", "root"), k("password", "")))
        self._factory = k("factory", Row)
        self._timeout = k("timeout", 10)
        self._connection = None
        if kwargs.get("connect", True):
            self.connect()
        if kwargs.get("schema"):
            # Database(schema="create table if not exists" `...`)
            # initializes the database table and index structure.
            for q in kwargs["schema"].split(";"):
                self.execute(q+";", commit=False)
            self.commit()
    
    @property
    def name(self):
        """ Yields the database name (for SQLITE, file path).
        """
        return self._name

    @property
    def type(self):
        """ Yields the database type (SQLITE or MYSQL).
        """
        return self._type
        
    @property
    def host(self):
        """ Yields the database server host (MYSQL).
        """
        return self._host
                
    @property
    def port(self):
        """ Yields the database server port (MYSQL).
        """
        return self._port
    
    @property
    def connection(self):
        """ Yields the sqlite3.Connection object.
        """
        return self._connection
        
    def connect(self):
        if self._type == SQLITE:
            self._connection = sqlite.connect(self._name, timeout=self._timeout)
            self._connection.row_factory = self._factory
        if self._type == MYSQL:
            import MySQLdb
            self._connection = MySQLdb.connect(
                  host = self._host, 
                  port = self._port, 
                  user = self._user[0], 
                passwd = self._user[1], 
       connect_timeout = self._timeout, 
           use_unicode = True, 
               charset = "utf8"
            )
            self._connection.row_factory = self._factory
            self._connection.cursor().execute("create database if not exists `%s`" % self._name)
            self._connection.cursor().execute("use `%s`" % self._name)
            
    def disconnect(self):
        if self._connection is not None:
            self._connection.commit()
            self._connection.close()
            self._connection = None
    
    def execute(self, sql, values=(), first=False, commit=True):
        """ Executes the given SQL query string and returns an iterator of rows.
            With first=True, returns the first row.
        """
        try:
            r = self._connection.cursor().execute(sql, values)
            if commit: 
                self._connection.commit()
        except Exception, e:
            # "OperationalError: database is locked" means that 
            # SQLite is receiving too many concurrent write ops.
            # A write operation locks the entire database;
            # other threaded connections may time out waiting.
            # In this case you can raise Database(timeout=10),
            # lower Application.run(threads=10) or switch to MySQL or Redis.
            self._connection.rollback()
            raise DatabaseError, str(e)
        return r.fetchone() if first else r
        
    def commit(self):
        """ Commits changes (pending insert/update/delete queries).
        """
        self._connection.commit()
        
    def rollback(self):
        """ Discard changes since the last commit.
        """
        self._connection.rollback()
        
    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def __repr__(self):
        return "Database(name=%s)" % repr(self._name)

    def __del__(self):
        try: 
            self.disconnect()
        except:
            pass
    
    @property
    def batch(self):
        return Database._batch.setdefault(self._name, DatabaseTransaction(self._name, **self.__dict__))

    _batch = {} # Shared across all instances.

#--- DATABASE TRANSACTION BUFFER -------------------------------------------------------------------

class DatabaseTransaction(Database):
    
    def __init__(self, name, **kwargs):
        """ Database.batch.execute() stores given the SQL query in RAM memory, across threads.
            Database.batch.commit() commits all buffered queries.
            This can be combined with @app.task() to periodically write batches to the database
            (instead of writing on each request).
        """
        Database.__init__(self, name, **dict(kwargs, connect=False))
        self._queue = []
    
    def execute(self, sql, values=()):
        self._queue.append((sql, values))
        
    def commit(self):
        q, self._queue = self._queue, []
        if q:
            try:
                Database.connect(self)  # Connect in this thread.
                for sql, v in q:
                    Database.execute(self, sql, v, commit=False)
                Database.commit(self)
            except DatabaseError, e:
                Database.rollback(self) # Data in q will be lost.
                raise e

    def rollback(self):
        self._queue = []
        
    def __len__(self):
        return len(self._queue)
        
    def __repr__(self):
        return "DatabaseTransaction(name=%s)" % repr(self._name)

    @property
    def batch(self):
        raise AttributeError

#---------------------------------------------------------------------------------------------------
# MySQL on Mac OS X installation notes:

# 1) Download Sequel Pro: http://www.sequelpro.com (GUI).
# 2) Download MySQL .dmg: http://dev.mysql.com/downloads/mysql/ (for 64-bit Python, 64-bit MySQL).
# 3) Install the .pkg, startup item and preferences pane.
# 4) Start server in preferences pane (user: "root", password: "").
# 5) Command line: open -a "TextEdit" .bash_profile =>
# 6) export PATH=~/bin:/usr/local/bin:/usr/local/mysql/bin:$PATH
# 7) Command line: sudo pip install MySQL-python
# 8) Command line: sudo ln -s /usr/local/mysql/lib/libmysqlclient.xx.dylib 
#                             /usr/lib/libmysqlclient.xx.dylib
# 9) import MySQLdb

#### RATE LIMITING #################################################################################
# With @app.route(path, limit=True), the decorated URL path handler function calls RateLimit().
# For performance, rate limiting uses a RAM cache of api keys + the time of the last request.
# This will not work with multi-processing, since each process gets its own RAM.

_RATELIMIT_CACHE = {} # RAM cache of request counts.
_RATELIMIT_LOCK  = threading.RLock()

MINUTE, HOUR, DAY = 60., 60*60., 60*60*24.

class RateLimitError(Exception):
    pass

class RateLimitExceeded(RateLimitError):
    pass

class RateLimitForbidden(RateLimitError):
    pass

class RateLimit(Database):
    
    def __init__(self, name="rate.db", **kwargs):
        """ A database for rate limiting API requests.
            It manages a table with (key, path, limit, time) entries.
            It grants each key a rate (number of requests / time) for a URL path.
            It keeps track of the number of requests in local memory (i.e., RAM).
            If RateLimit()() is called with the optional limit and time arguments,
            unknown keys are temporarily granted this rate.
        """
        Database.__init__(self, name, **dict(kwargs, factory=None, schema=(
            "create table if not exists `rate` ("
                  "`key` text,"    # API key (e.g., ?key="1234").
                 "`path` text,"    # API URL path (e.g., "/api/1/").
                "`limit` integer," # Maximum number of requests.
                 "`time` float"    # Time frame.
            ");"
            "create index if not exists `rate1` on rate(key);"
            "create index if not exists `rate2` on rate(path);")
        ))
        self.load()

    @property
    def cache(self):
        return _RATELIMIT_CACHE
        
    @property
    def lock(self):
        return _RATELIMIT_LOCK

    @property
    def key(self, pairs=("rA","aZ","gQ","hH","hG","aR","DD")):
        """ Yields a new random key ("ZjNmYTc4ZDk0MTkyYk...").
        """
        k = str(random.getrandbits(256))
        k = hashlib.sha256(k).hexdigest()
        k = base64.b64encode(k, random.choice(pairs)).rstrip('==')
        return k
        
    def reset(self):
        self.cache.clear()
        self.load()
            
    def load(self):
        """ For performance, rate limiting is handled in memory (i.e., RAM).
            Loads the stored rate limits in memory (100,000 records ~= 5MB RAM).
        """
        with self.lock: 
            if not self.cache:
                # Lock concurrent threads when modifying cache.
                for r in self.execute("select * from `rate`;"):
                    self.cache[(r[0], r[1])] = (0, r[2], r[3], _time.time())
                self._rowcount = len(self.cache)
    
    def set(self, key, path="/", limit=100, time=HOUR):
        """ Sets the rate for the given key and path,
            where limit is the maximum number of requests in the given time (e.g., 100/hour).
        """
        # Update database.
        p  = "/" + path.strip("/")
        q1 = "delete from `rate` where key=? and path=?;"
        q2 = "insert into `rate` values (?, ?, ?, ?);"
        self.execute(q1, (key, p), commit=False)
        self.execute(q2, (key, p, limit, time))
        # Update cache.
        with self.lock: 
            self.cache[(key, p)] = (0, limit, time, _time.time())
            self._rowcount += 1
        return (key, path, limit, time)
        
    def get(self, key, path="/"):
        """ Returns the rate for the given key and path (or None).
        """
        p = "/" + path.strip("/")
        q = "select * from `rate` where key=? and path=?;"
        return self.execute(q, (key, p), first=True, commit=False)
        
    def __setitem__(self, (key, path), (limit, time)):
        return self.set(key, path, limit, time)
        
    def __getitem__(self, (key, path)):
        return self.get(key, path)

    def __contains__(self, key, path="%"):
        """ Returns True if the given key exists (for the given path).
        """
        q = "select * from `rate` where key=? and path like ?;"
        return self.execute(q, (key, path), first=True, commit=False) is not None

    def __call__(self, key, path="/", limit=None, time=None, reset=100000):
        """ Increases the (cached) request count by 1 for the given key and path.
            If the request count exceeds its limit, raises RateLimitExceeded.
            If the optional limit and time are given, unknown keys (!= None) 
            are given this rate limit - as long as the cache exists in memory.
            Otherwise a RateLimitForbidden is raised.
        """
        with self.lock:
            t = _time.time()
            p = "/" + path.strip("/")
            r = self.cache.get((key, p))   
            # Reset the cache if too large (e.g., 1M+ IP addresses).
            if reset and reset < len(self.cache) and reset > self._rowcount:
                self.reset()
            # Unknown key (apply default limit / time rate).
            if r is None and key is not None and limit is not None and time is not None:
                self.cache[(key, p)] = r = (0, limit, time, t)
            # Unknown key (apply root key, if any).
            if r is None and p != "/":
                self.cache.get((key, "/"))
            if r is None:
                raise RateLimitForbidden
            # Limit reached within time frame (raise error).
            elif r[0] >= r[1] and r[2] > t - r[3]:
                raise RateLimitExceeded
            # Limit reached out of time frame (reset count).
            elif r[0] >= r[1]:
                self.cache[(key, p)] = (1, r[1], r[2], t)
            # Limit not reached (increment count).
            elif r[0] <  r[1]:
                self.cache[(key, p)] = (r[0] + 1, r[1], r[2], r[3])
        #print self.cache.get((key, path))

#### ROUTER ########################################################################################
# The @app.route(path) decorator registers each URL path handler in Application.router.

class RouteError(Exception):
    pass

class Router(dict):
    
    def __init__(self):
        """ A router resolves URL paths to handler functions.
        """
        pass
    
    def __setitem__(self, path, handler):
        """ Defines the handler function for the given URL path.
            The path is a slash-formatted string (e.g., "/api/1/en/parser").
            The handler is a function that takes 
            arguments (path) and keyword arguments (query data).
        """
        p = "/" + path.strip("/")
        p = p.lower()
        p = p.encode("utf8") if isinstance(p, unicode) else p
        # Store the handler + its argument names (tuple(args), dict(kwargs)),
        # so that we can call this function without (all) keyword arguments,
        # if it does not take (all) query data.
        if callable(handler):
            dict.__setitem__(self, p, (handler, define(handler)[2:]))
        else:
            dict.__setitem__(self, p, (handler, ((), {})))
        
    def __call__(self, path, **data):
        """ Calls the handler function for the given URL path.
            If no handler is found, raises a RouteError.
            If a base handler is found (e.g., "/api" for "/api/1/en"),
            calls the handler with arguments (e.g., handler("1", "en")).
        """
        if not isinstance(path, tuple):
            path = path.strip("/").split("/") # ["api", "1", "en"]
        n = len(path)
        for i in xrange(n + 1):
            p0 = "/" + "/".join(path[:n-i])
            p0 = p0.lower()                   # "/api/1/en", "/api/1", "/api", ...
            p1 = path[n-i:]                   # [], ["en"], ["1", "en"], ...
            if p0 in self:
                (handler, (args, kwargs)) = self[p0]
                i = len(p1)
                j = len(args) if args is not True else i
                # Handler takes 1 argument, 0 given (pass None for convenience).
                if i == 0 and j == 1:
                    p1 = (None,); i=j
                # Handler does not take path.
                if i != j:
                    continue
                # Handler is a string / dict.
                if not callable(handler):
                    return handler
                # Handler takes path, but no query data.
                if not kwargs:
                    return handler(*p1)
                # Handler takes path and all query data.
                if kwargs is True:
                    return handler(*p1, **data)
                # Handler takes path and some query data.
                return handler(*p1, **dict((k, v) for k, v in data.items() if k in kwargs))
        # No handler.
        raise RouteError

#### APPLICATION ###################################################################################

#--- APPLICATION ERRORS & REQUESTS -----------------------------------------------------------------

class HTTPRedirect(Exception):
    
    def __init__(self, url, code=303):
        """ A HTTP redirect raised in an @app.route() handler.
        """
        self.url  = url
        self.code = code
    
    def __repr__(self):
        return "HTTPRedirect(url=%s)" % repr(self.url)

class HTTPError(Exception):
    
    def __init__(self, code, status="", message="", traceback=""):
        """ A HTTP error raised in an @app.route() handler + passed to @app.error().
        """
        self.code      = code
        self.status    = status
        self.message   = message
        self.traceback = traceback or ""
        
    def __repr__(self):
        return "HTTPError(status=%s)" % repr(self.status)

class HTTPRequest(object):
    
    def __init__(self, app, ip, path="/", method="get", data={}, headers={}):
        """ A HTTP request object with metadata returned from app.request.
        """
        self.app     = app
        self.ip      = ip
        self.path    = "/" + path.strip("/")
        self.method  = method.lower()
        self.data    = dict(data)
        self.headers = dict(headers)
        
    def __repr__(self):
        return "HTTPRequest(ip=%s, path=%s)" % repr(self.ip, self.path)

#--- APPLICATION THREAD-SAFE DATA ------------------------------------------------------------------
# With a multi-threaded server, each thread requires its own local data (i.e., database connection).
# Local data can be initialized with @app.thread(START):
#
# >>> @app.thread(START)
# >>> def db():
# >>>    g.db = Database()
# >>>
# >>> @app.route("/")
# >>> def index(*path, db=None):
# >>>    print db # = Database object.
#
# The thread-safe database connection can then be retrieved from 
# app.thread.db, g.db, or as a keyword argument of a URL handler.

class localdict(dict):
    
    def __init__(self, data=None, **kwargs):
        """ Thread-safe dictionary.
        """
        self.__dict__["_data"] = data if data != None else threading.local()
        self.__dict__.update(kwargs) # Attributes are global in every thread.
        
    def items(self):
        return self._data.__dict__.items()
    def keys(self):
        return self._data.__dict__.keys()
    def values(self):
        return self._data.__dict__.values()
    def update(self, d):
        return self._data.__dict__.update(d)
    def clear(self):
        return self._data.__dict__.clear()
    def pop(self, *kv):
        return self._data.__dict__.pop(*kv)
    def setdefault(self, k, v=None):
        return self._data.__dict__.setdefault(k, v)
    def set(self, k, v):
        return setattr(self._data, k, v)
    def get(self, k, default=None):
        return getattr(self._data, k, default)
    def __delitem__(self, k):
        return delattr(self._data, k)
    def __getitem__(self, k):
        return getattr(self._data, k)
    def __setitem__(self, k, v):
        return setattr(self._data, k, v)
    def __delattr__(self, k):
        return delattr(self._data, k)
    def __getattr__(self, k):
        return getattr(self._data, k)
    def __setattr__(self, k, v):
        return setattr(self._data, k, v)
    def __len__(self):
        return  len(self._data.__dict__)
    def __iter__(self):
        return iter(self._data.__dict__)
    def __contains__(self, k):
        return k in self._data.__dict__
    def __str__(self):
        return repr(self)
    def __repr__(self):
        return "localdict({%s})" % ", ".join(
            ("%s: %s" % (repr(k), repr(v)) for k, v in self.items()))

# Global alias for app.thread (Flask-style):
g = localdict(data=cp.thread_data)

def threadsafe(function):
    """ The @threadsafe decorator ensures that no two threads execute the function simultaneously.
    """
    # In some cases, global data must be available across all threads (e.g., rate limits).
    # Atomic operations like dict.get() or list.append() (= single execution step) are thread-safe,
    # but some operations like dict[k] += 1 are not, and require a lock.
    # http://effbot.org/zone/thread-synchronization.htm
    #
    # >>> count = defaultdict(int)
    # >>> @threadsafe
    # >>> def inc(k):
    # >>>     count[k] += 1
    #
    lock = threading.RLock()
    def decorator(*args, **kwargs):
        with lock:
            v = function(*args, **kwargs)
        return v
    return decorator

#--- APPLICATION -----------------------------------------------------------------------------------
# With Apache + mod_wsgi, the Application instance must be named "application".

# Server host.
LOCALHOST = "127.0.0.1"
INTRANET = "0.0.0.0"

# Server thread handlers.
START = "start"
STOP = "stop"

class ApplicationError(Exception):
    pass

class Application(object):
    
    def __init__(self, name=None, path=SCRIPT, static="static/", rate="rate.db"):
        """ A web app served by a WSGI-server that starts with App.run().
            By default, the app is served from the folder of the script that imports pattern.server.
            By default, static content is served from the given subfolder.
            @App.route(path) defines a URL path handler.
            @App.error(code) defines a HTTP error handler.
        """
        # RateLimit db resides in app folder:
        rate = os.path.join(path, rate)
        self._name   = name         # App name.
        self._path   = path         # App path.
        self._host   = None         # Server host, see App.run().
        self._port   = None         # Server port, see App.run().
        self._app    = None         # CherryPy Application object.
        self._up     = False        # True if server is up & running.
        self._cache  = {}           # Memoize cache.
        self._static = static       # Static content folder.
        self._rate   = rate         # RateLimit db name, see also App.route(limit=True).
        self.router  = Router()     # Router object, maps URL paths to handlers.
        self.thread  = App.Thread() # Thread-safe dictionary.
        os.chdir(path)
        
    @property
    def name(self):
        return self._name
        
    @property
    def host(self):
        return self._host
    
    @property
    def port(self):
        return self._port
        
    @property
    def up(self):
        return self._up
        
    running = up
    
    @property
    def path(self):
        """ Yields the absolute path to the folder containing the app.
        """
        return self._path
        
    @property
    def static(self):
        """ Yields the absolute path to the folder with static content.
        """
        return os.path.join(self._path, self._static)

    @property
    def session(self):
        """ Yields the dictionary of session data.
        """
        return cp.session
        
    @property
    def request(self):
        """ Yields a request object with metadata
            (IP address, request path, query data and headers).
        """
        r = cp.request # Deep copy (ensures garbage colletion).
        return HTTPRequest(
                app = self, 
                 ip = r.remote.ip, 
               path = r.path_info, 
             method = r.method, 
               data = r.params, 
            headers = r.headers)
        
    @property
    def response(self):
        """ Yields a response object with metadata
            (status, headers).
        """
        return cp.response
        
    @property
    def elapsed(self):
        """ Yields the elapsed time since the start of the request.
        """
        return time.time() - cp.request.time # See also _request_time().

    def _cast(self, v):
        """ Returns the given value as a string (used to cast handler functions).
            If the value is a dictionary, returns a JSON-string.
            If the value is a generator, starts a stream.
            If the value is an iterable, joins the values with a space.
        """
        if isinstance(v, basestring):
            return v
        if isinstance(v, cp.lib.file_generator): # serve_file()
            return v
        if isinstance(v, dict):
            cp.response.headers["Content-Type"] = "application/json; charset=utf-8"
            cp.response.headers["Access-Control-Allow-Origin"] = "*" # CORS
            return json.dumps(v)
        if isinstance(v, types.GeneratorType):
            cp.response.stream = True
            return iter(self._cast(v) for v in v)
        if isinstance(v, (list, tuple, set)):
            return " ".join(self._cast(v) for v in v)
        if isinstance(v, HTTPError):
            raise cp.HTTPError(v.code)
        if v is None:
            return ""
        try: # (bool, int, float, object.__unicode__)
            return unicode(v)
        except:
            return encode_entities(repr(v))

    @cp.expose
    def default(self, *path, **data):
        """ Resolves URL paths to handler functions and casts the return value.
        """
        # If there is an app.thread.db connection,
        # pass it as a keyword argument named "db".
        # If there is a query parameter named "db",
        # it is overwritten (the reverse is not safe).
        for k, v in g.items():
            data[k] = v
        # Call the handler function for the given path.
        # Call @app.error(404) if no handler is found.
        # Call @app.error(403) if rate limit forbidden (= no API key).
        # Call @app.error(429) if rate limit exceeded.
        # Call @app.error(503) if a database error occurs.
        try:
            v = self.router(path, **data)
        except RouteError:
            raise cp.HTTPError("404 Not Found")
        except RateLimitForbidden:
            raise cp.HTTPError("403 Forbidden")
        except RateLimitExceeded:
            raise cp.HTTPError("429 Too Many Requests")
        except DatabaseError, e:
            raise cp.HTTPError("503 Service Unavailable", message=str(e))
        except HTTPRedirect, e:
            raise cp.HTTPRedirect(e.url)
        except HTTPError, e:
            raise cp.HTTPError(e.status)
        v = self._cast(v)
        #print self.elapsed
        return v
        
    def route(self, path, limit=False, time=None, key=lambda data: data.get("key"), reset=100000):
        """ The @app.route(path) decorator defines the handler function for the given path.
            The function can take arguments (path) and keyword arguments (query data), e.g.,
            if no handler exists for URL "/api/1/en", but a handler exists for URL "/api/1",
            this handler will be called with 1 argument: "en".
            It returns a string, a generator or a dictionary (which is parsed to a JSON-string).
        """
        _a = (key, limit, time, reset) # Avoid ambiguity with key=lambda inside define().
        def decorator(handler):
            def ratelimited(handler):
                # With @app.route(path, limit=True), rate limiting is applied.
                # The handler function is wrapped in a function that first calls
                # RateLimit()(key, path, limit, time) before calling the handler.
                # By default, a query parameter "key" is expected.
                # If the key is known, apply rate limiting (429 Too Many Requests).
                # If the key is unknown or None, deny access (403 Forbidden).
                # If the key is unknown and a default limit and time are given,
                # add the key and grant the given credentials, e.g.:
                # @app.route(path, limit=100, time=HOUR, key=lambda data: app.request.ip).
                # This grants each IP-address a 100 requests per hour.
                @self.thread(START)
                def connect():
                    g.rate = RateLimit(name=self._rate)
                def wrapper(*args, **kwargs):
                    r = cp.request
                    self = r.app.root
                    self.rate(
                          key = _a[0](r.params),
                         path = "/" + r.path_info.strip("/"),
                        limit = _a[1],  # Default limit for unknown keys.
                         time = _a[2],  # Default time for unknown keys.
                        reset = _a[3]   # Threshold for clearing cache.
                    )
                    return handler(*args, **kwargs)
                return wrapper
            if limit is True or (limit is not False and limit is not None and time is not None):
                handler = ratelimited(handler)
            self.router[path] = handler # Register the handler.
            return handler
        return decorator
        
    def error(self, code="*"):
        """ The @app.error(code) decorator defines the handler function for the given HTTP error.
            The function takes a HTTPError object and returns a string.
        """
        def decorator(handler):
            # CherryPy error handlers take keyword arguments.
            # Wrap as a HTTPError and pass it to the handler.
            def wrapper(status="", message="", traceback="", version=""):
                # Avoid CherryPy bug "ValueError: status message was not supplied":
                v = handler(HTTPError(int(status.split(" ")[0]), status, message, traceback))
                v = self._cast(v) if not isinstance(v, HTTPError) else repr(v)
                return v
            # app.error("*") catches all error codes.
            if code in ("*", None):
                cp.config.update({"error_page.default": wrapper})
            # app.error(404) catches 404 error codes.
            elif isinstance(code, (int, basestring)):
                cp.config.update({"error_page.%s" % code: wrapper})
            # app.error((404, 500)) catches 404 + 500 error codes.
            elif isinstance(code, (tuple, list)):
                for x in code:
                    cp.config.update({"error_page.%s" % x: wrapper})
            return handler
        return decorator
        
    def view(self, template, cached=True):
        """ The @app.view(template) decorator defines a template to format the handler function.
            The function returns a dict of keyword arguments for Template.render().
        """
        def decorator(handler):
            def wrapper(*args, **kwargs):
                if not hasattr(template, "render"): # bottle.py templates have render() too.
                    t = Template(template, root=self.static, cached=cached)
                else:
                    t = template
                v = handler(*args, **kwargs)
                if isinstance(v, dict):
                    return t.render(**v) # {kwargs}
                return t.render(*v) # (globals(), locals(), {kwargs})
            return wrapper
        return decorator

    class Thread(localdict):
        """ The @app.thread(event) decorator can be used to initialize thread-safe data.
            Get data (e.g., a database connection) with app.thread.[name] or g.[name].
        """
        def __init__(self):
            localdict.__init__(self, data=cp.thread_data, handlers=set())
        def __call__(self, event=START): # START / STOP
            def decorator(handler):
                def wrapper(id):
                    return handler()
                # If @app.thread() is called twice for 
                # the same handler, register it only once.
                if not (event, handler) in self.handlers:
                    self.handlers.add((event, handler))
                    cp.engine.subscribe(event + "_thread", wrapper)
                return handler
            return decorator

    @property
    def rate(self, name="rate"):
        """ Yields a thread-safe connection to the app's RateLimit db.
        """
        if not hasattr(g, name): setattr(g, name, RateLimit(name=self._rate))
        return getattr(g, name)

    def bind(self, name="db"):
        """ The @app.bind(name) decorator binds the given function to a keyword argument
            that can be used with @app.route() handlers.
            The return value is stored thread-safe in app.thread.[name] & g.[name].
            The return value is available in handlers as a keyword argument [name].
        """
        # This is useful for multi-threaded database connections:
        # >>>
        # >>> @app.bind("db")
        # >>> def db():
        # >>>     return Database("products.db")
        # >>>
        # >>> @app.route("/products")
        # >>> def products(id, db=None):
        # >>>     return db.execute("select * from products where id=?", (id,))
        def decorator(handler):
            return self.thread(START)(lambda: setattr(g, name, handler()))
        return decorator
    
    @property
    def cached(self):
        """ The @app.cached decorator caches the return value of the given handler.
            This is useful if the handler is computationally expensive,
            and often called with the same arguments (e.g., recursion).
        """
        def decorator(handler):
            def wrapper(*args, **kwargs):
                # Cache return value for given arguments.
                k = (handler, cPickle.dumps(args), cPickle.dumps(kwargs))
                if k not in self._cache:
                    self._cache[k] = handler(*args, **kwargs)
                return self._cache[k]
            return wrapper
        return decorator
        
    memoize = cached
    
    def task(self, interval=MINUTE):
        """ The @app.task(interval) decorator will call the given function repeatedly (in a thread).
            For example, this can be used to commit a Database.batch periodically,
            instead of executing and committing to a Database during each request.
        """
        def decorator(handler):
            _, _, args, kwargs = define(handler)
            def wrapper():
                # Bind data from @app.thread(START) or @app.set().
                m = cp.process.plugins.ThreadManager(cp.engine)
                m.acquire_thread()
                # If there is an app.thread.db connection,
                # pass it as a keyword argument named "db".
                return handler(**dict((k, v) for k, v in g.items() if k in kwargs))
            p = cp.process.plugins.BackgroundTask(interval, wrapper)
            p.start()
            return handler
        return decorator

    def redirect(path, code=303):
        """ Redirects the server to another route handler path 
            (or to another server for absolute URL's).
        """
        raise HTTPRedirect(path, int(code))

    def run(self, host=LOCALHOST, port=8080, threads=30, queue=20, timeout=10, sessions=False, embedded=False, debug=True):
        """ Starts the server.
            Static content (e.g., "g/img.jpg") is served from the App.static subfolder (e.g., "static/g").
            With threads=10, the server can handle up to 10 concurrent requests.
            With queue=10, the server will queue up to 10 waiting requests.
            With debug=False, starts a production server.
            With embedded=True, runs behind Apache mod_wsgi.
        """
        # Do nothing if the app is running.
        if self._up:
            return
        self._host = str(host)
        self._port = int(port)
        self._up   = True
        # Production environment disables errors.
        if debug is False: 
            cp.config.update({"environment": "production"})
        # Embedded environment (mod_wsgi) disables errors & signal handlers.
        if embedded is True: 
            cp.config.update({"environment": "embedded"})
        # Global configuration.
        # If more concurrent requests are made than can be queued / handled,
        # the server will time out and a "connection reset by peer" occurs.
        # Note: SQLite cannot handle many concurrent writes (e.g., UPDATE).
        else:
            cp.config.update({
                "server.socket_host"       : self._host,
                "server.socket_port"       : self._port,
                "server.socket_timeout"    : max(1, timeout),
                "server.socket_queue_size" : max(1, queue),
                "server.thread_pool"       : max(1, threads),
                "server.thread_pool_max"   : -1
            })
        # Static content is served from the /static subfolder, 
        # e.g., <img src="g/cat.jpg" /> refers to "/static/g/cat.jpg".
        self._app = cp.tree.mount(self, "/", 
            config={"/": {
                "tools.staticdir.on"       : self.static is not None,
                "tools.staticdir.dir"      : self.static,
                "tools.sessions.on"        : sessions
        }})
        # Relative root = project path.
        os.chdir(self._path)
        # With mod_wsgi, stdout is restriced.
        if embedded:
            sys.stdout = sys.stderr
        else:
            atexit.register(self.stop)
            cp.engine.start()
            cp.engine.block()
        
    def stop(self):
        """ Stops the server (registered with atexit).
        """
        try:
            atexit._exithandlers.remove((self.stop, (), {}))
        except:
            pass
        cp.engine.exit()
        sys.stdout = sys.__stdout__
        self._host = None
        self._port = None
        self._app  = None
        self._up   = False
    
    def __call__(self, *args, **kwargs):
        # Called when deployed with mod_wsgi.
        if self._app is not None:
            return self._app(*args, **kwargs)
        raise ApplicationError, "application not running"
        
App = Application

#---------------------------------------------------------------------------------------------------
# Apache + mod_wsgi installation notes (thanks to Frederik De Bleser).
# The APP placeholder is the URL of your app, e.g., pattern.emrg.be.
# 
# 1) Create a DNS-record for APP, which maps the url to your server's IP-address.
#
# 2) sudo apt-get install apache2
#    sudo apt-get install libapache2-mod-wsgi
#
# 3) sudo mkdir -p /www/APP/static
#    sudo mkdir -p /www/APP/log
#
# 4) sudo nano /etc/apache2/sites-available/APP
#    > <VirtualHost *:80>
#    >     ServerName APP
#    >     DocumentRoot /www/APP/static
#    >     CustomLog /www/APP/logs/access.log combined
#    >     ErrorLog /www/APP/logs/error.log
#    >     WSGIScriptAlias / /www/APP/app.py
#    >     WSGIDaemonProcess APP processes=1 threads=x
#    >     WSGIProcessGroup APP
#    > </VirtualHost>
#
# 5) sudo nano /www/APP/app.py
#    > from pattern.server import App
#    > from pattern.text import sentiment
#    >
#    > app = application = App() # mod_wsgi app must be available as "application"!
#    >
#    > @app.route("/api/1/sentiment", limit=100, time=HOUR, key=lambda data: app.request.ip)
#    > def api_sentiment(q=None, lang="en"):
#    >     return {"polarity": sentiment(q, language=lang)[0]}
#    >
#    > app.run(embedded=True)
#
# 6) sudo a2ensite APP
#    sudo apache2ctl configtest
#    sudo service apache2 restart
#
# 7) Try: http://APP/api/1/sentiment?q=marvelously+extravagant&lang=en

#---------------------------------------------------------------------------------------------------

def redirect(path, code=303):
    """ Redirects the server to another route handler path 
        (or to another server for absolute URL's).
    """
    raise HTTPRedirect(path, int(code))

#---------------------------------------------------------------------------------------------------

def static(path, root=None, mimetype=None):
    """ Returns the contents of the file at the given absolute path.
        To serve relative paths from the app folder, use root=app.path.
    """
    p = os.path.join(root or "", path)
    p = os.path.realpath(p)
    return cp.lib.static.serve_file(p, content_type=mimetype)

#---------------------------------------------------------------------------------------------------
# http://cherrypy.readthedocs.org/en/latest/progguide/extending/customtools.html

def _register(event, handler):
    """ Registers the given event handler (e.g., "on_end_request").
    """
    k = handler.__name__
    setattr(cp.tools, k, cp.Tool(event, handler))
    cp.config.update({"tools.%s.on" % k: True})

def _request_start(): 
    # Register request start time.
    cp.request.time = time.time()
    
def _request_end():
    #print time.time() - cp.request.time
    pass
    
_register("on_start_resource", _request_start)
_register("on_end_request", _request_end)

#### TEMPLATE ######################################################################################
# A template is a HTML-file with placeholders, which can be variable names or Python source code.
# Based on: http://davidbau.com/archives/2011/09/09/python_templating_with_stringfunction.html

_MARKUP = [
    r"\$[_a-z][\w]*",     # $var
    r"\$\{[_a-z][\w]*\}", # ${var}iable
    r"\<\%=.*?\%\>",      # <%= var + 1 %>
    r"\<\%.*?\%\>",       # <% print(var) %>
    r"\<\%[^\n]*?"        # SyntaxError (no closing tag)
]

# <% if x in y: %> ... <% end if %>
# <% for x in y: %> ... <% end for %>
_MARKUP.insert(0, r"\<\% if (.*?) : \%\>(.*)\<\% end if \%\>") # No "elif", "else" yet.
_MARKUP.insert(1, r"\<\% for (.*?) in (.*?) : \%\>(.*)\<\% end for \%\>")

_MARKUP = (p.replace(" ", r"\s*") for p in _MARKUP)
_MARKUP = "(%s)" % "|".join(_MARKUP)
_MARKUP = re.compile(_MARKUP, re.I | re.S | re.M)

class Template(object):
    
    _cache = {}
    
    def __init__(self, path, root=None, cached=True):
        """ A template with placeholders and/or source code loaded from the given string or path.
            Placeholders that start with $ are replaced with keyword arguments in Template.render().
            Source code enclosed in <?= var + 100 ?> is executed with eval().
            Source code enclosed in <? write(var) ?> is executed with exec().
        """
        p = os.path.join(root or "", path)
        k = hash(p)
        b = k in Template._cache
        # Caching enabled + template already cached.
        if cached is True and b is True:
            a = Template._cache[k]
        # Caching disabled / template not yet cached.
        if cached is False or b is False:
            a = "".join(static(p, mimetype="text/html")) if os.path.exists(p) else path
            a = self._compile(a)
        # Caching enabled + template not yet cached.
        if cached is True and b is False:
            a = Template._cache.setdefault(k, a)
        self._compiled = a

    def _escape(self, s):
        """ Returns a string with no leading indentation and escaped newlines.
        """
        # Used in Template._compile() with eval() and exec().
        s = s.replace("\n", "\\n")
        s = textwrap.dedent(s)
        return s
        
    def _encode(self, v, indent=""):
        """ Returns the given value as a string (empty string for None).
        """
        # Used in Template._render().
        v = "%s" % (v if v is not None else "")
        v = v.replace("\n", "\n" + indent) if indent else v
        return v

    def _dict(self, k="", v=[]):
        """ Returns a dictionary of keys k and values v, where k is a string.
            Used in Template._render() with <for> blocks.
        """
        # For example: "<% for $i, $x in enumerate([1, 2, 3]): %>",
        # "$i, $x" is mapped to {"i": 0, "x": 1}, {"i": 1, "x": 2}, ...
        # Nested tuples are not supported (e.g., "($i, ($k, $v))").
        k = [k.strip("$ ") for k in k.strip("()").split(",")]
        return dict(zip(k, v if len(k) > 1 else [v]))

    def _compile(self, string):
        """ Returns the template string as a (type, value, indent) list,
            where type is either <str>, <arg>, <if>, <for>, <eval> or <exec>.
            With <eval> and <exec>, value is a compiled code object
            that can be executed with eval() or exec() respectively.
        """
        a = []
        i = 0
        for m in _MARKUP.finditer(string):
            s = m.group(1)
            j = m.start(1)
            n = string[:j].count("\n")      # line number
            w = re.compile(r"(^|\n)(.*?)$") # line indent
            w = re.search(w, string[:j]) 
            w = re.sub(r"[^\t]", " ", string[w.start(2):j])
            if i != j:
                a.append(("<str>", string[i:j], ""))
            # $$escaped
            if s.startswith("$") and j > 0 and string[j-1] == "$":
                a.append(("<str>", s, ""))
            # ${var}iable
            elif s.startswith("${") and s.endswith("}"):
                a.append(("<arg>", s[2:-1], w))
            # $var
            elif s.startswith("$"):
                a.append(("<arg>", s[1:], w))
            # <% if x in y: %> ... <% end if %>
            elif s.startswith("<%") and m.group(2):
                a.append(("<if>", (m.group(2), self._compile(m.group(3).lstrip("\n"))), w))
            # <% for x in y: %> ... <% end for %>
            elif s.startswith("<%") and m.group(4):
                a.append(("<for>", (m.group(4), m.group(5), self._compile(m.group(6).lstrip("\n"))), w))
            # <%= var + 1 %>
            elif s.startswith("<%=") and s.endswith("%>"):
                a.append(("<eval>", compile("\n"*n + self._escape(s[3:-2]), "<string>", "eval"), w))
            # <% print(var) %>
            elif s.startswith("<%") and s.endswith("%>"):
                a.append(("<exec>", compile("\n"*n + self._escape(s[2:-2]), "<string>", "exec"), w))
            else:
                raise SyntaxError, "template has no end tag for '%s' (line %s)" % (s, n+1)
            i = m.end(1)
        a.append(("<str>", string[i:], ""))
        return a
        
    def _render(self, compiled, *args, **kwargs):
        """ Returns the rendered string as an iterator.
            Replaces template placeholders with keyword arguments (if any).
            Replaces source code with the return value of eval() or exec().
        """
        k = {}
        for d in args:
            k.update(d)
        k.update(kwargs)
        k["template"] = template
        indent = kwargs.pop("indent", False)
        for cmd, v, w in compiled:
            if indent is False:
                w = ""
            if cmd is None:
                continue
            elif cmd == "<str>":
                yield self._encode(v, w)
            elif cmd == "<arg>":
                yield self._encode(k.get(v, "$" + v), w)
            elif cmd == "<if>":
                yield "".join(self._render(v[1], k)) if eval(v[0]) else ""
            elif cmd == "<for>":
                yield "".join(["".join(self._render(v[2], k, self._dict(v[0], i))) for i in eval(v[1], k)])
            elif cmd == "<eval>":
                yield self._encode(eval(v, k), w)
            elif cmd == "<exec>":
                o = cStringIO.StringIO()
                k["write"] = o.write # Code blocks use write() for output.
                exec(v, k)
                yield self._encode(o.getvalue(), w)
                del k["write"]
                o.close()
                
    def render(self, *args, **kwargs):
        """ Returns the rendered template as a string.
            Replaces template placeholders with keyword arguments (if any).
            Replaces source code with the return value of eval() or exec().
            The keyword arguments are used as namespace for eval() and exec().
            For example, source code in Template.render(re=re) has access to the regex library.
            Multiple dictionaries can be given, e.g.,
            Template.render(globals(), locals(), foo="bar").
            Code blocks in <? ?> can use write() and template().
        """
        return "".join(self._render(self._compiled, *args, **kwargs))

def template(string, *args, **kwargs):
    """ Returns the rendered template as a string.
    """
    if hasattr(string, "render"):
        return string.render(*args, **kwargs)
    root, cached = (
        kwargs.pop("root", None),
        kwargs.pop("cached", None))
    if root is None and len(args) > 0 and isinstance(args[0], basestring):
        root = args[0]
        args = args[1:]
    return Template(string, root, cached).render(*args, **kwargs)

#s = """
#<html>
#<head>
#    <title>$title</title>
#</head>
#<body>
#<% for $i, $name in enumerate(names): %>
#    <b><%= i+1 %>) Hello $name!</b>
#<% end for %>
#</body>
#</html>
#"""
#
#print template(s.strip(), title="test", names=["Tom", "Walter"])

#### HTML ##########################################################################################
# Useful HTML generators.

class HTML:
    
    def _attrs(self, **kwargs):
        """ Returns a string of HTML element attributes.
            Use "css" for the CSS classname (since "class" is a reserved word).
        """
        a = []
        if "id" in kwargs:
            a.append("id=\"%s\"" % kwargs.pop("id"))
        if "name" in kwargs:
            a.append("name=\"%s\"" % kwargs.pop("name"))
        if "css" in kwargs:
            a.append("class=\"%s\"" % kwargs.pop("css"))
        for k, v in kwargs.items():
            a.append("%s=\"%s\"" % (k, v))
        return (" " + " ".join(a)).rstrip()
    
    def div(self, content, **attributes):
        """ Returns a string with a HTML <div> with the given content.
        """
        return "<div%s>\n\t%s\n</div>\n" % (self._attrs(**attributes), content)
        
    def span(self, content, **attributes):
        """ Returns a string with a HTML <span> with the given content.
        """
        return "<span%s>\n\t%s\n</span>\n" % (self._attrs(**attributes), content)
    
    def table(self, rows=[], headers=[], striped=True, **attributes):
        """ Returns a string with a HTML <table> for the given list,
            where each item is a list of values.
            With striped=True, generates <tr class="even|odd">.
            With striped=True and headers, generates <td class="header[i]">.
        """
        h = list(headers)
        r = list(rows) if not h else [h] + list(rows)
        a = ["<table%s>\n" % self._attrs(**attributes)]
        if h:
            a.append("\t<colgroup>\n")
            a.extend("\t\t<col class=\"%s\">\n" % v for v in h)
            a.append("\t</colgroup>\n")
        for i, row in enumerate(r):
            a.append("\t<tr%s>\n" % (" class=\"%s\"" % ("odd", "even")[i % 2] if striped else ""))
            for j, v in enumerate(row):
                if i == 0 and h:
                    a.append("\t\t<th>%s</th>\n" % v)
                else:
                    a.append("\t\t<td>%s</td>\n" % v)
            a.append("\t</tr>\n")
        a.append("</table>\n")
        return "".join(a)
        
    def select(self, options={}, selected=None, **attributes):
        """ Returns a string with a HTML <select> for the given dictionary,
            where each dict item is an <option value="key">value</option>.
        """
        a = ["<select%s>\n" % self._attrs(**attributes)]
        for k, v in sorted(options.items()):
            if k == selected:
                a.append("\t<option value=\"%s\" selected>%s</option>\n" % (k, v))
            else:
                a.append("\t<option value=\"%s\">%s</option>\n" % (k, v))
        a.append("</select>\n")
        return "".join(a)
        
    dropdown = select        

html = HTML()

####################################################################################################

#from pattern.en import sentiment
#
#app = App()
#app.rate[("1234", "/api/en/sentiment")] = (100, MINUTE)
#
#@app.bind("db")
#def db():
#    return Database("log.db", schema="create table if not exists `log` (q text);")
#
## http://localhost:8080/whatever
#@app.route("/")
#def index(*path, **data):
#    return "%s<br>%s" % (path, data.get("db"))
#
## http://localhost:8080/api/en/sentiment?q=awesome
##@app.route("/api/en/sentiment", limit=True)
#@app.route("/api/en/sentiment", limit=10, time=MINUTE, key=lambda data: app.request.ip)
#def nl_sentiment(q="", db=None):
#    polarity, subjectivity = sentiment(q)
#    db.batch.execute("insert into `log` (q) values (?);", (q,))
#    return {"polarity": polarity}
#    
#@app.task(interval=MINUTE)
#def log(db=None):
#    print "committing log..."
#    db.batch.commit()
#
#@app.error((403, 404, 429, 500, 503))
#def error(e):
#    return "<h2>%s</h2><pre>%s</pre>" % (e.status, e.traceback)
#
#app.run(debug=True, threads=100, queue=50)
