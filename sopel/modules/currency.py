# coding=utf-8
"""currency.py - Sopel Exchange Rate Module
Copyright 2013 Edward Powell, embolalia.com
Licensed under the Eiffel Forum License 2

http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import json
import xmltodict
import re

from sopel import web
from sopel.module import commands, example, NOLIMIT

# The Canadian central bank has better exchange rate data than the Fed, the
# Bank of England, or the European Central Bank. Who knew?
base_url = 'http://www.bankofcanada.ca/stats/assets/rates_rss/noon/en_{}.xml'
regex = re.compile(r'''
    (\d+(?:\.\d+)?)        # Decimal number
    \s*([a-zA-Z]{3})       # 3-letter currency code
    \s+(?:in|as|of|to)\s+  # preposition
    ([a-zA-Z]{3})          # 3-letter currency code
    ''', re.VERBOSE)


def get_rate(code):
    if code.upper() == 'CAD':
        return 1, 'Canadian Dollar'
    elif code.upper() == 'BTC':
        rates = json.loads(web.get('https://api.bitcoinaverage.com/ticker/all'))
        return 1 / rates['CAD']['24h_avg'], 'Bitcoin—24hr average'

    data, headers = web.get(base_url.format(code), dont_decode=True, return_headers=True)
    if headers['_http_status'] == 404:
        return False, False
    namespaces = {
        'http://www.cbwiki.net/wiki/index.php/Specification_1.1': 'cb', 
        'http://purl.org/rss/1.0/': None, 
        'http://www.w3.org/1999/02/22-rdf-syntax-ns#': 'rdf' }
    xml = xmltodict.parse(data, process_namespaces=True, namespaces=namespaces).get('rdf:RDF')
    namestring = xml.get('channel').get('title').get('#text')
    name = namestring[len('Bank of Canada noon rate: '):]
    name = re.sub(r'\s*\(noon\)\s*', '', name)
    rate = xml.get('item').get('cb:statistics').get('cb:exchangeRate').get('cb:value').get('#text')
    return float(rate), name


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
    except:
        bot.reply("Sorry, I didn't understand the input.")
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
    except Exception as e:
        raise
        bot.reply("Something went wrong while I was getting the exchange rate.")
        return NOLIMIT

    result = amount / of_rate * to_rate
    bot.say("{} {} ({}) = {} {} ({})".format(amount, of, of_name,
                                             result, to, to_name))


@commands('btc', 'bitcoin')
@example('.btc 20 EUR')
def bitcoin(bot, trigger):
    #if 2 args, 1st is number and 2nd is currency. If 1 arg, it's either the number or the currency.
    to = trigger.group(4)
    amount = trigger.group(3)
    if not to:
        to = trigger.group(3) or 'USD'
        amount = 1

    try:
        amount = float(amount)
    except:
        bot.reply("Sorry, I didn't understand the input.")
        return NOLIMIT

    display(bot, amount, 'BTC', to)
