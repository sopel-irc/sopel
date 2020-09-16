# coding=utf-8
"""
units.py - Sopel Unit Conversion Plugin
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Copyright © 2013, Dimitri Molenaars, <tyrope@tyrope.nl>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import re

from sopel import plugin


PLUGIN_OUTPUT_PREFIX = '[units] '

find_temp = re.compile(r'(-?[0-9]*\.?[0-9]*)[ °]*(K|C|F)', re.IGNORECASE)
find_length = re.compile(r'([0-9]*\.?[0-9]*)[ ]*(mile[s]?|mi|inch|in|foot|feet|ft|yard[s]?|yd|(?:milli|centi|kilo|)meter[s]?|[mkc]?m|ly|light-year[s]?|au|astronomical unit[s]?|parsec[s]?|pc)', re.IGNORECASE)
find_mass = re.compile(r'([0-9]*\.?[0-9]*)[ ]*(lb|lbm|pound[s]?|ounce|oz|(?:kilo|)gram(?:me|)[s]?|[k]?g)', re.IGNORECASE)


def f_to_c(temp):
    return (float(temp) - 32) * 5 / 9


def c_to_k(temp):
    return temp + 273.15


def c_to_f(temp):
    return (9.0 / 5.0 * temp + 32)


def k_to_c(temp):
    return temp - 273.15


@plugin.command('temp')
@plugin.example('.temp 100F', '37.78°C = 100.00°F = 310.93K')
@plugin.example('.temp 100C', '100.00°C = 212.00°F = 373.15K')
@plugin.example('.temp 100K', '-173.15°C = -279.67°F = 100.00K')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def temperature(bot, trigger):
    """Convert temperatures"""
    try:
        source = find_temp.match(trigger.group(2)).groups()
    except (AttributeError, TypeError):
        bot.reply("That's not a valid temperature.")
        return plugin.NOLIMIT
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

    if kelvin <= 0:
        bot.reply("Physically impossible temperature.")
        return

    bot.say("{:.2f}°C = {:.2f}°F = {:.2f}K".format(
        celsius,
        fahrenheit,
        kelvin,
    ))


@plugin.command('length', 'distance')
@plugin.example('.distance 3m', '3.00m = 9 feet, 10.11 inches')
@plugin.example('.distance 3km', '3.00km = 1.86 miles')
@plugin.example('.distance 3 miles', '4.83km = 3.00 miles')
@plugin.example('.distance 3 inch', '7.62cm = 3.00 inches')
@plugin.example('.distance 3 feet', '91.44cm = 3 feet, 0.00 inches')
@plugin.example('.distance 3 yards', '2.74m = 9 feet, 0.00 inches')
@plugin.example('.distance 155cm', '1.55m = 5 feet, 1.02 inches')
@plugin.example('.length 3 ly', '28382191417742.40km = 17635876112814.77 miles')
@plugin.example('.length 3 au', '448793612.10km = 278867421.71 miles')
@plugin.example('.length 3 parsec', '92570329129020.20km = 57520535754731.61 miles')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def distance(bot, trigger):
    """Convert distances"""
    try:
        source = find_length.match(trigger.group(2)).groups()
    except (AttributeError, TypeError):
        bot.reply("That's not a valid length unit.")
        return plugin.NOLIMIT
    unit = source[1].lower()
    numeric = float(source[0])
    meter = 0
    if unit in ("meters", "meter", "m"):
        meter = numeric
    elif unit in ("millimeters", "millimeter", "mm"):
        meter = numeric / 1000
    elif unit in ("kilometers", "kilometer", "km"):
        meter = numeric * 1000
    elif unit in ("miles", "mile", "mi"):
        meter = numeric / 0.00062137
    elif unit in ("inch", "in"):
        meter = numeric / 39.370
    elif unit in ("centimeters", "centimeter", "cm"):
        meter = numeric / 100
    elif unit in ("feet", "foot", "ft"):
        meter = numeric / 3.2808
    elif unit in ("yards", "yard", "yd"):
        meter = numeric / (3.2808 / 3)
    elif unit in ("light-year", "light-years", "ly"):
        meter = numeric * 9460730472580800
    elif unit in ("astronomical unit", "astronomical units", "au"):
        meter = numeric * 149597870700
    elif unit in ("parsec", "parsecs", "pc"):
        meter = numeric * 30856776376340068

    if meter >= 1000:
        metric_part = '{:.2f}km'.format(meter / 1000)
    elif meter < 0.01:
        metric_part = '{:.2f}mm'.format(meter * 1000)
    elif meter < 1:
        metric_part = '{:.2f}cm'.format(meter * 100)
    else:
        metric_part = '{:.2f}m'.format(meter)

    # Shit like this makes me hate being an American.
    inch = meter * 39.37
    foot = int(inch) // 12
    inch = inch - (foot * 12)
    yard = foot // 3
    mile = meter * 0.000621371192

    if yard > 500:
        stupid_part = '{:.2f} miles'.format(mile)
    else:
        parts = []
        if yard >= 100:
            parts.append('{} yards'.format(yard))
            foot -= (yard * 3)

        if foot == 1:
            parts.append('1 foot')
        elif foot != 0:
            parts.append('{:.0f} feet'.format(foot))

        parts.append('{:.2f} inches'.format(inch))

        stupid_part = ', '.join(parts)

    bot.say('{} = {}'.format(metric_part, stupid_part))


@plugin.command('weight', 'mass')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def mass(bot, trigger):
    """Convert mass"""
    try:
        source = find_mass.match(trigger.group(2)).groups()
    except (AttributeError, TypeError):
        bot.reply("That's not a valid mass unit.")
        return plugin.NOLIMIT
    unit = source[1].lower()
    numeric = float(source[0])
    metric = 0
    if unit in ("gram", "grams", "gramme", "grammes", "g"):
        metric = numeric
    elif unit in ("kilogram", "kilograms", "kilogramme", "kilogrammes", "kg"):
        metric = numeric * 1000
    elif unit in ("lb", "lbm", "pound", "pounds"):
        metric = numeric * 453.59237
    elif unit in ("oz", "ounce"):
        metric = numeric * 28.35

    if metric >= 1000:
        metric_part = '{:.2f}kg'.format(metric / 1000)
    else:
        metric_part = '{:.2f}g'.format(metric)

    ounce = metric * .035274
    pound = int(ounce) // 16
    ounce = ounce - (pound * 16)

    if pound >= 1:
        stupid_part = '{} {}'.format(pound, 'pound' if pound == 1 else 'pounds')
        if ounce > 0.01:
            stupid_part += ' {:.2f} ounces'.format(ounce)
    else:
        stupid_part = '{:.2f} oz'.format(ounce)

    bot.say('{} = {}'.format(metric_part, stupid_part))
