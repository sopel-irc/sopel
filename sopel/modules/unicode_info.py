# coding=utf-8
"""
codepoints.py - Sopel Codepoints Module
Copyright 2013, Edward Powell, embolalia.net
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division
import unicodedata
import sys
from sopel.module import commands, example, NOLIMIT

if sys.version_info.major >= 3:
    unichr = chr


@commands('u')
@example('.u ‽', 'U+203D INTERROBANG (‽)')
@example('.u 203D', 'U+203D INTERROBANG (‽)')
def codepoint(bot, trigger):
    arg = trigger.group(2).strip()
    if len(arg) == 0:
        bot.reply('What code point do you want me to look up?')
        return NOLIMIT
    elif len(arg) > 1:
        if arg.startswith('U+'):
            arg = arg[2:]
        try:
            arg = unichr(int(arg, 16))
        except:
            bot.reply("That's not a valid code point.")
            return NOLIMIT

    # Get the hex value for the code point, and drop the 0x from the front
    point = str(hex(ord(u'' + arg)))[2:]
    # Make the hex 4 characters long with preceding 0s, and all upper case
    point = point.rjust(4, str('0')).upper()
    try:
        name = unicodedata.name(arg)
    except ValueError:
        return 'U+%s (No name found)' % point

    if not unicodedata.combining(arg):
        template = 'U+%s %s (%s)'
    else:
        template = 'U+%s %s (\xe2\x97\x8c%s)'
    bot.say(template % (point, name, arg))

if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
