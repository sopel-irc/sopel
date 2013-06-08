# -*- coding: utf8 -*-
"""
*Availability: 3+*

The web class contains essential web-related functions for interaction with web applications or websites in your modules.
It supports HTTP GET, HTTP POST and HTTP HEAD.

"""

"""
web.py - Web Facilities
Copyright © 2008, Sean B. Palmer, inamidst.com
Copyright © 2009, Michael Yanovich <yanovich.1@osu.edu>
Copyright © 2012, Dimitri Molenaars, Tyrope.nl.
Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

More info:
http://willie.dftba.net

"""

import re, urllib, urllib2
from htmlentitydefs import name2codepoint

#HTTP GET
def get(uri, timeout=20, headers=None, return_headers=False):
    """
    Execute an HTTP GET query on `uri`, and return the result.
    `timeout` is an optional argument, which represents how much time we should wait before throwing a timeout exception. It defualts to 20, but can be set to higher values if you are communicating with a slow web application.
    `headers` is a dict of HTTP headers to send with the request.
    If `return_headers` is True, return a tuple of (bytes, headers)
    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    u = get_urllib_object(uri, timeout, headers)
    bytes = u.read()
    u.close()
    if not return_headers:
        return bytes
    else:
        return (bytes,u.info())

# Get HTTP headers
def head(uri, timeout=20, headers=None):
    """
    Execute an HTTP GET query on `uri`, and return the headers.
    `timeout` is an optional argument, which represents how much time we should wait before throwing a timeout exception. It defualts to 20, but can be set to higher values if you are communicating with a slow web application.
    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    u = get_urllib_object(uri, timeout, headers)
    info = u.info()
    u.close()
    return info

# HTTP POST
def post(uri, query):
    """
    Execute an HTTP POST query. `uri` is the target URI, and `query` is the POST data.
    `headers` is a dict of HTTP headers to send with the request.
    """
    if not uri.startswith('http'):
        uri = "http://" + uri
    u = urllib2.urlopen(uri, query)
    bytes = u.read()
    u.close()
    return bytes

r_entity = re.compile(r'&([^;\s]+);')

def entity(match):
    value = match.group(1).lower()
    if value.startswith('#x'):
        return unichr(int(value[2:], 16))
    elif value.startswith('#'):
        return unichr(int(value[1:]))
    elif name2codepoint.has_key(value):
        return unichr(name2codepoint[value])
    return '[' + value + ']'

def decode(html):
    return r_entity.sub(entity, html)

#For internal use in web.py, (modules can use this if they need a urllib object they can execute read() on)
#Both handles redirects and makes sure input URI is UTF-8
def get_urllib_object(uri, timeout, headers=None):
    """
    Return a urllib2 object for `uri` and `timeout` and `headers`. This is better than using urrlib2 directly, for it handles redirects, makes sure URI is utf8, and is shorter and easier to use.
    Modules may use this if they need a urllib2 object to execute .read() on. For more information, refer to the urllib2 documentation.
    """
    try:
        uri = uri.encode("utf-8")
    except:
        pass
    original_headers = {'Accept':'*/*', 'User-Agent':'Mozilla/5.0 (Willie)'}
    if headers is not None:
        original_headers.update(headers)
    else:
        headers = original_headers
    req = urllib2.Request(uri, headers=headers)
    try:
        u = urllib2.urlopen(req, None, timeout)
    except urllib2.HTTPError, e:
        # Even when there's an error (say HTTP 404), return page contents
        return e.fp

    return u

#Identical to urllib2.quote
def quote(string):
    """
    Like urllib2.quote but handles unicode properly
    """
    if isinstance(string, unicode):
        string = string.encode('utf8')
    return urllib2.quote(string)

#Identical to urllib.urlencode
def urlencode(data):
    """
    Identical to urllib.urlencode. Use this if you already importing web in your module and don't want to import urllib just to use the urlencode function.
    """
    return urllib.urlencode(data)
