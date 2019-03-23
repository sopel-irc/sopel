# coding=utf-8
"""Tests Sopel's web tools"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.web import search_urls, trim_url


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
