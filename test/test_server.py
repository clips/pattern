# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from builtins import object

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest

from pattern import server

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""

#---------------------------------------------------------------------------------------------------


class TestEntities(unittest.TestCase):

    def test_encode_entities(self):
        '''Assert HTML entity encoder (e.g., "&" => "&amp;")'''
        for a, b in (
          ("&#201;", "&#201;"),
          ("&", "&amp;"),
          ("<", "&lt;"),
          (">", "&gt;"),
          ('"', "&quot;"),
          ("'", "&#39;")):
            self.assertEqual(server.encode_entities(a), b)
        print("pattern.server.encode_entities()")

    def test_decode_entities(self):
        '''Assert HMTL entity decoder (e.g., "&amp;" => "&")'''
        for a, b in (
          ("&#38;", "&"),
          ("&amp;", "&"),
          ("&#x0026;", "&"),
          ("&#160;", "\xa0"),
          ("&foo;", "&foo;")):
            self.assertEqual(server.decode_entities(a), b)
        print("pattern.server.decode_entities()")

#---------------------------------------------------------------------------------------------------


class TestURL(unittest.TestCase):

    def setUp(self):
        self.utf_encoded_pairs = (
          (u'black/white', u'black%2Fwhite'),
          (u"| \\\n/!@#$%*()[]{}'\"", u"%7C+%5C%0A%2F%21%40%23%24%25%2A%28%29%5B%5D%7B%7D%27%22"))

    def test_encode_url(self):
        '''Assert query string url encoder (e.g., "black/white" => "black%2Fwhite")'''
        for utf, encoded in self.utf_encoded_pairs:
            self.assertEqual(server.encode_url(utf), encoded)
        print("pattern.server.encode_url()")

    def test_decode_url(self):
        '''Assert query string url decoder (e.g., "black%2Fwhite" => "black/white")'''
        for utf, encoded in self.utf_encoded_pairs:
            self.assertEqual(server.decode_url(encoded), utf)
        print("pattern.server.decode_url()")


#---------------------------------------------------------------------------------------------------


class TestTemplate(unittest.TestCase):

    def test_template(self):
        '''Assert template compiling, encoding and rendering works.'''
        self.assertEqual(
            server.template('test_template.html', root=PATH, cached=False),
            '<html>\n    <body>\n    \n    6\n    </body>\n</html>\n'
        )
        s = """
            <html>
            <head>
               <title>$title</title>
            </head>
            <body>
            <% for $i, $name in enumerate(names): %>
               <b><%= i+1 %>) Hello $name!</b>
            <% end for %>
            </body>
            </html>
            """
        self.assertEqual(
            server.template(s.strip(), title="test", names=["Tom", "Walter"]),
            '<html>\n            <head>\n               <title>test</title>\n            </head>\n            <body>\n                           <b>1) Hello Tom!</b>\n                           <b>2) Hello Walter!</b>\n            \n            </body>\n            </html>'
        )

    def test_caching(self):
        '''Assert cache works.'''
        self.assertEqual(id(server.Template("")._compiled), id(server.Template("")._compiled))

    def test_escape(self):
        '''Assert str, unicode, int, long, float, bool and None field values.'''
        for v, s in (
          ("Above\nUnder", "Above\\nUnder"), ):
            self.assertEqual(server.Template("")._escape(v), s)
        print("pattern.server.Template._escape()")

#---------------------------------------------------------------------------------------------------


def suite(**kwargs):

    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEntities))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestURL))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestTemplate))

    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
