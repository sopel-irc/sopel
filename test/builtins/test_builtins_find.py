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
def channel():
    return '#testing'


REPLACES_THAT_WORK = (
    ("A simple line.", r"s/line/message/", f"A simple {bold('message')}."),
    ("An escaped / line.", r"s/\//slash/", f"An escaped {bold('slash')} line."),
    ("A piped line.", r"s|line|replacement|", f"A piped {bold('replacement')}."),
    ("An escaped | line.", r"s|\||pipe|", f"An escaped {bold('pipe')} line."),
    ("An escaped \\ line.", r"s/\\/backslash/", f"An escaped {bold('backslash')} line."),
)


@pytest.mark.parametrize('original, command, result', REPLACES_THAT_WORK)
def test_valid_replacements(bot, irc, user, channel, original, command, result):
    irc.channel_joined(channel, ['User'])

    irc.say(user, channel, original)
    irc.say(user, channel, command)

    assert len(bot.backend.message_sent) == 1, (
        "The bot should respond with exactly one line.")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG %s :User meant to say: %s" % (channel, result),
    )
