# This file is part of CherryPy <http://www.cherrypy.org/>
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:expandtab:fileencoding=utf-8


import cherrypy
from cherrypy.lib import auth_digest

from cherrypy.test import helper

class DigestAuthTest(helper.CPWebCase):

    def setup_server():
        class Root:
            def index(self):
                return "This is public."
            index.exposed = True

        class DigestProtected:
            def index(self):
                return "Hello %s, you've been authorized." % cherrypy.request.login
            index.exposed = True

        def fetch_users():
            return {'test': 'test'}


        get_ha1 = cherrypy.lib.auth_digest.get_ha1_dict_plain(fetch_users())
        conf = {'/digest': {'tools.auth_digest.on': True,
                            'tools.auth_digest.realm': 'localhost',
                            'tools.auth_digest.get_ha1': get_ha1,
                            'tools.auth_digest.key': 'a565c27146791cfb',
                            'tools.auth_digest.debug': 'True'}}

        root = Root()
        root.digest = DigestProtected()
        cherrypy.tree.mount(root, config=conf)
    setup_server = staticmethod(setup_server)

    def testPublic(self):
        self.getPage("/")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/html;charset=utf-8')
        self.assertBody('This is public.')

    def testDigest(self):
        self.getPage("/digest/")
        self.assertStatus(401)

        value = None
        for k, v in self.headers:
            if k.lower() == "www-authenticate":
                if v.startswith("Digest"):
                    value = v
                    break

        if value is None:
            self._handlewebError("Digest authentification scheme was not found")

        value = value[7:]
        items = value.split(', ')
        tokens = {}
        for item in items:
            key, value = item.split('=')
            tokens[key.lower()] = value

        missing_msg = "%s is missing"
        bad_value_msg = "'%s' was expecting '%s' but found '%s'"
        nonce = None
        if 'realm' not in tokens:
            self._handlewebError(missing_msg % 'realm')
        elif tokens['realm'] != '"localhost"':
            self._handlewebError(bad_value_msg % ('realm', '"localhost"', tokens['realm']))
        if 'nonce' not in tokens:
            self._handlewebError(missing_msg % 'nonce')
        else:
            nonce = tokens['nonce'].strip('"')
        if 'algorithm' not in tokens:
            self._handlewebError(missing_msg % 'algorithm')
        elif tokens['algorithm'] != '"MD5"':
            self._handlewebError(bad_value_msg % ('algorithm', '"MD5"', tokens['algorithm']))
        if 'qop' not in tokens:
            self._handlewebError(missing_msg % 'qop')
        elif tokens['qop'] != '"auth"':
            self._handlewebError(bad_value_msg % ('qop', '"auth"', tokens['qop']))

        get_ha1 = auth_digest.get_ha1_dict_plain({'test' : 'test'})

        # Test user agent response with a wrong value for 'realm'
        base_auth = 'Digest username="test", realm="wrong realm", nonce="%s", uri="/digest/", algorithm=MD5, response="%s", qop=auth, nc=%s, cnonce="1522e61005789929"'

        auth_header = base_auth % (nonce, '11111111111111111111111111111111', '00000001')
        auth = auth_digest.HttpDigestAuthorization(auth_header, 'GET')
        # calculate the response digest
        ha1 = get_ha1(auth.realm, 'test')
        response = auth.request_digest(ha1)
        # send response with correct response digest, but wrong realm
        auth_header = base_auth % (nonce, response, '00000001')
        self.getPage('/digest/', [('Authorization', auth_header)])
        self.assertStatus(401)

        # Test that must pass
        base_auth = 'Digest username="test", realm="localhost", nonce="%s", uri="/digest/", algorithm=MD5, response="%s", qop=auth, nc=%s, cnonce="1522e61005789929"'

        auth_header = base_auth % (nonce, '11111111111111111111111111111111', '00000001')
        auth = auth_digest.HttpDigestAuthorization(auth_header, 'GET')
        # calculate the response digest
        ha1 = get_ha1('localhost', 'test')
        response = auth.request_digest(ha1)
        # send response with correct response digest
        auth_header = base_auth % (nonce, response, '00000001')
        self.getPage('/digest/', [('Authorization', auth_header)])
        self.assertStatus('200 OK')
        self.assertBody("Hello test, you've been authorized.")

