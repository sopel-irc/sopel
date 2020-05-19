# coding=utf-8
"""
*Availability: 3+, deprecated in 6.2.0*

This web class will be removed in Sopel 8.0. As of Sopel 7.0, non-deprecated
functions are available in a new package, ``sopel.tools.web``.
"""
# Copyright © 2008, Sean B. Palmer, inamidst.com
# Copyright © 2009, Michael Yanovich <yanovich.1@osu.edu>
# Copyright © 2012, Dimitri Molenaars, Tyrope.nl.
# Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
# Copyright © 2019, dgw, technobabbl.es
# Licensed under the Eiffel Forum License 2.

from __future__ import absolute_import, division, print_function, unicode_literals

import sys

import requests

from .tools import deprecated

if sys.version_info.major < 3:
    import httplib
else:
    import http.client as httplib

# Imports to facilitate transition from sopel.web to sopel.tools.web
from .tools.web import (  # noqa
    USER_AGENT,
    DEFAULT_HEADERS as default_headers,
    entity,
    decode,
    quote,
    quote_query,
    urlencode_non_ascii,
    iri_to_uri,
    urlencode,
)

__all__ = [
    'USER_AGENT',
    'default_headers',
    'ca_certs',
    'get',
    'head',
    'post',
    'get_urllib_object',
    'decode',
    'entity',
    'iri_to_uri',
    'quote',
    'quote_query',
    'urlencode',
    'urlencode_non_ascii',
    'MockHttpResponse',
]


# Deprecated sopel.web methods are not moved, so they won't be accessible from the
# new module location (to discourage new code from using them).

ca_certs = None
# This doesn't appear to be used anywhere any more, so it lives in the to-be-removed
# version of sopel.web. At some point it was used to cover an SSL edge case, long ago.


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


# solely for use by get_urllib_object()
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
