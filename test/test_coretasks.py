# coding=utf-8
"""coretasks.py tests"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.module import VOICE, HALFOP, OP, ADMIN, OWNER
from sopel.tools import Identifier
from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Uowner
nick = TestBot
enable = coretasks
"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('conf.ini', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig, botfactory):
    return botfactory.preloaded(tmpconfig)


def test_bot_mixed_modes(mockbot, ircfactory):
    """Ensure mixed modes like ``+vha`` are tracked correctly.

    Sopel 6.6.6 and older would assign all modes to all users.

    .. seealso::

        GitHub issue #1575.
    """
    irc = ircfactory(mockbot)
    irc.channel_joined('#test', [
        'Uowner', 'Uvoice', 'Uhalfop', 'Uadmin', 'Uop', 'Unothing'])
    irc.mode_set('#test', '+qvhao', [
        'Uowner', 'Uvoice', 'Uhalfop', 'Uadmin', 'Uop'])

    assert mockbot.channels["#test"].privileges[Identifier("Uowner")] == OWNER
    assert mockbot.channels["#test"].privileges[Identifier("Uvoice")] == VOICE
    assert mockbot.channels["#test"].privileges[Identifier("Uhalfop")] == HALFOP
    assert mockbot.channels["#test"].privileges[Identifier("Uadmin")] == ADMIN
    assert mockbot.channels["#test"].privileges[Identifier("Uop")] == OP
    assert mockbot.channels["#test"].privileges[Identifier("Unothing")] == 0


def test_bot_mixed_mode_removal(mockbot, ircfactory):
    """Ensure mixed mode types like ``-h+a`` are handled.

    Sopel 6.6.6 and older did not handle this correctly.

    .. seealso::

        GitHub issue #1575.
    """
    irc = ircfactory(mockbot)
    irc.channel_joined('#test', ['Uvoice', 'Uop'])

    irc.mode_set('#test', '+qao', ['Uvoice', 'Uvoice', 'Uvoice'])
    assert mockbot.channels["#test"].privileges[Identifier("Uop")] == 0
    assert mockbot.channels["#test"].privileges[Identifier("Uvoice")] == (
        ADMIN + OWNER + OP), 'Uvoice got +q, +a, and +o modes'

    irc.mode_set('#test', '-o+o-qa+v', [
        'Uvoice', 'Uop', 'Uvoice', 'Uvoice', 'Uvoice'])
    assert mockbot.channels["#test"].privileges[Identifier("Uop")] == OP, (
        'OP got +o only')
    assert mockbot.channels["#test"].privileges[Identifier("Uvoice")] == VOICE, (
        'Uvoice got -o, -q, -a, then +v')


def test_bot_mixed_mode_types(mockbot, ircfactory):
    """Ensure mixed argument-required and -not-required modes are handled.

    Sopel 6.6.6 and older did not behave well.

    .. seealso::

        GitHub issue #1575.
    """
    irc = ircfactory(mockbot)
    irc.channel_joined('#test', [
        'Uvoice', 'Uop', 'Uadmin', 'Uvoice2', 'Uop2', 'Uadmin2'])
    irc.mode_set('#test', '+amov', ['Uadmin', 'Uop', 'Uvoice'])

    assert mockbot.channels["#test"].privileges[Identifier("Uadmin")] == ADMIN
    assert mockbot.channels["#test"].privileges[Identifier("Uop")] == OP
    assert mockbot.channels["#test"].privileges[Identifier("Uvoice")] == VOICE

    irc.mode_set('#test', '+abov', ['Uadmin2', 'x!y@z', 'Uop2', 'Uvoice2'])

    assert mockbot.channels["#test"].privileges[Identifier("Uadmin2")] == 0
    assert mockbot.channels["#test"].privileges[Identifier("Uop2")] == 0
    assert mockbot.channels["#test"].privileges[Identifier("Uvoice2")] == 0

    assert mockbot.backend.message_sent == rawlist('WHO #test'), (
        'Upon finding an unexpected nick, the bot must send a WHO request.')


def test_mode_colon(mockbot, ircfactory):
    """Ensure mode messages with colons are parsed properly."""
    irc = ircfactory(mockbot)
    irc.channel_joined('#test', ['Uadmin', 'Uvoice'])
    irc.mode_set('#test', '+av', ['Uadmin', ':Uvoice'])

    assert mockbot.channels["#test"].privileges[Identifier("Uvoice")] == VOICE
    assert mockbot.channels["#test"].privileges[Identifier("Uadmin")] == ADMIN
