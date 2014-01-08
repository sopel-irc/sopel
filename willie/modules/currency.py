"""currency.py - Willie Exchange Rate Module
Copyright 2013 Edward Powell, embolalia.com
Licensed under the Eiffel Forum License 2

http://willie.dftba.net
"""

from lxml import etree
import re

from willie import web
from willie.module import commands, example, NOLIMIT


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
    if code == 'CAD':
        return 1, 'Canadian Dollar'

    data = web.get(base_url.format(code))
    xml = etree.fromstring(data)
    namestring = xml.find('{http://purl.org/rss/1.0/}channel/'
                          '{http://purl.org/rss/1.0/}title').text
    name = namestring[len('Bank of Canada noon rate: '):]
    name = re.sub(r'\s*\(noon\)\s*', '', name)
    rate = xml.find(
        '{http://purl.org/rss/1.0/}item/'
        '{http://www.cbwiki.net/wiki/index.php/Specification_1.1}statistics/'
        '{http://www.cbwiki.net/wiki/index.php/Specification_1.1}exchangeRate/'
        '{http://www.cbwiki.net/wiki/index.php/Specification_1.1}value').text
    return float(rate), name


@commands('cur', 'currency', 'exchange')
@example('.cur 20 EUR in USD')
def exchange(bot, trigger):
    """Show the exchange rate between two currencies"""
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

    if not amount:
        bot.reply("Zero is zero, no matter what country you're in.")
    try:
        of_rate, of_name = get_rate(of)
        to_rate, to_name = get_rate(to)
    except Exception as e:
        bot.reply("Something went wrong while I was getting the exchange rate.")
        return NOLIMIT

    result = amount / of_rate * to_rate
    bot.say("{} {} ({}) = {} {} ({})".format(amount, of, of_name,
                                           result, to, to_name))
