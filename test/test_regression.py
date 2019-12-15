# coding=utf-8
"""Regression tests"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel import coretasks, tools


TMP_CONFIG = """
[core]
owner = testnick
nick = Sopel
enable = coretasks
"""


def test_bot_legacy_permissions(configfactory, botfactory, triggerfactory):
    """
    Make sure permissions match after being updated from both RPL_NAMREPLY
    and RPL_WHOREPLY, #1482
    """
    mockbot = botfactory(configfactory('default.cfg', TMP_CONFIG))
    nick = tools.Identifier("Admin")

    # RPL_NAMREPLY
    mockwrapper = triggerfactory.wrapper(
        mockbot, ":test.example.com 353 Foo = #test :Foo ~@Admin")
    coretasks.handle_names(mockwrapper, mockwrapper._trigger)

    assert '#test' in mockbot.channels
    assert nick in mockbot.channels["#test"].privileges

    assert '#test' in mockbot.privileges
    assert nick in mockbot.privileges["#test"]

    channel_privileges = mockbot.channels["#test"].privileges[nick]
    privileges = mockbot.privileges["#test"][nick]

    assert channel_privileges == privileges

    # RPL_WHOREPLY
    mockwrapper = triggerfactory.wrapper(
        mockbot,
        ":test.example.com 352 Foo #test "
        "~Admin adminhost test.example.com Admin Hr~ :0 Admin")
    coretasks.recv_who(mockwrapper, mockwrapper._trigger)

    channel_privileges = mockbot.channels["#test"].privileges[nick]
    privileges = mockbot.privileges["#test"][nick]

    assert channel_privileges == privileges
    assert mockbot.users.get(nick) is not None
