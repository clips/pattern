"""Wrapper for mod_wsgi, for use as a CherryPy HTTP server.

To autostart modwsgi, the "apache" executable or script must be
on your system path, or you must override the global APACHE_PATH.
On some platforms, "apache" may be called "apachectl" or "apache2ctl"--
create a symlink to them if needed.


KNOWN BUGS
==========

##1. Apache processes Range headers automatically; CherryPy's truncated
##    output is then truncated again by Apache. See test_core.testRanges.
##    This was worked around in http://www.cherrypy.org/changeset/1319.
2. Apache does not allow custom HTTP methods like CONNECT as per the spec.
    See test_core.testHTTPMethods.
3. Max request header and body settings do not work with Apache.
##4. Apache replaces status "reason phrases" automatically. For example,
##    CherryPy may set "304 Not modified" but Apache will write out
##    "304 Not Modified" (capital "M").
##5. Apache does not allow custom error codes as per the spec.
##6. Apache (or perhaps modpython, or modpython_gateway) unquotes %xx in the
##    Request-URI too early.
7. mod_wsgi will not read request bodies which use the "chunked"
    transfer-coding (it passes REQUEST_CHUNKED_ERROR to ap_setup_client_block
    instead of REQUEST_CHUNKED_DECHUNK, see Apache2's http_protocol.c and
    mod_python's requestobject.c).
8. When responding with 204 No Content, mod_wsgi adds a Content-Length
    header for you.
9. When an error is raised, mod_wsgi has no facility for printing a
    traceback as the response content (it's sent to the Apache log instead).
10. Startup and shutdown of Apache when running mod_wsgi seems slow.
"""

import os
curdir = os.path.abspath(os.path.dirname(__file__))
import re
import sys
import time

import cherrypy
from cherrypy.test import helper, webtest


def read_process(cmd, args=""):
    pipein, pipeout = os.popen4("%s %s" % (cmd, args))
    try:
        firstline = pipeout.readline()
        if (re.search(r"(not recognized|No such file|not found)", firstline,
                      re.IGNORECASE)):
            raise IOError('%s must be on your system path.' % cmd)
        output = firstline + pipeout.read()
    finally:
        pipeout.close()
    return output


if sys.platform == 'win32':
    APACHE_PATH = "httpd"
else:
    APACHE_PATH = "apache"

CONF_PATH = "test_mw.conf"

conf_modwsgi = r"""
# Apache2 server conf file for testing CherryPy with modpython_gateway.

ServerName 127.0.0.1
DocumentRoot "/"
Listen %(port)s

AllowEncodedSlashes On
LoadModule rewrite_module modules/mod_rewrite.so
RewriteEngine on
RewriteMap escaping int:escape

LoadModule log_config_module modules/mod_log_config.so
LogFormat "%%h %%l %%u %%t \"%%r\" %%>s %%b \"%%{Referer}i\" \"%%{User-agent}i\"" combined
CustomLog "%(curdir)s/apache.access.log" combined
ErrorLog "%(curdir)s/apache.error.log"
LogLevel debug

LoadModule wsgi_module modules/mod_wsgi.so
LoadModule env_module modules/mod_env.so

WSGIScriptAlias / "%(curdir)s/modwsgi.py"
SetEnv testmod %(testmod)s
"""


class ModWSGISupervisor(helper.Supervisor):
    """Server Controller for ModWSGI and CherryPy."""

    using_apache = True
    using_wsgi = True
    template=conf_modwsgi

    def __str__(self):
        return "ModWSGI Server on %s:%s" % (self.host, self.port)

    def start(self, modulename):
        mpconf = CONF_PATH
        if not os.path.isabs(mpconf):
            mpconf = os.path.join(curdir, mpconf)

        f = open(mpconf, 'wb')
        try:
            output = (self.template %
                      {'port': self.port, 'testmod': modulename,
                       'curdir': curdir})
            f.write(output)
        finally:
            f.close()

        result = read_process(APACHE_PATH, "-k start -f %s" % mpconf)
        if result:
            print(result)

        # Make a request so mod_wsgi starts up our app.
        # If we don't, concurrent initial requests will 404.
        cherrypy._cpserver.wait_for_occupied_port("127.0.0.1", self.port)
        webtest.openURL('/ihopetheresnodefault', port=self.port)
        time.sleep(1)

    def stop(self):
        """Gracefully shutdown a server that is serving forever."""
        read_process(APACHE_PATH, "-k stop")


loaded = False
def application(environ, start_response):
    import cherrypy
    global loaded
    if not loaded:
        loaded = True
        modname = "cherrypy.test." + environ['testmod']
        mod = __import__(modname, globals(), locals(), [''])
        mod.setup_server()

        cherrypy.config.update({
            "log.error_file": os.path.join(curdir, "test.error.log"),
            "log.access_file": os.path.join(curdir, "test.access.log"),
            "environment": "test_suite",
            "engine.SIGHUP": None,
            "engine.SIGTERM": None,
            })
    return cherrypy.tree(environ, start_response)

