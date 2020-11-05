# coding=utf-8
"""Tests for targets: Channel & User"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import plugin
from sopel.tools import Identifier, target


def test_channel():
    name = Identifier('#chan')
    channel = target.Channel(name)

    assert channel.name == name
    assert not channel.users
    assert not channel.privileges
    assert channel.topic == ''
    assert channel.last_who is None


def test_channel_add_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user)

    assert user.nick in channel.users
    assert channel.users[user.nick] is user

    assert user.nick in channel.privileges
    assert channel.privileges[user.nick] == 0

    assert channel.name in user.channels


def test_channel_add_user_voiced():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.VOICE)

    assert user.nick in channel.users
    assert channel.users[user.nick] is user

    assert user.nick in channel.privileges
    assert channel.privileges[user.nick] == plugin.VOICE


def test_channel_add_user_multi_privileges():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.VOICE | plugin.OP)

    assert user.nick in channel.users
    assert channel.users[user.nick] is user

    assert user.nick in channel.privileges
    assert channel.privileges[user.nick] & plugin.VOICE == plugin.VOICE
    assert channel.privileges[user.nick] & plugin.OP == plugin.OP


def test_channel_add_user_replace():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.VOICE)
    channel.add_user(user, plugin.OP)

    assert user.nick in channel.users
    assert channel.users[user.nick] is user

    assert user.nick in channel.privileges
    assert channel.privileges[user.nick] == plugin.OP
    assert channel.privileges[user.nick] & plugin.VOICE == 0, (
        'This user must be replaced, without previous privileges')


def test_channel_has_privilege():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    # unknown user
    assert not channel.has_privilege(user.nick, plugin.VOICE)
    assert not channel.has_privilege(user.nick, plugin.OP)

    # user added without privileges
    channel.add_user(user)
    assert not channel.has_privilege(user.nick, plugin.VOICE)
    assert not channel.has_privilege(user.nick, plugin.OP)

    # user added with VOICE privilege
    channel.add_user(user, plugin.VOICE)
    assert channel.has_privilege(user.nick, plugin.VOICE)
    assert not channel.has_privilege(user.nick, plugin.OP)

    # user added with OP privilege
    channel.add_user(user, plugin.OP)
    assert channel.has_privilege(user.nick, plugin.VOICE)
    assert channel.has_privilege(user.nick, plugin.OP)

    # user added with both VOICE & OP privilege
    channel.add_user(user, plugin.VOICE | plugin.OP)
    assert channel.has_privilege(user.nick, plugin.VOICE)
    assert channel.has_privilege(user.nick, plugin.OP)


def test_channel_is_priv_level_unknown_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    assert not channel.is_oper(user.nick)
    assert not channel.is_owner(user.nick)
    assert not channel.is_admin(user.nick)
    assert not channel.is_op(user.nick)
    assert not channel.is_halfop(user.nick)
    assert not channel.is_voiced(user.nick)


def test_channel_is_priv_level_unprivileged_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user)

    assert not channel.is_oper(user.nick)
    assert not channel.is_owner(user.nick)
    assert not channel.is_admin(user.nick)
    assert not channel.is_op(user.nick)
    assert not channel.is_halfop(user.nick)
    assert not channel.is_voiced(user.nick)


def test_channel_is_priv_level_voiced_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.VOICE)

    assert not channel.is_oper(user.nick)
    assert not channel.is_owner(user.nick)
    assert not channel.is_admin(user.nick)
    assert not channel.is_op(user.nick)
    assert not channel.is_halfop(user.nick)
    assert channel.is_voiced(user.nick)


def test_channel_is_priv_level_halfop_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.HALFOP)

    assert not channel.is_oper(user.nick)
    assert not channel.is_owner(user.nick)
    assert not channel.is_admin(user.nick)
    assert not channel.is_op(user.nick)
    assert channel.is_halfop(user.nick)
    assert not channel.is_voiced(user.nick)


def test_channel_is_priv_level_op_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.OP)

    assert not channel.is_oper(user.nick)
    assert not channel.is_owner(user.nick)
    assert not channel.is_admin(user.nick)
    assert channel.is_op(user.nick)
    assert not channel.is_halfop(user.nick)
    assert not channel.is_voiced(user.nick)


def test_channel_is_priv_level_admin_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.ADMIN)

    assert not channel.is_oper(user.nick)
    assert not channel.is_owner(user.nick)
    assert channel.is_admin(user.nick)
    assert not channel.is_op(user.nick)
    assert not channel.is_halfop(user.nick)
    assert not channel.is_voiced(user.nick)


def test_channel_is_priv_level_owner_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.OWNER)

    assert not channel.is_oper(user.nick)
    assert channel.is_owner(user.nick)
    assert not channel.is_admin(user.nick)
    assert not channel.is_op(user.nick)
    assert not channel.is_halfop(user.nick)
    assert not channel.is_voiced(user.nick)


def test_channel_is_priv_level_oper_user():
    channel = target.Channel(Identifier('#chan'))
    user = target.User(Identifier('TestUser'), 'example', 'example.com')

    channel.add_user(user, plugin.OPER)

    assert channel.is_oper(user.nick)
    assert not channel.is_owner(user.nick)
    assert not channel.is_admin(user.nick)
    assert not channel.is_op(user.nick)
    assert not channel.is_halfop(user.nick)
    assert not channel.is_voiced(user.nick)
