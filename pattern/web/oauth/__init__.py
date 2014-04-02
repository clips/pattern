#### PATTERN | WEB | OAUTH #########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# Naive OAuth implementation for pattern.web.Yahoo and Yahoo! BOSS v2.

import urllib
import hmac
import time
import random
import base64

try:
    from hashlib import sha1
    from hashlib import md5
except:
    import sha as sha1
    import md5; md5=md5.new

_diacritics = {
    "a": ("á","ä","â","à","å"),
    "e": ("é","ë","ê","è"),
    "i": ("í","ï","î","ì"),
    "o": ("ó","ö","ô","ò","ō","ø"),
    "u": ("ú","ü","û","ù","ů"),
    "y": ("ý","ÿ","ý"),
    "s": ("š",),
    "c": ("ç","č"),
    "n": ("ñ",),
    "z": ("ž",)
}

####################################################################################################

def HMAC_SHA1(key, text):
    return hmac.new(key, text, sha1).digest()

def nonce():
    return md5(str(time.time()) + str(random.random())).hexdigest()

def timestamp():
    return int(time.time())

def escape(string):
    return urllib.quote(string, safe="~")

def utf8(string):
    return isinstance(string, unicode) and string.encode("utf-8") or str(string)

def normalize(string):
    # Normalize accents (é => e) for services that have problems with utf-8
    # (used to be the case with Yahoo BOSS but this appears to be fixed now).
    string = utf8(string)
    for k, v in _diacritics.items():
        for v in v: 
            string = string.replace(v, k)
    return string

def base(url, data={}, method="GET"):
    # Signature base string: http://tools.ietf.org/html/rfc5849#section-3.4.1
    base  = escape(utf8(method.upper())) + "&"
    base += escape(utf8(url.rstrip("?"))) + "&"
    base += escape(utf8("&".join(["%s=%s" % (
            escape(utf8(k)), 
            escape(utf8(v))) for k, v in sorted(data.items())])))
    return base

def sign(url, data={}, method="GET", secret="", token="", hash=HMAC_SHA1):
    # HMAC-SHA1 signature algorithm: http://tools.ietf.org/html/rfc5849#section-3.4.2
    signature = escape(utf8(secret)) + "&" + escape(utf8(token))
    signature = hash(signature, base(url, data, method))
    signature = base64.b64encode(signature)
    return signature

#CONSUMER_KEY = ""
#CONSUMER_SECRET = ""
#
#q = "cats"
#url = "http://yboss.yahooapis.com/ysearch/web"
#data = {
#    "q": normalize(q),
#    "start": 0,
#    "count": 50,
#    "format": "json",
#    "oauth_version": "1.0",
#    "oauth_nonce": nonce(),
#    "oauth_timestamp": timestamp(),
#    "oauth_consumer_key": CONSUMER_KEY,
#    "oauth_signature_method": "HMAC-SHA1" 
#}
#data["oauth_signature"] = sign(url, data, secret=CONSUMER_SECRET)
#data = dict((k, utf8(v)) for k, v in data.items())
#
#print(url + "?" + urllib.urlencode(data))
