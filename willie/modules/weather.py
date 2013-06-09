"""
weather.py - Willie Yahoo! Weather Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import re
import urllib
import json
from willie import web
from willie.module import command, commands, example
from lxml import etree
import feedparser


def setup(bot):
    #Having a db means pref's exists. Later, we can just use `if bot.db`.
    if bot.db and not bot.db.preferences.has_columns('woeid'):
        bot.db.preferences.add_columns(['woeid'])


def woeid_search(query):
    """
    Find the first Where On Earth ID for the given query. Result is the etree
    node for the result, so that location data can still be retrieved. Returns
    None if there is no result, or the woeid field is empty.
    """
    query = web.urlencode({'q': 'select * from geo.placefinder where text="%s"' % query})
    woeid_yml = 'http://query.yahooapis.com/v1/public/yql?' + query
    body = web.get(woeid_yml)
    parsed = etree.fromstring(body)
    first_result = parsed.find('results/Result')
    if len(first_result) == 0:
        return None

    woeid = first_result.find('woeid').text
    if not woeid:
        return None
    return first_result


def get_cover(parsed):
    try:
        condition = parsed.entries[0]['yweather_condition']
    except KeyError:
        return 'unknown'
    text = condition['text']
    code = int(condition['code'])
    #TODO parse code to get those little icon thingies.
    return text


def get_temp(parsed):
    try:
        condition = parsed.entries[0]['yweather_condition']
    except KeyError:
        return 'unknown'
    temp = int(condition['temp'])
    f = round((temp * 1.8) + 32, 2)
    return (u'%d\u00B0C (%d\u00B0F)' % (temp, f))


def get_pressure(parsed):
    try:
        pressure = parsed['feed']['yweather_atmosphere']['pressure']
    except KeyError:
        return 'unknown'
    millibar = float(pressure)
    inches = int(millibar / 33.7685)
    return ('%din (%dmb)' % (inches, int(millibar)))


def get_wind(parsed):
    try:
        wind_data = parsed['feed']['yweather_wind']
    except KeyError:
        return 'unknown'
    try:
        kph = float(wind_data['speed'])
    except ValueError:
        kph = -1
        #Incoming data isn't a number, default to zero.
        #This is a dirty fix for issue #218
    speed = int(round(kph / 1.852, 0))
    degrees = int(wind_data['direction'])
    if speed < 1:
        description = 'Calm'
    elif speed < 4:
        description = 'Light air'
    elif speed < 7:
        description = 'Light breeze'
    elif speed < 11:
        description = 'Gentle breeze'
    elif speed < 16:
        description = 'Moderate breeze'
    elif speed < 22:
        description = 'Fresh breeze'
    elif speed < 28:
        description = 'Strong breeze'
    elif speed < 34:
        description = 'Near gale'
    elif speed < 41:
        description = 'Gale'
    elif speed < 48:
        description = 'Strong gale'
    elif speed < 56:
        description = 'Storm'
    elif speed < 64:
        description = 'Violent storm'
    else:
        description = 'Hurricane'

    if (degrees <= 22.5) or (degrees > 337.5):
        degrees = u'\u2191'
    elif (degrees > 22.5) and (degrees <= 67.5):
        degrees = u'\u2197'
    elif (degrees > 67.5) and (degrees <= 112.5):
        degrees = u'\u2192'
    elif (degrees > 112.5) and (degrees <= 157.5):
        degrees = u'\u2198'
    elif (degrees > 157.5) and (degrees <= 202.5):
        degrees = u'\u2193'
    elif (degrees > 202.5) and (degrees <= 247.5):
        degrees = u'\u2199'
    elif (degrees > 247.5) and (degrees <= 292.5):
        degrees = u'\u2190'
    elif (degrees > 292.5) and (degrees <= 337.5):
        degrees = u'\u2196'

    return description + ' ' + str(speed) + 'kt (' + degrees + ')'


@command('weather')
@example('.weather London')
def weather(bot, trigger):
    """.weather location - Show the weather at the given location."""

    location = trigger.group(2)
    woeid = ''
    if not location:
        if bot.db and trigger.nick in bot.db.preferences:
            woeid = bot.db.preferences.get(trigger.nick, 'woeid')
        if not woeid:
            return bot.msg(trigger.sender, "I don't know where you live. " +
                           'Give me a location, like .weather London, or tell me where you live by saying .setlocation London, for example.')
    else:
        if bot.db and location in bot.db.preferences:
            woeid = bot.db.preferences.get(location, 'woeid')
        else:
            woeid = woeid_search(location).find('woeid').text

    if not woeid:
        return bot.reply("I don't know where that is.")

    query = web.urlencode({'w': woeid, 'u': 'c'})
    url = 'http://weather.yahooapis.com/forecastrss?' + query
    parsed = feedparser.parse(url)
    location = parsed['feed']['title']

    cover = get_cover(parsed)
    temp = get_temp(parsed)
    pressure = get_pressure(parsed)
    wind = get_wind(parsed)
    bot.say(u'%s: %s, %s, %s, %s' % (location, cover, temp, pressure, wind))


@commands('setlocation', 'setwoeid')
@example('.setlocation Columbus, OH')
def update_woeid(bot, trigger):
    """Set your default weather location."""
    if bot.db:
        first_result = woeid_search(trigger.group(2))
        woeid = first_result.find('woeid').text

        bot.db.preferences.update(trigger.nick, {'woeid': woeid})

        neighborhood = first_result.find('neighborhood').text or ''
        if neighborhood:
            neighborhood += ','
        city = first_result.find('city').text or ''
        state = first_result.find('state').text or ''
        country = first_result.find('country').text or ''
        uzip = first_result.find('uzip').text or ''
        bot.reply('I now have you at WOEID %s (%s %s, %s, %s %s.)' %
                  (woeid, neighborhood, city, state, country, uzip))
    else:
        bot.reply("I can't remember that; I don't have a database.")
