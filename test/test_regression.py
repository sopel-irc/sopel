# coding=utf-8
"""Regression tests"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel import coretasks
from sopel.tools import Identifier
from sopel.test_tools import MockSopel, MockSopelWrapper
from sopel.trigger import PreTrigger, Trigger


@pytest.fixture
def sopel():
    bot = MockSopel("Sopel")
    return bot


@pytest.fixture
def sopel_bot(sopel):
    pretrigger = PreTrigger(Identifier("Foo"), "PING abc")
    bot = MockSopelWrapper(sopel, pretrigger)
    bot.privileges = dict()
    bot.users = dict()
    return bot


def test_bot_legacy_permissions(sopel_bot):
    """
    Make sure permissions match after being updated from both RPL_NAMREPLY
    and RPL_WHOREPLY, #1482
    """

    nick = Identifier("Admin")

    # RPL_NAMREPLY
    pretrigger = PreTrigger("Foo", ":test.example.com 353 Foo = #test :Foo ~@Admin")
    trigger = Trigger(sopel_bot.config, pretrigger, None)
    coretasks.handle_names(sopel_bot, trigger)

    assert (
        sopel_bot.channels["#test"].privileges[nick] ==
        sopel_bot.privileges["#test"][nick]
    )

    # RPL_WHOREPLY
    pretrigger = PreTrigger(
        "Foo",
        ":test.example.com 352 Foo #test ~Admin adminhost test.example.com Admin Hr~ :0 Admin",
    )
    trigger = Trigger(sopel_bot.config, pretrigger, None)
    coretasks.recv_who(sopel_bot, trigger)

    assert (
        sopel_bot.channels["#test"].privileges[nick] ==
        sopel_bot.privileges["#test"][nick]
    )

    assert sopel_bot.users.get(nick) is not None
