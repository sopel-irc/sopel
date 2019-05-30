# coding=utf-8
"""
currency.py - Sopel Currency Conversion Module
Copyright 2013, Elsie Powell, embolalia.com
Copyright 2019, Mikkel Jeppesen
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import time

import requests

from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.logger import get_logger
from sopel.module import commands, example, NOLIMIT, rule


FIAT_URL = 'https://api.exchangeratesapi.io/latest?base=EUR'
FIXER_URL = 'http://data.fixer.io/api/latest?base=EUR&access_key={}'
CRYPTO_URL = 'https://apiv2.bitcoinaverage.com/indices/global/ticker/short?crypto=BTC'
EXCHANGE_REGEX = re.compile(r'''
    ^(\d+(?:\.\d+)?)                                            # Decimal number
    \s*([a-zA-Z]{3})                                            # 3-letter currency code
    \s+(?:in|as|of|to)\s+                                       # preposition
    (([a-zA-Z]{3}$)|([a-zA-Z]{3})\s)+$                          # one or more 3-letter currency code
''', re.VERBOSE)
LOGGER = get_logger(__name__)
UNSUPPORTED_CURRENCY = "Sorry, {} isn't currently supported."
UNRECOGNIZED_INPUT = "Sorry, I didn't understand the input."

rates_fiat_json = {}
rates_btc_json = {}
rates_updated = 0.0


class CurrencySection(StaticSection):
    fixer_io_key = ValidatedAttribute('fixer_io_key', default=None)
    """Optional API key for Fixer.io (increases currency support)"""
    auto_convert = ValidatedAttribute('auto_convert', parse=bool, default=False)
    """Whether to convert currencies without an explicit command"""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | auto\\_convert | False | Whether to convert currencies without an explicit command |
    | fixer\\_io\\_key | 0123456789abcdef0123456789abcdef | Optional API key for Fixer.io (increases currency support) |
    """
    config.define_section('currency', CurrencySection, validate=False)
    config.currency.configure_setting('fixer_io_key', 'Optional API key for Fixer.io (leave blank to use exchangeratesapi.io):')
    config.currency.configure_setting('auto_convert', 'Whether to convert currencies without an explicit command?')


def setup(bot):
    bot.config.define_section('currency', CurrencySection)


class FixerError(Exception):
    """A Fixer.io API Error Exception"""
    def __init__(self, status):
        super(FixerError, self).__init__("FixerError: {}".format(status))


class UnsupportedCurrencyError(Exception):
    """A currency is currently not supported by the API"""
    def __init__(self, currency):
        super(UnsupportedCurrencyError, self).__init__(currency)


def update_rates(bot):
    global rates_fiat_json, rates_btc_json, rates_updated

    # If we have data that is less than 24h old, return
    if time.time() - rates_updated < 24 * 60 * 60:
        return

    # Update crypto rates
    response = requests.get(CRYPTO_URL)
    response.raise_for_status()
    rates_btc_json = response.json()

    # Update fiat rates
    if bot.config.currency.fixer_io_key is not None:
        response = requests.get(FIXER_URL.format(bot.config.currency.fixer_io_key))
        if not response.json()['success']:
            raise FixerError('Fixer.io request failed with error: {}'.format(response.json()['error']))
    else:
        response = requests.get(FIAT_URL)

    response.raise_for_status()
    rates_fiat_json = response.json()
    rates_updated = time.time()
    rates_fiat_json['rates']['EUR'] = 1.0  # Put this here to make logic easier


def btc_rate(code, reverse=False):
    search = 'BTC{}'.format(code)

    if search in rates_btc_json:
        rate = rates_btc_json[search]['averages']['day']
    else:
        raise UnsupportedCurrencyError(code)

    if reverse:
        return 1 / rate
    else:
        return rate


def get_rate(of, to):
    of = of.upper()
    to = to.upper()

    if of == 'BTC':
        return btc_rate(to, False)
    elif to == 'BTC':
        return btc_rate(of, True)

    if of not in rates_fiat_json['rates']:
        raise UnsupportedCurrencyError(of)

    if to not in rates_fiat_json['rates']:
        raise UnsupportedCurrencyError(to)

    return (1 / rates_fiat_json['rates'][of]) * rates_fiat_json['rates'][to]


def exchange(bot, match):
    """Show the exchange rate between two currencies"""
    if not match:
        bot.reply(UNRECOGNIZED_INPUT)
        return NOLIMIT

    try:
        update_rates(bot)  # Try and update rates. Rate-limiting is done in update_rates()
    except requests.exceptions.RequestException as err:
        bot.reply("Something went wrong while I was getting the exchange rate.")
        LOGGER.error("Error in GET request: {}".format(err))
        return NOLIMIT
    except ValueError:
        bot.reply("Error: Got malformed data.")
        LOGGER.error("Invalid json on update_rates")
        return NOLIMIT
    except FixerError as err:
        bot.reply('Sorry, something went wrong with Fixer')
        LOGGER.error(err)
        return NOLIMIT

    query = match.string

    others = query.split()
    amount = others.pop(0)
    of = others.pop(0)
    others.pop(0)

    # TODO: Use this instead after dropping Python 2 support
    # amount, of, _, *others = query.split()

    try:
        amount = float(amount)
    except ValueError:
        bot.reply(UNRECOGNIZED_INPUT)
        return NOLIMIT
    except OverflowError:
        bot.reply("Sorry, input amount was out of range.")
        return NOLIMIT

    if not amount:
        bot.reply("Zero is zero, no matter what country you're in.")
        return NOLIMIT

    out_string = '{} {} is'.format(amount, of.upper())

    for to in others:
        try:
            out_string = build_reply(amount, of.upper(), to.upper(), out_string)
        except ValueError:
            LOGGER.error("Raw rate wasn't a float")
            return NOLIMIT
        except KeyError as err:
            bot.reply("Error: Invalid rates")
            LOGGER.error("No key: {} in json".format(err))
            return NOLIMIT
        except UnsupportedCurrencyError as cur:
            bot.reply(UNSUPPORTED_CURRENCY.format(cur))
            return NOLIMIT

    bot.reply(out_string[0:-1])


@commands('cur', 'currency', 'exchange')
@example('.cur 100 usd in btc cad eur',
         r'100\.0 USD is [\d\.]+ BTC, [\d\.]+ CAD, [\d\.]+ EUR',
         re=True)
@example('.cur 3 can in one day', 'Sorry, CAN isn\'t currently supported.')
def exchange_cmd(bot, trigger):
    if not trigger.group(2):
        return bot.reply("No search term. Usage: {}cur 100 usd in btc cad eur"
                         .format(bot.config.core.help_prefix))

    match = EXCHANGE_REGEX.match(trigger.group(2))
    exchange(bot, match)


@rule(EXCHANGE_REGEX)
@example('100 usd in btc cad eur')
def exchange_re(bot, trigger):
    if bot.config.currency.auto_convert:
        match = EXCHANGE_REGEX.match(trigger)
        exchange(bot, match)


def build_reply(amount, of, to, out_string):
    rate_raw = get_rate(of, to)
    rate = float(rate_raw)
    result = float(rate * amount)

    if to == 'BTC':
        return out_string + ' {:.5f} {},'.format(result, to)

    return out_string + ' {:.2f} {},'.format(result, to)
