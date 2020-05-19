# coding=utf-8
"""Tests Sopel's web tools"""
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from sopel.tools.web import quote, search_urls, trim_url, unquote


QUOTED_STRINGS = [
    'C%C3%BA_Chulainn',
    'Q%C4%B1zmeydan',
    'G%C3%BCn%C9%99%C5%9Fli%2C_Saatly',
    'Rozst%C4%99pniewo',
    'Two%20Blank%20Spaces',
    'with%2Bplus%2Bsigns',
    'Exclamatory%21',
    'either/or',
    'questioning...%3F',
    '100%25',
]
UNQUOTED_STRINGS = [
    'Cú_Chulainn',
    'Qızmeydan',
    'Günəşli,_Saatly',
    'Rozstępniewo',
    'Two Blank Spaces',
    'with+plus+signs',
    'Exclamatory!',
    'either/or',
    'questioning...?',
    '100%',
]
QUOTE_PAIRS = tuple(zip(UNQUOTED_STRINGS, QUOTED_STRINGS))
UNQUOTE_PAIRS = tuple(zip(QUOTED_STRINGS, UNQUOTED_STRINGS))


@pytest.mark.parametrize('text, result', QUOTE_PAIRS)
def test_quote(text, result):
    assert quote(text) == result


def test_search_urls():
    urls = list(search_urls('http://example.com'))
    assert len(urls) == 1, 'Must find 1 URL, found %d' % len(urls)
    assert 'http://example.com' in urls


def test_search_urls_with_text():
    urls = list(search_urls('before http://example.com after'))
    assert len(urls) == 1, 'Must find 1 URL, found %d' % len(urls)
    assert 'http://example.com' in urls


def test_search_urls_multiple_urls():
    urls = list(search_urls('http://a.com/ http://b.com/'))
    assert len(urls) == 2, 'Must find 2 URLs, found %d' % len(urls)
    assert 'http://a.com/' in urls
    assert 'http://b.com/' in urls


def test_search_urls_multiple_urls_with_text():
    urls = list(
        search_urls('before http://a.com/ between http://b.com/ after'))
    assert len(urls) == 2, 'Must find 2 URLs, found %d' % len(urls)
    assert 'http://a.com/' in urls
    assert 'http://b.com/' in urls


def test_search_urls_multiple_urls_unique():
    urls = list(search_urls('http://a.com/ http://b.com/ http://a.com/'))
    assert len(urls) == 2, 'Must find 2 URLs, found %d' % len(urls)
    assert 'http://a.com/' in urls
    assert 'http://b.com/' in urls


def test_search_urls_multiple_urls_unique_keep_ordering():
    urls = list(
        search_urls('http://a.com/ http://c.com/ http://b.com/ http://a.com/'))
    assert len(urls) == 3, 'Must find 3 URLs, found %d' % len(urls)
    assert 'http://a.com/' in urls
    assert 'http://b.com/' in urls
    assert 'http://c.com/' in urls
    assert urls == [
        'http://a.com/',
        'http://c.com/',
        'http://b.com/',
    ]


def test_search_urls_exclusion_char():
    # assert url is excluded
    urls = list(search_urls('!http://example.com', exclusion_char='!'))
    assert not urls, 'Must not find URL, found %d' % len(urls)

    # assert the other url is not excluded
    urls = list(
        search_urls('http://b.com !http://a.com', exclusion_char='!'))
    assert len(urls) == 1, 'Must find 1 URL, found %d' % len(urls)
    assert 'http://b.com' in urls

    # assert the order of appearance does not matter
    urls = list(
        search_urls('!http://a.com http://b.com', exclusion_char='!'))
    assert len(urls) == 1, 'Must find 1 URL, found %d' % len(urls)
    assert 'http://b.com' in urls


def test_search_urls_exclusion_char_with_text():
    urls = list(
        search_urls(
            'before !http://a.com between http://b.com after',
            exclusion_char='!')
    )
    assert len(urls) == 1, 'Must find 1 URL, found %d' % len(urls)
    assert 'http://b.com' in urls


def test_search_urls_exclusion_char_only_once():
    # assert only the instance excluded is excluded
    # ie. that it is not a global exclude, otherwise that would return 1 url
    urls = list(
        search_urls(
            '!http://a.com http://a.com http://b.com',
            exclusion_char='!')
    )
    assert len(urls) == 2, 'Must find 1 URL, found %d' % len(urls)
    assert 'http://a.com' in urls
    assert 'http://b.com' in urls


def test_search_urls_default_schemes():
    urls = list(search_urls('http://a.com ftp://b.com https://c.com'))
    assert len(urls) == 3, 'Must find all three URLs'
    assert 'http://a.com' in urls
    assert 'ftp://b.com' in urls
    assert 'https://c.com' in urls


@pytest.mark.parametrize('scheme', ['http', 'https', 'ftp', 'steam'])
def test_search_urls_defined_schemes(scheme):
    expected = {
        'http': 'http://a.com',
        'https': 'https://c.com',
        'ftp': 'ftp://b.com',
        'steam': 'steam://portal2',
    }.get(scheme)

    urls = list(
        search_urls(
            'http://a.com ftp://b.com https://c.com steam://portal2',
            schemes=[scheme]
        )
    )
    assert len(urls) == 1, 'Only %s URLs must be found' % scheme
    assert expected in urls


TRAILING_CHARS = list('.,?!\'":;')
ENCLOSING_PAIRS = [('(', ')'), ('[', ']'), ('{', '}'), ('<', '>')]


@pytest.mark.parametrize('trailing_char', TRAILING_CHARS)
def test_trim_url_remove_trailing_char(trailing_char):
    test_url = 'http://example.com/'
    assert trim_url(test_url + trailing_char) == test_url

    # assert trailing_char removed only if it is trailing
    test_url = 'http://example.com/' + trailing_char + 'content'
    assert trim_url(test_url) == test_url


@pytest.mark.parametrize('left, right', ENCLOSING_PAIRS)
def test_trim_url_remove_trailing_enclosing(left, right):
    # right without left => right is removed
    test_url = 'http://example.com/'
    assert test_url == trim_url(test_url + right)

    # right after path without left => right is removed
    test_url = 'http://example.com/a'
    assert test_url == trim_url(test_url + right)

    # trailing left without right => left is kept
    test_url = 'http://example.com/a' + left
    assert test_url == trim_url(test_url)

    # left before content without right => left is kept
    test_url = 'http://example.com/a' + left + 'something'
    assert test_url == trim_url(test_url)

    # left + content + right => right is kept
    assert test_url + right == trim_url(test_url + right)


@pytest.mark.parametrize('trailing_char', TRAILING_CHARS)
@pytest.mark.parametrize('left, right', ENCLOSING_PAIRS)
def test_trim_url_trailing_char_and_enclosing(trailing_char, left, right):
    test_url = 'http://example.com/'
    assert test_url == trim_url(test_url + right + trailing_char)

    # assert the trailing char is kept if there is something else
    test_url = 'http://example.com/' + trailing_char
    assert test_url == trim_url(test_url + right)


@pytest.mark.parametrize('text, result', UNQUOTE_PAIRS)
def test_unquote(text, result):
    assert unquote(text) == result
