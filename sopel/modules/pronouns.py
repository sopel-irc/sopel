# coding=utf-8
"""
pronouns.py - Sopel Pronouns Plugin
Copyright © 2016, Elsie Powell
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import plugin


# Copied from pronoun.is, leaving a *lot* out. If
# https://github.com/witch-house/pronoun.is/pull/96 gets merged, using that
# would be a lot easier.
KNOWN_SETS = {
    'ze': 'ze/hir/hir/hirs/hirself',
    'ze/hir': 'ze/hir/hir/hirs/hirself',
    'ze/zir': 'ze/zir/zir/zirs/zirself',
    'they': 'they/them/their/theirs/themselves',
    'they/them': 'they/them/their/theirs/themselves',
    'they/.../themselves': 'they/them/their/theirs/themselves',
    'they/.../themself': 'they/them/their/theirs/themself',
    'she': 'she/her/her/hers/herself',
    'she/her': 'she/her/her/hers/herself',
    'he': 'he/him/his/his/himself',
    'he/him': 'he/him/his/his/himself',
    'xey': 'xey/xem/xyr/xyrs/xemself',
    'xey/xem': 'xey/xem/xyr/xyrs/xemself',
    'sie': 'sie/hir/hir/hirs/hirself',
    'sie/hir': 'sie/hir/hir/hirs/hirself',
    'it': 'it/it/its/its/itself',
    'it/it': 'it/it/its/its/itself',
    'ey': 'ey/em/eir/eirs/eirself',
    'ey/em': 'ey/em/eir/eirs/eirself',
}


@plugin.command('pronouns')
@plugin.example('.pronouns Embolalia')
def pronouns(bot, trigger):
    """Show the pronouns for a given user, defaulting to the current user if left blank."""
    if not trigger.group(3):
        pronouns = bot.db.get_nick_value(trigger.nick, 'pronouns')
        if pronouns:
            say_pronouns(bot, trigger.nick, pronouns)
        else:
            bot.reply("I don't know your pronouns! You can set them with "
                      "{}setpronouns".format(bot.config.core.help_prefix))
    else:
        pronouns = bot.db.get_nick_value(trigger.group(3), 'pronouns')
        if pronouns:
            say_pronouns(bot, trigger.group(3), pronouns)
        elif trigger.group(3) == bot.nick:
            # You can stuff an entry into the database manually for your bot's
            # gender, but like… it's a bot.
            bot.say(
                "I am a bot. Beep boop. My pronouns are it/it/its/its/itself. "
                "See https://pronoun.is/it for examples."
            )
        else:
            bot.reply("I don't know {}'s pronouns. They can set them with "
                      "{}setpronouns".format(trigger.group(3),
                                             bot.config.core.help_prefix))


def say_pronouns(bot, nick, pronouns):
    for short, set_ in KNOWN_SETS.items():
        if pronouns == set_:
            break
        short = pronouns

    bot.say("{}'s pronouns are {}. See https://pronoun.is/{} for "
            "examples.".format(nick, pronouns, short))


@plugin.command('setpronouns')
@plugin.example('.setpronouns they/them/their/theirs/themselves')
def set_pronouns(bot, trigger):
    """Set your pronouns."""
    pronouns = trigger.group(2)
    if not pronouns:
        bot.reply('What pronouns do you use?')
        return

    disambig = ''
    if pronouns == 'they':
        disambig = ' You can also use they/.../themself, if you prefer.'
        pronouns = KNOWN_SETS.get(pronouns)
    elif pronouns == 'ze':
        disambig = ' I have ze/hir. If you meant ze/zir, you can use that instead.'
        pronouns = KNOWN_SETS.get(pronouns)
    elif len(pronouns.split('/')) != 5:
        pronouns = KNOWN_SETS.get(pronouns)
        if not pronouns:
            bot.reply(
                "I'm sorry, I don't know those pronouns. "
                "You can give me a set I don't know by formatting it "
                "subject/object/possessive-determiner/possessive-pronoun/"
                "reflexive, as in: they/them/their/theirs/themselves"
            )
            return
    bot.db.set_nick_value(trigger.nick, 'pronouns', pronouns)
    bot.reply("Thanks for telling me!" + disambig)
