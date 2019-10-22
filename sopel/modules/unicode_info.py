# coding=utf-8
"""
unicode_info.py - Sopel Codepoints Module
Copyright 2013, Elsie Powell, embolalia.com
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import sys
import unicodedata

from sopel import module

if sys.version_info.major >= 3:
    # Note on unicode and str (required for py2 compatibility)
    # the `hex` function returns a `str`, both in py2 and py3
    # however, a `str` is a unicode string in py3, but a bytestring in py2
    # in order to prevent that, we encode the return from `hex` as `unicode`
    # and since this class does not exist anymore on py3, we create an alias
    # for `str` in py3
    unichr = chr
    unicode = str


def get_codepoint_name(char):
    """Retrieve the code point (and name, if possible) for a given character"""
    # Get the hex value for the code point, and drop the 0x from the front
    point = unicode(hex(ord(char)))[2:]

    # Make the hex 4 characters long with preceding 0s, and all upper case
    point = point.rjust(4, '0').upper()

    # get codepoint's name
    name = None
    try:
        name = unicodedata.name(char)
    except ValueError:
        pass

    return point, name


@module.commands('u')
@module.example('.u ‽', 'U+203D INTERROBANG (‽)', user_help=True)
@module.example('.u 203D', 'U+203D INTERROBANG (‽)', user_help=True)
def codepoint(bot, trigger):
    """Look up a Unicode character or a hexadecimal code point."""
    arg = trigger.group(2)
    if not arg:
        bot.reply('What code point do you want me to look up?')
        return module.NOLIMIT
    stripped = arg.strip()
    if len(stripped) > 0:
        arg = stripped
    if len(arg) > 1:
        if arg.startswith('U+'):
            arg = arg[2:]
        try:
            arg = unichr(int(arg, 16))
        except (ValueError, TypeError):
            bot.reply("That's not a valid code point.")
            return module.NOLIMIT

    point, name = get_codepoint_name(arg)
    if name is None:
        name = '(No name found)'

    template = 'U+%s %s (\xe2\x97\x8c%s)'
    if not unicodedata.combining(arg):
        template = 'U+%s %s (%s)'

    bot.say(template % (point, name, arg))


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
