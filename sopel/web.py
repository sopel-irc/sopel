# coding=utf-8
"""
*Availability: 3+, depreacted in 6.2.0*

The web class contains essential web-related functions for interaction with web
applications or websites in your modules.  It supports HTTP GET, HTTP POST and
HTTP HEAD.
"""
# Copyright © 2008, Sean B. Palmer, inamidst.com
# Copyright © 2009, Michael Yanovich <yanovich.1@osu.edu>
# Copyright © 2012, Dimitri Molenaars, Tyrope.nl.
# Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals, absolute_import, print_function, division

import re
import sys
import urllib
import requests

from sopel import __version__
from sopel.tools import deprecated

if sys.version_info.major < 3:
    import httplib
    from htmlentitydefs import name2codepoint
    from urlparse import urlparse
    from urlparse import urlunparse
else:
    import http.client as httplib
    from html.entities import name2codepoint
    from urllib.parse import urlparse
    from urllib.parse import urlunparse
    unichr = chr
    unicode = str

try:
    import ssl
    if not hasattr(ssl, 'match_hostname'):
        # Attempt to import ssl_match_hostname from python-backports
        import backports.ssl_match_hostname
        ssl.match_hostname = backports.ssl_match_hostname.match_hostname
        ssl.CertificateError = backports.ssl_match_hostname.CertificateError
    has_ssl = True
except ImportError:
    has_ssl = False

USER_AGENT = 'Sopel/{} (https://sopel.chat)'.format(__version__)
default_headers = {'User-Agent': USER_AGENT}
ca_certs = None  # Will be overriden when config loads. This is for an edge case.


class MockHttpResponse(httplib.HTTPResponse):
    "Mock HTTPResponse with data that comes from requests."
    def __init__(self, response):
        self.headers = response.headers
        self.status = response.status_code
        self.reason = response.reason
        self.close = response.close
        self.read = response.raw.read
        self.url = response.url

    def geturl(self):
        return self.url


# HTTP GET
@deprecated
def get(uri, timeout=20, headers=None, return_headers=False,
        limit_bytes=None, verify_ssl=True, dont_decode=False):  # pragma: no cover
    """Execute an HTTP GET query on `uri`, and return the result. Deprecated.

    `timeout` is an optional argument, which represents how much time we should
    wait before throwing a timeout exception. It defaults to 20, but can be set
    to higher values if you are communicating with a slow web application.
    `headers` is a dict of HTTP headers to send with the request.  If
    `return_headers` is True, return a tuple of (bytes, headers)

    `limit_bytes` is ignored.

    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    if headers is None:
        headers = default_headers
    else:
        tmp = default_headers.copy()
        tmp.update(headers)
        headers = tmp
    u = requests.get(uri, timeout=timeout, headers=headers, verify=verify_ssl)
    bytes = u.content
    u.close()
    headers = u.headers
    if not dont_decode:
        bytes = u.text
    if not return_headers:
        return bytes
    else:
        headers['_http_status'] = u.status_code
        return (bytes, headers)


# Get HTTP headers
@deprecated
def head(uri, timeout=20, headers=None, verify_ssl=True):  # pragma: no cover
    """Execute an HTTP GET query on `uri`, and return the headers. Deprecated.

    `timeout` is an optional argument, which represents how much time we should
    wait before throwing a timeout exception. It defaults to 20, but can be set
    to higher values if you are communicating with a slow web application.

    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    if headers is None:
        headers = default_headers
    else:
        tmp = default_headers.copy()
        tmp.update(headers)
        headers = tmp
    u = requests.get(uri, timeout=timeout, headers=headers, verify=verify_ssl)
    info = u.headers
    u.close()
    return info


# HTTP POST
@deprecated
def post(uri, query, limit_bytes=None, timeout=20, verify_ssl=True, return_headers=False):  # pragma: no cover
    """Execute an HTTP POST query. Deprecated.

    `uri` is the target URI, and `query` is the POST data.

    If `return_headers` is true, returns a tuple of (bytes, headers).

    `limit_bytes` is ignored.

    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    u = requests.post(uri, timeout=timeout, verify=verify_ssl, data=query)
    bytes = u.raw.read(limit_bytes)
    headers = u.headers
    u.close()
    if not return_headers:
        return bytes
    else:
        headers['_http_status'] = u.status_code
        return (bytes, headers)


r_entity = re.compile(r'&([^;\s]+);')


def entity(match):
    value = match.group(1).lower()
    if value.startswith('#x'):
        return unichr(int(value[2:], 16))
    elif value.startswith('#'):
        return unichr(int(value[1:]))
    elif value in name2codepoint:
        return unichr(name2codepoint[value])
    return '[' + value + ']'


def decode(html):
    return r_entity.sub(entity, html)


# For internal use in web.py, (modules can use this if they need a urllib
# object they can execute read() on) Both handles redirects and makes sure
# input URI is UTF-8
@deprecated
def get_urllib_object(uri, timeout, headers=None, verify_ssl=True, data=None):  # pragma: no cover
    """Return an HTTPResponse object for `uri` and `timeout` and `headers`. Deprecated

    """

    if headers is None:
        headers = default_headers
    else:
        tmp = default_headers.copy()
        tmp.update(headers)
        headers = tmp
    if data is not None:
        response = requests.post(uri, timeout=timeout, verify=verify_ssl,
                                 data=data, headers=headers)
    else:
        response = requests.get(uri, timeout=timeout, verify=verify_ssl,
                                headers=headers)
    return MockHttpResponse(response)


# Identical to urllib2.quote
def quote(string, safe='/'):
    """Like urllib2.quote but handles unicode properly."""
    if sys.version_info.major < 3:
        if isinstance(string, unicode):
            string = string.encode('utf8')
        string = urllib.quote(string, safe.encode('utf8'))
    else:
        string = urllib.parse.quote(str(string), safe)
    return string


def quote_query(string):
    """Quotes the query parameters."""
    parsed = urlparse(string)
    string = string.replace(parsed.query, quote(parsed.query, "/=&"), 1)
    return string


# Functions for international domain name magic

def urlencode_non_ascii(b):
    regex = '[\x80-\xFF]'
    if sys.version_info.major > 2:
        regex = b'[\x80-\xFF]'
    return re.sub(regex, lambda c: '%%%02x' % ord(c.group(0)), b)


def iri_to_uri(iri):
    parts = urlparse(iri)
    parts_seq = (part.encode('idna') if parti == 1 else urlencode_non_ascii(part.encode('utf-8')) for parti, part in enumerate(parts))
    if sys.version_info.major > 2:
        parts_seq = list(parts_seq)

    parsed = urlunparse(parts_seq)
    if sys.version_info.major > 2:
        return parsed.decode()
    else:
        return parsed


if sys.version_info.major < 3:
    urlencode = urllib.urlencode
else:
    urlencode = urllib.parse.urlencode
