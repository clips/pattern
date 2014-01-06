"""Test the various means of instantiating and invoking tools."""

import gzip
import sys
import unittest
from cherrypy._cpcompat import BytesIO, copyitems, itervalues
from cherrypy._cpcompat import IncompleteRead, ntob, ntou, py3k, xrange
from cherrypy._cpcompat import bytestr, unicodestr
import time
timeout = 0.2
import types

import cherrypy
from cherrypy import tools


europoundUnicode = ntou('\x80\xa3')


#                             Client-side code                             #

from cherrypy.test import helper


class ToolTests(helper.CPWebCase):
    def setup_server():

        # Put check_access in a custom toolbox with its own namespace
        myauthtools = cherrypy._cptools.Toolbox("myauth")

        def check_access(default=False):
            if not getattr(cherrypy.request, "userid", default):
                raise cherrypy.HTTPError(401)
        myauthtools.check_access = cherrypy.Tool('before_request_body', check_access)

        def numerify():
            def number_it(body):
                for chunk in body:
                    for k, v in cherrypy.request.numerify_map:
                        chunk = chunk.replace(k, v)
                    yield chunk
            cherrypy.response.body = number_it(cherrypy.response.body)

        class NumTool(cherrypy.Tool):
            def _setup(self):
                def makemap():
                    m = self._merged_args().get("map", {})
                    cherrypy.request.numerify_map = copyitems(m)
                cherrypy.request.hooks.attach('on_start_resource', makemap)

                def critical():
                    cherrypy.request.error_response = cherrypy.HTTPError(502).set_response
                critical.failsafe = True

                cherrypy.request.hooks.attach('on_start_resource', critical)
                cherrypy.request.hooks.attach(self._point, self.callable)

        tools.numerify = NumTool('before_finalize', numerify)

        # It's not mandatory to inherit from cherrypy.Tool.
        class NadsatTool:

            def __init__(self):
                self.ended = {}
                self._name = "nadsat"

            def nadsat(self):
                def nadsat_it_up(body):
                    for chunk in body:
                        chunk = chunk.replace(ntob("good"), ntob("horrorshow"))
                        chunk = chunk.replace(ntob("piece"), ntob("lomtick"))
                        yield chunk
                cherrypy.response.body = nadsat_it_up(cherrypy.response.body)
            nadsat.priority = 0

            def cleanup(self):
                # This runs after the request has been completely written out.
                cherrypy.response.body = [ntob("razdrez")]
                id = cherrypy.request.params.get("id")
                if id:
                    self.ended[id] = True
            cleanup.failsafe = True

            def _setup(self):
                cherrypy.request.hooks.attach('before_finalize', self.nadsat)
                cherrypy.request.hooks.attach('on_end_request', self.cleanup)
        tools.nadsat = NadsatTool()

        def pipe_body():
            cherrypy.request.process_request_body = False
            clen = int(cherrypy.request.headers['Content-Length'])
            cherrypy.request.body = cherrypy.request.rfile.read(clen)

        # Assert that we can use a callable object instead of a function.
        class Rotator(object):
            def __call__(self, scale):
                r = cherrypy.response
                r.collapse_body()
                if py3k:
                    r.body = [bytes([(x + scale) % 256 for x in r.body[0]])]
                else:
                    r.body = [chr((ord(x) + scale) % 256) for x in r.body[0]]
        cherrypy.tools.rotator = cherrypy.Tool('before_finalize', Rotator())

        def stream_handler(next_handler, *args, **kwargs):
            cherrypy.response.output = o = BytesIO()
            try:
                response = next_handler(*args, **kwargs)
                # Ignore the response and return our accumulated output instead.
                return o.getvalue()
            finally:
                o.close()
        cherrypy.tools.streamer = cherrypy._cptools.HandlerWrapperTool(stream_handler)

        class Root:
            def index(self):
                return "Howdy earth!"
            index.exposed = True

            def tarfile(self):
                cherrypy.response.output.write(ntob('I am '))
                cherrypy.response.output.write(ntob('a tarfile'))
            tarfile.exposed = True
            tarfile._cp_config = {'tools.streamer.on': True}

            def euro(self):
                hooks = list(cherrypy.request.hooks['before_finalize'])
                hooks.sort()
                cbnames = [x.callback.__name__ for x in hooks]
                assert cbnames == ['gzip'], cbnames
                priorities = [x.priority for x in hooks]
                assert priorities == [80], priorities
                yield ntou("Hello,")
                yield ntou("world")
                yield europoundUnicode
            euro.exposed = True

            # Bare hooks
            def pipe(self):
                return cherrypy.request.body
            pipe.exposed = True
            pipe._cp_config = {'hooks.before_request_body': pipe_body}

            # Multiple decorators; include kwargs just for fun.
            # Note that rotator must run before gzip.
            def decorated_euro(self, *vpath):
                yield ntou("Hello,")
                yield ntou("world")
                yield europoundUnicode
            decorated_euro.exposed = True
            decorated_euro = tools.gzip(compress_level=6)(decorated_euro)
            decorated_euro = tools.rotator(scale=3)(decorated_euro)

        root = Root()

        class TestType(type):
            """Metaclass which automatically exposes all functions in each subclass,
            and adds an instance of the subclass as an attribute of root.
            """
            def __init__(cls, name, bases, dct):
                type.__init__(cls, name, bases, dct)
                for value in itervalues(dct):
                    if isinstance(value, types.FunctionType):
                        value.exposed = True
                setattr(root, name.lower(), cls())
        Test = TestType('Test', (object,), {})

        # METHOD ONE:
        # Declare Tools in _cp_config
        class Demo(Test):

            _cp_config = {"tools.nadsat.on": True}

            def index(self, id=None):
                return "A good piece of cherry pie"

            def ended(self, id):
                return repr(tools.nadsat.ended[id])

            def err(self, id=None):
                raise ValueError()

            def errinstream(self, id=None):
                yield "nonconfidential"
                raise ValueError()
                yield "confidential"

            # METHOD TWO: decorator using Tool()
            # We support Python 2.3, but the @-deco syntax would look like this:
            # @tools.check_access()
            def restricted(self):
                return "Welcome!"
            restricted = myauthtools.check_access()(restricted)
            userid = restricted

            def err_in_onstart(self):
                return "success!"

            def stream(self, id=None):
                for x in xrange(100000000):
                    yield str(x)
            stream._cp_config = {'response.stream': True}


        conf = {
            # METHOD THREE:
            # Declare Tools in detached config
            '/demo': {
                'tools.numerify.on': True,
                'tools.numerify.map': {ntob("pie"): ntob("3.14159")},
            },
            '/demo/restricted': {
                'request.show_tracebacks': False,
            },
            '/demo/userid': {
                'request.show_tracebacks': False,
                'myauth.check_access.default': True,
            },
            '/demo/errinstream': {
                'response.stream': True,
            },
            '/demo/err_in_onstart': {
                # Because this isn't a dict, on_start_resource will error.
                'tools.numerify.map': "pie->3.14159"
            },
            # Combined tools
            '/euro': {
                'tools.gzip.on': True,
                'tools.encode.on': True,
            },
            # Priority specified in config
            '/decorated_euro/subpath': {
                'tools.gzip.priority': 10,
            },
            # Handler wrappers
            '/tarfile': {'tools.streamer.on': True}
        }
        app = cherrypy.tree.mount(root, config=conf)
        app.request_class.namespaces['myauth'] = myauthtools

        if sys.version_info >= (2, 5):
            from cherrypy.test import _test_decorators
            root.tooldecs = _test_decorators.ToolExamples()
    setup_server = staticmethod(setup_server)

    def testHookErrors(self):
        self.getPage("/demo/?id=1")
        # If body is "razdrez", then on_end_request is being called too early.
        self.assertBody("A horrorshow lomtick of cherry 3.14159")
        # If this fails, then on_end_request isn't being called at all.
        time.sleep(0.1)
        self.getPage("/demo/ended/1")
        self.assertBody("True")

        valerr = '\n    raise ValueError()\nValueError'
        self.getPage("/demo/err?id=3")
        # If body is "razdrez", then on_end_request is being called too early.
        self.assertErrorPage(502, pattern=valerr)
        # If this fails, then on_end_request isn't being called at all.
        time.sleep(0.1)
        self.getPage("/demo/ended/3")
        self.assertBody("True")

        # If body is "razdrez", then on_end_request is being called too early.
        if (cherrypy.server.protocol_version == "HTTP/1.0" or
            getattr(cherrypy.server, "using_apache", False)):
            self.getPage("/demo/errinstream?id=5")
            # Because this error is raised after the response body has
            # started, the status should not change to an error status.
            self.assertStatus("200 OK")
            self.assertBody("nonconfidential")
        else:
            # Because this error is raised after the response body has
            # started, and because it's chunked output, an error is raised by
            # the HTTP client when it encounters incomplete output.
            self.assertRaises((ValueError, IncompleteRead), self.getPage,
                              "/demo/errinstream?id=5")
        # If this fails, then on_end_request isn't being called at all.
        time.sleep(0.1)
        self.getPage("/demo/ended/5")
        self.assertBody("True")

        # Test the "__call__" technique (compile-time decorator).
        self.getPage("/demo/restricted")
        self.assertErrorPage(401)

        # Test compile-time decorator with kwargs from config.
        self.getPage("/demo/userid")
        self.assertBody("Welcome!")

    def testEndRequestOnDrop(self):
        old_timeout = None
        try:
            httpserver = cherrypy.server.httpserver
            old_timeout = httpserver.timeout
        except (AttributeError, IndexError):
            return self.skip()

        try:
            httpserver.timeout = timeout

            # Test that on_end_request is called even if the client drops.
            self.persistent = True
            try:
                conn = self.HTTP_CONN
                conn.putrequest("GET", "/demo/stream?id=9", skip_host=True)
                conn.putheader("Host", self.HOST)
                conn.endheaders()
                # Skip the rest of the request and close the conn. This will
                # cause the server's active socket to error, which *should*
                # result in the request being aborted, and request.close being
                # called all the way up the stack (including WSGI middleware),
                # eventually calling our on_end_request hook.
            finally:
                self.persistent = False
            time.sleep(timeout * 2)
            # Test that the on_end_request hook was called.
            self.getPage("/demo/ended/9")
            self.assertBody("True")
        finally:
            if old_timeout is not None:
                httpserver.timeout = old_timeout

    def testGuaranteedHooks(self):
        # The 'critical' on_start_resource hook is 'failsafe' (guaranteed
        # to run even if there are failures in other on_start methods).
        # This is NOT true of the other hooks.
        # Here, we have set up a failure in NumerifyTool.numerify_map,
        # but our 'critical' hook should run and set the error to 502.
        self.getPage("/demo/err_in_onstart")
        self.assertErrorPage(502)
        self.assertInBody("AttributeError: 'str' object has no attribute 'items'")

    def testCombinedTools(self):
        expectedResult = (ntou("Hello,world") + europoundUnicode).encode('utf-8')
        zbuf = BytesIO()
        zfile = gzip.GzipFile(mode='wb', fileobj=zbuf, compresslevel=9)
        zfile.write(expectedResult)
        zfile.close()

        self.getPage("/euro", headers=[("Accept-Encoding", "gzip"),
                                        ("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7")])
        self.assertInBody(zbuf.getvalue()[:3])

        zbuf = BytesIO()
        zfile = gzip.GzipFile(mode='wb', fileobj=zbuf, compresslevel=6)
        zfile.write(expectedResult)
        zfile.close()

        self.getPage("/decorated_euro", headers=[("Accept-Encoding", "gzip")])
        self.assertInBody(zbuf.getvalue()[:3])

        # This returns a different value because gzip's priority was
        # lowered in conf, allowing the rotator to run after gzip.
        # Of course, we don't want breakage in production apps,
        # but it proves the priority was changed.
        self.getPage("/decorated_euro/subpath",
                     headers=[("Accept-Encoding", "gzip")])
        if py3k:
            self.assertInBody(bytes([(x + 3) % 256 for x in zbuf.getvalue()]))
        else:
            self.assertInBody(''.join([chr((ord(x) + 3) % 256) for x in zbuf.getvalue()]))

    def testBareHooks(self):
        content = "bit of a pain in me gulliver"
        self.getPage("/pipe",
                     headers=[("Content-Length", str(len(content))),
                              ("Content-Type", "text/plain")],
                     method="POST", body=content)
        self.assertBody(content)

    def testHandlerWrapperTool(self):
        self.getPage("/tarfile")
        self.assertBody("I am a tarfile")

    def testToolWithConfig(self):
        if not sys.version_info >= (2, 5):
            return self.skip("skipped (Python 2.5+ only)")

        self.getPage('/tooldecs/blah')
        self.assertHeader('Content-Type', 'application/data')

    def testWarnToolOn(self):
        # get
        try:
            cherrypy.tools.numerify.on
        except AttributeError:
            pass
        else:
            raise AssertionError("Tool.on did not error as it should have.")

        # set
        try:
            cherrypy.tools.numerify.on = True
        except AttributeError:
            pass
        else:
            raise AssertionError("Tool.on did not error as it should have.")

class SessionAuthTest(unittest.TestCase):
    def test_login_screen_returns_bytes(self):
        """
        login_screen must return bytes even if unicode parameters are passed.
        Issue 1132 revealed that login_screen would return unicode if the
        username and password were unicode.
        """
        sa = cherrypy.lib.cptools.SessionAuth()
        res = sa.login_screen(None, username=unicodestr('nobody'),
            password=unicodestr('anypass'))
        self.assertIsInstance(res, bytestr)
