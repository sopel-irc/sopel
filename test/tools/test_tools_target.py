"""Tests for targets: Channel & User"""
from __future__ import annotations

import pytest

from sopel import plugin
from sopel.tools import Identifier, target


def test_user():
    nick = Identifier('River')
    username = 'tamr'
    host = 'good.ship.serenity.example.com'
    user = target.User(nick, username, host)

    assert user.nick == nick
    assert user.user == username
    assert user.host == host
    assert user.realname is None
    assert user.channels == {}
    assert user.account is None
    assert user.away is None
    assert user.is_bot is None
    assert user.hostmask == '%s!%s@%s' % (nick, username, host)


def test_user_eq():
    nick = Identifier('Brian')
    username = 'brian'
    host = 'example.com'
    user = target.User(nick, username, host)

    assert user != nick
    assert user == target.User(nick, None, None)
    assert user == target.User(nick, username, None)
    assert user == target.User(nick, None, host)
    assert user == target.User(nick, username, host)
    assert user != target.User(Identifier('Mandy'), username, host)


def test_user_comparison():
    brian = target.User(Identifier('Brian'), None, None)
    mandy = target.User(Identifier('Mandy'), None, None)
    reg = target.User(Identifier('Reg'), None, None)

    assert brian < mandy < reg

    arthur = Identifier('Arthur')
    with pytest.raises(TypeError):
        arthur < brian


def test_channel():
    name = Identifier('#chan')
    channel = target.Channel(name)

    assert channel.name == name
    assert not channel.users
    assert not channel.privileges
    assert channel.topic == ''
    assert channel.last_who is None


def test_channel_eq():
    name = Identifier('#chan')
    channel = target.Channel(name)

    assert channel != name
    assert channel == target.Channel(name)
    assert channel != target.Channel(Identifier('#not_chan'))


def test_channel_comparison():
    channel = target.Channel(Identifier('#chan'))
    support = target.Channel(Identifier('#support'))
    love = target.Channel(Identifier('#love'))

    assert channel < love < support

    blasphemy = Identifier('#blasphemy')
    with pytest.raises(TypeError):
        blasphemy < channel


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


def test_channel_clear_user():
    channel = target.Channel(Identifier('#chan'))
    brian = target.User(Identifier('Brian'), 'brian', 'example.com')

    channel.add_user(brian, plugin.OP)
    assert brian.nick in channel.users
    assert channel.is_op(brian.nick)
    assert channel.name in brian.channels

    channel.clear_user(brian.nick)
    assert brian.nick not in channel.users
    assert not channel.is_op(brian.nick)
    assert channel.name not in brian.channels


def test_channel_clear_user_unknown():
    channel = target.Channel(Identifier('#chan'))
    brian = target.User(Identifier('Brian'), 'brian', 'example.com')
    mandy = target.User(Identifier('Mandy'), 'brian', 'example.com')

    channel.add_user(brian, plugin.OP)
    channel.clear_user(mandy.nick)

    assert brian.nick in channel.users
    assert mandy.nick not in channel.users


def test_channel_rename_user():
    old_name = Identifier('Brian')
    new_name = Identifier('Messiah')
    channel = target.Channel(Identifier('#chan'))
    brian = target.User(old_name, 'brian', 'example.com')

    channel.add_user(brian, plugin.OP)
    channel.rename_user(old_name, new_name)

    assert brian.nick == new_name
    assert new_name in channel.users
    assert old_name not in channel.users
    assert channel.is_op(new_name)
    assert not channel.is_op(old_name)


def test_channel_rename_unknown_user():
    old_name = Identifier('Brian')
    new_name = Identifier('Messiah')
    channel = target.Channel(Identifier('#chan'))

    channel.rename_user(old_name, new_name)

    assert old_name not in channel.users
    assert new_name not in channel.users
    assert not channel.is_op(old_name)
    assert not channel.is_op(new_name)
