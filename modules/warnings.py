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
alerts = "http://alerts.weather.gov/cap/wwaatmget.php?x={0}"
zip_code_lookup = "http://www.zip-codes.com/zip-code/{0}/zip-code-{0}.asp"
nomsg = "There are no active watches, warnings or advisories, for {0}."
re_fips = re.compile(r'(?i)title="FIPS: (.*)">')
re_state = re.compile(r'(?i)Welcome to\s(.*\,\s[A-Z][A-Z])')

def nws_lookup(jenni, input):
    """ Look up weather watches, warnings, and advisories. """
    text = input.group(2)
    if not text: return
    bits = text.split(",")
    if len(bits) == 2:
        ## county given
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
        if not url_part2:
            jenni.reply("Could not find county.")
            return
        master_url = url_part1 + url_part2
        location = text
    elif len(bits) == 1:
        ## zip code
        if bits[0]:
            urlz = zip_code_lookup.format(bits[0])
            pagez = web.get(urlz)
            fips = re_fips.findall(pagez)
            if fips:
                state = re_state.findall(pagez)
                if not state:
                    jenni.reply("Could not match ZIP code to a state")
                    return
                location = state[0]
                state = location[-2:]
                fips = unicode(state) + "C" + unicode(fips[0])
                master_url = alerts.format(fips)
    else:
        jenni.reply("Invalid input. Please enter a ZIP code or a county and state pairing, such as 'Franklin, Ohio'")
        return

    feed = feedparser.parse(master_url)
    for item in feed.entries:
        if nomsg[:51] == item["title"]:
            jenni.reply(nomsg.format(location))
            break
        else:
            jenni.reply(unicode(item["title"]))
            jenni.reply(unicode(item["summary"]))
nws_lookup.commands = ['nws']

if __name__ == '__main__':
    print __doc__.strip()
