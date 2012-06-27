#!/usr/bin/env python
"""
why.py - Jenni Why Module
Copyright 2009-10, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import feedparser

api = "http://api.woot.com/1/sales/current.rss/www.woot.com"


def woot(jenni, input):
    """ .woot -- pulls the latest information from woot.com """
    output = str()
    parsed = feedparser.parse(api)
    if not parsed['entries']:
        jenni.reply("No item currently available.")
        return
    item = parsed['entries'][0]['woot_products']
    link = parsed['entries'][0]['link']
    price = parsed['entries'][0]['woot_price']
    s = parsed['entries'][0]['woot_soldoutpercentage']
    if len(s) == 1:
        soldout = 0
    else:
        soldout = int(s.split('.')[1]) * 10
    condition = parsed['entries'][0]['woot_condition']
    quantity = parsed['entries'][0]['woot_product']['quantity']
    woot_off = parsed['entries'][0]['woot_wootoff']

    base1 = "{0} -- \x02Price:\x02 {1}, \x02Soldout:\x02 {2}% \x02Condition:"
    base2 = "\x02 {3}, \x02Quantity:\x02 {4}, \x02Woot-Off:\x02 {5} -- {6}"
    base = base1 + base2

    output = base.format(item, price, soldout, condition, quantity,
        woot_off, link)
    jenni.reply(output)
woot.commands = ['woot']
woot.priority = 'low'
woot.rate = 30

if __name__ == '__main__':
    print __doc__.strip()
