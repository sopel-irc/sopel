"""Tests for Sopel's ``isup`` plugin"""
from __future__ import annotations

import pytest
import requests.exceptions

from sopel.modules import isup
from sopel.tests import rawlist


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


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    isup
host = chat.freenode.net
"""


@pytest.fixture
def bot(botfactory, configfactory):
    settings = configfactory('default.ini', TMP_CONFIG)
    return botfactory.preloaded(settings, ['isup'])


@pytest.fixture
def irc(bot, ircfactory):
    return ircfactory(bot)


@pytest.fixture
def user(userfactory):
    return userfactory('User')


def test_isup_command_ok(irc, bot, user, requests_mock):
    """Test working URL."""
    requests_mock.head(
        'http://example.com',
        status_code=301,
    )

    irc.pm(user, '.isup example.com')

    assert len(bot.backend.message_sent) == 1, (
        '.isup command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[isup] http://example.com looks fine to me.'
    )


def test_isup_command_http_error(irc, bot, user, requests_mock):
    """Test URL that returns an HTTP error code."""
    requests_mock.head(
        'http://example.com',
        status_code=503,
        reason='Service Unavailable',
    )

    irc.pm(user, '.isup example.com')

    assert len(bot.backend.message_sent) == 1, (
        '.isup command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[isup] http://example.com looks down to me (HTTP 503 "Service Unavailable").'
    )


def test_isup_command_unparseable(irc, bot, user, requests_mock):
    """Test URL that can't be parsed."""
    requests_mock.head(
        'http://.foo',
        exc=ValueError("Invalid URL"),
    )

    irc.pm(user, '.isup .foo')

    assert len(bot.backend.message_sent) == 1, (
        '.isup command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :User: "http://.foo" is not a valid URL.'
    )


ISUP_EXCEPTIONS = (
    (
        requests.exceptions.ConnectionError,
        'http://127.0.0.1:1 looks down to me (connection error).'
    ),
    (
        requests.exceptions.ReadTimeout,
        'https://httpbingo.org/delay/10 looks down to me (timed out waiting for reply).'
    ),
    (
        requests.exceptions.ConnectTimeout,
        'http://10.0.0.0 looks down to me (timed out while connecting).'
    ),
    (
        requests.exceptions.SSLError,
        'https://expired.badssl.com/ looks down to me (SSL error). Try using `.isupinsecure`.'
    ),
)


@pytest.mark.parametrize('exc, result', ISUP_EXCEPTIONS)
def test_isup_command_requests_error(irc, bot, user, requests_mock, exc, result):
    """Test various error cases."""
    url = result.split()[0]
    requests_mock.head(
        url,
        exc=exc,
    )

    irc.pm(user, '.isup {}'.format(url))

    assert len(bot.backend.message_sent) == 1, (
        '.isup command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[isup] {}'.format(result)
    )


def test_isupinsecure_command(irc, bot, user, requests_mock):
    """Test working URL."""
    requests_mock.head(
        'https://example.com',
    )

    irc.pm(user, '.isupinsecure https://example.com')

    assert len(bot.backend.message_sent) == 1, (
        '.isupinsecure command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[isup] https://example.com looks fine to me.'
    )
