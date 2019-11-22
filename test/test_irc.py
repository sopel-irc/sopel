# coding=utf-8
"""Tests for core ``sopel.irc``"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Exirel
nick = Sopel
user = sopel
name = Sopel (https://sopel.chat)
# we don't want flood protection here
flood_burst_lines = 1000
"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('conf.ini', TMP_CONFIG)


@pytest.fixture
def bot(tmpconfig, botfactory):
    return botfactory(tmpconfig)


def test_on_connect(bot):
    bot.on_connect()

    assert bot.backend.message_sent == rawlist(
        'CAP LS 302',
        'NICK Sopel',
        'USER sopel +iw Sopel :Sopel (https://sopel.chat)'
    )


def test_on_connect_auth_password(bot):
    bot.settings.core.auth_method = 'server'
    bot.settings.core.auth_password = 'auth_secret'
    bot.on_connect()

    assert bot.backend.message_sent == rawlist(
        'CAP LS 302',
        'PASS auth_secret',
        'NICK Sopel',
        'USER sopel +iw Sopel :Sopel (https://sopel.chat)'
    )


def test_on_connect_server_auth_password(bot):
    bot.settings.core.server_auth_method = 'server'
    bot.settings.core.server_auth_password = 'server_secret'
    bot.on_connect()

    assert bot.backend.message_sent == rawlist(
        'CAP LS 302',
        'PASS server_secret',
        'NICK Sopel',
        'USER sopel +iw Sopel :Sopel (https://sopel.chat)'
    )


def test_on_connect_auth_password_override_server_auth(bot):
    bot.settings.core.auth_method = 'server'
    bot.settings.core.auth_password = 'auth_secret'
    bot.settings.core.server_auth_method = 'server'
    bot.settings.core.server_auth_password = 'server_secret'
    bot.on_connect()

    assert bot.backend.message_sent == rawlist(
        'CAP LS 302',
        'PASS auth_secret',
        'NICK Sopel',
        'USER sopel +iw Sopel :Sopel (https://sopel.chat)'
    )


def test_write(bot):
    bot.write(['INFO'])

    assert bot.backend.message_sent == rawlist('INFO')


def test_write_args(bot):
    bot.write(['NICK', 'Sopel'])

    assert bot.backend.message_sent == rawlist('NICK Sopel')


def test_write_text(bot):
    bot.write(['HELP'], '?')

    assert bot.backend.message_sent == rawlist('HELP :?')


def test_write_args_text_safe(bot):
    bot.write(['CMD\nUNSAFE'], 'Unsafe\rtext')

    assert bot.backend.message_sent == rawlist('CMDUNSAFE :Unsafetext')


def test_write_args_many(bot):
    bot.write(['NICK', 'Sopel'])
    bot.write(['JOIN', '#sopel'])

    assert bot.backend.message_sent == rawlist(
        'NICK Sopel',
        'JOIN #sopel',
    )


def test_write_text_many(bot):
    bot.write(['NICK', 'Sopel'])
    bot.write(['HELP'], '?')

    assert bot.backend.message_sent == rawlist(
        'NICK Sopel',
        'HELP :?',
    )


def test_action(bot):
    bot.action('is doing some tests', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :\001ACTION is doing some tests\001',
    )


def test_join(bot):
    bot.join('#sopel')

    assert bot.backend.message_sent == rawlist(
        'JOIN #sopel',
    )


def test_join_password(bot):
    bot.join('#sopel', 'secret_password')

    assert bot.backend.message_sent == rawlist(
        'JOIN #sopel secret_password',
    )


def test_kick(bot):
    bot.kick('spambot', '#channel')

    assert bot.backend.message_sent == rawlist(
        'KICK #channel spambot',
    )


def test_kick_reason(bot):
    bot.kick('spambot', '#channel', 'Flood!')

    assert bot.backend.message_sent == rawlist(
        'KICK #channel spambot :Flood!',
    )


def test_notice(bot):
    bot.notice('Hello world!', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'NOTICE #sopel :Hello world!',
    )


def test_part(bot):
    bot.part('#channel')

    assert bot.backend.message_sent == rawlist(
        'PART #channel',
    )


def test_part_reason(bot):
    bot.part('#channel', 'Bye!')

    assert bot.backend.message_sent == rawlist(
        'PART #channel :Bye!',
    )


def test_reply(bot):
    bot.reply('Thank you!', '#sopel', 'dgw')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :dgw: Thank you!',
    )


def test_reply_notice(bot):
    bot.reply('Thank you!', '#sopel', 'dgw', notice=True)

    assert bot.backend.message_sent == rawlist(
        'NOTICE #sopel :dgw: Thank you!',
    )


def test_say(bot):
    bot.say('Hello world!', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :Hello world!',
    )


def test_say_safe(bot):
    bot.say('Hello\r\nworld!\r\n', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :Helloworld!',
    )


def test_say_long_fit(bot):
    """Test a long message that fits into the 512 bytes limit."""
    text = 'a' * (512 - len('PRIVMSG #sopel :\r\n'))
    bot.say(text, '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :%s' % text,
    )


def test_say_long_extra(bot):
    """Test a long message that doesn't fit into the 512 bytes limit."""
    text = 'a' * (512 - len('PRIVMSG #sopel :\r\n'))
    bot.say(text + 'b', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :%s' % text,  # the 'b' is truncated out
    )


def test_say_long_extra_multi_message(bot):
    """Test a long message that doesn't fit, with split allowed."""
    text = 'a' * 400
    bot.say(text + 'b', '#sopel', max_messages=2)

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :%s' % text,  # the 'b' is split from message
        'PRIVMSG #sopel :b',
    )


def test_say_no_repeat_protection(bot):
    # five is fine
    bot.say('hello', '#sopel')
    bot.say('hello', '#sopel')
    bot.say('hello', '#sopel')
    bot.say('hello', '#sopel')
    bot.say('hello', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
    )

    # six: replaced by '...'
    bot.say('hello', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        # the extra hello is replaced by '...'
        'PRIVMSG #sopel :...',
    )

    # these one will add more '...'
    bot.say('hello', '#sopel')
    bot.say('hello', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :...',
        # the new ones are also replaced by '...'
        'PRIVMSG #sopel :...',
        'PRIVMSG #sopel :...',
    )

    # but at some point it just stops talking
    bot.say('hello', '#sopel')

    assert bot.backend.message_sent == rawlist(
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        'PRIVMSG #sopel :hello',
        #  three time, then stop
        'PRIVMSG #sopel :...',
        'PRIVMSG #sopel :...',
        'PRIVMSG #sopel :...',
    )
