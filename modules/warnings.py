#!/usr/bin/env python
"""
warnings.py -- NWS Alert Module
Copyright 2011, Michael Yanovich, yanovich.net

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module allows one to query the National Weather Service for active
watches, warnings, and advisories that are present.
"""

import feedparser
import re
import web

states = {
        "alabama" : "al",
        "alaska" : "ak",
        "arizona" : "az",
        "arkansas" : "ar",
        "california" : "ca",
        "colorado" : "co",
        "connecticut" : "ct",
        "delaware" : "de",
        "florida" : "fl",
        "georgia" : "ga",
        "hawaii" : "hi",
        "idaho" : "id",
        "illinois" : "il",
        "indiana" : "in",
        "iowa" : "ia",
        "kansas" : "ks",
        "kentucky" : "ky",
        "louisiana" : "la",
        "maine" : "me",
        "maryland" : "md",
        "massachusetts" : "ma",
        "michigan" : "mi",
        "minnesota" : "mn",
        "mississippi" : "ms",
        "missouri" : "mo",
        "montana" : "mt",
        "nebraska" : "ne",
        "nevada" : "nv",
        "new hampshire" : "nh",
        "new jersey" : "nj",
        "new mexico" : "nm",
        "new york" : "ny",
        "north carolina" : "nc",
        "north dakota" : "nd",
        "ohio" : "oh",
        "oklahoma" : "ok",
        "oregon" : "or",
        "pennsylvania" : "pa",
        "rhode island" : "ri",
        "south carolina" : "sc",
        "south dakota" : "sd",
        "tennessee" : "tn",
        "texas" : "tx",
        "utah" : "ut",
        "vermont" : "vt",
        "virginia" : "va",
        "washington" : "wa",
        "west virginia" : "wv",
        "wisconsin" : "wi",
        "wyoming" : "wy",
}

county_list = "http://alerts.weather.gov/cap/{0}.php?x=3"
nomsg = "There are no active watches, warnings or advisories"

def nws_lookup(jenni, input):
    """ Look up weather watches, warnings, and advisories. """
    text = input.group(2)
    if not text: return
    bits = text.split(",")
    if len(bits) == 2:
        url_part1 = "http://alerts.weather.gov"
        state = bits[1].lstrip().rstrip().lower()
        county = bits[0].lstrip().rstrip().lower()
        if state not in states:
            jenni.reply("State not found.")
            return
        url1 = county_list.format(states[state])
        page1 = web.get(url1).split("\n")
        for line in page1:
            mystr = ">" + unicode(county) + "<"
            if mystr in line.lower():
                url_part2 = line[9:36]
                break
        master_url = url_part1 + url_part2

        feed = feedparser.parse(master_url)
        for item in feed.entries:
            if nomsg == item["title"]:
                jenni.reply(nomsg)
            else:
                jenni.reply(unicode(item["title"]))
                jenni.reply(unicode(item["summary"]))
nws_lookup.commands = ['nws']

if __name__ == '__main__':
    print __doc__.strip()
