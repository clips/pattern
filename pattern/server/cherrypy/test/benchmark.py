"""CherryPy Benchmark Tool

    Usage:
        benchmark.py --null --notests --help --cpmodpy --modpython --ab=path --apache=path

    --null:        use a null Request object (to bench the HTTP server only)
    --notests:     start the server but do not run the tests; this allows
                   you to check the tested pages with a browser
    --help:        show this help message
    --cpmodpy:     run tests via apache on 54583 (with the builtin _cpmodpy)
    --modpython:   run tests via apache on 54583 (with modpython_gateway)
    --ab=path:     Use the ab script/executable at 'path' (see below)
    --apache=path: Use the apache script/exe at 'path' (see below)

    To run the benchmarks, the Apache Benchmark tool "ab" must either be on
    your system path, or specified via the --ab=path option.

    To run the modpython tests, the "apache" executable or script must be
    on your system path, or provided via the --apache=path option. On some
    platforms, "apache" may be called "apachectl" or "apache2ctl"--create
    a symlink to them if needed.
"""

import getopt
import os
curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))

import re
import sys
import time
import traceback

import cherrypy
from cherrypy._cpcompat import ntob
from cherrypy import _cperror, _cpmodpy
from cherrypy.lib import httputil


AB_PATH = ""
APACHE_PATH = "apache"
SCRIPT_NAME = "/cpbench/users/rdelon/apps/blog"

__all__ = ['ABSession', 'Root', 'print_report',
           'run_standard_benchmarks', 'safe_threads',
           'size_report', 'startup', 'thread_report',
           ]

size_cache = {}

class Root:

    def index(self):
        return """<html>
<head>
    <title>CherryPy Benchmark</title>
</head>
<body>
    <ul>
        <li><a href="hello">Hello, world! (14 byte dynamic)</a></li>
        <li><a href="static/index.html">Static file (14 bytes static)</a></li>
        <li><form action="sizer">Response of length:
            <input type='text' name='size' value='10' /></form>
        </li>
    </ul>
</body>
</html>"""
    index.exposed = True

    def hello(self):
        return "Hello, world\r\n"
    hello.exposed = True

    def sizer(self, size):
        resp = size_cache.get(size, None)
        if resp is None:
            size_cache[size] = resp = "X" * int(size)
        return resp
    sizer.exposed = True


cherrypy.config.update({
    'log.error.file': '',
    'environment': 'production',
    'server.socket_host': '127.0.0.1',
    'server.socket_port': 54583,
    'server.max_request_header_size': 0,
    'server.max_request_body_size': 0,
    'engine.deadlock_poll_freq': 0,
    })

# Cheat mode on ;)
del cherrypy.config['tools.log_tracebacks.on']
del cherrypy.config['tools.log_headers.on']
del cherrypy.config['tools.trailing_slash.on']

appconf = {
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'static',
        'tools.staticdir.root': curdir,
        },
    }
app = cherrypy.tree.mount(Root(), SCRIPT_NAME, appconf)


class NullRequest:
    """A null HTTP request class, returning 200 and an empty body."""

    def __init__(self, local, remote, scheme="http"):
        pass

    def close(self):
        pass

    def run(self, method, path, query_string, protocol, headers, rfile):
        cherrypy.response.status = "200 OK"
        cherrypy.response.header_list = [("Content-Type", 'text/html'),
                                         ("Server", "Null CherryPy"),
                                         ("Date", httputil.HTTPDate()),
                                         ("Content-Length", "0"),
                                         ]
        cherrypy.response.body = [""]
        return cherrypy.response


class NullResponse:
    pass


class ABSession:
    """A session of 'ab', the Apache HTTP server benchmarking tool.

Example output from ab:

This is ApacheBench, Version 2.0.40-dev <$Revision: 1.121.2.1 $> apache-2.0
Copyright (c) 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Copyright (c) 1998-2002 The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Completed 100 requests
Completed 200 requests
Completed 300 requests
Completed 400 requests
Completed 500 requests
Completed 600 requests
Completed 700 requests
Completed 800 requests
Completed 900 requests


Server Software:        CherryPy/3.1beta
Server Hostname:        127.0.0.1
Server Port:            54583

Document Path:          /static/index.html
Document Length:        14 bytes

Concurrency Level:      10
Time taken for tests:   9.643867 seconds
Complete requests:      1000
Failed requests:        0
Write errors:           0
Total transferred:      189000 bytes
HTML transferred:       14000 bytes
Requests per second:    103.69 [#/sec] (mean)
Time per request:       96.439 [ms] (mean)
Time per request:       9.644 [ms] (mean, across all concurrent requests)
Transfer rate:          19.08 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   2.9      0      10
Processing:    20   94   7.3     90     130
Waiting:        0   43  28.1     40     100
Total:         20   95   7.3    100     130

Percentage of the requests served within a certain time (ms)
  50%    100
  66%    100
  75%    100
  80%    100
  90%    100
  95%    100
  98%    100
  99%    110
 100%    130 (longest request)
Finished 1000 requests
"""

    parse_patterns = [('complete_requests', 'Completed',
                       ntob(r'^Complete requests:\s*(\d+)')),
                      ('failed_requests', 'Failed',
                       ntob(r'^Failed requests:\s*(\d+)')),
                      ('requests_per_second', 'req/sec',
                       ntob(r'^Requests per second:\s*([0-9.]+)')),
                      ('time_per_request_concurrent', 'msec/req',
                       ntob(r'^Time per request:\s*([0-9.]+).*concurrent requests\)$')),
                      ('transfer_rate', 'KB/sec',
                       ntob(r'^Transfer rate:\s*([0-9.]+)')),
                      ]

    def __init__(self, path=SCRIPT_NAME + "/hello", requests=1000, concurrency=10):
        self.path = path
        self.requests = requests
        self.concurrency = concurrency

    def args(self):
        port = cherrypy.server.socket_port
        assert self.concurrency > 0
        assert self.requests > 0
        # Don't use "localhost".
        # Cf http://mail.python.org/pipermail/python-win32/2008-March/007050.html
        return ("-k -n %s -c %s http://127.0.0.1:%s%s" %
                (self.requests, self.concurrency, port, self.path))

    def run(self):
        # Parse output of ab, setting attributes on self
        try:
            self.output = _cpmodpy.read_process(AB_PATH or "ab", self.args())
        except:
            print(_cperror.format_exc())
            raise

        for attr, name, pattern in self.parse_patterns:
            val = re.search(pattern, self.output, re.MULTILINE)
            if val:
                val = val.group(1)
                setattr(self, attr, val)
            else:
                setattr(self, attr, None)


safe_threads = (25, 50, 100, 200, 400)
if sys.platform in ("win32",):
    # For some reason, ab crashes with > 50 threads on my Win2k laptop.
    safe_threads = (10, 20, 30, 40, 50)


def thread_report(path=SCRIPT_NAME + "/hello", concurrency=safe_threads):
    sess = ABSession(path)
    attrs, names, patterns = list(zip(*sess.parse_patterns))
    avg = dict.fromkeys(attrs, 0.0)

    yield ('threads',) + names
    for c in concurrency:
        sess.concurrency = c
        sess.run()
        row = [c]
        for attr in attrs:
            val = getattr(sess, attr)
            if val is None:
                print(sess.output)
                row = None
                break
            val = float(val)
            avg[attr] += float(val)
            row.append(val)
        if row:
            yield row

    # Add a row of averages.
    yield ["Average"] + [str(avg[attr] / len(concurrency)) for attr in attrs]

def size_report(sizes=(10, 100, 1000, 10000, 100000, 100000000),
               concurrency=50):
    sess = ABSession(concurrency=concurrency)
    attrs, names, patterns = list(zip(*sess.parse_patterns))
    yield ('bytes',) + names
    for sz in sizes:
        sess.path = "%s/sizer?size=%s" % (SCRIPT_NAME, sz)
        sess.run()
        yield [sz] + [getattr(sess, attr) for attr in attrs]

def print_report(rows):
    for row in rows:
        print("")
        for i, val in enumerate(row):
            sys.stdout.write(str(val).rjust(10) + " | ")
    print("")


def run_standard_benchmarks():
    print("")
    print("Client Thread Report (1000 requests, 14 byte response body, "
           "%s server threads):" % cherrypy.server.thread_pool)
    print_report(thread_report())

    print("")
    print("Client Thread Report (1000 requests, 14 bytes via staticdir, "
           "%s server threads):" % cherrypy.server.thread_pool)
    print_report(thread_report("%s/static/index.html" % SCRIPT_NAME))

    print("")
    print("Size Report (1000 requests, 50 client threads, "
           "%s server threads):" % cherrypy.server.thread_pool)
    print_report(size_report())


#                         modpython and other WSGI                         #

def startup_modpython(req=None):
    """Start the CherryPy app server in 'serverless' mode (for modpython/WSGI)."""
    if cherrypy.engine.state == cherrypy._cpengine.STOPPED:
        if req:
            if "nullreq" in req.get_options():
                cherrypy.engine.request_class = NullRequest
                cherrypy.engine.response_class = NullResponse
            ab_opt = req.get_options().get("ab", "")
            if ab_opt:
                global AB_PATH
                AB_PATH = ab_opt
        cherrypy.engine.start()
    if cherrypy.engine.state == cherrypy._cpengine.STARTING:
        cherrypy.engine.wait()
    return 0 # apache.OK


def run_modpython(use_wsgi=False):
    print("Starting mod_python...")
    pyopts = []

    # Pass the null and ab=path options through Apache
    if "--null" in opts:
        pyopts.append(("nullreq", ""))

    if "--ab" in opts:
        pyopts.append(("ab", opts["--ab"]))

    s = _cpmodpy.ModPythonServer
    if use_wsgi:
        pyopts.append(("wsgi.application", "cherrypy::tree"))
        pyopts.append(("wsgi.startup", "cherrypy.test.benchmark::startup_modpython"))
        handler = "modpython_gateway::handler"
        s = s(port=54583, opts=pyopts, apache_path=APACHE_PATH, handler=handler)
    else:
        pyopts.append(("cherrypy.setup", "cherrypy.test.benchmark::startup_modpython"))
        s = s(port=54583, opts=pyopts, apache_path=APACHE_PATH)

    try:
        s.start()
        run()
    finally:
        s.stop()



if __name__ == '__main__':
    longopts = ['cpmodpy', 'modpython', 'null', 'notests',
                'help', 'ab=', 'apache=']
    try:
        switches, args = getopt.getopt(sys.argv[1:], "", longopts)
        opts = dict(switches)
    except getopt.GetoptError:
        print(__doc__)
        sys.exit(2)

    if "--help" in opts:
        print(__doc__)
        sys.exit(0)

    if "--ab" in opts:
        AB_PATH = opts['--ab']

    if "--notests" in opts:
        # Return without stopping the server, so that the pages
        # can be tested from a standard web browser.
        def run():
            port = cherrypy.server.socket_port
            print("You may now open http://127.0.0.1:%s%s/" %
                   (port, SCRIPT_NAME))

            if "--null" in opts:
                print("Using null Request object")
    else:
        def run():
            end = time.time() - start
            print("Started in %s seconds" % end)
            if "--null" in opts:
                print("\nUsing null Request object")
            try:
                try:
                    run_standard_benchmarks()
                except:
                    print(_cperror.format_exc())
                    raise
            finally:
                cherrypy.engine.exit()

    print("Starting CherryPy app server...")

    class NullWriter(object):
        """Suppresses the printing of socket errors."""
        def write(self, data):
            pass
    sys.stderr = NullWriter()

    start = time.time()

    if "--cpmodpy" in opts:
        run_modpython()
    elif "--modpython" in opts:
        run_modpython(use_wsgi=True)
    else:
        if "--null" in opts:
            cherrypy.server.request_class = NullRequest
            cherrypy.server.response_class = NullResponse

        cherrypy.engine.start_with_callback(run)
        cherrypy.engine.block()
