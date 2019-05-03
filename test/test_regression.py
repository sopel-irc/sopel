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


def test_bot_legacy_permissions(sopel):
    """
    Make sure permissions match after being updated from both RPL_NAMREPLY
    and RPL_WHOREPLY, #1482
    """

    nick = Identifier("Admin")

    # RPL_NAMREPLY
    pretrigger = PreTrigger("Foo", ":test.example.com 353 Foo = #test :Foo ~@Admin")
    trigger = Trigger(sopel.config, pretrigger, None)
    coretasks.handle_names(MockSopelWrapper(sopel, trigger), trigger)

    assert sopel.channels["#test"].privileges[nick] == sopel.privileges["#test"][nick]

    # RPL_WHOREPLY
    pretrigger = PreTrigger(
        "Foo",
        ":test.example.com 352 Foo #test ~Admin adminhost test.example.com Admin Hr~ :0 Admin",
    )
    trigger = Trigger(sopel.config, pretrigger, None)
    coretasks.recv_who(MockSopelWrapper(sopel, trigger), trigger)

    assert sopel.channels["#test"].privileges[nick] == sopel.privileges["#test"][nick]

    assert sopel.users.get(nick) is not None
