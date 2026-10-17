"""Tests of the bot's blocking/ignoring features.

The ``[core]`` config section contains three lists that can be used to
block/ignore users:

- ``host_blocks``: hostnames
- ``hostmask_blocks``: hostmasks
- ``nick_blocks``: nicknames

After we complete enhancements to the ignore system (see issue 1355), the tests
here can be expanded to check both regex and non-regex pattern behavior in
various combinations. For now, each setting is checked in isolation and we
simply trust that ``or`` logic works as expected.
"""
from __future__ import annotations

import typing

import pytest

from sopel import bot, trigger


if typing.TYPE_CHECKING:
    from sopel.config import Config
    from sopel.tests.factories import BotFactory, ConfigFactory


BASE_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable = coretasks
"""

NICK_CONFIG = f"""
{BASE_CONFIG}
nick_blocks =
    spamuser
    escaped\\[user\\]
"""

HOST_CONFIG = f"""
{BASE_CONFIG}
host_blocks =
    spamhost\\.com
"""

HOSTMASK_CONFIG = f"""
{BASE_CONFIG}
hostmask_blocks =
    spamuser!.*@spamhost\\.com
"""


def mockbot(
    botfactory: BotFactory,
    configfactory: ConfigFactory,
    config: Config,
) -> bot.Sopel:
    return botfactory(configfactory('test.cfg', config))


def test_is_pretrigger_blocked_empty(
    configfactory: ConfigFactory,
    botfactory: BotFactory,
):
    """Test that no user is blocked when no blocking settings are configured."""
    bot = mockbot(botfactory, configfactory, BASE_CONFIG)

    # basic "hello" message from a user
    line = ':Foo!foo@example.com PRIVMSG #sopel :hello'
    pretrigger = trigger.PreTrigger(bot.nick, line)

    assert bot._is_pretrigger_blocked(pretrigger) == (None, None, None)


@pytest.mark.parametrize(
    'cfg, result',
    [
        (NICK_CONFIG, (True, False, False)),
        (HOST_CONFIG, (False, True, False)),
        (HOSTMASK_CONFIG, (False, False, True)),
    ],
    ids=['nick_blocks', 'host_blocks', 'hostmask_blocks'],
)
def test_is_pretrigger_blocked_single(
    configfactory: ConfigFactory,
    botfactory: BotFactory,
    cfg: str,
    result: tuple[bool, bool, bool],
):
    """Test that each block type returns ``True`` in the correct tuple slot."""
    bot = mockbot(botfactory, configfactory, cfg)

    # basic "hello" message from a blocked user
    line = ':spamuser!notevil@spamhost.com PRIVMSG #sopel :hello'
    pretrigger = trigger.PreTrigger(bot.nick, line)

    assert bot._is_pretrigger_blocked(pretrigger) == result
