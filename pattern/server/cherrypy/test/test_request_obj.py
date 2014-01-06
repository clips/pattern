"""Basic tests for the cherrypy.Request object."""

import os
localDir = os.path.dirname(__file__)
import sys
import types
from cherrypy._cpcompat import IncompleteRead, ntob, ntou, unicodestr

import cherrypy
from cherrypy import _cptools, tools
from cherrypy.lib import httputil

defined_http_methods = ("OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE",
                        "TRACE", "PROPFIND")


#                             Client-side code                             #

from cherrypy.test import helper

class RequestObjectTests(helper.CPWebCase):

    def setup_server():
        class Root:

            def index(self):
                return "hello"
            index.exposed = True

            def scheme(self):
                return cherrypy.request.scheme
            scheme.exposed = True

        root = Root()


        class TestType(type):
            """Metaclass which automatically exposes all functions in each subclass,
            and adds an instance of the subclass as an attribute of root.
            """
            def __init__(cls, name, bases, dct):
                type.__init__(cls, name, bases, dct)
                for value in dct.values():
                    if isinstance(value, types.FunctionType):
                        value.exposed = True
                setattr(root, name.lower(), cls())
        Test = TestType('Test', (object,), {})

        class PathInfo(Test):

            def default(self, *args):
                return cherrypy.request.path_info

        class Params(Test):

            def index(self, thing):
                return repr(thing)

            def ismap(self, x, y):
                return "Coordinates: %s, %s" % (x, y)

            def default(self, *args, **kwargs):
                return "args: %s kwargs: %s" % (args, kwargs)
            default._cp_config = {'request.query_string_encoding': 'latin1'}


        class ParamErrorsCallable(object):
            exposed = True
            def __call__(self):
                return "data"

        class ParamErrors(Test):

            def one_positional(self, param1):
                return "data"
            one_positional.exposed = True

            def one_positional_args(self, param1, *args):
                return "data"
            one_positional_args.exposed = True

            def one_positional_args_kwargs(self, param1, *args, **kwargs):
                return "data"
            one_positional_args_kwargs.exposed = True

            def one_positional_kwargs(self, param1, **kwargs):
                return "data"
            one_positional_kwargs.exposed = True

            def no_positional(self):
                return "data"
            no_positional.exposed = True

            def no_positional_args(self, *args):
                return "data"
            no_positional_args.exposed = True

            def no_positional_args_kwargs(self, *args, **kwargs):
                return "data"
            no_positional_args_kwargs.exposed = True

            def no_positional_kwargs(self, **kwargs):
                return "data"
            no_positional_kwargs.exposed = True

            callable_object = ParamErrorsCallable()

            def raise_type_error(self, **kwargs):
                raise TypeError("Client Error")
            raise_type_error.exposed = True

            def raise_type_error_with_default_param(self, x, y=None):
                return '%d' % 'a' # throw an exception
            raise_type_error_with_default_param.exposed = True

        def callable_error_page(status, **kwargs):
            return "Error %s - Well, I'm very sorry but you haven't paid!" % status


        class Error(Test):

            _cp_config = {'tools.log_tracebacks.on': True,
                          }

            def reason_phrase(self):
                raise cherrypy.HTTPError("410 Gone fishin'")

            def custom(self, err='404'):
                raise cherrypy.HTTPError(int(err), "No, <b>really</b>, not found!")
            custom._cp_config = {'error_page.404': os.path.join(localDir, "static/index.html"),
                                 'error_page.401': callable_error_page,
                                 }

            def custom_default(self):
                return 1 + 'a' # raise an unexpected error
            custom_default._cp_config = {'error_page.default': callable_error_page}

            def noexist(self):
                raise cherrypy.HTTPError(404, "No, <b>really</b>, not found!")
            noexist._cp_config = {'error_page.404': "nonexistent.html"}

            def page_method(self):
                raise ValueError()

            def page_yield(self):
                yield "howdy"
                raise ValueError()

            def page_streamed(self):
                yield "word up"
                raise ValueError()
                yield "very oops"
            page_streamed._cp_config = {"response.stream": True}

            def cause_err_in_finalize(self):
                # Since status must start with an int, this should error.
                cherrypy.response.status = "ZOO OK"
            cause_err_in_finalize._cp_config = {'request.show_tracebacks': False}

            def rethrow(self):
                """Test that an error raised here will be thrown out to the server."""
                raise ValueError()
            rethrow._cp_config = {'request.throw_errors': True}


        class Expect(Test):

            def expectation_failed(self):
                expect = cherrypy.request.headers.elements("Expect")
                if expect and expect[0].value != '100-continue':
                    raise cherrypy.HTTPError(400)
                raise cherrypy.HTTPError(417, 'Expectation Failed')

        class Headers(Test):

            def default(self, headername):
                """Spit back out the value for the requested header."""
                return cherrypy.request.headers[headername]

            def doubledheaders(self):
                # From http://www.cherrypy.org/ticket/165:
                # "header field names should not be case sensitive sayes the rfc.
                # if i set a headerfield in complete lowercase i end up with two
                # header fields, one in lowercase, the other in mixed-case."

                # Set the most common headers
                hMap = cherrypy.response.headers
                hMap['content-type'] = "text/html"
                hMap['content-length'] = 18
                hMap['server'] = 'CherryPy headertest'
                hMap['location'] = ('%s://%s:%s/headers/'
                                    % (cherrypy.request.local.ip,
                                       cherrypy.request.local.port,
                                       cherrypy.request.scheme))

                # Set a rare header for fun
                hMap['Expires'] = 'Thu, 01 Dec 2194 16:00:00 GMT'

                return "double header test"

            def ifmatch(self):
                val = cherrypy.request.headers['If-Match']
                assert isinstance(val, unicodestr)
                cherrypy.response.headers['ETag'] = val
                return val


        class HeaderElements(Test):

            def get_elements(self, headername):
                e = cherrypy.request.headers.elements(headername)
                return "\n".join([unicodestr(x) for x in e])


        class Method(Test):

            def index(self):
                m = cherrypy.request.method
                if m in defined_http_methods or m == "CONNECT":
                    return m

                if m == "LINK":
                    raise cherrypy.HTTPError(405)
                else:
                    raise cherrypy.HTTPError(501)

            def parameterized(self, data):
                return data

            def request_body(self):
                # This should be a file object (temp file),
                # which CP will just pipe back out if we tell it to.
                return cherrypy.request.body

            def reachable(self):
                return "success"

        class Divorce:
            """HTTP Method handlers shouldn't collide with normal method names.
            For example, a GET-handler shouldn't collide with a method named 'get'.

            If you build HTTP method dispatching into CherryPy, rewrite this class
            to use your new dispatch mechanism and make sure that:
                "GET /divorce HTTP/1.1" maps to divorce.index() and
                "GET /divorce/get?ID=13 HTTP/1.1" maps to divorce.get()
            """

            documents = {}

            def index(self):
                yield "<h1>Choose your document</h1>\n"
                yield "<ul>\n"
                for id, contents in self.documents.items():
                    yield ("    <li><a href='/divorce/get?ID=%s'>%s</a>: %s</li>\n"
                           % (id, id, contents))
                yield "</ul>"
            index.exposed = True

            def get(self, ID):
                return ("Divorce document %s: %s" %
                        (ID, self.documents.get(ID, "empty")))
            get.exposed = True

        root.divorce = Divorce()


        class ThreadLocal(Test):

            def index(self):
                existing = repr(getattr(cherrypy.request, "asdf", None))
                cherrypy.request.asdf = "rassfrassin"
                return existing

        appconf = {
            '/method': {'request.methods_with_bodies': ("POST", "PUT", "PROPFIND")},
            }
        cherrypy.tree.mount(root, config=appconf)
    setup_server = staticmethod(setup_server)

    def test_scheme(self):
        self.getPage("/scheme")
        self.assertBody(self.scheme)

    def testRelativeURIPathInfo(self):
        self.getPage("/pathinfo/foo/bar")
        self.assertBody("/pathinfo/foo/bar")

    def testAbsoluteURIPathInfo(self):
        # http://cherrypy.org/ticket/1061
        self.getPage("http://localhost/pathinfo/foo/bar")
        self.assertBody("/pathinfo/foo/bar")

    def testParams(self):
        self.getPage("/params/?thing=a")
        self.assertBody(repr(ntou("a")))

        self.getPage("/params/?thing=a&thing=b&thing=c")
        self.assertBody(repr([ntou('a'), ntou('b'), ntou('c')]))

        # Test friendly error message when given params are not accepted.
        cherrypy.config.update({"request.show_mismatched_params": True})
        self.getPage("/params/?notathing=meeting")
        self.assertInBody("Missing parameters: thing")
        self.getPage("/params/?thing=meeting&notathing=meeting")
        self.assertInBody("Unexpected query string parameters: notathing")

        # Test ability to turn off friendly error messages
        cherrypy.config.update({"request.show_mismatched_params": False})
        self.getPage("/params/?notathing=meeting")
        self.assertInBody("Not Found")
        self.getPage("/params/?thing=meeting&notathing=meeting")
        self.assertInBody("Not Found")

        # Test "% HEX HEX"-encoded URL, param keys, and values
        self.getPage("/params/%d4%20%e3/cheese?Gruy%E8re=Bulgn%e9ville")
        self.assertBody("args: %s kwargs: %s" %
                        (('\xd4 \xe3', 'cheese'),
                         {'Gruy\xe8re': ntou('Bulgn\xe9ville')}))

        # Make sure that encoded = and & get parsed correctly
        self.getPage("/params/code?url=http%3A//cherrypy.org/index%3Fa%3D1%26b%3D2")
        self.assertBody("args: %s kwargs: %s" %
                        (('code',),
                         {'url': ntou('http://cherrypy.org/index?a=1&b=2')}))

        # Test coordinates sent by <img ismap>
        self.getPage("/params/ismap?223,114")
        self.assertBody("Coordinates: 223, 114")

        # Test "name[key]" dict-like params
        self.getPage("/params/dictlike?a[1]=1&a[2]=2&b=foo&b[bar]=baz")
        self.assertBody("args: %s kwargs: %s" %
                        (('dictlike',),
                         {'a[1]': ntou('1'), 'b[bar]': ntou('baz'),
                          'b': ntou('foo'), 'a[2]': ntou('2')}))

    def testParamErrors(self):

        # test that all of the handlers work when given
        # the correct parameters in order to ensure that the
        # errors below aren't coming from some other source.
        for uri in (
                '/paramerrors/one_positional?param1=foo',
                '/paramerrors/one_positional_args?param1=foo',
                '/paramerrors/one_positional_args/foo',
                '/paramerrors/one_positional_args/foo/bar/baz',
                '/paramerrors/one_positional_args_kwargs?param1=foo&param2=bar',
                '/paramerrors/one_positional_args_kwargs/foo?param2=bar&param3=baz',
                '/paramerrors/one_positional_args_kwargs/foo/bar/baz?param2=bar&param3=baz',
                '/paramerrors/one_positional_kwargs?param1=foo&param2=bar&param3=baz',
                '/paramerrors/one_positional_kwargs/foo?param4=foo&param2=bar&param3=baz',
                '/paramerrors/no_positional',
                '/paramerrors/no_positional_args/foo',
                '/paramerrors/no_positional_args/foo/bar/baz',
                '/paramerrors/no_positional_args_kwargs?param1=foo&param2=bar',
                '/paramerrors/no_positional_args_kwargs/foo?param2=bar',
                '/paramerrors/no_positional_args_kwargs/foo/bar/baz?param2=bar&param3=baz',
                '/paramerrors/no_positional_kwargs?param1=foo&param2=bar',
                '/paramerrors/callable_object',
            ):
            self.getPage(uri)
            self.assertStatus(200)

        # query string parameters are part of the URI, so if they are wrong
        # for a particular handler, the status MUST be a 404.
        error_msgs = [
                'Missing parameters',
                'Nothing matches the given URI',
                'Multiple values for parameters',
                'Unexpected query string parameters',
                'Unexpected body parameters',
            ]
        for uri, msg in (
            ('/paramerrors/one_positional', error_msgs[0]),
            ('/paramerrors/one_positional?foo=foo', error_msgs[0]),
            ('/paramerrors/one_positional/foo/bar/baz', error_msgs[1]),
            ('/paramerrors/one_positional/foo?param1=foo', error_msgs[2]),
            ('/paramerrors/one_positional/foo?param1=foo&param2=foo', error_msgs[2]),
            ('/paramerrors/one_positional_args/foo?param1=foo&param2=foo', error_msgs[2]),
            ('/paramerrors/one_positional_args/foo/bar/baz?param2=foo', error_msgs[3]),
            ('/paramerrors/one_positional_args_kwargs/foo/bar/baz?param1=bar&param3=baz', error_msgs[2]),
            ('/paramerrors/one_positional_kwargs/foo?param1=foo&param2=bar&param3=baz', error_msgs[2]),
            ('/paramerrors/no_positional/boo', error_msgs[1]),
            ('/paramerrors/no_positional?param1=foo', error_msgs[3]),
            ('/paramerrors/no_positional_args/boo?param1=foo', error_msgs[3]),
            ('/paramerrors/no_positional_kwargs/boo?param1=foo', error_msgs[1]),
            ('/paramerrors/callable_object?param1=foo', error_msgs[3]),
            ('/paramerrors/callable_object/boo', error_msgs[1]),
            ):
            for show_mismatched_params in (True, False):
                cherrypy.config.update({'request.show_mismatched_params': show_mismatched_params})
                self.getPage(uri)
                self.assertStatus(404)
                if show_mismatched_params:
                    self.assertInBody(msg)
                else:
                    self.assertInBody("Not Found")

        # if body parameters are wrong, a 400 must be returned.
        for uri, body, msg in (
                ('/paramerrors/one_positional/foo', 'param1=foo', error_msgs[2]),
                ('/paramerrors/one_positional/foo', 'param1=foo&param2=foo', error_msgs[2]),
                ('/paramerrors/one_positional_args/foo', 'param1=foo&param2=foo', error_msgs[2]),
                ('/paramerrors/one_positional_args/foo/bar/baz', 'param2=foo', error_msgs[4]),
                ('/paramerrors/one_positional_args_kwargs/foo/bar/baz', 'param1=bar&param3=baz', error_msgs[2]),
                ('/paramerrors/one_positional_kwargs/foo', 'param1=foo&param2=bar&param3=baz', error_msgs[2]),
                ('/paramerrors/no_positional', 'param1=foo', error_msgs[4]),
                ('/paramerrors/no_positional_args/boo', 'param1=foo', error_msgs[4]),
                ('/paramerrors/callable_object', 'param1=foo', error_msgs[4]),
            ):
            for show_mismatched_params in (True, False):
                cherrypy.config.update({'request.show_mismatched_params': show_mismatched_params})
                self.getPage(uri, method='POST', body=body)
                self.assertStatus(400)
                if show_mismatched_params:
                    self.assertInBody(msg)
                else:
                    self.assertInBody("400 Bad")


        # even if body parameters are wrong, if we get the uri wrong, then
        # it's a 404
        for uri, body, msg in (
                ('/paramerrors/one_positional?param2=foo', 'param1=foo', error_msgs[3]),
                ('/paramerrors/one_positional/foo/bar', 'param2=foo', error_msgs[1]),
                ('/paramerrors/one_positional_args/foo/bar?param2=foo', 'param3=foo', error_msgs[3]),
                ('/paramerrors/one_positional_kwargs/foo/bar', 'param2=bar&param3=baz', error_msgs[1]),
                ('/paramerrors/no_positional?param1=foo', 'param2=foo', error_msgs[3]),
                ('/paramerrors/no_positional_args/boo?param2=foo', 'param1=foo', error_msgs[3]),
                ('/paramerrors/callable_object?param2=bar', 'param1=foo', error_msgs[3]),
            ):
            for show_mismatched_params in (True, False):
                cherrypy.config.update({'request.show_mismatched_params': show_mismatched_params})
                self.getPage(uri, method='POST', body=body)
                self.assertStatus(404)
                if show_mismatched_params:
                    self.assertInBody(msg)
                else:
                    self.assertInBody("Not Found")

        # In the case that a handler raises a TypeError we should
        # let that type error through.
        for uri in (
                '/paramerrors/raise_type_error',
                '/paramerrors/raise_type_error_with_default_param?x=0',
                '/paramerrors/raise_type_error_with_default_param?x=0&y=0',
            ):
            self.getPage(uri, method='GET')
            self.assertStatus(500)
            self.assertTrue('Client Error', self.body)

    def testErrorHandling(self):
        self.getPage("/error/missing")
        self.assertStatus(404)
        self.assertErrorPage(404, "The path '/error/missing' was not found.")

        ignore = helper.webtest.ignored_exceptions
        ignore.append(ValueError)
        try:
            valerr = '\n    raise ValueError()\nValueError'
            self.getPage("/error/page_method")
            self.assertErrorPage(500, pattern=valerr)

            self.getPage("/error/page_yield")
            self.assertErrorPage(500, pattern=valerr)

            if (cherrypy.server.protocol_version == "HTTP/1.0" or
                getattr(cherrypy.server, "using_apache", False)):
                self.getPage("/error/page_streamed")
                # Because this error is raised after the response body has
                # started, the status should not change to an error status.
                self.assertStatus(200)
                self.assertBody("word up")
            else:
                # Under HTTP/1.1, the chunked transfer-coding is used.
                # The HTTP client will choke when the output is incomplete.
                self.assertRaises((ValueError, IncompleteRead), self.getPage,
                                  "/error/page_streamed")

            # No traceback should be present
            self.getPage("/error/cause_err_in_finalize")
            msg = "Illegal response status from server ('ZOO' is non-numeric)."
            self.assertErrorPage(500, msg, None)
        finally:
            ignore.pop()

        # Test HTTPError with a reason-phrase in the status arg.
        self.getPage('/error/reason_phrase')
        self.assertStatus("410 Gone fishin'")

        # Test custom error page for a specific error.
        self.getPage("/error/custom")
        self.assertStatus(404)
        self.assertBody("Hello, world\r\n" + (" " * 499))

        # Test custom error page for a specific error.
        self.getPage("/error/custom?err=401")
        self.assertStatus(401)
        self.assertBody("Error 401 Unauthorized - Well, I'm very sorry but you haven't paid!")

        # Test default custom error page.
        self.getPage("/error/custom_default")
        self.assertStatus(500)
        self.assertBody("Error 500 Internal Server Error - Well, I'm very sorry but you haven't paid!".ljust(513))

        # Test error in custom error page (ticket #305).
        # Note that the message is escaped for HTML (ticket #310).
        self.getPage("/error/noexist")
        self.assertStatus(404)
        msg = ("No, &lt;b&gt;really&lt;/b&gt;, not found!<br />"
               "In addition, the custom error page failed:\n<br />"
               "IOError: [Errno 2] No such file or directory: 'nonexistent.html'")
        self.assertInBody(msg)

        if getattr(cherrypy.server, "using_apache", False):
            pass
        else:
            # Test throw_errors (ticket #186).
            self.getPage("/error/rethrow")
            self.assertInBody("raise ValueError()")

    def testExpect(self):
        e = ('Expect', '100-continue')
        self.getPage("/headerelements/get_elements?headername=Expect", [e])
        self.assertBody('100-continue')

        self.getPage("/expect/expectation_failed", [e])
        self.assertStatus(417)

    def testHeaderElements(self):
        # Accept-* header elements should be sorted, with most preferred first.
        h = [('Accept', 'audio/*; q=0.2, audio/basic')]
        self.getPage("/headerelements/get_elements?headername=Accept", h)
        self.assertStatus(200)
        self.assertBody("audio/basic\n"
                        "audio/*;q=0.2")

        h = [('Accept', 'text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c')]
        self.getPage("/headerelements/get_elements?headername=Accept", h)
        self.assertStatus(200)
        self.assertBody("text/x-c\n"
                        "text/html\n"
                        "text/x-dvi;q=0.8\n"
                        "text/plain;q=0.5")

        # Test that more specific media ranges get priority.
        h = [('Accept', 'text/*, text/html, text/html;level=1, */*')]
        self.getPage("/headerelements/get_elements?headername=Accept", h)
        self.assertStatus(200)
        self.assertBody("text/html;level=1\n"
                        "text/html\n"
                        "text/*\n"
                        "*/*")

        # Test Accept-Charset
        h = [('Accept-Charset', 'iso-8859-5, unicode-1-1;q=0.8')]
        self.getPage("/headerelements/get_elements?headername=Accept-Charset", h)
        self.assertStatus("200 OK")
        self.assertBody("iso-8859-5\n"
                        "unicode-1-1;q=0.8")

        # Test Accept-Encoding
        h = [('Accept-Encoding', 'gzip;q=1.0, identity; q=0.5, *;q=0')]
        self.getPage("/headerelements/get_elements?headername=Accept-Encoding", h)
        self.assertStatus("200 OK")
        self.assertBody("gzip;q=1.0\n"
                        "identity;q=0.5\n"
                        "*;q=0")

        # Test Accept-Language
        h = [('Accept-Language', 'da, en-gb;q=0.8, en;q=0.7')]
        self.getPage("/headerelements/get_elements?headername=Accept-Language", h)
        self.assertStatus("200 OK")
        self.assertBody("da\n"
                        "en-gb;q=0.8\n"
                        "en;q=0.7")

        # Test malformed header parsing. See http://www.cherrypy.org/ticket/763.
        self.getPage("/headerelements/get_elements?headername=Content-Type",
                     # Note the illegal trailing ";"
                     headers=[('Content-Type', 'text/html; charset=utf-8;')])
        self.assertStatus(200)
        self.assertBody("text/html;charset=utf-8")

    def test_repeated_headers(self):
        # Test that two request headers are collapsed into one.
        # See http://www.cherrypy.org/ticket/542.
        self.getPage("/headers/Accept-Charset",
                     headers=[("Accept-Charset", "iso-8859-5"),
                              ("Accept-Charset", "unicode-1-1;q=0.8")])
        self.assertBody("iso-8859-5, unicode-1-1;q=0.8")

        # Tests that each header only appears once, regardless of case.
        self.getPage("/headers/doubledheaders")
        self.assertBody("double header test")
        hnames = [name.title() for name, val in self.headers]
        for key in ['Content-Length', 'Content-Type', 'Date',
                    'Expires', 'Location', 'Server']:
            self.assertEqual(hnames.count(key), 1, self.headers)

    def test_encoded_headers(self):
        # First, make sure the innards work like expected.
        self.assertEqual(httputil.decode_TEXT(ntou("=?utf-8?q?f=C3=BCr?=")), ntou("f\xfcr"))

        if cherrypy.server.protocol_version == "HTTP/1.1":
            # Test RFC-2047-encoded request and response header values
            u = ntou('\u212bngstr\xf6m', 'escape')
            c = ntou("=E2=84=ABngstr=C3=B6m")
            self.getPage("/headers/ifmatch", [('If-Match', ntou('=?utf-8?q?%s?=') % c)])
            # The body should be utf-8 encoded.
            self.assertBody(ntob("\xe2\x84\xabngstr\xc3\xb6m"))
            # But the Etag header should be RFC-2047 encoded (binary)
            self.assertHeader("ETag", ntou('=?utf-8?b?4oSrbmdzdHLDtm0=?='))

            # Test a *LONG* RFC-2047-encoded request and response header value
            self.getPage("/headers/ifmatch",
                         [('If-Match', ntou('=?utf-8?q?%s?=') % (c * 10))])
            self.assertBody(ntob("\xe2\x84\xabngstr\xc3\xb6m") * 10)
            # Note: this is different output for Python3, but it decodes fine.
            etag = self.assertHeader("ETag",
                '=?utf-8?b?4oSrbmdzdHLDtm3ihKtuZ3N0csO2beKEq25nc3Ryw7Zt'
                '4oSrbmdzdHLDtm3ihKtuZ3N0csO2beKEq25nc3Ryw7Zt'
                '4oSrbmdzdHLDtm3ihKtuZ3N0csO2beKEq25nc3Ryw7Zt'
                '4oSrbmdzdHLDtm0=?=')
            self.assertEqual(httputil.decode_TEXT(etag), u * 10)

    def test_header_presence(self):
        # If we don't pass a Content-Type header, it should not be present
        # in cherrypy.request.headers
        self.getPage("/headers/Content-Type",
                     headers=[])
        self.assertStatus(500)

        # If Content-Type is present in the request, it should be present in
        # cherrypy.request.headers
        self.getPage("/headers/Content-Type",
                     headers=[("Content-type", "application/json")])
        self.assertBody("application/json")

    def test_basic_HTTPMethods(self):
        helper.webtest.methods_with_bodies = ("POST", "PUT", "PROPFIND")

        # Test that all defined HTTP methods work.
        for m in defined_http_methods:
            self.getPage("/method/", method=m)

            # HEAD requests should not return any body.
            if m == "HEAD":
                self.assertBody("")
            elif m == "TRACE":
                # Some HTTP servers (like modpy) have their own TRACE support
                self.assertEqual(self.body[:5], ntob("TRACE"))
            else:
                self.assertBody(m)

        # Request a PUT method with a form-urlencoded body
        self.getPage("/method/parameterized", method="PUT",
                       body="data=on+top+of+other+things")
        self.assertBody("on top of other things")

        # Request a PUT method with a file body
        b = "one thing on top of another"
        h = [("Content-Type", "text/plain"),
             ("Content-Length", str(len(b)))]
        self.getPage("/method/request_body", headers=h, method="PUT", body=b)
        self.assertStatus(200)
        self.assertBody(b)

        # Request a PUT method with a file body but no Content-Type.
        # See http://www.cherrypy.org/ticket/790.
        b = ntob("one thing on top of another")
        self.persistent = True
        try:
            conn = self.HTTP_CONN
            conn.putrequest("PUT", "/method/request_body", skip_host=True)
            conn.putheader("Host", self.HOST)
            conn.putheader('Content-Length', str(len(b)))
            conn.endheaders()
            conn.send(b)
            response = conn.response_class(conn.sock, method="PUT")
            response.begin()
            self.assertEqual(response.status, 200)
            self.body = response.read()
            self.assertBody(b)
        finally:
            self.persistent = False

        # Request a PUT method with no body whatsoever (not an empty one).
        # See http://www.cherrypy.org/ticket/650.
        # Provide a C-T or webtest will provide one (and a C-L) for us.
        h = [("Content-Type", "text/plain")]
        self.getPage("/method/reachable", headers=h, method="PUT")
        self.assertStatus(411)

        # Request a custom method with a request body
        b = ('<?xml version="1.0" encoding="utf-8" ?>\n\n'
             '<propfind xmlns="DAV:"><prop><getlastmodified/>'
             '</prop></propfind>')
        h = [('Content-Type', 'text/xml'),
             ('Content-Length', str(len(b)))]
        self.getPage("/method/request_body", headers=h, method="PROPFIND", body=b)
        self.assertStatus(200)
        self.assertBody(b)

        # Request a disallowed method
        self.getPage("/method/", method="LINK")
        self.assertStatus(405)

        # Request an unknown method
        self.getPage("/method/", method="SEARCH")
        self.assertStatus(501)

        # For method dispatchers: make sure that an HTTP method doesn't
        # collide with a virtual path atom. If you build HTTP-method
        # dispatching into the core, rewrite these handlers to use
        # your dispatch idioms.
        self.getPage("/divorce/get?ID=13")
        self.assertBody('Divorce document 13: empty')
        self.assertStatus(200)
        self.getPage("/divorce/", method="GET")
        self.assertBody('<h1>Choose your document</h1>\n<ul>\n</ul>')
        self.assertStatus(200)

    def test_CONNECT_method(self):
        if getattr(cherrypy.server, "using_apache", False):
            return self.skip("skipped due to known Apache differences... ")

        self.getPage("/method/", method="CONNECT")
        self.assertBody("CONNECT")

    def testEmptyThreadlocals(self):
        results = []
        for x in range(20):
            self.getPage("/threadlocal/")
            results.append(self.body)
        self.assertEqual(results, [ntob("None")] * 20)

