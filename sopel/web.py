# coding=utf-8
"""
*Availability: 3+*

The web class contains essential web-related functions for interaction with web
applications or websites in your modules.  It supports HTTP GET, HTTP POST and
HTTP HEAD.
"""
#Copyright © 2008, Sean B. Palmer, inamidst.com
#Copyright © 2009, Michael Yanovich <yanovich.1@osu.edu>
#Copyright © 2012, Dimitri Molenaars, Tyrope.nl.
#Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
#Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals, absolute_import, print_function, division

import re
import sys
import urllib
import os.path
import socket

from sopel import __version__

if sys.version_info.major < 3:
    import urllib2
    import httplib
    from htmlentitydefs import name2codepoint
    from urlparse import urlparse
    from urlparse import urlunparse
else:
    import urllib.request as urllib2
    import http.client as httplib
    from html.entities import name2codepoint
    from urllib.parse import urlparse
    from urllib.parse import urlunparse
    unichr = chr

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

USER_AGENT = 'Sopel/{} (http://sopel.chat)'.format(__version__)


# HTTP GET
# Note: dont_decode is a horrible name for an argument, double negative
# is super confusing. We need to replace it, maybe in 5.0 because this would
# mean breaking backwards compatability
def get(uri, timeout=20, headers=None, return_headers=False,
        limit_bytes=None, verify_ssl=True, dont_decode=False):
    """Execute an HTTP GET query on `uri`, and return the result.

    `timeout` is an optional argument, which represents how much time we should
    wait before throwing a timeout exception. It defaults to 20, but can be set
    to higher values if you are communicating with a slow web application.
    `headers` is a dict of HTTP headers to send with the request.  If
    `return_headers` is True, return a tuple of (bytes, headers)

    If `limit_bytes` is provided, only read that many bytes from the URL. This
    may be a good idea when reading from unknown sites, to prevent excessively
    large files from being downloaded.

    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    u = get_urllib_object(uri, timeout, headers, verify_ssl)
    bytes = u.read(limit_bytes)
    u.close()
    headers = dict(u.info())
    if not dont_decode:
        # Detect encoding automatically from HTTP headers
        content_type = headers.get('content-type') or ''
        encoding_match = re.match('.*?charset *= *(\S+)', content_type, re.IGNORECASE)
        if encoding_match:
            try:
                bytes = bytes.decode(encoding_match.group(1))
            except:
                # attempt unicode on failure
                encoding_match = None
        if not encoding_match:
            bytes = bytes.decode('utf-8', "ignore")
    if not return_headers:
        return bytes
    else:
        headers['_http_status'] = u.code
        return (bytes, headers)


# Get HTTP headers
def head(uri, timeout=20, headers=None, verify_ssl=True):
    """Execute an HTTP GET query on `uri`, and return the headers.

    `timeout` is an optional argument, which represents how much time we should
    wait before throwing a timeout exception. It defaults to 20, but can be set
    to higher values if you are communicating with a slow web application.

    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    u = get_urllib_object(uri, timeout, headers, verify_ssl)
    info = u.info()
    u.close()
    return info


# HTTP POST
def post(uri, query, limit_bytes=None, timeout=20, verify_ssl=True, return_headers=False):
    """Execute an HTTP POST query.

    `uri` is the target URI, and `query` is the POST data. `headers` is a dict
    of HTTP headers to send with the request.

    If `limit_bytes` is provided, only read that many bytes from the URL. This
    may be a good idea when reading from unknown sites, to prevent excessively
    large files from being downloaded.

    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    u = get_urllib_object(uri, timeout=timeout, verify_ssl=verify_ssl, data=query)
    bytes = u.read(limit_bytes)
    headers = dict(u.info())
    u.close()
    if not return_headers:
        return bytes
    else:
        headers['_http_status'] = u.code
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


class VerifiedHTTPSConnection(httplib.HTTPConnection):
        "Verified HTTPS Connection handler"

        default_port = httplib.HTTPS_PORT

        def __init__(self, *args, **kwargs):
            if not has_ssl:
                raise Exception('SSL verification is not available.')
            httplib.HTTPConnection.__init__(self, *args, **kwargs)

        def connect(self):
            """Connect to the host and port specified in __init__."""
            sock = socket.create_connection((self.host, self.port),
                                            self.timeout, self.source_address)
            if self._tunnel_host:
                self.sock = sock
                self._tunnel()
            if not os.path.exists(ca_certs):
                raise Exception('CA Certificate bundle %s is not readable' % ca_certs)
            self.sock = ssl.wrap_socket(sock,
                                        ca_certs=ca_certs,
                                        cert_reqs=ssl.CERT_REQUIRED)
            ssl.match_hostname(self.sock.getpeercert(), self.host)


class VerifiedHTTPSHandler(urllib2.HTTPSHandler):

    def https_open(self, req):
            return self.do_open(VerifiedHTTPSConnection, req)


# For internal use in web.py, (modules can use this if they need a urllib
# object they can execute read() on) Both handles redirects and makes sure
# input URI is UTF-8
def get_urllib_object(uri, timeout, headers=None, verify_ssl=True, data=None):
    """Return a urllib2 object for `uri` and `timeout` and `headers`.

    This is better than using urlib2 directly, for it handles SSL verifcation, makes
    sure URI is utf8, and is shorter and easier to use.  Modules may use this
    if they need a urllib2 object to execute .read() on.

    For more information, refer to the urllib2 documentation.

    """

    uri = quote_query(uri)

    try:
        # Check if we need to do IDN parsing
        uri.encode('ascii')
    except:
        uri = iri_to_uri(uri)

    original_headers = {'Accept': '*/*', 'User-Agent': USER_AGENT}
    if headers is not None:
        original_headers.update(headers)
    else:
        headers = original_headers

    if verify_ssl:
        opener = urllib2.build_opener(VerifiedHTTPSHandler)
    else:
        opener = urllib2.build_opener()

    if type(data) is dict:
        data = urlencode(data).encode('utf-8')

    req = urllib2.Request(uri, headers=headers, data=data)
    try:
        u = opener.open(req, None, timeout)
    except urllib2.HTTPError as e:
        # Even when there's an error (say HTTP 404), return page contents
        return e.fp

    return u


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
