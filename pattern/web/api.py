#--- API LICENSE CONFIGURATION -----------------------------------------------------------------------
# Default license keys used by pattern.web.SearchEngine to contact different API's.
# Google and Yahoo are paid services for which you need a personal license + payment method.
# The default Google license is for testing purposes (= 100 daily queries).
# Wikipedia, Twitter and Facebook are free.
# Bing, Flickr and ProductsWiki use licenses shared among all Pattern users.

from __future__ import unicode_literals
from builtins import dict

license = {}
license["Google"] = \
    "AIzaSyBxe9jC4WLr-Rry_5OUMOZ7PCsEyWpiU48"

license["Bing"] = \
    "VnJEK4HTlntE3SyF58QLkUCLp/78tkYjV1Fl3J7lHa0="

license["Yahoo"] = \
    ("", "") # OAuth (key, secret)

license["DuckDuckGo"] = \
    None

license["Faroo"] = \
    ""

license["Wikipedia"] = \
    None

license["Twitter"] = (
    "p7HUdPLlkKaqlPn6TzKkA", # OAuth (key, secret, token)
    "R7I1LRuLY27EKjzulutov74lKB0FjqcI2DYRUmsu7DQ", (
    "14898655-TE9dXQLrzrNd0Zwf4zhK7koR5Ahqt40Ftt35Y2qY",
    "q1lSRDOguxQrfgeWWSJgnMHsO67bqTd5dTElBsyTM"))

license["Facebook"] = \
    "332061826907464|jdHvL3lslFvN-s_sphK1ypCwNaY"

license["Flickr"] = \
    "787081027f43b0412ba41142d4540480"

license["ProductWiki"] = \
    "64819965ec784395a494a0d7ed0def32"
