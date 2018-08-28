# coding=utf-8
# Copyright 2013 Elsie Powell, embolalia.com
# Licensed under the Eiffel Forum License 2
from __future__ import unicode_literals, absolute_import, print_function, division

import re

from requests import get
from sopel.module import commands, example, NOLIMIT

# The Canadian central bank has better exchange rate data than the Fed, the
# Bank of England, or the European Central Bank. Who knew?
base_url = 'https://www.bankofcanada.ca/valet/observations/FX{}CAD/json'
regex = re.compile(r'''
    (\d+(?:\.\d+)?)        # Decimal number
    \s*([a-zA-Z]{3})       # 3-letter currency code
    \s+(?:in|as|of|to)\s+  # preposition
    ([a-zA-Z]{3})          # 3-letter currency code
    ''', re.VERBOSE)


def get_rate(code):
    code = code.upper()
    if code == 'CAD':
        return 1, 'Canadian Dollar'
    elif code == 'BTC':
        btc_rate = get('https://apiv2.bitcoinaverage.com/indices/global/ticker/BTCCAD')
        rates = btc_rate.json()
        return 1 / rates['averages']['day'], 'Bitcoin—24hr average'

    data = get(base_url.format(code))
    name = data.json()['seriesDetail']['FX{}CAD'.format(code)]['description']
    name = name.split(" to Canadian")[0]
    json = data.json()['observations']
    for element in reversed(json):
        if 'v' in element['FX{}CAD'.format(code)]:
            return 1 / float(element['FX{}CAD'.format(code)]['v']), name


@commands('cur', 'currency', 'exchange')
@example('.cur 20 EUR in USD')
def exchange(bot, trigger):
    """Show the exchange rate between two currencies"""
    if not trigger.group(2):
        return bot.reply("No search term. An example: .cur 20 EUR in USD")
    match = regex.match(trigger.group(2))
    if not match:
        # It's apologetic, because it's using Canadian data.
        bot.reply("Sorry, I didn't understand the input.")
        return NOLIMIT

    amount, of, to = match.groups()
    try:
        amount = float(amount)
    except ValueError:
        bot.reply("Sorry, I didn't understand the input.")
    except OverflowError:
        bot.reply("Sorry, input amount was out of range.")
    display(bot, amount, of, to)


def display(bot, amount, of, to):
    if not amount:
        bot.reply("Zero is zero, no matter what country you're in.")
    try:
        of_rate, of_name = get_rate(of)
        if not of_name:
            bot.reply("Unknown currency: %s" % of)
            return
        to_rate, to_name = get_rate(to)
        if not to_name:
            bot.reply("Unknown currency: %s" % to)
            return
    except Exception:  # TODO: Be specific
        bot.reply("Something went wrong while I was getting the exchange rate.")
        return NOLIMIT

    result = amount / of_rate * to_rate
    bot.say("{:.2f} {} ({}) = {:.2f} {} ({})".format(amount, of.upper(), of_name,
                                             result, to.upper(), to_name))


@commands('btc', 'bitcoin')
@example('.btc 20 EUR')
def bitcoin(bot, trigger):
    # if 2 args, 1st is number and 2nd is currency. If 1 arg, it's either the number or the currency.
    to = trigger.group(4)
    amount = trigger.group(3)
    if not to:
        to = trigger.group(3) or 'USD'
        amount = 1

    try:
        amount = float(amount)
    except ValueError:
        bot.reply("Sorry, I didn't understand the input.")
        return NOLIMIT
    except OverflowError:
        bot.reply("Sorry, input amount was out of range.")
        return NOLIMIT

    display(bot, amount, 'BTC', to)
