from __future__ import annotations

import random

import pytest

from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    dice
host = irc.libera.chat
"""


@pytest.fixture
def bot(botfactory, configfactory):
    settings = configfactory('default.ini', TMP_CONFIG)
    return botfactory.preloaded(settings, ['dice'])


@pytest.fixture
def irc(bot, ircfactory):
    return ircfactory(bot)


@pytest.fixture
def user(userfactory):
    return userfactory('User')


def test_dice_command(irc, bot, user):
    random.seed(42)
    irc.pm(user, ".dice 1d20 + 2d10 + 7")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG User :[dice] 1d20 + 2d10 + 7: (4) + (1+5) + 7 = 17"
    )
