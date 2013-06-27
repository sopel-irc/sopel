# -*- coding: utf8 -*-
"""
units.py - Unit conversion module for Willie
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Copyright © 2013, Dimitri Molenaars, <tyrope@tyrope.nl>
Licensed under the Eiffel Forum License 2.

"""
from willie.module import commands, example, NOLIMIT
import re

find_temp = re.compile('(-?[0-9]*\.?[0-9]*)[ °]*(K|C|F)', re.IGNORECASE)
find_length = re.compile('([0-9]*\.?[0-9]*)[ ]*(mile[s]?|mi|inch|in|foot|feet|ft|yard[s]?|yd|(?:centi|kilo|)meter[s]?|[kc]?m)', re.IGNORECASE)


def f_to_c(temp):
    return (float(temp) - 32) * 5 / 9


def c_to_k(temp):
    return temp + 273.15


def c_to_f(temp):
    return (9.0 / 5.0 * temp + 32)


def k_to_c(temp):
    return temp - 273.15


@commands('temp')
@example('.temp 100F', '37.7777777778°C = 100.0°F = 310.927777778K')
@example('.temp 100C', '100.0°C = 212.0°F = 373.15K')
@example('.temp 100K', '-173.15°C = -279.67°F = 100.0K')
def temperature(bot, trigger):
    """
    Convert temperatures
    """
    try:
        source = find_temp.match(trigger.group(2)).groups()
    except AttributeError:
        bot.reply("That's not a valid temperature.")
        return NOLIMIT
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
    bot.reply("%s°C = %s°F = %sK" % (celsius, fahrenheit, kelvin))


@commands('length', 'distance')
@example('.distance 3m', '3.0m = 9 feet, 10.11 inches')
@example('.distance 3km', '3.0km = 1.86411 miles')
@example('.distance 3 miles', '4.82804126366km = 3.0 miles')
@example('.distance 3 inch', '7.62001524003cm = 3.0 inches')
@example('.distance 3 feet', '91.4411119239cm = 3 feet, 0.000365764447693 inches')
@example('.distance 3 yards', '30.4803706413cm = 1 foot, 0.000121921482561 inches')
def distance(bot, trigger):
    """
    Convert distances
    """
    try:
        source = find_length.match(trigger.group(2)).groups()
    except AttributeError:
        bot.reply("That's not a valid length unit.")
        return NOLIMIT
    unit = source[1].lower()
    numeric = float(source[0])
    meter = 0
    if unit in ("meters", "meter", "m"):
        meter = numeric
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


if __name__ == "__main__":
    from willie.test_tools import run_example_tests
    run_example_tests(__file__)
