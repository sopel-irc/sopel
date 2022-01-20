"""
unicode_info.py - Sopel Codepoints Plugin
Copyright 2013, Elsie Powell, embolalia.com
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

import unicodedata

from sopel import plugin


def get_codepoint_name(char):
    """Retrieve the code point (and name, if possible) for a given character"""
    # Get the hex value for the code point, and drop the 0x from the front
    point = hex(ord(char))[2:]

    # Make the hex 4 characters long with preceding 0s, and all upper case
    point = point.rjust(4, '0').upper()

    # get codepoint's name
    name = None
    try:
        name = unicodedata.name(char)
    except ValueError:
        pass

    return point, name


@plugin.command('u')
@plugin.example('.u ‽', 'U+203D INTERROBANG (‽)', user_help=True)
@plugin.example('.u 203D', 'U+203D INTERROBANG (‽)', user_help=True)
@plugin.output_prefix('[unicode] ')
def codepoint(bot, trigger):
    """Look up a Unicode character or a hexadecimal code point."""
    arg = trigger.group(2)
    if not arg:
        bot.reply('What code point do you want me to look up?')
        return plugin.NOLIMIT
    stripped = arg.strip()
    if len(stripped) > 0:
        arg = stripped
    if len(arg) > 1:
        if arg.startswith('U+'):
            arg = arg[2:]
        try:
            arg = chr(int(arg, 16))
        except (ValueError, TypeError):
            bot.reply("That's not a valid code point.")
            return plugin.NOLIMIT

    point, name = get_codepoint_name(arg)
    if name is None:
        name = '(No name found)'

    template = 'U+%s %s (\xe2\x97\x8c%s)'
    if not unicodedata.combining(arg):
        template = 'U+%s %s (%s)'

    bot.say(template % (point, name, arg))
