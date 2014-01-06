import cherrypy
from cherrypy._cpcompat import ntou
from cherrypy.test import helper


class ETagTest(helper.CPWebCase):

    def setup_server():
        class Root:
            def resource(self):
                return "Oh wah ta goo Siam."
            resource.exposed = True

            def fail(self, code):
                code = int(code)
                if 300 <= code <= 399:
                    raise cherrypy.HTTPRedirect([], code)
                else:
                    raise cherrypy.HTTPError(code)
            fail.exposed = True

            def unicoded(self):
                return ntou('I am a \u1ee4nicode string.', 'escape')
            unicoded.exposed = True
            # In Python 3, tools.encode is on by default
            unicoded._cp_config = {'tools.encode.on': True}

        conf = {'/': {'tools.etags.on': True,
                      'tools.etags.autotags': True,
                      }}
        cherrypy.tree.mount(Root(), config=conf)
    setup_server = staticmethod(setup_server)

    def test_etags(self):
        self.getPage("/resource")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/html;charset=utf-8')
        self.assertBody('Oh wah ta goo Siam.')
        etag = self.assertHeader('ETag')

        # Test If-Match (both valid and invalid)
        self.getPage("/resource", headers=[('If-Match', etag)])
        self.assertStatus("200 OK")
        self.getPage("/resource", headers=[('If-Match', "*")])
        self.assertStatus("200 OK")
        self.getPage("/resource", headers=[('If-Match', "*")], method="POST")
        self.assertStatus("200 OK")
        self.getPage("/resource", headers=[('If-Match', "a bogus tag")])
        self.assertStatus("412 Precondition Failed")

        # Test If-None-Match (both valid and invalid)
        self.getPage("/resource", headers=[('If-None-Match', etag)])
        self.assertStatus(304)
        self.getPage("/resource", method='POST', headers=[('If-None-Match', etag)])
        self.assertStatus("412 Precondition Failed")
        self.getPage("/resource", headers=[('If-None-Match', "*")])
        self.assertStatus(304)
        self.getPage("/resource", headers=[('If-None-Match', "a bogus tag")])
        self.assertStatus("200 OK")

    def test_errors(self):
        self.getPage("/resource")
        self.assertStatus(200)
        etag = self.assertHeader('ETag')

        # Test raising errors in page handler
        self.getPage("/fail/412", headers=[('If-Match', etag)])
        self.assertStatus(412)
        self.getPage("/fail/304", headers=[('If-Match', etag)])
        self.assertStatus(304)
        self.getPage("/fail/412", headers=[('If-None-Match', "*")])
        self.assertStatus(412)
        self.getPage("/fail/304", headers=[('If-None-Match', "*")])
        self.assertStatus(304)

    def test_unicode_body(self):
        self.getPage("/unicoded")
        self.assertStatus(200)
        etag1 = self.assertHeader('ETag')
        self.getPage("/unicoded", headers=[('If-Match', etag1)])
        self.assertStatus(200)
        self.assertHeader('ETag', etag1)

