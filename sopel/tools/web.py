# coding=utf-8
"""
The ``tools.web`` package contains utility functions for interaction with web
applications, APIs, or websites in your plugins.

.. versionadded:: 7.0

.. note::
    Some parts of this module will remain accessible through ``sopel.web`` as
    well until its final removal in Sopel 8. This is for backward
    compatibility only; please update old code as soon as possible.
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
"""User agent string to be sent with HTTP requests.

Meant to be passed like so::

    import requests

    from sopel.tools import web

    result = requests.get(
        'https://some.site/api/endpoint',
        user_agent=web.USER_AGENT
    )

"""
DEFAULT_HEADERS = {'User-Agent': USER_AGENT}
"""Default header dict for use with ``requests`` methods.

Use it like this::

    import requests

    from sopel.tools import web

    result = requests.get(
        'https://some.site/api/endpoint',
        headers=web.DEFAULT_HEADERS
    )

.. important::
   You should *never* modify this directly in your plugin code. Make a copy
   and use :py:meth:`~dict.update` if you need to add or change headers::

       from sopel.tools import web

       default_headers = web.DEFAULT_HEADERS.copy()
       custom_headers = {'Accept': 'text/*'}

       default_headers.update(custom_headers)

"""


r_entity = re.compile(r'&([^;\s]+);')
"""Regular expression to match HTML entities."""


def entity(match):
    """Convert an entity reference to the appropriate character.

    :param str match: the entity name or code, as matched by
        :py:const:`r_entity`
    :return str: the Unicode character corresponding to the given ``match``
        string, or a fallback representation if the reference cannot be
        resolved to a character
    """
    value = match.group(1).lower()
    if value.startswith('#x'):
        return unichr(int(value[2:], 16))
    elif value.startswith('#'):
        return unichr(int(value[1:]))
    elif value in name2codepoint:
        return unichr(name2codepoint[value])
    return '[' + value + ']'


def decode(html):
    """Decode HTML entities into Unicode text.

    :param str html: the HTML page or snippet to process
    :return str: ``html`` with all entity references replaced
    """
    return r_entity.sub(entity, html)


# Identical to urllib2.quote
def quote(string, safe='/'):
    """Safely encodes a string for use in a URL.

    :param str string: the string to encode
    :param str safe: a list of characters that should not be quoted; defaults
                     to ``'/'``
    :return str: the ``string`` with special characters URL-encoded

    .. note::
        This is a shim to make writing cross-compatible plugins for both
        Python 2 and Python 3 easier.
    """
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
    """Safely encodes a URL's query parameters.

    :param str string: a URL containing query parameters
    :return str: the input URL with query parameter values URL-encoded
    """
    parsed = urlparse(string)
    string = string.replace(parsed.query, quote(parsed.query, "/=&"), 1)
    return string


# Functions for international domain name magic

def urlencode_non_ascii(b):
    """Safely encodes non-ASCII characters in a URL."""
    regex = '[\x80-\xFF]'
    if sys.version_info.major > 2:
        regex = b'[\x80-\xFF]'
    return re.sub(regex, lambda c: '%%%02x' % ord(c.group(0)), b)


def iri_to_uri(iri):
    """Decodes an internationalized domain name (IDN)."""
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
    """Removes extra punctuation from URLs found in text.

    :param str url: the raw URL match
    :return str: the cleaned URL

    This function removes trailing punctuation that looks like it was not
    intended to be part of the URL:

        * trailing sentence- or clause-ending marks like ``.``, ``;``, etc.
        * unmatched trailing brackets/braces like ``}``, ``)``, etc.

    It is intended for use with the output of :py:func:`~.search_urls`, which
    may include trailing punctuation when used on input from chat.
    """
    # clean trailing sentence- or clause-ending punctuation
    while url[-1] in '.,?!\'":;':
        url = url[:-1]

    # clean unmatched parentheses/braces/brackets
    for (opener, closer) in [('(', ')'), ('[', ']'), ('{', '}'), ('<', '>')]:
        if url[-1] == closer and url.count(opener) < url.count(closer):
            url = url[:-1]

    return url


def search_urls(text, exclusion_char=None, clean=False, schemes=None):
    """Extracts all URLs in ``text``.

    :param str text: the text to search for URLs
    :param str exclusion_char: optional character that, if placed before a URL
        in the ``text``, will exclude it from being extracted
    :param bool clean: if ``True``, all found URLs are passed through
        :py:func:`~.trim_url` before being returned; default ``False``
    :param list schemes: optional list of URL schemes to look for; defaults to
        ``['http', 'https', 'ftp']``
    :return: :py:term:`generator iterator` of all URLs found in ``text``

    To get the URLs as a plain list, use e.g.::

        list(search_urls(text))

    """
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
