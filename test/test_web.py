# coding=utf-8
"""Tests Sopel's web tools"""
from __future__ import unicode_literals, absolute_import, print_function, division


from sopel.web import search_urls


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
