"""Basic tests for the CherryPy core: request handling."""

import os
localDir = os.path.dirname(__file__)

import cherrypy
from cherrypy._cpcompat import ntob, ntou, py3k

access_log = os.path.join(localDir, "access.log")
error_log = os.path.join(localDir, "error.log")

# Some unicode strings.
tartaros = ntou('\u03a4\u1f71\u03c1\u03c4\u03b1\u03c1\u03bf\u03c2', 'escape')
erebos = ntou('\u0388\u03c1\u03b5\u03b2\u03bf\u03c2.com', 'escape')


def setup_server():
    class Root:

        def index(self):
            return "hello"
        index.exposed = True

        def uni_code(self):
            cherrypy.request.login = tartaros
            cherrypy.request.remote.name = erebos
        uni_code.exposed = True

        def slashes(self):
            cherrypy.request.request_line = r'GET /slashed\path HTTP/1.1'
        slashes.exposed = True

        def whitespace(self):
            # User-Agent = "User-Agent" ":" 1*( product | comment )
            # comment    = "(" *( ctext | quoted-pair | comment ) ")"
            # ctext      = <any TEXT excluding "(" and ")">
            # TEXT       = <any OCTET except CTLs, but including LWS>
            # LWS        = [CRLF] 1*( SP | HT )
            cherrypy.request.headers['User-Agent'] = 'Browzuh (1.0\r\n\t\t.3)'
        whitespace.exposed = True

        def as_string(self):
            return "content"
        as_string.exposed = True

        def as_yield(self):
            yield "content"
        as_yield.exposed = True

        def error(self):
            raise ValueError()
        error.exposed = True
        error._cp_config = {'tools.log_tracebacks.on': True}

    root = Root()


    cherrypy.config.update({'log.error_file': error_log,
                            'log.access_file': access_log,
                            })
    cherrypy.tree.mount(root)



from cherrypy.test import helper, logtest

class AccessLogTests(helper.CPWebCase, logtest.LogCase):
    setup_server = staticmethod(setup_server)

    logfile = access_log

    def testNormalReturn(self):
        self.markLog()
        self.getPage("/as_string",
                     headers=[('Referer', 'http://www.cherrypy.org/'),
                              ('User-Agent', 'Mozilla/5.0')])
        self.assertBody('content')
        self.assertStatus(200)

        intro = '%s - - [' % self.interface()

        self.assertLog(-1, intro)

        if [k for k, v in self.headers if k.lower() == 'content-length']:
            self.assertLog(-1, '] "GET %s/as_string HTTP/1.1" 200 7 '
                           '"http://www.cherrypy.org/" "Mozilla/5.0"'
                           % self.prefix())
        else:
            self.assertLog(-1, '] "GET %s/as_string HTTP/1.1" 200 - '
                           '"http://www.cherrypy.org/" "Mozilla/5.0"'
                           % self.prefix())

    def testNormalYield(self):
        self.markLog()
        self.getPage("/as_yield")
        self.assertBody('content')
        self.assertStatus(200)

        intro = '%s - - [' % self.interface()

        self.assertLog(-1, intro)
        if [k for k, v in self.headers if k.lower() == 'content-length']:
            self.assertLog(-1, '] "GET %s/as_yield HTTP/1.1" 200 7 "" ""' %
                           self.prefix())
        else:
            self.assertLog(-1, '] "GET %s/as_yield HTTP/1.1" 200 - "" ""'
                           % self.prefix())

    def testEscapedOutput(self):
        # Test unicode in access log pieces.
        self.markLog()
        self.getPage("/uni_code")
        self.assertStatus(200)
        if py3k:
            # The repr of a bytestring in py3k includes a b'' prefix
            self.assertLog(-1, repr(tartaros.encode('utf8'))[2:-1])
        else:
            self.assertLog(-1, repr(tartaros.encode('utf8'))[1:-1])
        # Test the erebos value. Included inline for your enlightenment.
        # Note the 'r' prefix--those backslashes are literals.
        self.assertLog(-1, r'\xce\x88\xcf\x81\xce\xb5\xce\xb2\xce\xbf\xcf\x82')

        # Test backslashes in output.
        self.markLog()
        self.getPage("/slashes")
        self.assertStatus(200)
        if py3k:
            self.assertLog(-1, ntob('"GET /slashed\\path HTTP/1.1"'))
        else:
            self.assertLog(-1, r'"GET /slashed\\path HTTP/1.1"')

        # Test whitespace in output.
        self.markLog()
        self.getPage("/whitespace")
        self.assertStatus(200)
        # Again, note the 'r' prefix.
        self.assertLog(-1, r'"Browzuh (1.0\r\n\t\t.3)"')


class ErrorLogTests(helper.CPWebCase, logtest.LogCase):
    setup_server = staticmethod(setup_server)

    logfile = error_log

    def testTracebacks(self):
        # Test that tracebacks get written to the error log.
        self.markLog()
        ignore = helper.webtest.ignored_exceptions
        ignore.append(ValueError)
        try:
            self.getPage("/error")
            self.assertInBody("raise ValueError()")
            self.assertLog(0, 'HTTP Traceback (most recent call last):')
            self.assertLog(-3, 'raise ValueError()')
        finally:
            ignore.pop()

