# -*- coding: utf8 -*-
"""
units.py - Unit conversion module for Willie
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

"""
from willie.module import command, commands, example
import re

find_temp = re.compile('([0-9]*\.?[0-9]*)[ °]*(K|C|F)',  re.IGNORECASE)
find_length = re.compile('([0-9]*\.?[0-9]*)[ ]*(mile|m|meter|km|cm|kilometer|inch|in|ft|foot|feet|yd|yard|yards)',  re.IGNORECASE)

def f_to_c(temp):
    return (float(temp) - 32) * 5/9

def c_to_k(temp):
    return temp + 273.15

def c_to_f(temp):
    return (9.0/5.0 * temp + 32)

def k_to_c(temp):
    return temp - 273.15


@command('temp')
@example('.temp 100F')
def temperature(bot, trigger):
    """
    Convert temperatures
    """
    source = find_temp.match(trigger.group(2)).groups()
    unit = source[1].upper()
    numeric = float(source[0])
    celsius = 0
    if unit == 'C':
        celsius = numeric
    elif unit == 'F':
        celsius = f_to_c(numeric)
    elif unit == 'K':
        celsius = k_to_c(numeric)

    kelvin = c_to_k(celsius)
    fahrenheit = c_to_f(celsius)
    bot.reply("%s°C = %s°F = %s°K" % (celsius, fahrenheit, kelvin))

@commands('length', 'distance')
@example('.distance 3km')
def distance(bot, trigger):
    """
    Convert distances
    """
    source = find_length.match(trigger.group(2)).groups()
    unit = source[1].lower()
    numeric = float(source[0])
    meter = 0
    if unit == "m" or unit == "meter":
        meter = numeric
    elif unit == "kilometer" or unit == "km":
        meter = numeric * 1000
    elif unit == "mile":
        meter = numeric / 0.00062137
    elif unit == "inch" or unit == "in":
        meter = numeric / 39.370
    elif unit == "cm":
        meter = numeric / 100
    elif unit == "ft" or unit == "foot" or unit == "feet":
        meter = numeric / 3.2808
    elif unit == 'yard' or unit == 'yd' or unit == 'yards':
        meter = numeric / (3.2808 * 3)

    if meter >= 1000:
        metric_part = '%skm' % (meter / 1000)
    elif meter < 1:
        metric_part = '%scm' % (meter * 100)
    else:
        metric_part = '%sm' % meter


    # Shit like this makes me hate being an American.
    inch = meter * 39.37
    foot = int(inch) / 12
    inch = inch - (foot * 12)
    yard = foot / 3
    mile = meter * 0.00062137

    if yard > 500:
        if mile == 1:
            stupid_part = '1 mile'
        else:
            stupid_part = '%s miles' % mile
    else:
        parts = []
        if yard >= 100:
            parts.append('%s yards' % yard)
            foot -= (yard * 3)

        if foot == 1:
            parts.append('1 foot')
        elif foot != 0:
            parts.append('%s feet' % foot)

        if inch == 1:
            parts.append('1 inch')
        elif inch != 0:
            parts.append('%s inches' % inch)

        stupid_part = ', '.join(parts)

    bot.reply('%s = %s' % (metric_part, stupid_part))
