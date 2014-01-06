import cherrypy
from cherrypy.test import helper

from cherrypy._cpcompat import json

class JsonTest(helper.CPWebCase):
    def setup_server():
        class Root(object):
            def plain(self):
                return 'hello'
            plain.exposed = True

            def json_string(self):
                return 'hello'
            json_string.exposed = True
            json_string._cp_config = {'tools.json_out.on': True}

            def json_list(self):
                return ['a', 'b', 42]
            json_list.exposed = True
            json_list._cp_config = {'tools.json_out.on': True}

            def json_dict(self):
                return {'answer': 42}
            json_dict.exposed = True
            json_dict._cp_config = {'tools.json_out.on': True}

            def json_post(self):
                if cherrypy.request.json == [13, 'c']:
                    return 'ok'
                else:
                    return 'nok'
            json_post.exposed = True
            json_post._cp_config = {'tools.json_in.on': True}

        root = Root()
        cherrypy.tree.mount(root)
    setup_server = staticmethod(setup_server)

    def test_json_output(self):
        if json is None:
            self.skip("json not found ")
            return

        self.getPage("/plain")
        self.assertBody("hello")

        self.getPage("/json_string")
        self.assertBody('"hello"')

        self.getPage("/json_list")
        self.assertBody('["a", "b", 42]')

        self.getPage("/json_dict")
        self.assertBody('{"answer": 42}')

    def test_json_input(self):
        if json is None:
            self.skip("json not found ")
            return

        body = '[13, "c"]'
        headers = [('Content-Type', 'application/json'),
                   ('Content-Length', str(len(body)))]
        self.getPage("/json_post", method="POST", headers=headers, body=body)
        self.assertBody('ok')

        body = '[13, "c"]'
        headers = [('Content-Type', 'text/plain'),
                   ('Content-Length', str(len(body)))]
        self.getPage("/json_post", method="POST", headers=headers, body=body)
        self.assertStatus(415, 'Expected an application/json content type')

        body = '[13, -]'
        headers = [('Content-Type', 'application/json'),
                   ('Content-Length', str(len(body)))]
        self.getPage("/json_post", method="POST", headers=headers, body=body)
        self.assertStatus(400, 'Invalid JSON document')

