"""Tests for Sopel's ``admin`` plugin"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sopel.tests import rawlist


if TYPE_CHECKING:
    from sopel.bot import Sopel
    from sopel.config import Config
    from sopel.tests.factories import (
        BotFactory,
        ConfigFactory,
        IRCFactory,
        UserFactory,
    )
    from sopel.tests.mocks import MockIRCServer, MockUser


BOT_NICK = 'TestBot'
TEST_CHAN = '#test'
OWNER_NICK = 'Uowner'

TMP_CONFIG = f"""
[core]
owner = {OWNER_NICK}
nick = {BOT_NICK}

[admin]
auto_accept_invite = True
"""


@pytest.fixture
def tmpconfig(configfactory: ConfigFactory) -> Config:
    return configfactory('conf.ini', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig: Config, botfactory: BotFactory) -> Sopel:
    return botfactory.preloaded(tmpconfig, ['admin'])


@pytest.fixture
def irc(mockbot: Sopel, ircfactory: IRCFactory) -> MockIRCServer:
    return ircfactory(mockbot, join_threads=True)


@pytest.fixture
def owner(userfactory: UserFactory) -> MockUser:
    return userfactory(OWNER_NICK, 'owner', 'example.com')


@pytest.fixture
def henry(userfactory: UserFactory) -> MockUser:
    return userfactory('Henry', 'king', 'palace.example.com')


def test_invite_accept_admin(irc: MockIRCServer, owner: MockUser) -> None:
    """Verify that bot admins' invites are accepted."""
    irc.bot.settings.admin.auto_accept_invite = False
    irc.invite(owner, BOT_NICK, TEST_CHAN)
    assert len(irc.bot.backend.message_sent) == 1
    assert irc.bot.backend.message_sent == rawlist('JOIN #test')


def test_invite_accept_non_admin_auto(
    irc: MockIRCServer,
    henry: MockUser,
) -> None:
    """Verify that non-admin invites are accepted if enabled."""
    irc.bot.settings.admin.auto_accept_invite = True
    irc.invite(henry, BOT_NICK, TEST_CHAN)
    assert len(irc.bot.backend.message_sent) == 1
    assert irc.bot.backend.message_sent == rawlist('JOIN #test')


def test_invite_accept_non_admin_no_auto(
    irc: MockIRCServer,
    henry: MockUser,
) -> None:
    """Verify that non-admin invites are ignored if disabled."""
    irc.bot.settings.admin.auto_accept_invite = False
    irc.invite(henry, BOT_NICK, TEST_CHAN)
    assert len(irc.bot.backend.message_sent) == 0


def test_invite_accept_not_us(irc: MockIRCServer, henry: MockUser) -> None:
    """Verify that the plugin ignores invites not meant for it."""
    irc.bot.settings.admin.auto_accept_invite = True
    irc.invite(henry, 'Anne', '#boudoir')
    assert len(irc.bot.backend.message_sent) == 0
