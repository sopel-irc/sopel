"""Tests for Sopel's ``find`` plugin"""
from __future__ import annotations

import pytest

from sopel.formatting import bold
from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    find
host = irc.libera.chat
"""


@pytest.fixture
def bot(botfactory, configfactory):
    settings = configfactory('default.ini', TMP_CONFIG)
    return botfactory.preloaded(settings, ['find'])


@pytest.fixture
def irc(bot, ircfactory):
    return ircfactory(bot)


@pytest.fixture
def user(userfactory):
    return userfactory('User')


@pytest.fixture
def other_user(userfactory):
    return userfactory('other_user')


@pytest.fixture
def channel():
    return '#testing'


REPLACES_THAT_WORK = (
    ("A simple line.", r"s/line/message/", f"A simple {bold('message')}."),
    ("An escaped / line.", r"s/\//slash/", f"An escaped {bold('slash')} line."),
    ("A piped line.", r"s|line|replacement|", f"A piped {bold('replacement')}."),
    ("An escaped | line.", r"s|\||pipe|", f"An escaped {bold('pipe')} line."),
    ("An escaped \\ line.", r"s/\\/backslash/", f"An escaped {bold('backslash')} line."),
    ("abABab", r"s/b/c/g", "abABab".replace('b', bold('c'))),  # g (global) flag
    ("ABabAB", r"s/b/c/i", f"A{bold('c')}abAB"),  # i (case-insensitive) flag
    ("ABabAB", r"s/b/c/ig", f"A{bold('c')}a{bold('c')}A{bold('c')}"),  # both flags
)


@pytest.mark.parametrize('original, command, result', REPLACES_THAT_WORK)
def test_valid_replacements(bot, irc, user, channel, original, command, result):
    """Verify that basic replacement functionality works."""
    irc.channel_joined(channel, [user.nick])

    irc.say(user, channel, original)
    irc.say(user, channel, command)

    assert len(bot.backend.message_sent) == 1, (
        "The bot should respond with exactly one line.")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG %s :%s meant to say: %s" % (channel, user.nick, result),
    )


def test_multiple_users(bot, irc, user, other_user, channel):
    """Verify that correcting another user's line works."""
    irc.channel_joined(channel, [user.nick, other_user.nick])

    irc.say(other_user, channel, 'Some weather we got yesterday')
    irc.say(user, channel, '%s: s/yester/to/' % other_user.nick)

    assert len(bot.backend.message_sent) == 1, (
        "The bot should respond with exactly one line.")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG %s :%s thinks %s meant to say: %s" % (
            channel, user.nick, other_user.nick,
            f"Some weather we got {bold('to')}day",
        ),
    )


def test_replace_the_replacement(bot, irc, user, channel):
    """Verify replacing text that was already replaced."""
    irc.channel_joined(channel, [user.nick])

    irc.say(user, channel, 'spam')
    irc.say(user, channel, 's/spam/eggs/')
    irc.say(user, channel, 's/eggs/bacon/')

    assert len(bot.backend.message_sent) == 2, (
        "The bot should respond twice.")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG %s :%s meant to say: %s" % (
            channel, user.nick, bold('eggs'),
        ),
        "PRIVMSG %s :%s meant to say: %s" % (
            channel, user.nick, bold('bacon'),
        ),
    )
