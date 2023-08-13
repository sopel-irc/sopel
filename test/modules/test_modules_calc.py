from __future__ import annotations

import pytest

from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    calc
host = irc.libera.chat
"""


@pytest.fixture
def bot(botfactory, configfactory):
    settings = configfactory('default.ini', TMP_CONFIG)
    return botfactory.preloaded(settings, ['calc'])


@pytest.fixture
def irc(bot, ircfactory):
    return ircfactory(bot)


@pytest.fixture
def user(userfactory):
    return userfactory('User')


def test_calc_command(irc, bot, user):
    irc.pm(user, ".calc 1 + 1")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG User :[calc] 2"
    )
