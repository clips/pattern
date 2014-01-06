import cherrypy
from cherrypy.test import helper


class WSGI_VirtualHost_Test(helper.CPWebCase):

    def setup_server():

        class ClassOfRoot(object):

            def __init__(self, name):
                self.name = name

            def index(self):
                return "Welcome to the %s website!" % self.name
            index.exposed = True


        default = cherrypy.Application(None)

        domains = {}
        for year in range(1997, 2008):
            app = cherrypy.Application(ClassOfRoot('Class of %s' % year))
            domains['www.classof%s.example' % year] = app

        cherrypy.tree.graft(cherrypy._cpwsgi.VirtualHost(default, domains))
    setup_server = staticmethod(setup_server)

    def test_welcome(self):
        if not cherrypy.server.using_wsgi:
            return self.skip("skipped (not using WSGI)... ")

        for year in range(1997, 2008):
            self.getPage("/", headers=[('Host', 'www.classof%s.example' % year)])
            self.assertBody("Welcome to the Class of %s website!" % year)

