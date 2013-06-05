# -*- coding: utf8 -*-
"""
units.py - Unit conversion module for Willie
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

"""
from willie.module import command, example
import re

find_temp = re.compile('([0-9]*\.?[0-9]*)[ °]*(K|C|F)',  re.IGNORECASE)

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
