#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
web.py - Web Facilities
Copyright © 2008, Sean B. Palmer, inamidst.com
Copyright © 2009, Michael Yanovich <yanovich.1@osu.edu>
Copyright © 2012, Dimitri Molenaars, Tyrope.nl.
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

"""

import re, urllib2
from htmlentitydefs import name2codepoint

#HTTP GET
def get(uri, timeout=20):
    if not uri.startswith('http'):
        return
    u = get_urllib_object(uri, timeout)
    bytes = u.read()
    u.close()
    return bytes

# Get HTTP headers
def head(uri, timeout=20):
    if not uri.startswith('http'):
        return
    u = get_urllib_object(uri, timeout)
    info = u.info()
    u.close()
    return info

# HTTP POST
def post(uri, query):
    if not uri.startswith('http'):
        return
    data = urllib2.urlencode(query)
    u = urllib2.urlopen(uri, data)
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
def get_urllib_object(uri, timeout):
    redirects = 0
    try:
        uri = uri.encode("utf-8")
    except:
        pass
    while True:
        req = urllib2.Request(uri, headers={'Accept':'*/*', 'User-Agent':'Mozilla/5.0 (Jenni)'})
        try: u = urllib2.urlopen(req, None, timeout)
        except urllib2.HTTPError, e:
            return e.fp
        except:
            raise
        info = u.info()
        if not isinstance(info, list):
            status = '200'
        else:
            status = str(info[1])
            try: info = info[0]
            except: pass
        if status.startswith('3'):
            uri = urlparse.urljoin(uri, info['Location'])
        else: break
        redirects += 1
        if redirects >= 50:
            return "Too many re-directs."
    return u

#Identical to urllib2.quote
def quote(string):
    return urllib2.quote(string)

r_string = re.compile(r'("(\\.|[^"\\])*")')
r_json = re.compile(r'^[,:{}\[\]0-9.\-+Eaeflnr-u \n\r\t]+$')
env = {'__builtins__': None, 'null': None, 'true': True, 'false': False}

def json(text):
    """Evaluate JSON text safely (we hope)."""
    if r_json.match(r_string.sub('', text)):
        text = r_string.sub(lambda m: 'u' + m.group(1), text)
        return eval(text.strip(' \t\r\n'), env, {})
    raise ValueError('Input must be serialised JSON.')

if __name__=="__main__":
    main()
