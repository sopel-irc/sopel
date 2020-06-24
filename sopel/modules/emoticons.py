# coding=utf-8
"""
emoticons.py - Sopel Emoticons Module
Copyright 2018, brasstax
Licensed under the Eiffel Forum License 2

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import module


@module.commands('shrug')
@module.action_commands('shrugs')
@module.example('.shrug', r'¯\_(ツ)_/¯')
def shrug(bot, trigger):
    bot.say('¯\\_(ツ)_/¯')


@module.commands('happy')
@module.example('.happy', 'ᕕ( ᐛ )ᕗ')
def happy(bot, trigger):
    bot.say('ᕕ( ᐛ )ᕗ')


@module.commands('tableflip', 'tflip')
@module.action_commands('flips table', 'flips a table', 'flips the table')
@module.example('.tableflip', '(╯°□°）╯︵ ┻━┻')
@module.example('.tflip', '(╯°□°）╯︵ ┻━┻')
def tableflip(bot, trigger):
    bot.say('(╯°□°）╯︵ ┻━┻')


@module.commands('unflip')
@module.action_commands('unflips table', 'unflips the table')
@module.example('.unflip', '┬┬ ﻿ノ( ゜-゜ノ)')
def unflip(bot, trigger):
    bot.say('┬┬ ﻿ノ( ゜-゜ノ)')


@module.commands('lenny')
@module.example('.lenny', '( ͡° ͜ʖ ͡°)')
def lenny(bot, trigger):
    bot.say('( ͡° ͜ʖ ͡°)')


@module.commands('rage', 'anger')
@module.example('.rage', 'щ(ಠ益ಠщ)')
@module.example('.anger', 'щ(ಠ益ಠщ)')
def anger(bot, trigger):
    bot.say('щ(ಠ益ಠщ)')


@module.commands('cry')
@module.action_commands('cries')
@module.example('.cry', '( p′︵‵。)')
def cry(bot, trigger):
    bot.say('( p′︵‵。)')


@module.commands('love')
@module.example('.love', '(●♡∀♡)')
def love(bot, trigger):
    bot.say('(●♡∀♡)')


@module.commands('success', 'winner')
@module.example('.success', '٩( ᐛ )و')
@module.example('.winner', '٩( ᐛ )و')
def success(bot, trigger):
    bot.say('٩( ᐛ )و')


@module.commands('confused', 'wat')
@module.example('.confused', '(●__●)???')
@module.example('.wat', '(●__●)???')
def wat(bot, trigger):
    bot.say('(●__●)???')


@module.commands('crazy')
@module.example('.crazy', '⊙_ʘ')
def crazy(bot, trigger):
    bot.say('⊙_ʘ')


@module.commands('hungry')
@module.example('.hungry', 'ლ(´ڡ`ლ)')
def hungry(bot, trigger):
    bot.say('ლ(´ڡ`ლ)')


@module.commands('surprised')
@module.example('.surprised', '(((( ;°Д°))))')
def surprised(bot, trigger):
    bot.say('(((( ;°Д°))))')


@module.commands('sick')
@module.example('.sick', '(-﹏-。)')
def sick(bot, trigger):
    bot.say('(-﹏-。)')


@module.commands('afraid')
@module.example('.afraid', '(　〇□〇）')
def afraid(bot, trigger):
    bot.say('(　〇□〇）')


@module.commands('worried')
@module.example('.worried', '(　ﾟдﾟ)')
def worried(bot, trigger):
    bot.say('(　ﾟдﾟ)')
