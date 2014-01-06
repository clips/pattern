"""Tests for various MIME issues, including the safe_multipart Tool."""

import cherrypy
from cherrypy._cpcompat import ntob, ntou, sorted

def setup_server():

    class Root:

        def multipart(self, parts):
            return repr(parts)
        multipart.exposed = True

        def multipart_form_data(self, **kwargs):
            return repr(list(sorted(kwargs.items())))
        multipart_form_data.exposed = True

        def flashupload(self, Filedata, Upload, Filename):
            return ("Upload: %s, Filename: %s, Filedata: %r" %
                    (Upload, Filename, Filedata.file.read()))
        flashupload.exposed = True

    cherrypy.config.update({'server.max_request_body_size': 0})
    cherrypy.tree.mount(Root())


#                             Client-side code                             #

from cherrypy.test import helper

class MultipartTest(helper.CPWebCase):
    setup_server = staticmethod(setup_server)

    def test_multipart(self):
        text_part = ntou("This is the text version")
        html_part = ntou("""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
 <meta content="text/html;charset=ISO-8859-1" http-equiv="Content-Type">
</head>
<body bgcolor="#ffffff" text="#000000">

This is the <strong>HTML</strong> version
</body>
</html>
""")
        body = '\r\n'.join([
            "--123456789",
            "Content-Type: text/plain; charset='ISO-8859-1'",
            "Content-Transfer-Encoding: 7bit",
            "",
            text_part,
            "--123456789",
            "Content-Type: text/html; charset='ISO-8859-1'",
            "",
            html_part,
            "--123456789--"])
        headers = [
            ('Content-Type', 'multipart/mixed; boundary=123456789'),
            ('Content-Length', str(len(body))),
            ]
        self.getPage('/multipart', headers, "POST", body)
        self.assertBody(repr([text_part, html_part]))

    def test_multipart_form_data(self):
        body='\r\n'.join(['--X',
                          'Content-Disposition: form-data; name="foo"',
                          '',
                          'bar',
                          '--X',
                          # Test a param with more than one value.
                          # See http://www.cherrypy.org/ticket/1028
                          'Content-Disposition: form-data; name="baz"',
                          '',
                          '111',
                          '--X',
                          'Content-Disposition: form-data; name="baz"',
                          '',
                          '333',
                          '--X--'])
        self.getPage('/multipart_form_data', method='POST',
                     headers=[("Content-Type", "multipart/form-data;boundary=X"),
                              ("Content-Length", str(len(body))),
                              ],
                     body=body),
        self.assertBody(repr([('baz', [ntou('111'), ntou('333')]), ('foo', ntou('bar'))]))


class SafeMultipartHandlingTest(helper.CPWebCase):
    setup_server = staticmethod(setup_server)

    def test_Flash_Upload(self):
        headers = [
            ('Accept', 'text/*'),
            ('Content-Type', 'multipart/form-data; '
                 'boundary=----------KM7Ij5cH2KM7Ef1gL6ae0ae0cH2gL6'),
            ('User-Agent', 'Shockwave Flash'),
            ('Host', 'www.example.com:54583'),
            ('Content-Length', '499'),
            ('Connection', 'Keep-Alive'),
            ('Cache-Control', 'no-cache'),
            ]
        filedata = ntob('<?xml version="1.0" encoding="UTF-8"?>\r\n'
                        '<projectDescription>\r\n'
                        '</projectDescription>\r\n')
        body = (ntob(
            '------------KM7Ij5cH2KM7Ef1gL6ae0ae0cH2gL6\r\n'
            'Content-Disposition: form-data; name="Filename"\r\n'
            '\r\n'
            '.project\r\n'
            '------------KM7Ij5cH2KM7Ef1gL6ae0ae0cH2gL6\r\n'
            'Content-Disposition: form-data; '
                'name="Filedata"; filename=".project"\r\n'
            'Content-Type: application/octet-stream\r\n'
            '\r\n')
            + filedata +
            ntob('\r\n'
            '------------KM7Ij5cH2KM7Ef1gL6ae0ae0cH2gL6\r\n'
            'Content-Disposition: form-data; name="Upload"\r\n'
            '\r\n'
            'Submit Query\r\n'
            # Flash apps omit the trailing \r\n on the last line:
            '------------KM7Ij5cH2KM7Ef1gL6ae0ae0cH2gL6--'
            ))
        self.getPage('/flashupload', headers, "POST", body)
        self.assertBody("Upload: Submit Query, Filename: .project, "
                        "Filedata: %r" % filedata)

