"""Wrapper for mod_python, for use as a CherryPy HTTP server when testing.

To autostart modpython, the "apache" executable or script must be
on your system path, or you must override the global APACHE_PATH.
On some platforms, "apache" may be called "apachectl" or "apache2ctl"--
create a symlink to them if needed.

If you wish to test the WSGI interface instead of our _cpmodpy interface,
you also need the 'modpython_gateway' module at:
http://projects.amor.org/misc/wiki/ModPythonGateway


KNOWN BUGS
==========

1. Apache processes Range headers automatically; CherryPy's truncated
    output is then truncated again by Apache. See test_core.testRanges.
    This was worked around in http://www.cherrypy.org/changeset/1319.
2. Apache does not allow custom HTTP methods like CONNECT as per the spec.
    See test_core.testHTTPMethods.
3. Max request header and body settings do not work with Apache.
4. Apache replaces status "reason phrases" automatically. For example,
    CherryPy may set "304 Not modified" but Apache will write out
    "304 Not Modified" (capital "M").
5. Apache does not allow custom error codes as per the spec.
6. Apache (or perhaps modpython, or modpython_gateway) unquotes %xx in the
    Request-URI too early.
7. mod_python will not read request bodies which use the "chunked"
    transfer-coding (it passes REQUEST_CHUNKED_ERROR to ap_setup_client_block
    instead of REQUEST_CHUNKED_DECHUNK, see Apache2's http_protocol.c and
    mod_python's requestobject.c).
8. Apache will output a "Content-Length: 0" response header even if there's
    no response entity body. This isn't really a bug; it just differs from
    the CherryPy default.
"""

import os
curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))
import re
import time

from cherrypy.test import helper


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


APACHE_PATH = "httpd"
CONF_PATH = "test_mp.conf"

conf_modpython_gateway = """
# Apache2 server conf file for testing CherryPy with modpython_gateway.

ServerName 127.0.0.1
DocumentRoot "/"
Listen %(port)s
LoadModule python_module modules/mod_python.so

SetHandler python-program
PythonFixupHandler cherrypy.test.modpy::wsgisetup
PythonOption testmod %(modulename)s
PythonHandler modpython_gateway::handler
PythonOption wsgi.application cherrypy::tree
PythonOption socket_host %(host)s
PythonDebug On
"""

conf_cpmodpy = """
# Apache2 server conf file for testing CherryPy with _cpmodpy.

ServerName 127.0.0.1
DocumentRoot "/"
Listen %(port)s
LoadModule python_module modules/mod_python.so

SetHandler python-program
PythonFixupHandler cherrypy.test.modpy::cpmodpysetup
PythonHandler cherrypy._cpmodpy::handler
PythonOption cherrypy.setup cherrypy.test.%(modulename)s::setup_server
PythonOption socket_host %(host)s
PythonDebug On
"""

class ModPythonSupervisor(helper.Supervisor):

    using_apache = True
    using_wsgi = False
    template = None

    def __str__(self):
        return "ModPython Server on %s:%s" % (self.host, self.port)

    def start(self, modulename):
        mpconf = CONF_PATH
        if not os.path.isabs(mpconf):
            mpconf = os.path.join(curdir, mpconf)

        f = open(mpconf, 'wb')
        try:
            f.write(self.template %
                    {'port': self.port, 'modulename': modulename,
                     'host': self.host})
        finally:
            f.close()

        result = read_process(APACHE_PATH, "-k start -f %s" % mpconf)
        if result:
            print(result)

    def stop(self):
        """Gracefully shutdown a server that is serving forever."""
        read_process(APACHE_PATH, "-k stop")


loaded = False
def wsgisetup(req):
    global loaded
    if not loaded:
        loaded = True
        options = req.get_options()

        import cherrypy
        cherrypy.config.update({
            "log.error_file": os.path.join(curdir, "test.log"),
            "environment": "test_suite",
            "server.socket_host": options['socket_host'],
            })

        modname = options['testmod']
        mod = __import__(modname, globals(), locals(), [''])
        mod.setup_server()

        cherrypy.server.unsubscribe()
        cherrypy.engine.start()
    from mod_python import apache
    return apache.OK


def cpmodpysetup(req):
    global loaded
    if not loaded:
        loaded = True
        options = req.get_options()

        import cherrypy
        cherrypy.config.update({
            "log.error_file": os.path.join(curdir, "test.log"),
            "environment": "test_suite",
            "server.socket_host": options['socket_host'],
            })
    from mod_python import apache
    return apache.OK

