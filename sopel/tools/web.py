# coding=utf-8
"""
*Availability: 7+; replaces ``sopel.web``*

The ``web`` class contains web-related utility functions for interaction with
web applications, APIs, or websites in your modules.
"""
# Copyright © 2008, Sean B. Palmer, inamidst.com
# Copyright © 2009, Michael Yanovich <yanovich.1@osu.edu>
# Copyright © 2012, Dimitri Molenaars, Tyrope.nl.
# Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
# Copyright © 2019, dgw, technobabbl.es
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals, absolute_import, print_function, division

import re
import sys
import urllib

from sopel import __version__

if sys.version_info.major < 3:
    from htmlentitydefs import name2codepoint
    from urlparse import urlparse, urlunparse
else:
    from html.entities import name2codepoint
    from urllib.parse import urlparse, urlunparse
    unichr = chr
    unicode = str

__all__ = [
    'USER_AGENT',
    'DEFAULT_HEADERS',
    'decode',
    'entity',
    'iri_to_uri',
    'quote',
    'unquote',
    'quote_query',
    'search_urls',
    'trim_url',
    'urlencode',
    'urlencode_non_ascii',
]

USER_AGENT = 'Sopel/{} (https://sopel.chat)'.format(__version__)
DEFAULT_HEADERS = {'User-Agent': USER_AGENT}


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


# six-like shim for Unicode safety
def unquote(string):
    """Decodes a URL-encoded string.

    :param str string: the string to decode
    :return str: the decoded ``string``

    .. note::
        This is a shim to make writing cross-compatible plugins for both
        Python 2 and Python 3 easier.
    """
    if sys.version_info.major < 3:
        return urllib.unquote(string.encode('utf-8')).decode('utf-8')
    else:
        return urllib.parse.unquote(string)


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


# Functions for URL detection

def trim_url(url):
    # clean trailing sentence- or clause-ending punctuation
    while url[-1] in '.,?!\'":;':
        url = url[:-1]

    # clean unmatched parentheses/braces/brackets
    for (opener, closer) in [('(', ')'), ('[', ']'), ('{', '}'), ('<', '>')]:
        if url[-1] == closer and url.count(opener) < url.count(closer):
            url = url[:-1]

    return url


def search_urls(text, exclusion_char=None, clean=False, schemes=None):
    schemes = schemes or ['http', 'https', 'ftp']
    schemes_patterns = '|'.join(re.escape(scheme) for scheme in schemes)
    re_url = r'((?:%s)(?::\/\/\S+))' % schemes_patterns
    if exclusion_char is not None:
        re_url = r'((?<!%s)(?:%s)(?::\/\/\S+))' % (
            exclusion_char, schemes_patterns)

    r = re.compile(re_url, re.IGNORECASE | re.UNICODE)

    urls = re.findall(r, text)
    if clean:
        urls = (trim_url(url) for url in urls)

    # yield unique URLs in their order of appearance
    seen = set()
    for url in urls:
        try:
            url = iri_to_uri(url)
        except Exception:  # TODO: Be specific
            pass

        if url not in seen:
            seen.add(url)
            yield url
