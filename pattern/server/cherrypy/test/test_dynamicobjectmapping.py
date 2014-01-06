import cherrypy
from cherrypy._cpcompat import sorted, unicodestr
from cherrypy._cptree import Application
from cherrypy.test import helper

script_names = ["", "/foo", "/users/fred/blog", "/corp/blog"]



def setup_server():
    class SubSubRoot:
        def index(self):
            return "SubSubRoot index"
        index.exposed = True

        def default(self, *args):
            return "SubSubRoot default"
        default.exposed = True

        def handler(self):
            return "SubSubRoot handler"
        handler.exposed = True

        def dispatch(self):
            return "SubSubRoot dispatch"
        dispatch.exposed = True

    subsubnodes = {
        '1': SubSubRoot(),
        '2': SubSubRoot(),
    }

    class SubRoot:
        def index(self):
            return "SubRoot index"
        index.exposed = True

        def default(self, *args):
            return "SubRoot %s" % (args,)
        default.exposed = True

        def handler(self):
            return "SubRoot handler"
        handler.exposed = True

        def _cp_dispatch(self, vpath):
            return subsubnodes.get(vpath[0], None)

    subnodes = {
        '1': SubRoot(),
        '2': SubRoot(),
    }
    class Root:
        def index(self):
            return "index"
        index.exposed = True

        def default(self, *args):
            return "default %s" % (args,)
        default.exposed = True

        def handler(self):
            return "handler"
        handler.exposed = True

        def _cp_dispatch(self, vpath):
            return subnodes.get(vpath[0])

    #--------------------------------------------------------------------------
    # DynamicNodeAndMethodDispatcher example.
    # This example exposes a fairly naive HTTP api
    class User(object):
        def __init__(self, id, name):
            self.id = id
            self.name = name

        def __unicode__(self):
            return unicode(self.name)
        def __str__(self):
            return str(self.name)

    user_lookup = {
        1: User(1, 'foo'),
        2: User(2, 'bar'),
    }

    def make_user(name, id=None):
        if not id:
            id = max(*list(user_lookup.keys())) + 1
        user_lookup[id] = User(id, name)
        return id

    class UserContainerNode(object):
        exposed = True

        def POST(self, name):
            """
            Allow the creation of a new Object
            """
            return "POST %d" % make_user(name)

        def GET(self):
            return unicodestr(sorted(user_lookup.keys()))

        def dynamic_dispatch(self, vpath):
            try:
                id = int(vpath[0])
            except (ValueError, IndexError):
                return None
            return UserInstanceNode(id)

    class UserInstanceNode(object):
        exposed = True
        def __init__(self, id):
            self.id = id
            self.user = user_lookup.get(id, None)

            # For all but PUT methods there MUST be a valid user identified
            # by self.id
            if not self.user and cherrypy.request.method != 'PUT':
                raise cherrypy.HTTPError(404)

        def GET(self, *args, **kwargs):
            """
            Return the appropriate representation of the instance.
            """
            return unicodestr(self.user)

        def POST(self, name):
            """
            Update the fields of the user instance.
            """
            self.user.name = name
            return "POST %d" % self.user.id

        def PUT(self, name):
            """
            Create a new user with the specified id, or edit it if it already exists
            """
            if self.user:
                # Edit the current user
                self.user.name = name
                return "PUT %d" % self.user.id
            else:
                # Make a new user with said attributes.
                return "PUT %d" % make_user(name, self.id)

        def DELETE(self):
            """
            Delete the user specified at the id.
            """
            id = self.user.id
            del user_lookup[self.user.id]
            del self.user
            return "DELETE %d" % id


    class ABHandler:
        class CustomDispatch:
            def index(self, a, b):
                return "custom"
            index.exposed = True

        def _cp_dispatch(self, vpath):
            """Make sure that if we don't pop anything from vpath,
            processing still works.
            """
            return self.CustomDispatch()

        def index(self, a, b=None):
            body = [ 'a:' + str(a) ]
            if b is not None:
                body.append(',b:' + str(b))
            return ''.join(body)
        index.exposed = True

        def delete(self, a, b):
            return 'deleting ' + str(a) + ' and ' + str(b)
        delete.exposed = True

    class IndexOnly:
        def _cp_dispatch(self, vpath):
            """Make sure that popping ALL of vpath still shows the index
            handler.
            """
            while vpath:
                vpath.pop()
            return self

        def index(self):
            return "IndexOnly index"
        index.exposed = True

    class DecoratedPopArgs:
        """Test _cp_dispatch with @cherrypy.popargs."""
        def index(self):
            return "no params"
        index.exposed = True

        def hi(self):
            return "hi was not interpreted as 'a' param"
        hi.exposed = True
    DecoratedPopArgs = cherrypy.popargs('a', 'b', handler=ABHandler())(DecoratedPopArgs)

    class NonDecoratedPopArgs:
        """Test _cp_dispatch = cherrypy.popargs()"""

        _cp_dispatch = cherrypy.popargs('a')

        def index(self, a):
            return "index: " + str(a)
        index.exposed = True

    class ParameterizedHandler:
        """Special handler created for each request"""

        def __init__(self, a):
            self.a = a

        def index(self):
            if 'a' in cherrypy.request.params:
                raise Exception("Parameterized handler argument ended up in request.params")
            return self.a
        index.exposed = True

    class ParameterizedPopArgs:
        """Test cherrypy.popargs() with a function call handler"""
    ParameterizedPopArgs = cherrypy.popargs('a', handler=ParameterizedHandler)(ParameterizedPopArgs)

    Root.decorated = DecoratedPopArgs()
    Root.undecorated = NonDecoratedPopArgs()
    Root.index_only = IndexOnly()
    Root.parameter_test = ParameterizedPopArgs()

    Root.users = UserContainerNode()

    md = cherrypy.dispatch.MethodDispatcher('dynamic_dispatch')
    for url in script_names:
        conf = {'/': {
                    'user': (url or "/").split("/")[-2],
                },
                '/users': {
                    'request.dispatch': md
                },
            }
        cherrypy.tree.mount(Root(), url, conf)

class DynamicObjectMappingTest(helper.CPWebCase):
    setup_server = staticmethod(setup_server)

    def testObjectMapping(self):
        for url in script_names:
            prefix = self.script_name = url

            self.getPage('/')
            self.assertBody('index')

            self.getPage('/handler')
            self.assertBody('handler')

            # Dynamic dispatch will succeed here for the subnodes
            # so the subroot gets called
            self.getPage('/1/')
            self.assertBody('SubRoot index')

            self.getPage('/2/')
            self.assertBody('SubRoot index')

            self.getPage('/1/handler')
            self.assertBody('SubRoot handler')

            self.getPage('/2/handler')
            self.assertBody('SubRoot handler')

            # Dynamic dispatch will fail here for the subnodes
            # so the default gets called
            self.getPage('/asdf/')
            self.assertBody("default ('asdf',)")

            self.getPage('/asdf/asdf')
            self.assertBody("default ('asdf', 'asdf')")

            self.getPage('/asdf/handler')
            self.assertBody("default ('asdf', 'handler')")

            # Dynamic dispatch will succeed here for the subsubnodes
            # so the subsubroot gets called
            self.getPage('/1/1/')
            self.assertBody('SubSubRoot index')

            self.getPage('/2/2/')
            self.assertBody('SubSubRoot index')

            self.getPage('/1/1/handler')
            self.assertBody('SubSubRoot handler')

            self.getPage('/2/2/handler')
            self.assertBody('SubSubRoot handler')

            self.getPage('/2/2/dispatch')
            self.assertBody('SubSubRoot dispatch')

            # The exposed dispatch will not be called as a dispatch
            # method.
            self.getPage('/2/2/foo/foo')
            self.assertBody("SubSubRoot default")

            # Dynamic dispatch will fail here for the subsubnodes
            # so the SubRoot gets called
            self.getPage('/1/asdf/')
            self.assertBody("SubRoot ('asdf',)")

            self.getPage('/1/asdf/asdf')
            self.assertBody("SubRoot ('asdf', 'asdf')")

            self.getPage('/1/asdf/handler')
            self.assertBody("SubRoot ('asdf', 'handler')")

    def testMethodDispatch(self):
        # GET acts like a container
        self.getPage("/users")
        self.assertBody("[1, 2]")
        self.assertHeader('Allow', 'GET, HEAD, POST')

        # POST to the container URI allows creation
        self.getPage("/users", method="POST", body="name=baz")
        self.assertBody("POST 3")
        self.assertHeader('Allow', 'GET, HEAD, POST')

        # POST to a specific instanct URI results in a 404
        # as the resource does not exit.
        self.getPage("/users/5", method="POST", body="name=baz")
        self.assertStatus(404)

        # PUT to a specific instanct URI results in creation
        self.getPage("/users/5", method="PUT", body="name=boris")
        self.assertBody("PUT 5")
        self.assertHeader('Allow', 'DELETE, GET, HEAD, POST, PUT')

        # GET acts like a container
        self.getPage("/users")
        self.assertBody("[1, 2, 3, 5]")
        self.assertHeader('Allow', 'GET, HEAD, POST')

        test_cases = (
            (1, 'foo', 'fooupdated', 'DELETE, GET, HEAD, POST, PUT'),
            (2, 'bar', 'barupdated', 'DELETE, GET, HEAD, POST, PUT'),
            (3, 'baz', 'bazupdated', 'DELETE, GET, HEAD, POST, PUT'),
            (5, 'boris', 'borisupdated', 'DELETE, GET, HEAD, POST, PUT'),
        )
        for id, name, updatedname, headers in test_cases:
            self.getPage("/users/%d" % id)
            self.assertBody(name)
            self.assertHeader('Allow', headers)

            # Make sure POSTs update already existings resources
            self.getPage("/users/%d" % id, method='POST', body="name=%s" % updatedname)
            self.assertBody("POST %d" % id)
            self.assertHeader('Allow', headers)

            # Make sure PUTs Update already existing resources.
            self.getPage("/users/%d" % id, method='PUT', body="name=%s" % updatedname)
            self.assertBody("PUT %d" % id)
            self.assertHeader('Allow', headers)

            # Make sure DELETES Remove already existing resources.
            self.getPage("/users/%d" % id, method='DELETE')
            self.assertBody("DELETE %d" % id)
            self.assertHeader('Allow', headers)


        # GET acts like a container
        self.getPage("/users")
        self.assertBody("[]")
        self.assertHeader('Allow', 'GET, HEAD, POST')

    def testVpathDispatch(self):
        self.getPage("/decorated/")
        self.assertBody("no params")

        self.getPage("/decorated/hi")
        self.assertBody("hi was not interpreted as 'a' param")

        self.getPage("/decorated/yo/")
        self.assertBody("a:yo")

        self.getPage("/decorated/yo/there/")
        self.assertBody("a:yo,b:there")

        self.getPage("/decorated/yo/there/delete")
        self.assertBody("deleting yo and there")

        self.getPage("/decorated/yo/there/handled_by_dispatch/")
        self.assertBody("custom")

        self.getPage("/undecorated/blah/")
        self.assertBody("index: blah")

        self.getPage("/index_only/a/b/c/d/e/f/g/")
        self.assertBody("IndexOnly index")

        self.getPage("/parameter_test/argument2/")
        self.assertBody("argument2")

