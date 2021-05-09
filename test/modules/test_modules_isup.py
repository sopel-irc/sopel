# coding=utf-8
"""Tests for Sopel's ``isup`` plugin"""
from __future__ import absolute_import, division, print_function, unicode_literals

import time

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


def test_isup_command_ok(botfactory, configfactory, ircfactory, userfactory, requests_mock):
    """Test working URL."""
    requests_mock.head(
        'http://example.com',
        status_code=301,
    )

    settings = configfactory('default.ini', TMP_CONFIG)
    bot = botfactory.preloaded(settings, ['isup'])
    irc = ircfactory(bot)
    user = userfactory('User')

    irc.pm(user, '.isup example.com')

    while bot.running_triggers:
        # TODO: remove when botfactory can force everything to be unthreaded
        time.sleep(0.1)

    assert len(bot.backend.message_sent) == 1, (
        '.isup command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[isup] http://example.com looks fine to me.'
    )


def test_isup_command_http_error(botfactory, configfactory, ircfactory, userfactory, requests_mock):
    """Test URL that returns an HTTP error code."""
    requests_mock.head(
        'http://example.com',
        status_code=503,
        reason='Service Unavailable',
    )

    settings = configfactory('default.ini', TMP_CONFIG)
    bot = botfactory.preloaded(settings, ['isup'])
    irc = ircfactory(bot)
    user = userfactory('User')

    irc.pm(user, '.isup example.com')

    while bot.running_triggers:
        # TODO: remove when botfactory can force everything to be unthreaded
        time.sleep(0.1)

    assert len(bot.backend.message_sent) == 1, (
        '.isup command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[isup] http://example.com looks down to me (HTTP 503 "Service Unavailable").'
    )


def test_isup_command_unparseable(botfactory, configfactory, ircfactory, userfactory, requests_mock):
    """Test URL that can't be parsed."""
    requests_mock.head(
        'http://.foo',
        exc=ValueError("Failed to parse: '.foo', label empty or too long"),
    )

    settings = configfactory('default.ini', TMP_CONFIG)
    bot = botfactory.preloaded(settings, ['isup'])
    irc = ircfactory(bot)
    user = userfactory('User')

    irc.pm(user, '.isup .foo')

    while bot.running_triggers:
        # TODO: remove when botfactory can force everything to be unthreaded
        time.sleep(0.1)

    assert len(bot.backend.message_sent) == 1, (
        '.isup command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :User: Failed to parse: \'.foo\', label empty or too long'
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
def test_isup_command_requests_error(
    exc, result, botfactory, configfactory, ircfactory, userfactory, requests_mock
):
    """Test various error cases."""
    url = result.split()[0]
    requests_mock.head(
        url,
        exc=exc,
    )

    settings = configfactory('default.ini', TMP_CONFIG)
    bot = botfactory.preloaded(settings, ['isup'])
    irc = ircfactory(bot)
    user = userfactory('User')

    irc.pm(user, '.isup {}'.format(url))

    while bot.running_triggers:
        # TODO: remove when botfactory can force everything to be unthreaded
        time.sleep(0.1)

    assert len(bot.backend.message_sent) == 1, (
        '.isup command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[isup] {}'.format(result)
    )


def test_isupinsecure_command(botfactory, configfactory, ircfactory, userfactory, requests_mock):
    """Test working URL."""
    requests_mock.head(
        'https://example.com',
    )

    settings = configfactory('default.ini', TMP_CONFIG)
    bot = botfactory.preloaded(settings, ['isup'])
    irc = ircfactory(bot)
    user = userfactory('User')

    irc.pm(user, '.isupinsecure https://example.com')

    while bot.running_triggers:
        # TODO: remove when botfactory can force everything to be unthreaded
        time.sleep(0.1)

    assert len(bot.backend.message_sent) == 1, (
        '.isupinsecure command should output exactly one line')
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[isup] https://example.com looks fine to me.'
    )
