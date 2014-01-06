import cherrypy
from cherrypy._cpcompat import ntou
from cherrypy._cptree import Application
from cherrypy.test import helper

script_names = ["", "/foo", "/users/fred/blog", "/corp/blog"]


class ObjectMappingTest(helper.CPWebCase):

    def setup_server():
        class Root:
            def index(self, name="world"):
                return name
            index.exposed = True

            def foobar(self):
                return "bar"
            foobar.exposed = True

            def default(self, *params, **kwargs):
                return "default:" + repr(params)
            default.exposed = True

            def other(self):
                return "other"
            other.exposed = True

            def extra(self, *p):
                return repr(p)
            extra.exposed = True

            def redirect(self):
                raise cherrypy.HTTPRedirect('dir1/', 302)
            redirect.exposed = True

            def notExposed(self):
                return "not exposed"

            def confvalue(self):
                return cherrypy.request.config.get("user")
            confvalue.exposed = True

            def redirect_via_url(self, path):
                raise cherrypy.HTTPRedirect(cherrypy.url(path))
            redirect_via_url.exposed = True

            def translate_html(self):
                return "OK"
            translate_html.exposed = True

        def mapped_func(self, ID=None):
            return "ID is %s" % ID
        mapped_func.exposed = True
        setattr(Root, "Von B\xfclow", mapped_func)


        class Exposing:
            def base(self):
                return "expose works!"
            cherrypy.expose(base)
            cherrypy.expose(base, "1")
            cherrypy.expose(base, "2")

        class ExposingNewStyle(object):
            def base(self):
                return "expose works!"
            cherrypy.expose(base)
            cherrypy.expose(base, "1")
            cherrypy.expose(base, "2")


        class Dir1:
            def index(self):
                return "index for dir1"
            index.exposed = True

            def myMethod(self):
                return "myMethod from dir1, path_info is:" + repr(cherrypy.request.path_info)
            myMethod.exposed = True
            myMethod._cp_config = {'tools.trailing_slash.extra': True}

            def default(self, *params):
                return "default for dir1, param is:" + repr(params)
            default.exposed = True


        class Dir2:
            def index(self):
                return "index for dir2, path is:" + cherrypy.request.path_info
            index.exposed = True

            def script_name(self):
                return cherrypy.tree.script_name()
            script_name.exposed = True

            def cherrypy_url(self):
                return cherrypy.url("/extra")
            cherrypy_url.exposed = True

            def posparam(self, *vpath):
                return "/".join(vpath)
            posparam.exposed = True


        class Dir3:
            def default(self):
                return "default for dir3, not exposed"

        class Dir4:
            def index(self):
                return "index for dir4, not exposed"

        class DefNoIndex:
            def default(self, *args):
                raise cherrypy.HTTPRedirect("contact")
            default.exposed = True

        # MethodDispatcher code
        class ByMethod:
            exposed = True

            def __init__(self, *things):
                self.things = list(things)

            def GET(self):
                return repr(self.things)

            def POST(self, thing):
                self.things.append(thing)

        class Collection:
            default = ByMethod('a', 'bit')

        Root.exposing = Exposing()
        Root.exposingnew = ExposingNewStyle()
        Root.dir1 = Dir1()
        Root.dir1.dir2 = Dir2()
        Root.dir1.dir2.dir3 = Dir3()
        Root.dir1.dir2.dir3.dir4 = Dir4()
        Root.defnoindex = DefNoIndex()
        Root.bymethod = ByMethod('another')
        Root.collection = Collection()

        d = cherrypy.dispatch.MethodDispatcher()
        for url in script_names:
            conf = {'/': {'user': (url or "/").split("/")[-2]},
                    '/bymethod': {'request.dispatch': d},
                    '/collection': {'request.dispatch': d},
                    }
            cherrypy.tree.mount(Root(), url, conf)


        class Isolated:
            def index(self):
                return "made it!"
            index.exposed = True

        cherrypy.tree.mount(Isolated(), "/isolated")

        class AnotherApp:

            exposed = True

            def GET(self):
                return "milk"

        cherrypy.tree.mount(AnotherApp(), "/app", {'/': {'request.dispatch': d}})
    setup_server = staticmethod(setup_server)


    def testObjectMapping(self):
        for url in script_names:
            prefix = self.script_name = url

            self.getPage('/')
            self.assertBody('world')

            self.getPage("/dir1/myMethod")
            self.assertBody("myMethod from dir1, path_info is:'/dir1/myMethod'")

            self.getPage("/this/method/does/not/exist")
            self.assertBody("default:('this', 'method', 'does', 'not', 'exist')")

            self.getPage("/extra/too/much")
            self.assertBody("('too', 'much')")

            self.getPage("/other")
            self.assertBody('other')

            self.getPage("/notExposed")
            self.assertBody("default:('notExposed',)")

            self.getPage("/dir1/dir2/")
            self.assertBody('index for dir2, path is:/dir1/dir2/')

            # Test omitted trailing slash (should be redirected by default).
            self.getPage("/dir1/dir2")
            self.assertStatus(301)
            self.assertHeader('Location', '%s/dir1/dir2/' % self.base())

            # Test extra trailing slash (should be redirected if configured).
            self.getPage("/dir1/myMethod/")
            self.assertStatus(301)
            self.assertHeader('Location', '%s/dir1/myMethod' % self.base())

            # Test that default method must be exposed in order to match.
            self.getPage("/dir1/dir2/dir3/dir4/index")
            self.assertBody("default for dir1, param is:('dir2', 'dir3', 'dir4', 'index')")

            # Test *vpath when default() is defined but not index()
            # This also tests HTTPRedirect with default.
            self.getPage("/defnoindex")
            self.assertStatus((302, 303))
            self.assertHeader('Location', '%s/contact' % self.base())
            self.getPage("/defnoindex/")
            self.assertStatus((302, 303))
            self.assertHeader('Location', '%s/defnoindex/contact' % self.base())
            self.getPage("/defnoindex/page")
            self.assertStatus((302, 303))
            self.assertHeader('Location', '%s/defnoindex/contact' % self.base())

            self.getPage("/redirect")
            self.assertStatus('302 Found')
            self.assertHeader('Location', '%s/dir1/' % self.base())

            if not getattr(cherrypy.server, "using_apache", False):
                # Test that we can use URL's which aren't all valid Python identifiers
                # This should also test the %XX-unquoting of URL's.
                self.getPage("/Von%20B%fclow?ID=14")
                self.assertBody("ID is 14")

                # Test that %2F in the path doesn't get unquoted too early;
                # that is, it should not be used to separate path components.
                # See ticket #393.
                self.getPage("/page%2Fname")
                self.assertBody("default:('page/name',)")

            self.getPage("/dir1/dir2/script_name")
            self.assertBody(url)
            self.getPage("/dir1/dir2/cherrypy_url")
            self.assertBody("%s/extra" % self.base())

            # Test that configs don't overwrite each other from diferent apps
            self.getPage("/confvalue")
            self.assertBody((url or "/").split("/")[-2])

        self.script_name = ""

        # Test absoluteURI's in the Request-Line
        self.getPage('http://%s:%s/' % (self.interface(), self.PORT))
        self.assertBody('world')

        self.getPage('http://%s:%s/abs/?service=http://192.168.0.1/x/y/z' %
                     (self.interface(), self.PORT))
        self.assertBody("default:('abs',)")

        self.getPage('/rel/?service=http://192.168.120.121:8000/x/y/z')
        self.assertBody("default:('rel',)")

        # Test that the "isolated" app doesn't leak url's into the root app.
        # If it did leak, Root.default() would answer with
        #   "default:('isolated', 'doesnt', 'exist')".
        self.getPage("/isolated/")
        self.assertStatus("200 OK")
        self.assertBody("made it!")
        self.getPage("/isolated/doesnt/exist")
        self.assertStatus("404 Not Found")

        # Make sure /foobar maps to Root.foobar and not to the app
        # mounted at /foo. See http://www.cherrypy.org/ticket/573
        self.getPage("/foobar")
        self.assertBody("bar")

    def test_translate(self):
        self.getPage("/translate_html")
        self.assertStatus("200 OK")
        self.assertBody("OK")

        self.getPage("/translate.html")
        self.assertStatus("200 OK")
        self.assertBody("OK")

        self.getPage("/translate-html")
        self.assertStatus("200 OK")
        self.assertBody("OK")

    def test_redir_using_url(self):
        for url in script_names:
            prefix = self.script_name = url

            # Test the absolute path to the parent (leading slash)
            self.getPage('/redirect_via_url?path=./')
            self.assertStatus(('302 Found', '303 See Other'))
            self.assertHeader('Location', '%s/' % self.base())

            # Test the relative path to the parent (no leading slash)
            self.getPage('/redirect_via_url?path=./')
            self.assertStatus(('302 Found', '303 See Other'))
            self.assertHeader('Location', '%s/' % self.base())

            # Test the absolute path to the parent (leading slash)
            self.getPage('/redirect_via_url/?path=./')
            self.assertStatus(('302 Found', '303 See Other'))
            self.assertHeader('Location', '%s/' % self.base())

            # Test the relative path to the parent (no leading slash)
            self.getPage('/redirect_via_url/?path=./')
            self.assertStatus(('302 Found', '303 See Other'))
            self.assertHeader('Location', '%s/' % self.base())

    def testPositionalParams(self):
        self.getPage("/dir1/dir2/posparam/18/24/hut/hike")
        self.assertBody("18/24/hut/hike")

        # intermediate index methods should not receive posparams;
        # only the "final" index method should do so.
        self.getPage("/dir1/dir2/5/3/sir")
        self.assertBody("default for dir1, param is:('dir2', '5', '3', 'sir')")

        # test that extra positional args raises an 404 Not Found
        # See http://www.cherrypy.org/ticket/733.
        self.getPage("/dir1/dir2/script_name/extra/stuff")
        self.assertStatus(404)

    def testExpose(self):
        # Test the cherrypy.expose function/decorator
        self.getPage("/exposing/base")
        self.assertBody("expose works!")

        self.getPage("/exposing/1")
        self.assertBody("expose works!")

        self.getPage("/exposing/2")
        self.assertBody("expose works!")

        self.getPage("/exposingnew/base")
        self.assertBody("expose works!")

        self.getPage("/exposingnew/1")
        self.assertBody("expose works!")

        self.getPage("/exposingnew/2")
        self.assertBody("expose works!")

    def testMethodDispatch(self):
        self.getPage("/bymethod")
        self.assertBody("['another']")
        self.assertHeader('Allow', 'GET, HEAD, POST')

        self.getPage("/bymethod", method="HEAD")
        self.assertBody("")
        self.assertHeader('Allow', 'GET, HEAD, POST')

        self.getPage("/bymethod", method="POST", body="thing=one")
        self.assertBody("")
        self.assertHeader('Allow', 'GET, HEAD, POST')

        self.getPage("/bymethod")
        self.assertBody(repr(['another', ntou('one')]))
        self.assertHeader('Allow', 'GET, HEAD, POST')

        self.getPage("/bymethod", method="PUT")
        self.assertErrorPage(405)
        self.assertHeader('Allow', 'GET, HEAD, POST')

        # Test default with posparams
        self.getPage("/collection/silly", method="POST")
        self.getPage("/collection", method="GET")
        self.assertBody("['a', 'bit', 'silly']")

        # Test custom dispatcher set on app root (see #737).
        self.getPage("/app")
        self.assertBody("milk")

    def testTreeMounting(self):
        class Root(object):
            def hello(self):
                return "Hello world!"
            hello.exposed = True

        # When mounting an application instance,
        # we can't specify a different script name in the call to mount.
        a = Application(Root(), '/somewhere')
        self.assertRaises(ValueError, cherrypy.tree.mount, a, '/somewhereelse')

        # When mounting an application instance...
        a = Application(Root(), '/somewhere')
        # ...we MUST allow in identical script name in the call to mount...
        cherrypy.tree.mount(a, '/somewhere')
        self.getPage('/somewhere/hello')
        self.assertStatus(200)
        # ...and MUST allow a missing script_name.
        del cherrypy.tree.apps['/somewhere']
        cherrypy.tree.mount(a)
        self.getPage('/somewhere/hello')
        self.assertStatus(200)

        # In addition, we MUST be able to create an Application using
        # script_name == None for access to the wsgi_environ.
        a = Application(Root(), script_name=None)
        # However, this does not apply to tree.mount
        self.assertRaises(TypeError, cherrypy.tree.mount, a, None)

