# coding=utf-8

"""
spellcheck.py - Sopel spelling checker module
Copyright © 2016, Alan Huang
Licensed under the Eiffel Forum License 2.
http://sopel.chat

This module relies on aspell-python-py2 or py3, available through pypi or
https://github.com/WojciechMula/aspell-python
"""
from __future__ import unicode_literals, absolute_import, print_function, division
import aspell
from sopel.module import commands


@commands('add')
def add_command(bot, trigger):
    """
    Add words to the bot's personal dictionary
    """
    if(trigger.owner):
        c = aspell.Speller('lang', 'en')
        c.addtoPersonal(trigger.group(2))
        c.saveAllwords()
        bot.say('Added {0}.'.format(trigger.group(2)))
    else:
        bot.say('I only trust {0} to add words >:c'.format(bot.config.core.owner))


@commands('spell')
def spellchecker(bot, trigger):
    """
    Checks if the given word is spelled correctly, and suggests corrections.
    """
    if not trigger.group(2):
        bot.say('What word am I checking?')
        return

    if trigger.group(2) == bot.nick:
        bot.say('Hey, that\'s my name! Nothing wrong with it.')
        return

    if len(trigger.group(2).split(' ')) > 1:
        bot.say('One word at a time, please.')
        return

    c = aspell.Speller('lang', 'en')
    if c.check(trigger.group(2)):
        bot.say("I don't see any problems with that word.")
        return

    suggestions = c.suggest(trigger.group(2))
    count = 0
    suggestion = ''
    for word in suggestions:
        if count < 5:
            suggestion += '"{0}", '.format(word)
            count += 1

    if len(suggestion) == 0:
        bot.say("That doesn't seem to be correct.")
    else:
        bot.say("That doesn't seem to be correct. Try {0}.".format(suggestion[:-2]))
