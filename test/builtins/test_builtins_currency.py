"""Tests for Sopel's ``currency`` plugin"""
from __future__ import annotations

import pytest

from sopel.builtins import currency
from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    currency
host = irc.libera.chat

[currency]
fiat_provider = allratestoday.com
allratestoday_key = test-key
"""


@pytest.fixture
def bot(botfactory, configfactory):
    settings = configfactory('default.ini', TMP_CONFIG)
    return botfactory.preloaded(settings, ['currency'])


@pytest.fixture
def irc(bot, ircfactory):
    return ircfactory(bot)


@pytest.fixture
def user(userfactory):
    return userfactory('User')


@pytest.fixture(autouse=True)
def reset_rates(monkeypatch):
    monkeypatch.setattr(currency, 'rates', {})
    monkeypatch.setattr(currency, 'rates_updated', 0.0)


def test_allratestoday_provider(irc, bot, user, requests_mock):
    """Test the AllRatesToday fiat provider."""
    requests_mock.get(currency.CRYPTO_URL, json={
        'rates': {'eur': {'value': 2.0}},
    })
    rates_mock = requests_mock.get(
        currency.FIAT_PROVIDERS['allratestoday.com'],
        json=[
            {'source': 'EUR', 'target': 'USD', 'rate': 2.0,
             'time': '2026-10-22T12:00:00Z'},
            {'source': 'EUR', 'target': 'GBP', 'rate': 0.5,
             'time': '2026-10-22T12:00:00Z'},
        ],
    )

    irc.pm(user, '.cur 10 usd in gbp')

    assert rates_mock.last_request.headers['Authorization'] == 'Bearer test-key'
    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :[currency] 10 USD is 2.50 GBP'
    )


def test_allratestoday_provider_no_key(irc, bot, user, requests_mock):
    """Test the AllRatesToday fiat provider without an API key."""
    bot.settings.currency.allratestoday_key = None
    requests_mock.get(currency.CRYPTO_URL, json={
        'rates': {'eur': {'value': 2.0}},
    })

    irc.pm(user, '.cur 10 usd in gbp')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG User :User: Sorry, something went wrong with AllRatesToday'
    )
