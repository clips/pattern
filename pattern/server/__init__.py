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
import random
import hashlib
import base64
import string
import StringIO
import textwrap
import types
import inspect
import threading
import collections
import sqlite3 as sqlite
import cherrypy; cp=cherrypy

try: import json # Python 2.6+
except:
    try: from pattern.web import json # simplejson
    except:
        json = None

# Folder that contains the script that imports pattern.server.
SCRIPT = os.path.dirname(os.path.abspath(__main__.__file__))

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
            f = f[0]   # guess...
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
# A simple wrapper for SQLite databases.

DatabaseError = sqlite.DatabaseError

class Row(dict):
    
    def __init__(self, cursor, row):
        """ Row as dictionary.
        """
        d = cursor.description
        dict.__init__(self, ((d[i][0], v) for i, v in enumerate(row)))

class Database(object):
    
    def __init__(self, name, schema="", factory=Row, timeout=10.0): # or sqlite.Row
        """ Creates and opens the SQLite database with the given name.
            Optionally, the given SQL schema string is executed (once).
        """
        if isinstance(name, Database):
            name, factory = name.name, name.factory if factory == Row else factory
        if os.path.exists(name):
            schema = ";"
        self._name = name
        self._factory = factory
        self._connection = sqlite.connect(name, timeout=timeout)
        self._connection.row_factory = factory
        self._connection.executescript(schema)
        self._connection.commit()
    
    @property
    def name(self):
        """ Yields the path to the database file.
        """
        return self._name
    
    @property
    def connection(self):
        """ Yields the sqlite3.Connection object.
        """
        return self._connection
    
    def execute(self, sql, values=(), first=False, commit=True):
        """ Executes the given SQL query string and returns an iterator of rows.
            With first=True, returns the first row.
        """
        try:
            r = self._connection.execute(sql, values)
            if commit: 
                self._connection.commit()
        except DatabaseError, e:
            # "OperationalError: database is locked" means that 
            # SQLite is receiving too many concurrent write ops.
            # A write operation locks the entire database;
            # other threaded connections may time out waiting.
            # In this case you can raise Database(timeout=10),
            # lower Application.run(threads=10) or switch to MySQL or Redis.
            self._connection.rollback()
            raise e
        return r.fetchone() if first else r
        
    def commit(self):
        """ Commits changes (pending insert/update/delete queries).
        """
        self._connection.commit()
        
    def rollback(self):
        """ Discard changes since the last commit.
        """
        self._conncection.rollback()
        
    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def __repr__(self):
        return "Database(name=%s)" % repr(self._name)

    def __del__(self):
        try:
            self._connection.commit()
            self._connection.close()
            self._connection = None
        except:
            pass
    
    @property
    def batch(self):
        k = self._name
        return Database._batch.setdefault(k, DatabaseTransaction(k))

    _batch = {} # Shared across instances.

#--- DATABASE TRANSACTION BUFFER -------------------------------------------------------------------

class DatabaseTransaction:
    
    def __init__(self, name, timeout=10.0):
        """ Database.batch.execute() stores given the SQL query in RAM memory, across threads.
            Database.batch.commit() commits all buffered queries.
            This can be combined with @app.task() to periodically write batches to the database
            (instead of writing on each request).
        """
        self._name   = name
        self._queue  = []
        self.timeout = timeout
    
    def execute(self, sql, values=()):
        self._queue.append((sql, values))
        
    def commit(self):
        q, self._queue = self._queue, []
        if q:
            try:
                connection = sqlite.connect(self._name, timeout=self.timeout)
                for sql, v in q:
                    connection.execute(sql, v)
                connection.commit()
            except DatabaseError, e:
                connection.rollback(); raise e # Data in q will be lost.
            finally:
                connection.close()
            
    def rollback(self):
        self._queue = []
        
    def __len__(self):
        return len(self._queue)

#### RATE LIMITING #################################################################################
# With @app.route(path, throttle=True), the decorated URL path handler function calls Throttle().

_THROTTLE_CACHE = {} # RAM cache of request counts.
_THROTTLE_LOCK  = threading.RLock()

MINUTE, HOUR, DAY = 60., 60*60., 60*60*24.

class ThrottleError(Exception):
    pass

class ThrottleLimitExceeded(ThrottleError):
    pass

class ThrottleForbidden(ThrottleError):
    pass

class Throttle(Database):
    
    def __init__(self, name="throttle.db", timeout=10.0):
        """ A database for rate limiting API requests.
            It manages a table with (key, path, limit, time) entries.
            It grants each key a rate (number of requests / time) for a URL path.
            It keeps track of the number of requests in local memory (i.e., RAM).
            If Throttle()() is called with the optional limit and time arguments,
            unknown keys are temporarily granted this rate.
        """
        Database.__init__(self, name, 
            schema = (
                "create table if not exists `throttle` ("
                      "`key` text,"    # API key (e.g., ?key="1234").
                     "`path` text,"    # API URL path (e.g., "/api/1/").
                    "`limit` integer," # Maximum number of requests.
                     "`time` float"    # Time frame.
                ");"
                "create index if not exists `throttle1` on throttle(key);"
                "create index if not exists `throttle2` on throttle(path);"
            ), 
            factory = None, 
            timeout = timeout)
        self.load()

    @property
    def cache(self):
        return _THROTTLE_CACHE
        
    @property
    def lock(self):
        return _THROTTLE_LOCK

    @property
    def key(self, pairs=("rA","aZ","gQ","hH","hG","aR","DD")):
        """ Yields a new random key.
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
                for r in self.execute("select * from `throttle`;"):
                    self.cache[(r[0], r[1])] = (0, r[2], r[3], _time.time())
                self._rowcount = len(self.cache)
    
    def set(self, key, path="/", limit=100, time=HOUR):
        """ Sets the rate for the given key and path,
            where limit is the maximum number of requests in the given time (e.g., 100/hour).
        """
        # Update database.
        p  = "/" + path.strip("/")
        q1 = "delete from `throttle` where key=? and path=?;"
        q2 = "insert into `throttle` values (?, ?, ?, ?);"
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
        q = "select * from `throttle` where key=? and path=?;"
        return self.execute(q, (key, p), first=True, commit=False)
        
    def __setitem__(self, (key, path), (limit, time)):
        return self.set(key, path, limit, time)
        
    def __getitem__(self, (key, path)):
        return self.get(key, path)

    def __contains__(self, key, path="%"):
        """ Returns True if the given key exists (for the given path).
        """
        q = "select * from `throttle` where key=? and path like ?;"
        return self.execute(q, (key, path), first=True, commit=False) is not None

    def __call__(self, key, path="/", limit=None, time=None, reset=100000):
        """ Increases the (cached) request count by 1 for the given key and path.
            If the request count exceeds its limit, raises ThrottleLimitExceeded.
            If the optional limit and time are given, unknown keys (!= None) 
            are given this rate limit - as long as the cache exists in memory.
            Otherwise a ThrottleForbidden is raised.
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
            if r is None:
                raise ThrottleForbidden
            # Limit reached within time frame (raise error).
            elif r[0] >= r[1] and r[2] > t - r[3]:
                raise ThrottleLimitExceeded
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
        dict.__setitem__(self, p, (handler, define(handler)[2:]))
        
    def __call__(self, path, **data):
        """ Calls the handler function for the given URL path.
            If no handler is found, raises a RouteError.
            If a base handler is found (e.g., "/api" for "/api/1/en"),
            calls the handler with arguments (e.g., handler("1", "en")).
        """
        if not isinstance(path, tuple):
            path = path.strip("/").split("/") # ("api", "1", "en")
        n = len(path)
        for i in xrange(n + 1):
            p = "/" + "/".join(path[:n-i])    # "/api/1/en", "/api/1", "/api", ...
            p = p.lower()
            if p in self:
                # Call the handler function and return its response.
                (handler, (args, kwargs)), path = self[p], path[n-i:]
                i = len(path)
                j = len(args) if args is not True else i
                if i != j:
                    continue
                # Handler takes path, but no query data.
                if not kwargs:
                    return handler(*path)
                # Handler takes path and all query data.
                if kwargs is True:
                    return handler(*path, **data)
                # Handler takes path and some query data.
                return handler(*path, **dict((k, v) for k, v in data.items() if k in kwargs))
        # No handler.
        raise RouteError

#### APPLICATION ###################################################################################

#--- APPLICATION ERRORS & REQUESTS -----------------------------------------------------------------

class HTTPRedirect(Exception):
    
    def __init__(self, url):
        """ A HTTP redirect raised in an @app.route() handler.
        """
        self.url = url
    
    def __repr__(self):
        return "HTTPRedirect(url=%s)" % repr(self.url)

class HTTPError(Exception):
    
    def __init__(self, code, status="", message="", traceback=None):
        """ A HTTP error passed to an @app.error handler (or raised in a route handler).
        """
        self.code      = code
        self.status    = status
        self.message   = message
        self.traceback = traceback or None
        
    def __repr__(self):
        return "HTTPError(code=%s)" % repr(self.code)

class HTTPRequest(object):
    
    def __init__(self, app, ip, path="/", method="get", data={}, headers={}):
        """ A Request object with metadata returned from app.request.
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
        self.__dict__["_data"] = data or threading.local()
        self.__dict__.update(kwargs) # Global in every thread.
        
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

# Alias for app.thread (Flask-style):
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
    #
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

LOCALHOST = "127.0.0.1"

START = "start"
STOP  = "stop"

class Application(object):
    
    def __init__(self, name=None, static="static/", throttle="throttle.db"):
        """ A web app served by a WSGI-server that starts with App.run().
            @App.route(path) defines a URL path handler.
            @App.error(code) defines a HTTP error handler.
        """
        # Create Throttle db in the app folder:
        throttle = os.path.join(SCRIPT, throttle)
        self._name     = name         # App name.
        self._host     = None         # Server host, see App.run().
        self._port     = None         # Server port, see App.run().
        self._up       = False        # True if server is up & running.
        self._static   = static       # Static content folder.
        self._throttle = throttle     # Throttle db name, see also App.route(throttle=True).
        self.router    = Router()     # Router object, maps URL paths to handlers.
        self.thread    = App.Thread() # Thread-safe dictionary.
        
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
    
    @property
    def path(self):
        """ Yields the absolute path to the folder containing the app.
        """
        return SCRIPT
        
    @property
    def static(self):
        """ Yields the absolute path to the folder with static content.
        """
        return os.path.join(self.path, self._static)

    @property
    def session(self):
        """ Yields the dictionary of session data.
        """
        return cp.session
        
    @property
    def request(self):
        """ Yields a Request object with metadata
            (IP address, request path, query data and headers).
        """
        r = cp.request # Deep copy (ensure garbage colletion).
        return HTTPRequest(
                app = self, 
                 ip = r.remote.ip, 
               path = r.path_info, 
             method = r.method, 
               data = r.params, 
            headers = r.headers)
        
    @property
    def response(self):
        """ Yields a Response object with metadata
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
            cp.response.headers['Content-Type'] = "application/json"
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
        try:
            v = self.router(path, **data)
        except RouteError:
            raise cp.HTTPError(404)         # 404 Not Found
        except ThrottleForbidden:
            raise cp.HTTPError(403)         # 403 Forbidden
        except ThrottleLimitExceeded:
            raise cp.HTTPError(429)         # 429 Too Many Requests
        except DatabaseError, e:
            raise cp.HTTPError(503, str(e)) # 503 Service Unavailable
        except HTTPRedirect, e:
            raise cp.HTTPRedirect(e.url)
        except HTTPError, e:
            raise cp.HTTPError(e.code)
        v = self._cast(v)
        #print self.elapsed
        return v
        
    def route(self, path, throttle=False, limit=None, time=None, key=lambda data: data.get("key"), reset=100000):
        """ The @app.route(path) decorator defines the handler function for the given path.
            The function can take arguments (path) and keyword arguments (query data), e.g.,
            if no handler exists for URL "/api/1/en", but a handler exists for URL "/api/1",
            this handler will be called with 1 argument: "en".
            It returns a string, a generator or a dictionary (which is parsed to a JSON-string).
        """
        _a = (key, limit, time, reset) # Avoid trouble with key=lambda inside define().
        def decorator(handler):
            def throttled(handler):
                # With @app.route(path, throttle=True), rate limiting is applied.
                # The handler function is wrapped in a function that first calls
                # Throttle(key, path, limit, time) before calling the handler.
                # By default, a query parameter "key" is expected.
                # If the key is known, apply rate limiting (429 Too Many Requests).
                # If the key is unknown or None, deny access (403 Forbidden).
                # If the key is unknown and a default limit and time are given,
                # add the key and grant the given credentials, e.g.:
                # @app.route(path, limit=100, time=HOUR, key=lambda data: app.request.ip).
                @self.thread(START)
                def connect():
                    g.throttle = Throttle(name=self._throttle)
                def wrapper(*args, **kwargs):
                    r = cp.request
                    self = r.app.root
                    self.throttle(
                          key = _a[0](r.params),
                         path = "/" + r.path_info.strip("/"),
                        limit = _a[1],  # Default limit for unknown keys.
                         time = _a[2],  # Default time for unknown keys.
                        reset = _a[3]   # Threshold for clearing cache.
                    )
                    return handler(*args, **kwargs)
                return wrapper
            if throttle is True or (limit is not None and time is not None):
                handler = throttled(handler)
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
                return handler(HTTPError(int(status.split(" ")[0]), status, message, traceback))
            if code in ("*", None):
                cp.config.update({"error_page.default": wrapper})
            elif isinstance(code, (int, basestring)):
                cp.config.update({"error_page.%s" % code: wrapper})
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
                if not hasattr(template, "render"):
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
    def throttle(self, name="throttle"):
        """ Yields a thread-safe connection to the app's Throttle (used for rate limiting).
        """
        if not hasattr(g, name): setattr(g, name, Throttle(name=self._throttle))
        return getattr(g, name)

    def set(self, name="db"):
        """ The @app.set(name) decorator defines the function that spawns a database connection.
            The database connection is stored thread-safe in app.thread.[name] & g.[name].
            The database connection is available in handlers as a keyword argument [name].
        """
        def decorator(handler):
            return self.thread(START)(lambda: setattr(g, name, handler()))
        return decorator
    
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

    def redirect(path):
        """ Redirects the server to another route handler path 
            (or to another server for absolute URL's).
        """
        raise HTTPRedirect(path)

    def run(self, host=LOCALHOST, port=8080, threads=30, queue=20, timeout=10, sessions=False, debug=True):
        """ Starts the server and blocks until the server stops.
            Static content (e.g., "g/img.jpg") is served from the given subfolder (e.g., "static/g").
            With threads=10, the server can handle up to 10 concurrent requests.
            With queue=10, the server will queue up to 10 waiting requests.
            With debug=False, starts a production server.
        """
        self._host = str(host)
        self._port = int(port)
        self._up   = True
        if not debug: cp.config.update({
            # Production environment disables errors.
            "environment": "production"
        })
        cp.config.update({
            # Global configuration.
            # If more concurrent requests are made than can be queued / handled,
            # the server will time out and a "connection reset by peer" occurs.
            # Note: SQLite cannot handle many concurrent writes (e.g., UPDATE).
            "server.socket_host"       : self._host,
            "server.socket_port"       : self._port,
            "server.socket_timeout"    : max(1, timeout),
            "server.socket_queue_size" : max(1, queue),
            "server.thread_pool"       : max(1, threads),
            "server.thread_pool_max"   : -1
        })
        cp.tree.mount(self, "/", config={"/": {
            # Static content is served from the /static subfolder, 
            # e.g., <img src="g/cat.jpg" /> refers to "/static/g/cat.jpg".
            "tools.staticdir.on"       : True,
            "tools.staticdir.dir"      : self.static,
            "tools.sessions.on"        : sessions
        }})
        cp.engine.start()
        cp.engine.block()
        self._host = None
        self._port = None
        self._up   = False

App = Application

#---------------------------------------------------------------------------------------------------

def redirect(path):
    """ Redirects the server to another route handler path 
        (or to another server for absolute URL's).
    """
    raise HTTPRedirect(path)

#---------------------------------------------------------------------------------------------------

def static(path, root=None, mimetype=None):
    """ Returns the contents of the file at the given absolute path.
        To serve relative paths from the app folder, use root=app.path.
    """
    p = os.path.join(root or "", path)
    p = os.path.abspath(p)
    return cp.lib.static.serve_file(p, content_type=mimetype)

#---------------------------------------------------------------------------------------------------
# http://cherrypy.readthedocs.org/en/latest/progguide/extending/customtools.html

def _register(event, handler):
    """ Registers the given event handler.
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
# Based on: http://davidbau.com/archives/2011/09/09/python_templating_with_stringfunction.html

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
        
    def _format(self, v, indent=""):
        """ Returns the given value as a string (empty string for None).
        """
        v = "%s" % (v if v is not None else "")
        v = v.replace("\n", "\n" + indent)
        return v

    def _compile(self, string):
        """ Returns the template string as a (type, value, indent) list,
            where type is either <str>, <arg>, <eval> or <exec>.
            With <eval> and <exec>, value is a compiled code object
            that can be executed with eval() or exec() respectively.
        """
        r = r"(%s|%s|%s|%s|%s)" % (
            r"\$[_a-z][\w]*",     # $var
            r"\$\{[_a-z][\w]*\}", # ${var}iable
            r"\<\%\=.*?\%\>",     # <%= var + 1 %>
            r"\<\%.*?\%\>",       # <% print(var) %>
            r"\<\%[^\n]*?"
        )
        a = []
        i = 0
        for m in re.finditer(r, string, re.I | re.M):
            s = m.group(1)
            j = m.start(1)
            n = string[:j].count("\n")      # line number
            p = re.compile(r"(^|\n)(.*?)$") # line indent
            p = re.search(p, string[:j]) 
            p = re.sub(r"[^\t]", " ", string[p.start(2):j])
            if i != j:
                a.append(("<str>", string[i:j], ""))
            if s.startswith("$") and j > 0 and string[j-1] == "$":
                a.append(("<str>", s, ""))
            elif s.startswith("${") and s.endswith("}"):
                a.append(("<arg>", s[2:-1], p))
            elif s.startswith("$"):
                a.append(("<arg>", s[1:], p))
            elif s.startswith("<%=") and s.endswith("%>"):
                a.append(("<eval>", compile("\n"*n + textwrap.dedent(s[3:-2]), "<string>", "eval"), p))
            elif s.startswith("<%") and s.endswith("%>"):
                a.append(("<exec>", compile("\n"*n + textwrap.dedent(s[2:-2]), "<string>", "exec"), p))
            else:
                raise SyntaxError, "template has no end tag for '%s' (line %s)" % (s, n+1)
            i = m.end(1)
        a.append(("<str>", string[i:], ""))
        return a
        
    def _render(self, *args, **kwargs):
        """ Returns the rendered string as an iterator.
            Replaces template placeholders with keyword arguments (if any).
            Replaces source code with the return value of eval() or exec().
        """
        k = {}
        for d in args:
            k.update(d)
        k.update(kwargs)
        for cmd, v, p in self._compiled:
            if cmd is None:
                continue
            elif cmd == "<str>":
                yield v
            elif cmd == "<arg>":
                yield self._format(k.get(v, "$" + v), p)
            elif cmd == "<eval>":
                yield self._format(eval(v, k), p)
            elif cmd == "<exec>":
                o = StringIO.StringIO()
                k["write"] = o.write # Code blocks use write() for output.
                exec(v, k)
                yield self._format(o.getvalue(), p)
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
        """
        return "".join(self._render(*args, **kwargs))

def template(string, *args, **kwargs):
    """ Returns the rendered template as a string.
    """
    root, cached = (
        kwargs.pop("root", None),
        kwargs.pop("cached", None)
    )
    if root is None and len(args) > 0 and isinstance(args[0], basestring):
        root = args[0]
        args = args[1:]
    if hasattr(string, "render"):
        return string
    return Template(string, root, cached).render(*args, **kwargs)

####################################################################################################

# TODO: if you already have CherryPy installed, remove the one bundled in Pattern,
# otherwise it will try to start two servers.

####################################################################################################

#from pattern.en import sentiment
#
#app = App()
##app.throttle[("1234", "/api/en/sentiment")] = (5, MINUTE)
#
#@app.set("db")
#def db():
#    return Database("log.db", schema="create table if not exists `log` (q text);")
#
## http://localhost:8080/whatever
#@app.route("/")
#def index(*path, **data):
#    return "%s<br>%s" % (path, data.get("db"))
#
## http://localhost:8080/api/en/sentiment?q=awesome
##@app.route("/api/en/sentiment", throttle=True)
#@app.route("/api/en/sentiment", throttle=True, limit=10, time=MINUTE, key=lambda data: app.request.ip)
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
