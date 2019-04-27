# coding=utf-8
"""coretasks.py tests"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel import coretasks
from sopel.module import VOICE, HALFOP, OP, ADMIN, OWNER
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


def test_bot_mixed_modes(sopel_bot):
    """
    Ensure mixed modes like +vha are tracked correctly.
    Sopel 6.6.6 and older would assign all modes to all users. #1575
    """

    # RPL_NAMREPLY to create Users and (zeroed) privs
    for user in set("Unothing Uvoice Uhalfop Uop Uadmin Uowner".split(" ")):
        pretrigger = PreTrigger(
            "Foo", ":test.example.com 353 Foo = #test :Foo %s" % user
        )
        trigger = Trigger(sopel_bot.config, pretrigger, None)
        coretasks.handle_names(sopel_bot, trigger)

    pretrigger = PreTrigger("Foo", "MODE #test +qvhao Uowner Uvoice Uhalfop Uadmin Uop")
    trigger = Trigger(sopel_bot.config, pretrigger, None)
    coretasks.track_modes(sopel_bot, trigger)

    assert sopel_bot.channels["#test"].privileges[Identifier("Unothing")] == 0
    assert sopel_bot.channels["#test"].privileges[Identifier("Uvoice")] == VOICE
    assert sopel_bot.channels["#test"].privileges[Identifier("Uhalfop")] == HALFOP
    assert sopel_bot.channels["#test"].privileges[Identifier("Uop")] == OP
    assert sopel_bot.channels["#test"].privileges[Identifier("Uadmin")] == ADMIN
    assert sopel_bot.channels["#test"].privileges[Identifier("Uowner")] == OWNER


def test_bot_mixed_mode_removal(sopel_bot):
    """
    Ensure mixed mode types like -h+a are handled
    Sopel 6.6.6 and older did not handle this correctly. #1575
    """

    # RPL_NAMREPLY to create Users and (zeroed) privs
    for user in set("Uvoice Uop".split(" ")):
        pretrigger = PreTrigger(
            "Foo", ":test.example.com 353 Foo = #test :Foo %s" % user
        )
        trigger = Trigger(sopel_bot.config, pretrigger, None)
        coretasks.handle_names(sopel_bot, trigger)

    pretrigger = PreTrigger("Foo", "MODE #test +qao Uvoice Uvoice Uvoice")
    trigger = Trigger(sopel_bot.config, pretrigger, None)
    coretasks.track_modes(sopel_bot, trigger)

    pretrigger = PreTrigger(
        "Foo", "MODE #test -o+o-qa+v Uvoice Uop Uvoice Uvoice Uvoice"
    )
    trigger = Trigger(sopel_bot.config, pretrigger, None)
    coretasks.track_modes(sopel_bot, trigger)

    assert sopel_bot.channels["#test"].privileges[Identifier("Uvoice")] == VOICE
    assert sopel_bot.channels["#test"].privileges[Identifier("Uop")] == OP


def test_bot_mixed_mode_types(sopel_bot):
    """
    Ensure mixed argument- and non-argument- modes are handled
    Sopel 6.6.6 and older did not behave well. #1575
    """

    # RPL_NAMREPLY to create Users and (zeroed) privs
    for user in set("Uvoice Uop Uadmin Uvoice2 Uop2 Uadmin2".split(" ")):
        pretrigger = PreTrigger(
            "Foo", ":test.example.com 353 Foo = #test :Foo %s" % user
        )
        trigger = Trigger(sopel_bot.config, pretrigger, None)
        coretasks.handle_names(sopel_bot, trigger)

    # Non-attribute-requiring non-permission mode
    pretrigger = PreTrigger("Foo", "MODE #test +amov Uadmin Uop Uvoice")
    trigger = Trigger(sopel_bot.config, pretrigger, None)
    coretasks.track_modes(sopel_bot, trigger)

    assert sopel_bot.channels["#test"].privileges[Identifier("Uvoice")] == VOICE
    assert sopel_bot.channels["#test"].privileges[Identifier("Uop")] == OP
    assert sopel_bot.channels["#test"].privileges[Identifier("Uadmin")] == ADMIN

    # Attribute-requiring non-permission modes
    # This results in a _send_who, which isn't supported in MockSopel or this
    # test, so we just make sure it results in an exception instead of privesc.
    pretrigger = PreTrigger("Foo", "MODE #test +abov Uadmin2 x!y@z Uop2 Uvoice2")
    trigger = Trigger(sopel_bot.config, pretrigger, None)
    try:
        coretasks.track_modes(sopel_bot, trigger)
    except AttributeError as e:
        if e.args[0] == "'MockSopel' object has no attribute 'enabled_capabilities'":
            return

    assert sopel_bot.channels["#test"].privileges[Identifier("Uvoice2")] == VOICE
    assert sopel_bot.channels["#test"].privileges[Identifier("Uop2")] == OP
    assert sopel_bot.channels["#test"].privileges[Identifier("Uadmin2")] == ADMIN
