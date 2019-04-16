# coding=utf-8
"""
emoticons.py - Sopel Emoticons Module
Copyright 2018, brasstax
Licensed under the Eiffel Forum License 2

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, example


@commands('shrug')
@example('.shrug', r'¯\_(ツ)_/¯')
def shrug(bot, trigger):
    bot.say('¯\\_(ツ)_/¯')


@commands('happy')
@example('.happy', 'ᕕ( ᐛ )ᕗ')
def happy(bot, trigger):
    bot.say('ᕕ( ᐛ )ᕗ')


@commands('tableflip', 'tflip')
@example('.tableflip', '(╯°□°）╯︵ ┻━┻')
@example('.tflip', '(╯°□°）╯︵ ┻━┻')
def tableflip(bot, trigger):
    bot.say('(╯°□°）╯︵ ┻━┻')


@commands('unflip')
@example('.unflip', '┬┬ ﻿ノ( ゜-゜ノ)')
def unflip(bot, trigger):
    bot.say('┬┬ ﻿ノ( ゜-゜ノ)')


@commands('lenny')
@example('.lenny', '( ͡° ͜ʖ ͡°)')
def lenny(bot, trigger):
    bot.say('( ͡° ͜ʖ ͡°)')


@commands('rage', 'anger')
@example('.rage', 'щ(ಠ益ಠщ)')
@example('.anger', 'щ(ಠ益ಠщ)')
def anger(bot, trigger):
    bot.say('щ(ಠ益ಠщ)')


@commands('cry')
@example('.cry', '( p′︵‵。)')
def cry(bot, trigger):
    bot.say('( p′︵‵。)')


@commands('love')
@example('.love', '(●♡∀♡)')
def love(bot, trigger):
    bot.say('(●♡∀♡)')


@commands('success', 'winner')
@example('.success', '٩( ᐛ )و')
@example('.winner', '٩( ᐛ )و')
def success(bot, trigger):
    bot.say('٩( ᐛ )و')


@commands('confused', 'wat')
@example('.confused', '(●__●)???')
@example('.wat', '(●__●)???')
def wat(bot, trigger):
    bot.say('(●__●)???')


@commands('crazy')
@example('.crazy', '⊙_ʘ')
def crazy(bot, trigger):
    bot.say('⊙_ʘ')


@commands('hungry')
@example('.hungry', 'ლ(´ڡ`ლ)')
def hungry(bot, trigger):
    bot.say('ლ(´ڡ`ლ)')


@commands('surprised')
@example('.surprised', '(((( ;°Д°))))')
def surprised(bot, trigger):
    bot.say('(((( ;°Д°))))')


@commands('sick')
@example('.sick', '(-﹏-。)')
def sick(bot, trigger):
    bot.say('(-﹏-。)')


@commands('afraid')
@example('.afraid', '(　〇□〇）')
def afraid(bot, trigger):
    bot.say('(　〇□〇）')


@commands('worried')
@example('.worried', '(　ﾟдﾟ)')
def worried(bot, trigger):
    bot.say('(　ﾟдﾟ)')
