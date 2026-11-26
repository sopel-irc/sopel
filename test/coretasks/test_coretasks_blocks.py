"""Test behavior of the .blocks command from ``sopel.coretasks``"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sopel.tests import rawlist


if TYPE_CHECKING:
    from sopel.bot import Sopel
    from sopel.config import Config
    from sopel.tests.factories import BotFactory, ConfigFactory


TMP_CONFIG = """
[core]
owner = owner
nick = TestBot
enable = coretasks
"""


@pytest.fixture
def tmpconfig(configfactory: ConfigFactory) -> Config:
    return configfactory('conf.ini', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig: Config, botfactory: BotFactory) -> Sopel:
    mockbot = botfactory.preloaded(tmpconfig)
    mockbot.backend.connected = True
    return mockbot


def test_blocks_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


# .blocks list

def test_blocks_list_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_list_wrong_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list thisiswrong")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: Invalid input for displaying blocks.',
    )


def test_blocks_list_host(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list host")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: No hosts listed in the blocklist.',
    )

    # adding a blocked host pattern
    mockbot.settings.core.host_blocks = [r'example\.com']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list host")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :Blocked hosts: example\\.com',
    )

    # adding more than one blocked host pattern
    mockbot.settings.core.host_blocks = [
        r'a\.example\.com',
        r'b\.example\.com',
        r'c\.example\.com',
    ]

    expected = ', '.join(set(mockbot.settings.core.host_blocks))
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list host")
    assert mockbot.backend.message_sent[2:] == rawlist(
        'PRIVMSG #test :Blocked hosts: %s' % expected,
    )


def test_blocks_list_nick(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list nick")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: No nicks listed in the blocklist.',
    )

    # adding a blocked nick pattern
    mockbot.settings.core.nick_blocks = [r'Nicks?']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list nick")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :Blocked nicks: Nicks?',
    )

    # adding more than one blocked nick pattern
    mockbot.settings.core.nick_blocks = [
        r'Alii?ce_*',
        r'Bo+b_*',
        r'Ch[a4]rl[i1]e_*',
    ]

    expected = ', '.join(set(
        mockbot.make_identifier(nick)
        for nick in mockbot.settings.core.nick_blocks))
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list nick")
    assert mockbot.backend.message_sent[2:] == rawlist(
        'PRIVMSG #test :Blocked nicks: %s' % expected,
    )


def test_blocks_list_hostmask(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list hostmask")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: No hostmasks listed in the blocklist.',
    )

    # adding a blocked hostmask pattern
    mockbot.settings.core.hostmask_blocks = [r'Guest.*!.*@example\.com']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list hostmask")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :Blocked hostmasks: Guest.*!.*@example\\.com',
    )

    # adding more than one blocked hostmask pattern
    mockbot.settings.core.hostmask_blocks = [
        r'Alice.*!.*@a\.example\.com',
        r'Bob.*!.*@b\.example\.com',
        r'Charlie.*!.*@c\.example\.com',
    ]

    expected = ', '.join(set(mockbot.settings.core.hostmask_blocks))
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks list hostmask")
    assert mockbot.backend.message_sent[2:] == rawlist(
        'PRIVMSG #test :Blocked hostmasks: %s' % expected,
    )


# .blocks add

def test_blocks_add_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_add_wrong_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add how")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add how come")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :owner: Invalid format for adding a block. Try: .blocks add (nick|host|hostmask) pattern',
    )


def test_blocks_add_nick_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add nick")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_add_host_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add host")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_add_hostmask_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add hostmask")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_add_nick(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add nick Ali+ce")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: Successfully added block: Ali+ce',
    )

    assert mockbot.settings.core.nick_blocks == ['Ali+ce']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add nick Ch[a4]rlie")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :owner: Successfully added block: Ch[a4]rlie',
    )

    assert sorted(mockbot.settings.core.nick_blocks) == [
        'Ali+ce', 'Ch[a4]rlie',
    ]


def test_blocks_add_host(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add host a\\.example\\.com")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: Successfully added block: a\\.example\\.com',
    )

    assert mockbot.settings.core.host_blocks == ['a\\.example\\.com']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add host b\\.example\\.com")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :owner: Successfully added block: b\\.example\\.com',
    )

    assert sorted(mockbot.settings.core.host_blocks) == [
        'a\\.example\\.com', 'b\\.example\\.com',
    ]


def test_blocks_add_hostmask(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add hostmask Alice.*!.*@a\\.example\\.com")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: Successfully added block: Alice.*!.*@a\\.example\\.com',
    )

    assert mockbot.settings.core.hostmask_blocks == ['Alice.*!.*@a\\.example\\.com']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks add hostmask Bob.*!.*@b\\.example\\.com")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :owner: Successfully added block: Bob.*!.*@b\\.example\\.com',
    )

    assert sorted(mockbot.settings.core.hostmask_blocks) == [
        'Alice.*!.*@a\\.example\\.com', 'Bob.*!.*@b\\.example\\.com',
    ]


# .blocks del

def test_blocks_del_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_del_wrong_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del how")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del how come")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :owner: Invalid format for deleting a block. Try: .blocks add (nick|host|hostmask) pattern',
    )


def test_blocks_del_nick_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del nick")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_del_host_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del host")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_del_hostmask_no_arg(mockbot: Sopel):
    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del hostmask")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: I could not figure out what you wanted to do.',
    )


def test_blocks_del_nick(mockbot: Sopel):
    mockbot.settings.core.nick_blocks = ['Ali+ce', 'Bo+b']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del nick Ch[a4]rlie")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: No matching nick block found for: Ch[a4]rlie',
    )

    assert sorted(mockbot.settings.core.nick_blocks) == ['Ali+ce', 'Bo+b']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del nick Ali+ce")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :owner: Successfully deleted block: Ali+ce',
    )

    assert mockbot.settings.core.nick_blocks == ['Bo+b']


def test_blocks_del_host(mockbot: Sopel):
    mockbot.settings.core.host_blocks = ['a\\.example\\.com', 'b\\.example\\.com']

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del host c\\.example\\.com")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: No matching host block found for: c\\.example\\.com',
    )

    assert sorted(mockbot.settings.core.host_blocks) == [
        'a\\.example\\.com',
        'b\\.example\\.com',
    ]

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del host a\\.example\\.com")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :owner: Successfully deleted block: a\\.example\\.com',
    )

    assert mockbot.settings.core.host_blocks == ['b\\.example\\.com']


def test_blocks_del_hostmask(mockbot: Sopel):
    mockbot.settings.core.hostmask_blocks = [
        'Alice.*!.*@a\\.example\\.com',
        'Bob.*!.*@b\\.example\\.com',
    ]

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del hostmask Charlie.*!.*@a\\.example\\.com")
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #test :owner: No matching hostmask block found for: Charlie.*!.*@a\\.example\\.com',
    )

    assert sorted(mockbot.settings.core.hostmask_blocks) == [
        'Alice.*!.*@a\\.example\\.com',
        'Bob.*!.*@b\\.example\\.com',
    ]

    mockbot.on_message(
        ":owner!owner@user PRIVMSG #test :.blocks del hostmask Alice.*!.*@a\\.example\\.com")
    assert mockbot.backend.message_sent[1:] == rawlist(
        'PRIVMSG #test :owner: Successfully deleted block: Alice.*!.*@a\\.example\\.com',
    )

    assert mockbot.settings.core.hostmask_blocks == ['Bob.*!.*@b\\.example\\.com']
