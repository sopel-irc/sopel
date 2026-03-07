"""
The ``tools.web`` package contains utility functions for interaction with web
applications, APIs, or websites in your plugins.

.. versionadded:: 7.0

.. versionchanged:: 8.1

    Several utility functions are now deprecated due to Python's builtin
    library containing the appropriate functions. These functions will be
    removed in Sopel 9.

"""
# Copyright © 2008, Sean B. Palmer, inamidst.com
# Copyright © 2009, Michael Yanovich <yanovich.1@osu.edu>
# Copyright © 2012, Dimitri Molenaars, Tyrope.nl.
# Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
# Copyright © 2019, dgw, technobabbl.es
# Licensed under the Eiffel Forum License 2.

from __future__ import annotations

import html
from html.entities import name2codepoint
import re
from typing import TYPE_CHECKING
import urllib
from urllib.parse import urlparse, urlunparse

from sopel import __version__
from sopel.lifecycle import deprecated


if TYPE_CHECKING:
    from typing import Iterable


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
"""Regular expression to match HTML entities.

.. deprecated:: 8.0

    Will be removed in Sopel 9, along with :func:`entity`.
"""


@deprecated(
    version='8.0',
    removed_in='9.0',
    reason="No longer needed now that Python 3.4+ has `html.unescape()`",
)
def entity(match: re.Match) -> str:
    """Convert an entity reference to the appropriate character.

    :param str match: the entity name or code, as matched by
        :py:const:`r_entity`
    :return str: the Unicode character corresponding to the given ``match``
        string, or a fallback representation if the reference cannot be
        resolved to a character

    .. deprecated:: 8.0

        Will be removed in Sopel 9. Use :func:`decode` directly or migrate to
        Python's standard-library equivalent, :func:`html.unescape`.

    """
    value = match.group(1).lower()
    if value.startswith('#x'):
        return chr(int(value[2:], 16))
    elif value.startswith('#'):
        return chr(int(value[1:]))
    elif value in name2codepoint:
        return chr(name2codepoint[value])
    return '[' + value + ']'


@deprecated(
    version='8.1',
    removed_in='9.0',
    reason="Obsolete, use Python's html.unescape() function",
)
def decode(text: str) -> str:
    """Decode HTML entities into Unicode text.

    :param str text: the HTML page or snippet to process
    :return str: ``text`` with all entity references replaced

    .. versionchanged:: 8.0

        Renamed ``html`` parameter to ``text``. (Python gained a standard
        library module named :mod:`html` in version 3.4.)

    .. deprecated:: 8.1

        Will be removed in Sopel 9. Migrate to Python's standard-library
        equivalent, :func:`html.unescape`.

    """
    return html.unescape(text)


@deprecated(
    version='8.1',
    removed_in='9.0',
    reason="Obsolete, use Python's urllib.parse.quote() function",
)
def quote(string: str, safe: str = '/') -> str:
    """Safely encodes a string for use in a URL.

    :param str string: the string to encode
    :param str safe: a list of characters that should not be quoted; defaults
                     to ``'/'``
    :return str: the ``string`` with special characters URL-encoded

    .. note::
        This is a shim to make writing cross-compatible plugins for both
        Python 2 and Python 3 easier.

    .. deprecated:: 8.1

        Will be removed in Sopel 9. Migrate to Python's standard-library
        equivalent, :func:`urllib.parse.quote`.
    """
    return urllib.parse.quote(str(string), safe)


# six-like shim for Unicode safety
@deprecated(
    version='8.1',
    removed_in='9.0',
    reason="Obsolete, use Python's urllib.parse.unquote() function",
)
def unquote(string: str) -> str:
    """Decodes a URL-encoded string.

    :param str string: the string to decode
    :return str: the decoded ``string``

    .. note::

        This is a convenient shortcut for ``urllib.parse.unquote``.

    .. deprecated:: 8.1

        Will be removed in Sopel 9. Migrate to Python's standard-library
        equivalent, :func:`urllib.parse.unquote`.
    """
    return urllib.parse.unquote(string)


def quote_query(string: str) -> str:
    """Safely encodes a URL's query parameters.

    :param string: a URL containing query parameters
    :return: the input URL with query parameter values URL-encoded

    .. note::

        This is a convenient function using :func:`urllib.parse.urlparse` and
        :func:`urllib.parse.quote`.

    """
    parsed = urlparse(string)
    string = string.replace(
        parsed.query,
        urllib.parse.quote(parsed.query, "/=&"),
        1,
    )
    return string


# Functions for international domain name magic

def urlencode_non_ascii(b: bytes) -> bytes:
    """Safely encodes non-ASCII characters in a URL."""
    return re.sub(b'[\x80-\xFF]', lambda c: b'%%%02x' % ord(c.group(0)), b)


def iri_to_uri(iri: str) -> str:
    """Decodes an internationalized domain name (IDN)."""
    parts = urlparse(iri)
    parts_seq = list(
        part.encode('idna')
        if parti == 1 else urlencode_non_ascii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )
    parsed = urlunparse(parts_seq)
    return parsed.decode()


# direct shortcut kept for backward compatibility reasons
urlencode = deprecated(
    version='8.1',
    removed_in='9.0',
    reason="Obsolete, use Python's urllib.parse.urlencode() function",
    func=urllib.parse.urlencode
)


# Functions for URL detection

def trim_url(url: str) -> str:
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


def search_urls(
    text: str,
    exclusion_char: str | None = None,
    clean: bool = False,
    schemes: Iterable[str] | None = None,
) -> Iterable[str]:
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
    allowed: Iterable[str] = schemes or ['http', 'https', 'ftp']
    schemes_patterns = '|'.join(re.escape(scheme) for scheme in allowed)
    re_url = r'((?<!\S)(?:%s)(?::\/\/\S+))' % schemes_patterns
    if exclusion_char is not None:
        re_url = r'((?<!\S)(?<!%s)(?:%s)(?::\/\/\S+))' % (
            exclusion_char, schemes_patterns)

    r = re.compile(re_url, re.IGNORECASE | re.UNICODE)

    urls = re.findall(r, text)
    if clean:
        urls = [trim_url(url) for url in urls]

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
