from cherrypy._cpcompat import HTTPConnection, HTTPSConnection, ntob
from cherrypy._cpcompat import BytesIO

import os
curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))
has_space_filepath = os.path.join(curdir, 'static', 'has space.html')
bigfile_filepath = os.path.join(curdir, "static", "bigfile.log")
BIGFILE_SIZE = 1024 * 1024

import cherrypy
from cherrypy.lib import static
from cherrypy.test import helper


class StaticTest(helper.CPWebCase):

    def setup_server():
        if not os.path.exists(has_space_filepath):
            open(has_space_filepath, 'wb').write(ntob('Hello, world\r\n'))
        if not os.path.exists(bigfile_filepath):
            open(bigfile_filepath, 'wb').write(ntob("x" * BIGFILE_SIZE))

        class Root:

            def bigfile(self):
                from cherrypy.lib import static
                self.f = static.serve_file(bigfile_filepath)
                return self.f
            bigfile.exposed = True
            bigfile._cp_config = {'response.stream': True}

            def tell(self):
                if self.f.input.closed:
                    return ''
                return repr(self.f.input.tell()).rstrip('L')
            tell.exposed = True

            def fileobj(self):
                f = open(os.path.join(curdir, 'style.css'), 'rb')
                return static.serve_fileobj(f, content_type='text/css')
            fileobj.exposed = True

            def bytesio(self):
                f = BytesIO(ntob('Fee\nfie\nfo\nfum'))
                return static.serve_fileobj(f, content_type='text/plain')
            bytesio.exposed = True

        class Static:

            def index(self):
                return 'You want the Baron? You can have the Baron!'
            index.exposed = True

            def dynamic(self):
                return "This is a DYNAMIC page"
            dynamic.exposed = True


        root = Root()
        root.static = Static()

        rootconf = {
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': 'static',
                'tools.staticdir.root': curdir,
            },
            '/style.css': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': os.path.join(curdir, 'style.css'),
            },
            '/docroot': {
                'tools.staticdir.on': True,
                'tools.staticdir.root': curdir,
                'tools.staticdir.dir': 'static',
                'tools.staticdir.index': 'index.html',
            },
            '/error': {
                'tools.staticdir.on': True,
                'request.show_tracebacks': True,
            },
            }
        rootApp = cherrypy.Application(root)
        rootApp.merge(rootconf)

        test_app_conf = {
            '/test': {
                'tools.staticdir.index': 'index.html',
                'tools.staticdir.on': True,
                'tools.staticdir.root': curdir,
                'tools.staticdir.dir': 'static',
                },
            }
        testApp = cherrypy.Application(Static())
        testApp.merge(test_app_conf)

        vhost = cherrypy._cpwsgi.VirtualHost(rootApp, {'virt.net': testApp})
        cherrypy.tree.graft(vhost)
    setup_server = staticmethod(setup_server)


    def teardown_server():
        for f in (has_space_filepath, bigfile_filepath):
            if os.path.exists(f):
                try:
                    os.unlink(f)
                except:
                    pass
    teardown_server = staticmethod(teardown_server)


    def testStatic(self):
        self.getPage("/static/index.html")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/html')
        self.assertBody('Hello, world\r\n')

        # Using a staticdir.root value in a subdir...
        self.getPage("/docroot/index.html")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/html')
        self.assertBody('Hello, world\r\n')

        # Check a filename with spaces in it
        self.getPage("/static/has%20space.html")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/html')
        self.assertBody('Hello, world\r\n')

        self.getPage("/style.css")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/css')
        # Note: The body should be exactly 'Dummy stylesheet\n', but
        #   unfortunately some tools such as WinZip sometimes turn \n
        #   into \r\n on Windows when extracting the CherryPy tarball so
        #   we just check the content
        self.assertMatchesBody('^Dummy stylesheet')

    def test_fallthrough(self):
        # Test that NotFound will then try dynamic handlers (see [878]).
        self.getPage("/static/dynamic")
        self.assertBody("This is a DYNAMIC page")

        # Check a directory via fall-through to dynamic handler.
        self.getPage("/static/")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/html;charset=utf-8')
        self.assertBody('You want the Baron? You can have the Baron!')

    def test_index(self):
        # Check a directory via "staticdir.index".
        self.getPage("/docroot/")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/html')
        self.assertBody('Hello, world\r\n')
        # The same page should be returned even if redirected.
        self.getPage("/docroot")
        self.assertStatus(301)
        self.assertHeader('Location', '%s/docroot/' % self.base())
        self.assertMatchesBody("This resource .* <a href='%s/docroot/'>"
                               "%s/docroot/</a>." % (self.base(), self.base()))

    def test_config_errors(self):
        # Check that we get an error if no .file or .dir
        self.getPage("/error/thing.html")
        self.assertErrorPage(500)
        self.assertMatchesBody(ntob("TypeError: staticdir\(\) takes at least 2 "
                                    "(positional )?arguments \(0 given\)"))

    def test_security(self):
        # Test up-level security
        self.getPage("/static/../../test/style.css")
        self.assertStatus((400, 403))

    def test_modif(self):
        # Test modified-since on a reasonably-large file
        self.getPage("/static/dirback.jpg")
        self.assertStatus("200 OK")
        lastmod = ""
        for k, v in self.headers:
            if k == 'Last-Modified':
                lastmod = v
        ims = ("If-Modified-Since", lastmod)
        self.getPage("/static/dirback.jpg", headers=[ims])
        self.assertStatus(304)
        self.assertNoHeader("Content-Type")
        self.assertNoHeader("Content-Length")
        self.assertNoHeader("Content-Disposition")
        self.assertBody("")

    def test_755_vhost(self):
        self.getPage("/test/", [('Host', 'virt.net')])
        self.assertStatus(200)
        self.getPage("/test", [('Host', 'virt.net')])
        self.assertStatus(301)
        self.assertHeader('Location', self.scheme + '://virt.net/test/')

    def test_serve_fileobj(self):
        self.getPage("/fileobj")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/css;charset=utf-8')
        self.assertMatchesBody('^Dummy stylesheet')

    def test_serve_bytesio(self):
        self.getPage("/bytesio")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/plain;charset=utf-8')
        self.assertHeader('Content-Length', 14)
        self.assertMatchesBody('Fee\nfie\nfo\nfum')

    def test_file_stream(self):
        if cherrypy.server.protocol_version != "HTTP/1.1":
            return self.skip()

        self.PROTOCOL = "HTTP/1.1"

        # Make an initial request
        self.persistent = True
        conn = self.HTTP_CONN
        conn.putrequest("GET", "/bigfile", skip_host=True)
        conn.putheader("Host", self.HOST)
        conn.endheaders()
        response = conn.response_class(conn.sock, method="GET")
        response.begin()
        self.assertEqual(response.status, 200)

        body = ntob('')
        remaining = BIGFILE_SIZE
        while remaining > 0:
            data = response.fp.read(65536)
            if not data:
                break
            body += data
            remaining -= len(data)

            if self.scheme == "https":
                newconn = HTTPSConnection
            else:
                newconn = HTTPConnection
            s, h, b = helper.webtest.openURL(
                ntob("/tell"), headers=[], host=self.HOST, port=self.PORT,
                http_conn=newconn)
            if not b:
                # The file was closed on the server.
                tell_position = BIGFILE_SIZE
            else:
                tell_position = int(b)

            expected = len(body)
            if tell_position >= BIGFILE_SIZE:
                # We can't exactly control how much content the server asks for.
                # Fudge it by only checking the first half of the reads.
                if expected < (BIGFILE_SIZE / 2):
                    self.fail(
                        "The file should have advanced to position %r, but has "
                        "already advanced to the end of the file. It may not be "
                        "streamed as intended, or at the wrong chunk size (64k)" %
                        expected)
            elif tell_position < expected:
                self.fail(
                    "The file should have advanced to position %r, but has "
                    "only advanced to position %r. It may not be streamed "
                    "as intended, or at the wrong chunk size (65536)" %
                    (expected, tell_position))

        if body != ntob("x" * BIGFILE_SIZE):
            self.fail("Body != 'x' * %d. Got %r instead (%d bytes)." %
                      (BIGFILE_SIZE, body[:50], len(body)))
        conn.close()

    def test_file_stream_deadlock(self):
        if cherrypy.server.protocol_version != "HTTP/1.1":
            return self.skip()

        self.PROTOCOL = "HTTP/1.1"

        # Make an initial request but abort early.
        self.persistent = True
        conn = self.HTTP_CONN
        conn.putrequest("GET", "/bigfile", skip_host=True)
        conn.putheader("Host", self.HOST)
        conn.endheaders()
        response = conn.response_class(conn.sock, method="GET")
        response.begin()
        self.assertEqual(response.status, 200)
        body = response.fp.read(65536)
        if body != ntob("x" * len(body)):
            self.fail("Body != 'x' * %d. Got %r instead (%d bytes)." %
                      (65536, body[:50], len(body)))
        response.close()
        conn.close()

        # Make a second request, which should fetch the whole file.
        self.persistent = False
        self.getPage("/bigfile")
        if self.body != ntob("x" * BIGFILE_SIZE):
            self.fail("Body != 'x' * %d. Got %r instead (%d bytes)." %
                      (BIGFILE_SIZE, self.body[:50], len(body)))
