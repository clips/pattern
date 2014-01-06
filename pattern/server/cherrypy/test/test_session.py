import os
localDir = os.path.dirname(__file__)
import sys
import threading
import time

import cherrypy
from cherrypy._cpcompat import copykeys, HTTPConnection, HTTPSConnection
from cherrypy.lib import sessions
from cherrypy.lib.httputil import response_codes

def http_methods_allowed(methods=['GET', 'HEAD']):
    method = cherrypy.request.method.upper()
    if method not in methods:
        cherrypy.response.headers['Allow'] = ", ".join(methods)
        raise cherrypy.HTTPError(405)

cherrypy.tools.allow = cherrypy.Tool('on_start_resource', http_methods_allowed)


def setup_server():

    class Root:

        _cp_config = {'tools.sessions.on': True,
                      'tools.sessions.storage_type' : 'ram',
                      'tools.sessions.storage_path' : localDir,
                      'tools.sessions.timeout': (1.0 / 60),
                      'tools.sessions.clean_freq': (1.0 / 60),
                      }

        def clear(self):
            cherrypy.session.cache.clear()
        clear.exposed = True

        def data(self):
            cherrypy.session['aha'] = 'foo'
            return repr(cherrypy.session._data)
        data.exposed = True

        def testGen(self):
            counter = cherrypy.session.get('counter', 0) + 1
            cherrypy.session['counter'] = counter
            yield str(counter)
        testGen.exposed = True

        def testStr(self):
            counter = cherrypy.session.get('counter', 0) + 1
            cherrypy.session['counter'] = counter
            return str(counter)
        testStr.exposed = True

        def setsessiontype(self, newtype):
            self.__class__._cp_config.update({'tools.sessions.storage_type': newtype})
            if hasattr(cherrypy, "session"):
                del cherrypy.session
            cls = getattr(sessions, newtype.title() + 'Session')
            if cls.clean_thread:
                cls.clean_thread.stop()
                cls.clean_thread.unsubscribe()
                del cls.clean_thread
        setsessiontype.exposed = True
        setsessiontype._cp_config = {'tools.sessions.on': False}

        def index(self):
            sess = cherrypy.session
            c = sess.get('counter', 0) + 1
            time.sleep(0.01)
            sess['counter'] = c
            return str(c)
        index.exposed = True

        def keyin(self, key):
            return str(key in cherrypy.session)
        keyin.exposed = True

        def delete(self):
            cherrypy.session.delete()
            sessions.expire()
            return "done"
        delete.exposed = True

        def delkey(self, key):
            del cherrypy.session[key]
            return "OK"
        delkey.exposed = True

        def blah(self):
            return self._cp_config['tools.sessions.storage_type']
        blah.exposed = True

        def iredir(self):
            raise cherrypy.InternalRedirect('/blah')
        iredir.exposed = True

        def restricted(self):
            return cherrypy.request.method
        restricted.exposed = True
        restricted._cp_config = {'tools.allow.on': True,
                                 'tools.allow.methods': ['GET']}

        def regen(self):
            cherrypy.tools.sessions.regenerate()
            return "logged in"
        regen.exposed = True

        def length(self):
            return str(len(cherrypy.session))
        length.exposed = True

        def session_cookie(self):
            # Must load() to start the clean thread.
            cherrypy.session.load()
            return cherrypy.session.id
        session_cookie.exposed = True
        session_cookie._cp_config = {
            'tools.sessions.path': '/session_cookie',
            'tools.sessions.name': 'temp',
            'tools.sessions.persistent': False}

    cherrypy.tree.mount(Root())


from cherrypy.test import helper

class SessionTest(helper.CPWebCase):
    setup_server = staticmethod(setup_server)

    def tearDown(self):
        # Clean up sessions.
        for fname in os.listdir(localDir):
            if fname.startswith(sessions.FileSession.SESSION_PREFIX):
                os.unlink(os.path.join(localDir, fname))

    def test_0_Session(self):
        self.getPage('/setsessiontype/ram')
        self.getPage('/clear')

        # Test that a normal request gets the same id in the cookies.
        # Note: this wouldn't work if /data didn't load the session.
        self.getPage('/data')
        self.assertBody("{'aha': 'foo'}")
        c = self.cookies[0]
        self.getPage('/data', self.cookies)
        self.assertEqual(self.cookies[0], c)

        self.getPage('/testStr')
        self.assertBody('1')
        cookie_parts = dict([p.strip().split('=')
                             for p in self.cookies[0][1].split(";")])
        # Assert there is an 'expires' param
        self.assertEqual(set(cookie_parts.keys()),
                         set(['session_id', 'expires', 'Path']))
        self.getPage('/testGen', self.cookies)
        self.assertBody('2')
        self.getPage('/testStr', self.cookies)
        self.assertBody('3')
        self.getPage('/data', self.cookies)
        self.assertBody("{'aha': 'foo', 'counter': 3}")
        self.getPage('/length', self.cookies)
        self.assertBody('2')
        self.getPage('/delkey?key=counter', self.cookies)
        self.assertStatus(200)

        self.getPage('/setsessiontype/file')
        self.getPage('/testStr')
        self.assertBody('1')
        self.getPage('/testGen', self.cookies)
        self.assertBody('2')
        self.getPage('/testStr', self.cookies)
        self.assertBody('3')
        self.getPage('/delkey?key=counter', self.cookies)
        self.assertStatus(200)

        # Wait for the session.timeout (1 second)
        time.sleep(2)
        self.getPage('/')
        self.assertBody('1')
        self.getPage('/length', self.cookies)
        self.assertBody('1')

        # Test session __contains__
        self.getPage('/keyin?key=counter', self.cookies)
        self.assertBody("True")
        cookieset1 = self.cookies

        # Make a new session and test __len__ again
        self.getPage('/')
        self.getPage('/length', self.cookies)
        self.assertBody('2')

        # Test session delete
        self.getPage('/delete', self.cookies)
        self.assertBody("done")
        self.getPage('/delete', cookieset1)
        self.assertBody("done")
        f = lambda: [x for x in os.listdir(localDir) if x.startswith('session-')]
        self.assertEqual(f(), [])

        # Wait for the cleanup thread to delete remaining session files
        self.getPage('/')
        f = lambda: [x for x in os.listdir(localDir) if x.startswith('session-')]
        self.assertNotEqual(f(), [])
        time.sleep(2)
        self.assertEqual(f(), [])

    def test_1_Ram_Concurrency(self):
        self.getPage('/setsessiontype/ram')
        self._test_Concurrency()

    def test_2_File_Concurrency(self):
        self.getPage('/setsessiontype/file')
        self._test_Concurrency()

    def _test_Concurrency(self):
        client_thread_count = 5
        request_count = 30

        # Get initial cookie
        self.getPage("/")
        self.assertBody("1")
        cookies = self.cookies

        data_dict = {}
        errors = []

        def request(index):
            if self.scheme == 'https':
                c = HTTPSConnection('%s:%s' % (self.interface(), self.PORT))
            else:
                c = HTTPConnection('%s:%s' % (self.interface(), self.PORT))
            for i in range(request_count):
                c.putrequest('GET', '/')
                for k, v in cookies:
                    c.putheader(k, v)
                c.endheaders()
                response = c.getresponse()
                body = response.read()
                if response.status != 200 or not body.isdigit():
                    errors.append((response.status, body))
                else:
                    data_dict[index] = max(data_dict[index], int(body))
                # Uncomment the following line to prove threads overlap.
##                sys.stdout.write("%d " % index)

        # Start <request_count> requests from each of
        # <client_thread_count> concurrent clients
        ts = []
        for c in range(client_thread_count):
            data_dict[c] = 0
            t = threading.Thread(target=request, args=(c,))
            ts.append(t)
            t.start()

        for t in ts:
            t.join()

        hitcount = max(data_dict.values())
        expected = 1 + (client_thread_count * request_count)

        for e in errors:
            print(e)
        self.assertEqual(hitcount, expected)

    def test_3_Redirect(self):
        # Start a new session
        self.getPage('/testStr')
        self.getPage('/iredir', self.cookies)
        self.assertBody("file")

    def test_4_File_deletion(self):
        # Start a new session
        self.getPage('/testStr')
        # Delete the session file manually and retry.
        id = self.cookies[0][1].split(";", 1)[0].split("=", 1)[1]
        path = os.path.join(localDir, "session-" + id)
        os.unlink(path)
        self.getPage('/testStr', self.cookies)

    def test_5_Error_paths(self):
        self.getPage('/unknown/page')
        self.assertErrorPage(404, "The path '/unknown/page' was not found.")

        # Note: this path is *not* the same as above. The above
        # takes a normal route through the session code; this one
        # skips the session code's before_handler and only calls
        # before_finalize (save) and on_end (close). So the session
        # code has to survive calling save/close without init.
        self.getPage('/restricted', self.cookies, method='POST')
        self.assertErrorPage(405, response_codes[405][1])

    def test_6_regenerate(self):
        self.getPage('/testStr')
        # grab the cookie ID
        id1 = self.cookies[0][1].split(";", 1)[0].split("=", 1)[1]
        self.getPage('/regen')
        self.assertBody('logged in')
        id2 = self.cookies[0][1].split(";", 1)[0].split("=", 1)[1]
        self.assertNotEqual(id1, id2)

        self.getPage('/testStr')
        # grab the cookie ID
        id1 = self.cookies[0][1].split(";", 1)[0].split("=", 1)[1]
        self.getPage('/testStr',
                     headers=[('Cookie',
                               'session_id=maliciousid; '
                               'expires=Sat, 27 Oct 2017 04:18:28 GMT; Path=/;')])
        id2 = self.cookies[0][1].split(";", 1)[0].split("=", 1)[1]
        self.assertNotEqual(id1, id2)
        self.assertNotEqual(id2, 'maliciousid')

    def test_7_session_cookies(self):
        self.getPage('/setsessiontype/ram')
        self.getPage('/clear')
        self.getPage('/session_cookie')
        # grab the cookie ID
        cookie_parts = dict([p.strip().split('=') for p in self.cookies[0][1].split(";")])
        # Assert there is no 'expires' param
        self.assertEqual(set(cookie_parts.keys()), set(['temp', 'Path']))
        id1 = cookie_parts['temp']
        self.assertEqual(copykeys(sessions.RamSession.cache), [id1])

        # Send another request in the same "browser session".
        self.getPage('/session_cookie', self.cookies)
        cookie_parts = dict([p.strip().split('=') for p in self.cookies[0][1].split(";")])
        # Assert there is no 'expires' param
        self.assertEqual(set(cookie_parts.keys()), set(['temp', 'Path']))
        self.assertBody(id1)
        self.assertEqual(copykeys(sessions.RamSession.cache), [id1])

        # Simulate a browser close by just not sending the cookies
        self.getPage('/session_cookie')
        # grab the cookie ID
        cookie_parts = dict([p.strip().split('=') for p in self.cookies[0][1].split(";")])
        # Assert there is no 'expires' param
        self.assertEqual(set(cookie_parts.keys()), set(['temp', 'Path']))
        # Assert a new id has been generated...
        id2 = cookie_parts['temp']
        self.assertNotEqual(id1, id2)
        self.assertEqual(set(sessions.RamSession.cache.keys()), set([id1, id2]))

        # Wait for the session.timeout on both sessions
        time.sleep(2.5)
        cache = copykeys(sessions.RamSession.cache)
        if cache:
            if cache == [id2]:
                self.fail("The second session did not time out.")
            else:
                self.fail("Unknown session id in cache: %r", cache)


import socket
try:
    import memcache

    host, port = '127.0.0.1', 11211
    for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                  socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        s = None
        try:
            s = socket.socket(af, socktype, proto)
            # See http://groups.google.com/group/cherrypy-users/
            #        browse_frm/thread/bbfe5eb39c904fe0
            s.settimeout(1.0)
            s.connect((host, port))
            s.close()
        except socket.error:
            if s:
                s.close()
            raise
        break
except (ImportError, socket.error):
    class MemcachedSessionTest(helper.CPWebCase):
        setup_server = staticmethod(setup_server)

        def test(self):
            return self.skip("memcached not reachable ")
else:
    class MemcachedSessionTest(helper.CPWebCase):
        setup_server = staticmethod(setup_server)

        def test_0_Session(self):
            self.getPage('/setsessiontype/memcached')

            self.getPage('/testStr')
            self.assertBody('1')
            self.getPage('/testGen', self.cookies)
            self.assertBody('2')
            self.getPage('/testStr', self.cookies)
            self.assertBody('3')
            self.getPage('/length', self.cookies)
            self.assertErrorPage(500)
            self.assertInBody("NotImplementedError")
            self.getPage('/delkey?key=counter', self.cookies)
            self.assertStatus(200)

            # Wait for the session.timeout (1 second)
            time.sleep(1.25)
            self.getPage('/')
            self.assertBody('1')

            # Test session __contains__
            self.getPage('/keyin?key=counter', self.cookies)
            self.assertBody("True")

            # Test session delete
            self.getPage('/delete', self.cookies)
            self.assertBody("done")

        def test_1_Concurrency(self):
            client_thread_count = 5
            request_count = 30

            # Get initial cookie
            self.getPage("/")
            self.assertBody("1")
            cookies = self.cookies

            data_dict = {}

            def request(index):
                for i in range(request_count):
                    self.getPage("/", cookies)
                    # Uncomment the following line to prove threads overlap.
##                    sys.stdout.write("%d " % index)
                if not self.body.isdigit():
                    self.fail(self.body)
                data_dict[index] = v = int(self.body)

            # Start <request_count> concurrent requests from
            # each of <client_thread_count> clients
            ts = []
            for c in range(client_thread_count):
                data_dict[c] = 0
                t = threading.Thread(target=request, args=(c,))
                ts.append(t)
                t.start()

            for t in ts:
                t.join()

            hitcount = max(data_dict.values())
            expected = 1 + (client_thread_count * request_count)
            self.assertEqual(hitcount, expected)

        def test_3_Redirect(self):
            # Start a new session
            self.getPage('/testStr')
            self.getPage('/iredir', self.cookies)
            self.assertBody("memcached")

        def test_5_Error_paths(self):
            self.getPage('/unknown/page')
            self.assertErrorPage(404, "The path '/unknown/page' was not found.")

            # Note: this path is *not* the same as above. The above
            # takes a normal route through the session code; this one
            # skips the session code's before_handler and only calls
            # before_finalize (save) and on_end (close). So the session
            # code has to survive calling save/close without init.
            self.getPage('/restricted', self.cookies, method='POST')
            self.assertErrorPage(405, response_codes[405][1])

