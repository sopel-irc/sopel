# coding=utf-8
"""Tests for Sopel's ``isup`` plugin"""
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from sopel.modules import isup


VALID_SITE_URLS = (
    # no scheme
    ('www.example.com', 'http://www.example.com'),
    # with scheme
    ('http://example.com', 'http://example.com'),
    ('https://example.com', 'https://example.com'),
    # with scheme and URL path
    ('http://example.com/path', 'http://example.com/path'),
    ('https://example.com/path', 'https://example.com/path'),
    # with scheme, URL path, and query string
    ('http://example.com/path?p=val', 'http://example.com/path?p=val'),
    ('https://example.com/path?p=val', 'https://example.com/path?p=val'),
    # not .com TLD
    ('example.io', 'http://example.io'),
    ('www.example.io', 'http://www.example.io'),
)


@pytest.mark.parametrize('site, expected', VALID_SITE_URLS)
def test_get_site_url(site, expected):
    assert isup.get_site_url(site) == expected


INVALID_SITE_URLS = (
    None,  # missing
    '',  # empty
    '      ',  # empty once stripped
    'steam://browsemedia',  # invalid protocol
    '://',  # invalid protocol (that's a weird one)
    'example',  # no TLD, no scheme
    'something.local',  # LAN-local address
    'something.local:8080',  # LAN-local address with explicit port
    'lanmachine/path/to/iot.device',  # unqualified name with dot in path
    'lanmachine:8080/path/to/iot.device',  # unqualified name with explicit port & dot in path
)


@pytest.mark.parametrize('site', INVALID_SITE_URLS)
def test_get_site_url_invalid(site):
    with pytest.raises(ValueError):
        isup.get_site_url(site)
