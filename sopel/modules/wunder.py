"""
weather.py - sopel Weather Underground Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, embolalia.net
Copyleft  2015, Kyle Wilson, kylewilson.info
Licensed under the Eiffel Forum License 2.

http://sopel.dftba.net
"""

from sopel import web
from sopel.module import commands, example, NOLIMIT

import feedparser
from lxml import etree
import xml.etree.ElementTree as ET
import urllib

""" NOTE: Requires API key from Weather Underground available here: https://www.wunderground.com/weather/api/ """
apikey = ''


def geolookup(query):
    """
    Find the first PWS
    node for the result, so that location data can still be retrieved. Returns
    None if there is no result
    """
    url = 'http://api.wunderground.com/api/' + apikey + '/geolookup/q/' + query + '.xml'
    wresult = ET.parse(urllib.urlopen(url))
    root = wresult.getroot()
    result = root.find('results/result')
    if result is None or len(result) == 0:
        result = root.find('location')
        if result is None or len(result) == 0:
            return None
    pws = result.find('nearby_weather_stations/pws/station')
    if pws is None or len(pws) == 0:
        return result.find('l').text
    else:
        return '/q/pws:' + pws.find('id').text


@commands('weather', 'wea')
@example('.weather London')
def weather(bot, trigger):
    """.weather location - Show the weather at the given location."""

    location = trigger.group(2)
    if not location:
        first_result = bot.db.get_nick_value(trigger.nick, 'location')
        if not first_result:
            return bot.msg(trigger.sender, "I don't know where you live. " +
                           'Give me a location, like .weather London, or tell me where you live by saying .setlocation London, for example.')
    else:
        location = location.strip()
        first_result = bot.db.get_nick_value(location, 'location')
        if first_result is None:
            first_result = geolookup(location)
            if first_result is None:
                return bot.reply("I don't know where that is.")
    url = 'http://api.wunderground.com/api/' + apikey + '/conditions/' + first_result + '.xml'
    wresult = ET.parse(urllib.urlopen(url))
    root = wresult.getroot()
    parsed = root[3]
    if len(parsed) > 1:
        location = 'Weather for ' + parsed[2][0].text
    cover = parsed.find('weather').text
    temp = parsed.find('temperature_string').text
    humidity = parsed.find('relative_humidity').text
    pressure = parsed.find('pressure_in').text + 'in (' + parsed.find('pressure_mb').text + 'mb)'
    wind = 'Wind ' + parsed.find('wind_string').text
    bot.say(u'%s: %s, %s, %s humidity, %s, %s' % (location, cover, temp, humidity, pressure, wind))


@commands('setlocation', 'setloc')
@example('.setlocation Columbus, OH')
def setlocation(bot, trigger):
    """Set your default weather location."""
    first_result = geolookup(trigger.group(2))
    if first_result is None:
        return bot.reply("I don't know where that is.")

    location = first_result

    bot.db.set_nick_value(trigger.nick, 'location', location)

    bot.reply('I now have you at %s.' %(location))

