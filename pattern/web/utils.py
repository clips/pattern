import re
from collections import Iterable

try:
    # Python 2
    str_type = unicode
except NameError:
    # Python 3
    str_type = str

STRING_LIKE_TYPES = (str_type, bytes, bytearray)

try:
    # Python 2
    from urlparse import urlparse, parse_qsl
except ImportError:
    # Python 3
    from urllib.parse import urlparse, parse_qsl

try:
    import simplejson as json
except ImportError:
    import json


def json_iter_parse(response_text):
    decoder = json.JSONDecoder(strict=False)
    idx = 0
    while idx < len(response_text):
        obj, idx = decoder.raw_decode(response_text, idx)
        yield obj


def stringify_values(dictionary):
    stringified_values_dict = {}
    for key, value in dictionary.items():
        if isinstance(value, Iterable) and not isinstance(value, STRING_LIKE_TYPES):
            value = u','.join(map(str_type, value))
        stringified_values_dict[key] = value
    return stringified_values_dict


def get_url_query(url):
    parsed_url = urlparse(url)
    url_query = parse_qsl(parsed_url.fragment)
    # login_response_url_query can have multiple key
    url_query = dict(url_query)
    return url_query


def get_form_action(html):
    form_action = re.findall(r'<form(?= ).* action="(.+)"', html)
    if form_action:
        return form_action[0]


def censor_access_token(access_token):
    if isinstance(access_token, str_type) and len(access_token) >= 12:
        return '{}***{}'.format(access_token[:4], access_token[-4:])
    elif access_token:
        return '***'
    else:
        return access_token
