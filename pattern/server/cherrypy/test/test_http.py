"""Tests for managing HTTP issues (malformed requests, etc)."""

import errno
import mimetypes
import socket
import sys

import cherrypy
from cherrypy._cpcompat import HTTPConnection, HTTPSConnection, ntob, py3k


def encode_multipart_formdata(files):
    """Return (content_type, body) ready for httplib.HTTP instance.

    files: a sequence of (name, filename, value) tuples for multipart uploads.
    """
    BOUNDARY = '________ThIs_Is_tHe_bouNdaRY_$'
    L = []
    for key, filename, value in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' %
                 (key, filename))
        ct = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        L.append('Content-Type: %s' % ct)
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = '\r\n'.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body




from cherrypy.test import helper

class HTTPTests(helper.CPWebCase):

    def setup_server():
        class Root:
            def index(self, *args, **kwargs):
                return "Hello world!"
            index.exposed = True

            def no_body(self, *args, **kwargs):
                return "Hello world!"
            no_body.exposed = True
            no_body._cp_config = {'request.process_request_body': False}

            def post_multipart(self, file):
                """Return a summary ("a * 65536\nb * 65536") of the uploaded file."""
                contents = file.file.read()
                summary = []
                curchar = None
                count = 0
                for c in contents:
                    if c == curchar:
                        count += 1
                    else:
                        if count:
                            if py3k: curchar = chr(curchar)
                            summary.append("%s * %d" % (curchar, count))
                        count = 1
                        curchar = c
                if count:
                    if py3k: curchar = chr(curchar)
                    summary.append("%s * %d" % (curchar, count))
                return ", ".join(summary)
            post_multipart.exposed = True

        cherrypy.tree.mount(Root())
        cherrypy.config.update({'server.max_request_body_size': 30000000})
    setup_server = staticmethod(setup_server)

    def test_no_content_length(self):
        # "The presence of a message-body in a request is signaled by the
        # inclusion of a Content-Length or Transfer-Encoding header field in
        # the request's message-headers."
        #
        # Send a message with neither header and no body. Even though
        # the request is of method POST, this should be OK because we set
        # request.process_request_body to False for our handler.
        if self.scheme == "https":
            c = HTTPSConnection('%s:%s' % (self.interface(), self.PORT))
        else:
            c = HTTPConnection('%s:%s' % (self.interface(), self.PORT))
        c.request("POST", "/no_body")
        response = c.getresponse()
        self.body = response.fp.read()
        self.status = str(response.status)
        self.assertStatus(200)
        self.assertBody(ntob('Hello world!'))

        # Now send a message that has no Content-Length, but does send a body.
        # Verify that CP times out the socket and responds
        # with 411 Length Required.
        if self.scheme == "https":
            c = HTTPSConnection('%s:%s' % (self.interface(), self.PORT))
        else:
            c = HTTPConnection('%s:%s' % (self.interface(), self.PORT))
        c.request("POST", "/")
        response = c.getresponse()
        self.body = response.fp.read()
        self.status = str(response.status)
        self.assertStatus(411)

    def test_post_multipart(self):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        # generate file contents for a large post
        contents = "".join([c * 65536 for c in alphabet])

        # encode as multipart form data
        files=[('file', 'file.txt', contents)]
        content_type, body = encode_multipart_formdata(files)
        body = body.encode('Latin-1')

        # post file
        if self.scheme == 'https':
            c = HTTPSConnection('%s:%s' % (self.interface(), self.PORT))
        else:
            c = HTTPConnection('%s:%s' % (self.interface(), self.PORT))
        c.putrequest('POST', '/post_multipart')
        c.putheader('Content-Type', content_type)
        c.putheader('Content-Length', str(len(body)))
        c.endheaders()
        c.send(body)

        response = c.getresponse()
        self.body = response.fp.read()
        self.status = str(response.status)
        self.assertStatus(200)
        self.assertBody(", ".join(["%s * 65536" % c for c in alphabet]))

    def test_malformed_request_line(self):
        if getattr(cherrypy.server, "using_apache", False):
            return self.skip("skipped due to known Apache differences...")

        # Test missing version in Request-Line
        if self.scheme == 'https':
            c = HTTPSConnection('%s:%s' % (self.interface(), self.PORT))
        else:
            c = HTTPConnection('%s:%s' % (self.interface(), self.PORT))
        c._output(ntob('GET /'))
        c._send_output()
        if hasattr(c, 'strict'):
            response = c.response_class(c.sock, strict=c.strict, method='GET')
        else:
            # Python 3.2 removed the 'strict' feature, saying:
            # "http.client now always assumes HTTP/1.x compliant servers."
            response = c.response_class(c.sock, method='GET')
        response.begin()
        self.assertEqual(response.status, 400)
        self.assertEqual(response.fp.read(22), ntob("Malformed Request-Line"))
        c.close()

    def test_malformed_header(self):
        if self.scheme == 'https':
            c = HTTPSConnection('%s:%s' % (self.interface(), self.PORT))
        else:
            c = HTTPConnection('%s:%s' % (self.interface(), self.PORT))
        c.putrequest('GET', '/')
        c.putheader('Content-Type', 'text/plain')
        # See http://www.cherrypy.org/ticket/941
        c._output(ntob('Re, 1.2.3.4#015#012'))
        c.endheaders()

        response = c.getresponse()
        self.status = str(response.status)
        self.assertStatus(400)
        self.body = response.fp.read(20)
        self.assertBody("Illegal header line.")

    def test_http_over_https(self):
        if self.scheme != 'https':
            return self.skip("skipped (not running HTTPS)... ")

        # Try connecting without SSL.
        conn = HTTPConnection('%s:%s' % (self.interface(), self.PORT))
        conn.putrequest("GET", "/", skip_host=True)
        conn.putheader("Host", self.HOST)
        conn.endheaders()
        response = conn.response_class(conn.sock, method="GET")
        try:
            response.begin()
            self.assertEqual(response.status, 400)
            self.body = response.read()
            self.assertBody("The client sent a plain HTTP request, but this "
                            "server only speaks HTTPS on this port.")
        except socket.error:
            e = sys.exc_info()[1]
            # "Connection reset by peer" is also acceptable.
            if e.errno != errno.ECONNRESET:
                raise

    def test_garbage_in(self):
        # Connect without SSL regardless of server.scheme
        c = HTTPConnection('%s:%s' % (self.interface(), self.PORT))
        c._output(ntob('gjkgjklsgjklsgjkljklsg'))
        c._send_output()
        response = c.response_class(c.sock, method="GET")
        try:
            response.begin()
            self.assertEqual(response.status, 400)
            self.assertEqual(response.fp.read(22), ntob("Malformed Request-Line"))
            c.close()
        except socket.error:
            e = sys.exc_info()[1]
            # "Connection reset by peer" is also acceptable.
            if e.errno != errno.ECONNRESET:
                raise

