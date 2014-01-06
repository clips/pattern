import cherrypy
from cherrypy.test import helper


class SessionAuthenticateTest(helper.CPWebCase):

    def setup_server():

        def check(username, password):
            # Dummy check_username_and_password function
            if username != 'test' or password != 'password':
                return 'Wrong login/password'

        def augment_params():
            # A simple tool to add some things to request.params
            # This is to check to make sure that session_auth can handle request
            # params (ticket #780)
            cherrypy.request.params["test"] = "test"

        cherrypy.tools.augment_params = cherrypy.Tool('before_handler',
                 augment_params, None, priority=30)

        class Test:

            _cp_config = {'tools.sessions.on': True,
                          'tools.session_auth.on': True,
                          'tools.session_auth.check_username_and_password': check,
                          'tools.augment_params.on': True,
                          }

            def index(self, **kwargs):
                return "Hi %s, you are logged in" % cherrypy.request.login
            index.exposed = True

        cherrypy.tree.mount(Test())
    setup_server = staticmethod(setup_server)


    def testSessionAuthenticate(self):
        # request a page and check for login form
        self.getPage('/')
        self.assertInBody('<form method="post" action="do_login">')

        # setup credentials
        login_body = 'username=test&password=password&from_page=/'

        # attempt a login
        self.getPage('/do_login', method='POST', body=login_body)
        self.assertStatus((302, 303))

        # get the page now that we are logged in
        self.getPage('/', self.cookies)
        self.assertBody('Hi test, you are logged in')

        # do a logout
        self.getPage('/do_logout', self.cookies, method='POST')
        self.assertStatus((302, 303))

        # verify we are logged out
        self.getPage('/', self.cookies)
        self.assertInBody('<form method="post" action="do_login">')

