#!/usr/bin/env python
"""
tld.py - Jenni Why Module
Copyright 2009-10, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import re, urllib2
import web

uri = 'https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains'
r_tag = re.compile(r'<(?!!)[^>]+>')

def gettld(jenni, input):
    page = web.get(uri)
    #page = urllib2.urlopen(uri).read()
    search = r'(?i)<td><a href="\S+" title="\S+">\.{0}</a></td>\n<td>(\S+)</td>\n<td>(.*)</td>\n'
    search = search.format(input.group(2))
    re_country = re.compile(search)
    matches = re_country.findall(page)
    if matches:
        desc = r_tag.sub("", matches[0][1])
        if len(desc) > 400:
            desc = desc[:400] + "..."
        reply = "%s -- %s" % (matches[0][0], desc)
        jenni.reply(reply)
    else:
        search = r'<td><a href="\S+" title="\S+">.{0}</a></td>\n<td><span class="flagicon"><img.*?">(.*?)</a></td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n'
        search = search.format(unicode(input.group(2)))
        re_country = re.compile(search)
        matches = re_country.findall(page)
        if len(matches) > 0:
            matches = matches[0]
            dict_val = dict()
            dict_val["country"], dict_val["expl"], dict_val["notes"], dict_val["idn"], dict_val["dnssec"], dict_val["sld"] = matches
            for key in dict_val:
                if dict_val[key] == "&#160;":
                    dict_val[key] = "N/A"
            reply = "%s (%s, %s). IDN: %s, DNSSEC: %s, SLD: %s" % (dict_val["country"], dict_val["expl"], dict_val["notes"], dict_val["idn"], dict_val["dnssec"], dict_val["sld"])
            jenni.reply(reply)
        else:
            reply = "No matches found for TLD: {0}".format(unicode(input.group(2)))
            jenni.reply(reply)
gettld.commands = ['tld']
gettld.thread = False

if __name__ == '__main__':
    print __doc__.strip()
