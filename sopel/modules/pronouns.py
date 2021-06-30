"""
pronouns.py - Sopel Pronouns Plugin
Copyright © 2016, Elsie Powell
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import generator_stop

from sopel import plugin


# Copied from pronoun.is, leaving a *lot* out. If
# https://github.com/witch-house/pronoun.is/pull/96 gets merged, using that
# would be a lot easier.
# If ambiguous, the earlier one will be used.
KNOWN_SETS = {
    "ze/hir": "ze/hir/hir/hirs/hirself",
    "ze/zir": "ze/zir/zir/zirs/zirself",
    "they/.../themselves": "they/them/their/theirs/themselves",
    "they/.../themself": "they/them/their/theirs/themself",
    "she/her": "she/her/her/hers/herself",
    "he/him": "he/him/his/his/himself",
    "xey/xem": "xey/xem/xyr/xyrs/xemself",
    "sie/hir": "sie/hir/hir/hirs/hirself",
    "it/it": "it/it/its/its/itself",
    "ey/em": "ey/em/eir/eirs/eirself",
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
@plugin.example('.setpronouns fae/faer/faer/faers/faerself')
@plugin.example('.setpronouns they/them/theirs')
@plugin.example('.setpronouns they/them')
def set_pronouns(bot, trigger):
    """Set your pronouns."""
    pronouns = trigger.group(2)
    if not pronouns:
        bot.reply('What pronouns do you use?')
        return

    disambig = ''
    requested_pronoun_split = pronouns.split("/")
    if len(requested_pronoun_split) < 5:
        matching = []
        for known_pronoun_set in KNOWN_SETS.values():
            known_pronoun_split = known_pronoun_set.split("/")
            if known_pronoun_set.startswith(pronouns + "/") or (
                len(requested_pronoun_split) == 3
                and (
                    (
                        # "they/.../themself"
                        requested_pronoun_split[1] == "..."
                        and requested_pronoun_split[0] == known_pronoun_split[0]
                        and requested_pronoun_split[2] == known_pronoun_split[4]
                    )
                    or (
                        # "they/them/theirs"
                        requested_pronoun_split[0:2] == known_pronoun_split[0:2]
                        and requested_pronoun_split[2] == known_pronoun_split[3]
                    )
                )
            ):
                matching.append(known_pronoun_set)

        if len(matching) == 0:
            bot.reply(
                "I'm sorry, I don't know those pronouns. "
                "You can give me a set I don't know by formatting it "
                "subject/object/possessive-determiner/possessive-pronoun/"
                "reflexive, as in: they/them/their/theirs/themselves"
            )
            return

        pronouns = matching[0]
        if len(matching) > 1:
            disambig = " Or, if you meant one of these, please tell me: {}".format(
                ", ".join(matching[1:])
            )

    bot.db.set_nick_value(trigger.nick, 'pronouns', pronouns)
    bot.reply(
        "Thanks for telling me! I'll remember you use {}.{}".format(pronouns, disambig)
    )
