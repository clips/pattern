
import gzip
import sys

import cherrypy
from cherrypy._cpcompat import BytesIO, IncompleteRead, ntob, ntou

europoundUnicode = ntou('\x80\xa3')
sing = ntou("\u6bdb\u6cfd\u4e1c: Sing, Little Birdie?", 'escape')
sing8 = sing.encode('utf-8')
sing16 = sing.encode('utf-16')


from cherrypy.test import helper


class EncodingTests(helper.CPWebCase):

    def setup_server():
        class Root:
            def index(self, param):
                assert param == europoundUnicode, "%r != %r" % (param, europoundUnicode)
                yield europoundUnicode
            index.exposed = True

            def mao_zedong(self):
                return sing
            mao_zedong.exposed = True

            def utf8(self):
                return sing8
            utf8.exposed = True
            utf8._cp_config = {'tools.encode.encoding': 'utf-8'}

            def cookies_and_headers(self):
                # if the headers have non-ascii characters and a cookie has
                #  any part which is unicode (even ascii), the response
                #  should not fail.
                cherrypy.response.cookie['candy'] = 'bar'
                cherrypy.response.cookie['candy']['domain'] = 'cherrypy.org'
                cherrypy.response.headers['Some-Header'] = 'My d\xc3\xb6g has fleas'
                return 'Any content'
            cookies_and_headers.exposed = True

            def reqparams(self, *args, **kwargs):
                return ntob(', ').join([": ".join((k, v)).encode('utf8')
                                  for k, v in cherrypy.request.params.items()])
            reqparams.exposed = True

            def nontext(self, *args, **kwargs):
                cherrypy.response.headers['Content-Type'] = 'application/binary'
                return '\x00\x01\x02\x03'
            nontext.exposed = True
            nontext._cp_config = {'tools.encode.text_only': False,
                                  'tools.encode.add_charset': True,
                                  }

        class GZIP:
            def index(self):
                yield "Hello, world"
            index.exposed = True

            def noshow(self):
                # Test for ticket #147, where yield showed no exceptions (content-
                # encoding was still gzip even though traceback wasn't zipped).
                raise IndexError()
                yield "Here be dragons"
            noshow.exposed = True
            # Turn encoding off so the gzip tool is the one doing the collapse.
            noshow._cp_config = {'tools.encode.on': False}

            def noshow_stream(self):
                # Test for ticket #147, where yield showed no exceptions (content-
                # encoding was still gzip even though traceback wasn't zipped).
                raise IndexError()
                yield "Here be dragons"
            noshow_stream.exposed = True
            noshow_stream._cp_config = {'response.stream': True}

        class Decode:
            def extra_charset(self, *args, **kwargs):
                return ', '.join([": ".join((k, v))
                                  for k, v in cherrypy.request.params.items()])
            extra_charset.exposed = True
            extra_charset._cp_config = {
                'tools.decode.on': True,
                'tools.decode.default_encoding': ['utf-16'],
                }

            def force_charset(self, *args, **kwargs):
                return ', '.join([": ".join((k, v))
                                  for k, v in cherrypy.request.params.items()])
            force_charset.exposed = True
            force_charset._cp_config = {
                'tools.decode.on': True,
                'tools.decode.encoding': 'utf-16',
                }

        root = Root()
        root.gzip = GZIP()
        root.decode = Decode()
        cherrypy.tree.mount(root, config={'/gzip': {'tools.gzip.on': True}})
    setup_server = staticmethod(setup_server)

    def test_query_string_decoding(self):
        europoundUtf8 = europoundUnicode.encode('utf-8')
        self.getPage(ntob('/?param=') + europoundUtf8)
        self.assertBody(europoundUtf8)

        # Encoded utf8 query strings MUST be parsed correctly.
        # Here, q is the POUND SIGN U+00A3 encoded in utf8 and then %HEX
        self.getPage("/reqparams?q=%C2%A3")
        # The return value will be encoded as utf8.
        self.assertBody(ntob("q: \xc2\xa3"))

        # Query strings that are incorrectly encoded MUST raise 404.
        # Here, q is the POUND SIGN U+00A3 encoded in latin1 and then %HEX
        self.getPage("/reqparams?q=%A3")
        self.assertStatus(404)
        self.assertErrorPage(404,
            "The given query string could not be processed. Query "
            "strings for this resource must be encoded with 'utf8'.")

    def test_urlencoded_decoding(self):
        # Test the decoding of an application/x-www-form-urlencoded entity.
        europoundUtf8 = europoundUnicode.encode('utf-8')
        body=ntob("param=") + europoundUtf8
        self.getPage('/', method='POST',
                     headers=[("Content-Type", "application/x-www-form-urlencoded"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertBody(europoundUtf8)

        # Encoded utf8 entities MUST be parsed and decoded correctly.
        # Here, q is the POUND SIGN U+00A3 encoded in utf8
        body = ntob("q=\xc2\xa3")
        self.getPage('/reqparams', method='POST',
                     headers=[("Content-Type", "application/x-www-form-urlencoded"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertBody(ntob("q: \xc2\xa3"))

        # ...and in utf16, which is not in the default attempt_charsets list:
        body = ntob("\xff\xfeq\x00=\xff\xfe\xa3\x00")
        self.getPage('/reqparams', method='POST',
                     headers=[("Content-Type", "application/x-www-form-urlencoded;charset=utf-16"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertBody(ntob("q: \xc2\xa3"))

        # Entities that are incorrectly encoded MUST raise 400.
        # Here, q is the POUND SIGN U+00A3 encoded in utf16, but
        # the Content-Type incorrectly labels it utf-8.
        body = ntob("\xff\xfeq\x00=\xff\xfe\xa3\x00")
        self.getPage('/reqparams', method='POST',
                     headers=[("Content-Type", "application/x-www-form-urlencoded;charset=utf-8"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertStatus(400)
        self.assertErrorPage(400,
            "The request entity could not be decoded. The following charsets "
            "were attempted: ['utf-8']")

    def test_decode_tool(self):
        # An extra charset should be tried first, and succeed if it matches.
        # Here, we add utf-16 as a charset and pass a utf-16 body.
        body = ntob("\xff\xfeq\x00=\xff\xfe\xa3\x00")
        self.getPage('/decode/extra_charset', method='POST',
                     headers=[("Content-Type", "application/x-www-form-urlencoded"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertBody(ntob("q: \xc2\xa3"))

        # An extra charset should be tried first, and continue to other default
        # charsets if it doesn't match.
        # Here, we add utf-16 as a charset but still pass a utf-8 body.
        body = ntob("q=\xc2\xa3")
        self.getPage('/decode/extra_charset', method='POST',
                     headers=[("Content-Type", "application/x-www-form-urlencoded"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertBody(ntob("q: \xc2\xa3"))

        # An extra charset should error if force is True and it doesn't match.
        # Here, we force utf-16 as a charset but still pass a utf-8 body.
        body = ntob("q=\xc2\xa3")
        self.getPage('/decode/force_charset', method='POST',
                     headers=[("Content-Type", "application/x-www-form-urlencoded"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertErrorPage(400,
            "The request entity could not be decoded. The following charsets "
            "were attempted: ['utf-16']")

    def test_multipart_decoding(self):
        # Test the decoding of a multipart entity when the charset (utf16) is
        # explicitly given.
        body=ntob('\r\n'.join(['--X',
                               'Content-Type: text/plain;charset=utf-16',
                               'Content-Disposition: form-data; name="text"',
                               '',
                               '\xff\xfea\x00b\x00\x1c c\x00',
                               '--X',
                               'Content-Type: text/plain;charset=utf-16',
                               'Content-Disposition: form-data; name="submit"',
                               '',
                               '\xff\xfeC\x00r\x00e\x00a\x00t\x00e\x00',
                               '--X--']))
        self.getPage('/reqparams', method='POST',
                     headers=[("Content-Type", "multipart/form-data;boundary=X"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertBody(ntob("text: ab\xe2\x80\x9cc, submit: Create"))

    def test_multipart_decoding_no_charset(self):
        # Test the decoding of a multipart entity when the charset (utf8) is
        # NOT explicitly given, but is in the list of charsets to attempt.
        body=ntob('\r\n'.join(['--X',
                               'Content-Disposition: form-data; name="text"',
                               '',
                               '\xe2\x80\x9c',
                               '--X',
                               'Content-Disposition: form-data; name="submit"',
                               '',
                               'Create',
                               '--X--']))
        self.getPage('/reqparams', method='POST',
                     headers=[("Content-Type", "multipart/form-data;boundary=X"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertBody(ntob("text: \xe2\x80\x9c, submit: Create"))

    def test_multipart_decoding_no_successful_charset(self):
        # Test the decoding of a multipart entity when the charset (utf16) is
        # NOT explicitly given, and is NOT in the list of charsets to attempt.
        body=ntob('\r\n'.join(['--X',
                               'Content-Disposition: form-data; name="text"',
                               '',
                               '\xff\xfea\x00b\x00\x1c c\x00',
                               '--X',
                               'Content-Disposition: form-data; name="submit"',
                               '',
                               '\xff\xfeC\x00r\x00e\x00a\x00t\x00e\x00',
                               '--X--']))
        self.getPage('/reqparams', method='POST',
                     headers=[("Content-Type", "multipart/form-data;boundary=X"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertStatus(400)
        self.assertErrorPage(400,
            "The request entity could not be decoded. The following charsets "
            "were attempted: ['us-ascii', 'utf-8']")

    def test_nontext(self):
        self.getPage('/nontext')
        self.assertHeader('Content-Type', 'application/binary;charset=utf-8')
        self.assertBody('\x00\x01\x02\x03')

    def testEncoding(self):
        # Default encoding should be utf-8
        self.getPage('/mao_zedong')
        self.assertBody(sing8)

        # Ask for utf-16.
        self.getPage('/mao_zedong', [('Accept-Charset', 'utf-16')])
        self.assertHeader('Content-Type', 'text/html;charset=utf-16')
        self.assertBody(sing16)

        # Ask for multiple encodings. ISO-8859-1 should fail, and utf-16
        # should be produced.
        self.getPage('/mao_zedong', [('Accept-Charset',
                                      'iso-8859-1;q=1, utf-16;q=0.5')])
        self.assertBody(sing16)

        # The "*" value should default to our default_encoding, utf-8
        self.getPage('/mao_zedong', [('Accept-Charset', '*;q=1, utf-7;q=.2')])
        self.assertBody(sing8)

        # Only allow iso-8859-1, which should fail and raise 406.
        self.getPage('/mao_zedong', [('Accept-Charset', 'iso-8859-1, *;q=0')])
        self.assertStatus("406 Not Acceptable")
        self.assertInBody("Your client sent this Accept-Charset header: "
                          "iso-8859-1, *;q=0. We tried these charsets: "
                          "iso-8859-1.")

        # Ask for x-mac-ce, which should be unknown. See ticket #569.
        self.getPage('/mao_zedong', [('Accept-Charset',
                                      'us-ascii, ISO-8859-1, x-mac-ce')])
        self.assertStatus("406 Not Acceptable")
        self.assertInBody("Your client sent this Accept-Charset header: "
                          "us-ascii, ISO-8859-1, x-mac-ce. We tried these "
                          "charsets: ISO-8859-1, us-ascii, x-mac-ce.")

        # Test the 'encoding' arg to encode.
        self.getPage('/utf8')
        self.assertBody(sing8)
        self.getPage('/utf8', [('Accept-Charset', 'us-ascii, ISO-8859-1')])
        self.assertStatus("406 Not Acceptable")

    def testGzip(self):
        zbuf = BytesIO()
        zfile = gzip.GzipFile(mode='wb', fileobj=zbuf, compresslevel=9)
        zfile.write(ntob("Hello, world"))
        zfile.close()

        self.getPage('/gzip/', headers=[("Accept-Encoding", "gzip")])
        self.assertInBody(zbuf.getvalue()[:3])
        self.assertHeader("Vary", "Accept-Encoding")
        self.assertHeader("Content-Encoding", "gzip")

        # Test when gzip is denied.
        self.getPage('/gzip/', headers=[("Accept-Encoding", "identity")])
        self.assertHeader("Vary", "Accept-Encoding")
        self.assertNoHeader("Content-Encoding")
        self.assertBody("Hello, world")

        self.getPage('/gzip/', headers=[("Accept-Encoding", "gzip;q=0")])
        self.assertHeader("Vary", "Accept-Encoding")
        self.assertNoHeader("Content-Encoding")
        self.assertBody("Hello, world")

        self.getPage('/gzip/', headers=[("Accept-Encoding", "*;q=0")])
        self.assertStatus(406)
        self.assertNoHeader("Content-Encoding")
        self.assertErrorPage(406, "identity, gzip")

        # Test for ticket #147
        self.getPage('/gzip/noshow', headers=[("Accept-Encoding", "gzip")])
        self.assertNoHeader('Content-Encoding')
        self.assertStatus(500)
        self.assertErrorPage(500, pattern="IndexError\n")

        # In this case, there's nothing we can do to deliver a
        # readable page, since 1) the gzip header is already set,
        # and 2) we may have already written some of the body.
        # The fix is to never stream yields when using gzip.
        if (cherrypy.server.protocol_version == "HTTP/1.0" or
            getattr(cherrypy.server, "using_apache", False)):
            self.getPage('/gzip/noshow_stream',
                         headers=[("Accept-Encoding", "gzip")])
            self.assertHeader('Content-Encoding', 'gzip')
            self.assertInBody('\x1f\x8b\x08\x00')
        else:
            # The wsgiserver will simply stop sending data, and the HTTP client
            # will error due to an incomplete chunk-encoded stream.
            self.assertRaises((ValueError, IncompleteRead), self.getPage,
                              '/gzip/noshow_stream',
                              headers=[("Accept-Encoding", "gzip")])

    def test_UnicodeHeaders(self):
        self.getPage('/cookies_and_headers')
        self.assertBody('Any content')

