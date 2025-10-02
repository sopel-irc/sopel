"""
currency.py - Sopel Currency Conversion Plugin
Copyright 2013, Elsie Powell, embolalia.com
Copyright 2019, Mikkel Jeppesen
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

import logging
import re
import time

import requests

from sopel import plugin
from sopel.config import types
from sopel.tools import web


PLUGIN_OUTPUT_PREFIX = '[currency] '
FIAT_PROVIDERS = {
    'open.er-api.com': 'https://open.er-api.com/v6/latest/EUR',
    'fixer.io': '//data.fixer.io/api/latest?base=EUR&access_key={}',
}
CRYPTO_URL = 'https://api.coingecko.com/api/v3/exchange_rates'
EXCHANGE_REGEX = re.compile(r'''
    ^(\d+(?:\.\d+)?)                                            # Decimal number
    \s*([a-zA-Z]{3})                                            # 3-letter currency code
    \s+(?:in|as|of|to)\s+                                       # preposition
    (([a-zA-Z]{3}$)|([a-zA-Z]{3})\s)+$                          # one or more 3-letter currency code
''', re.VERBOSE)
LOGGER = logging.getLogger(__name__)
UNSUPPORTED_CURRENCY = "Sorry, {} isn't currently supported."
UNRECOGNIZED_INPUT = "Sorry, I didn't understand the input."

rates: dict[str, float] = {}
rates_updated = 0.0


class CurrencySection(types.StaticSection):
    fiat_provider = types.ChoiceAttribute(
        'fiat_provider',
        list(FIAT_PROVIDERS.keys()),
        default='open.er-api.com',
    )
    """Which data provider to use (some of which require no API key)"""
    fixer_io_key = types.ValidatedAttribute('fixer_io_key', default=None)
    """API key for Fixer.io (widest currency support)"""
    fixer_use_ssl = types.BooleanAttribute('fixer_use_ssl', default=False)
    """Whether to use SSL (HTTPS) for Fixer API"""
    auto_convert = types.BooleanAttribute('auto_convert', default=False)
    """Whether to convert currencies without an explicit command"""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | auto\\_convert | False | Whether to convert currencies without an explicit command |
    | fiat\\_provider | ratesapi.io | Which data provider to use (some of which require no API key) |
    | fixer\\_io\\_key | 0123456789abcdef0123456789abcdef | API key for Fixer.io (widest currency support) |
    | fixer\\_use\\_ssl | False | Whether to use SSL (HTTPS) for Fixer API (requires paid API access) |
    """
    config.define_section('currency', CurrencySection, validate=False)
    config.currency.configure_setting(
        'fiat_provider',
        'Which exchange rate provider do you want to use?\n'
        'Available choices: {}'.format(
            ', '.join(FIAT_PROVIDERS.keys())
        ))
    if config.currency.fiat_provider == 'fixer.io':
        config.currency.configure_setting(
            'fixer_io_key', 'API key for Fixer.io:')
        config.currency.configure_setting(
            'fixer_use_ssl', 'Use SSL (paid plans only) for Fixer.io?')

    config.currency.configure_setting(
        'auto_convert', 'Convert currencies without an explicit command?')


def setup(bot):
    bot.settings.define_section('currency', CurrencySection)


class FixerError(Exception):
    """A Fixer.io API Error Exception"""
    def __init__(self, status):
        super().__init__("FixerError: {}".format(status))


class UnsupportedCurrencyError(Exception):
    """A currency is currently not supported by the API"""
    def __init__(self, currency):
        super().__init__(currency)


def build_reply(amount, base, target, out_string):
    rate_raw = get_rate(base, target)
    rate = float(rate_raw)
    result = float(rate * amount)

    digits = 0
    # up to 10 (8+2) digits precision when result is less than 1
    # as smaller results need more precision
    while digits < 8 and 1 / 10**digits > result:
        digits += 1

    digits += 2

    out_string += ' {value:,.{precision}f} {currency},'.format(value=result, precision=digits, currency=target)

    return out_string


def exchange(bot, match):
    """Show the exchange rate between two currencies"""
    if not match:
        bot.reply(UNRECOGNIZED_INPUT)
        return

    try:
        update_rates(bot)  # Try and update rates. Rate-limiting is done in update_rates()
    except requests.exceptions.RequestException as err:
        bot.reply("Something went wrong while I was getting the exchange rate.")
        LOGGER.error("Error in GET request: {}".format(err))
        return
    except (KeyError, ValueError) as err:
        bot.reply("Error: Could not update exchange rates. Try again later.")
        LOGGER.error("{} on update_rates".format(
            'Invalid JSON' if type(err).__name__ == 'ValueError' else 'Missing JSON value',
        ))
        return
    except FixerError as err:
        bot.reply('Sorry, something went wrong with Fixer')
        LOGGER.error(err)
        return

    amount_in, base, _, *targets = match.string.split()

    try:
        amount = float(amount_in)
    except ValueError:
        bot.reply(UNRECOGNIZED_INPUT)
        return
    except OverflowError:
        bot.reply("Sorry, input amount was out of range.")
        return

    if not amount:
        bot.reply("Zero is zero, no matter what country you're in.")
        return

    out_string = '{} {} is'.format(amount_in, base.upper())

    unsupported_currencies = []
    for target in targets:
        try:
            out_string = build_reply(amount, base.upper(), target.upper(), out_string)
        except ValueError:
            LOGGER.error("Raw rate wasn't a float")
            return
        except KeyError as err:
            bot.reply("Error: Invalid rates")
            LOGGER.error("No key: {} in json".format(err))
            return
        except UnsupportedCurrencyError as cur:
            unsupported_currencies.append(cur)

    if unsupported_currencies:
        out_string = out_string + ' (unsupported:'
        for target in unsupported_currencies:
            out_string = out_string + ' {},'.format(target)
        out_string = out_string[0:-1] + ')'
    else:
        out_string = out_string[0:-1]

    bot.say(out_string)


def get_rate(base, target):
    base = base.upper()
    target = target.upper()

    if base not in rates:
        raise UnsupportedCurrencyError(base)

    if target not in rates:
        raise UnsupportedCurrencyError(target)

    return (1 / rates[base]) * rates[target]


def update_rates(bot):
    global rates, rates_updated

    # If we have data that is less than 24h old, return
    if time.time() - rates_updated < 24 * 60 * 60:
        LOGGER.debug('Skipping rate update; cache is less than 24h old')
        return

    # Update crypto rates
    LOGGER.debug('Updating crypto rates from %s', CRYPTO_URL)
    response = requests.get(CRYPTO_URL)
    response.raise_for_status()
    rates_crypto = response.json()

    # Update fiat rates
    fiat_provider = bot.settings.currency.fiat_provider
    fixer_io_key = bot.settings.currency.fixer_io_key
    fixer_use_ssl = bot.settings.currency.fixer_use_ssl

    if fiat_provider == 'fixer.io':
        LOGGER.debug('Updating fiat rates from Fixer.io')
        if not fixer_io_key:
            raise FixerError('Fixer.io requires an API key.')

        proto = 'https:' if fixer_use_ssl else 'http:'
        response = requests.get(
            proto +
            FIAT_PROVIDERS['fixer.io'].format(web.quote(fixer_io_key))
        )

        if not response.json()['success']:
            error_message = response.json()['error']
            raise FixerError(
                'Fixer.io request failed with error: {}'.format(error_message),
            )
    else:
        LOGGER.debug('Updating fiat rates from %s', fiat_provider)
        response = requests.get(FIAT_PROVIDERS[fiat_provider])

    response.raise_for_status()
    rates_fiat = response.json()

    rates = rates_fiat['rates']
    rates['EUR'] = 1.0  # Put this here to make logic easier

    eur_btc_rate = 1 / rates_crypto['rates']['eur']['value']

    for rate in rates_crypto['rates']:
        if rate.upper() not in rates:
            rates[rate.upper()] = rates_crypto['rates'][rate]['value'] * eur_btc_rate

    # if an error aborted the operation prematurely, we want the next call to retry updating rates
    # therefore we'll update the stored timestamp at the last possible moment
    rates_updated = time.time()
    LOGGER.debug('Rate update completed')


@plugin.commands('cur', 'currency', 'exchange')
@plugin.example('.cur 100 usd in btc cad eur',
                r'100 USD is [\d\.]+ BTC, [\d\.]+ CAD, [\d\.]+ EUR',
                re=True, online=True, vcr=True)
@plugin.example('.cur 100 usd in btc cad eur can aux',
                r'100 USD is [\d\.]+ BTC, [\d\.]+ CAD, [\d\.]+ EUR, \(unsupported: CAN, AUX\)',
                re=True, online=True, vcr=True)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def exchange_cmd(bot, trigger):
    """Show the exchange rate between two currencies."""
    if not trigger.group(2):
        bot.reply("No search term. Usage: {}cur 100 usd in btc cad eur"
                  .format(bot.settings.core.help_prefix))
        return

    match = EXCHANGE_REGEX.match(trigger.group(2))
    exchange(bot, match)


@plugin.rule(EXCHANGE_REGEX)
@plugin.example('100 usd in btc cad eur')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def exchange_re(bot, trigger):
    if bot.settings.currency.auto_convert:
        match = EXCHANGE_REGEX.match(trigger)
        exchange(bot, match)


@plugin.command('currencies')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def supported_cmd(bot, trigger):
    """List which currency codes are supported for conversion."""
    if not rates:
        try:
            update_rates(bot)
        except Exception:
            bot.reply("Couldn't fetch supported currencies. Please try again later.")
            return

    codes = sorted(list(rates.keys()))

    bot.say(
        "Supported currency codes: " + ' '.join(codes),
        trigger.nick, max_messages=5)
