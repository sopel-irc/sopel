"""
codepoints.py - Willie Codepoints Module
Copyright 2013, Edward Powell, embolalia.net
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
import unicodedata
from willie.module import commands, example, NOLIMIT


@commands('u')
@example('.u 203D')
def codepoint(bot, trigger):
    arg = trigger.group(2).strip()
    if len(arg) == 0:
        bot.reply('What code point do you want me to look up?')
        return NOLIMIT
    elif len(arg) > 1:
        try:
            arg = unichr(int(arg, 16))
        except:
            bot.reply("That's not a valid code point.")
            return NOLIMIT

    # Get the hex value for the code point, and drop the 0x from the front
    point = str(hex(ord(u'' + arg)))[2:]
    # Make the hex 4 characters long with preceding 0s, and all upper case
    point = point.rjust(4, '0').upper()
    try:
        name = unicodedata.name(arg)
    except ValueError:
        return 'U+%s (No name found)' % point

    if not unicodedata.combining(arg):
        template = 'U+%s %s (%s)'
    else:
        template = 'U+%s %s (\xe2\x97\x8c%s)'
    bot.say(template % (point, name, arg))
