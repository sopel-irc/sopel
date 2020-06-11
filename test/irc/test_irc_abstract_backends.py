# coding=utf-8
"""Tests for core ``sopel.irc.backends``"""
from __future__ import absolute_import, division, print_function, unicode_literals


from sopel.irc.abstract_backends import AbstractIRCBackend
from sopel.tests.mocks import MockIRCBackend


class BotCollector:
    def __init__(self):
        self.message_sent = []

    def on_message_sent(self, raw):
        self.message_sent.append(raw)


def test_prepare_command():
    backend = AbstractIRCBackend(BotCollector())

    result = backend.prepare_command('INFO')
    assert result == 'INFO\r\n'

    result = backend.prepare_command('NICK', 'Sopel')
    assert result == 'NICK Sopel\r\n'


def test_prepare_command_text():
    backend = AbstractIRCBackend(BotCollector())

    result = backend.prepare_command('PRIVMSG', '#sopel', text='Hello world!')
    assert result == 'PRIVMSG #sopel :Hello world!\r\n'

    max_length = 510 - len('PRIVMSG #sopel :')
    text = '-' * max_length
    expected = 'PRIVMSG #sopel :%s\r\n' % text
    result = backend.prepare_command('PRIVMSG', '#sopel', text=text)
    assert result == expected


def test_prepare_command_text_too_long():
    backend = AbstractIRCBackend(BotCollector())

    max_length = 510 - len('PRIVMSG #sopel :')
    text = '-' * (max_length + 1)  # going above max length by one
    expected = 'PRIVMSG #sopel :%s\r\n' % text[:max_length]
    result = backend.prepare_command('PRIVMSG', '#sopel', text=text)
    assert result == expected


def test_send_command():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_command('INFO')

    expected = 'INFO\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_command_args():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_command('NICK', 'Sopel')

    expected = 'NICK Sopel\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_command_text():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_command('HELP', text='?')

    expected = 'HELP :?\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_command_args_text():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_command('KICK', 'Exirel', text='Too many PRs!')

    expected = 'KICK Exirel :Too many PRs!\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_command_args_text_safe():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_command('PRIVMSG', '#sopel', text='Unsafe\ntext')

    expected = 'PRIVMSG #sopel :Unsafetext\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_command_args_text_many():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_command('PRIVMSG', '#sopel', text='Hello here!')
    backend.send_command('PRIVMSG', '#sopel', text='I have a question.')

    expected_1 = 'PRIVMSG #sopel :Hello here!\r\n'
    expected_2 = 'PRIVMSG #sopel :I have a question.\r\n'
    assert backend.message_sent == [
        expected_1.encode('utf-8'),
        expected_2.encode('utf-8')
    ]
    assert bot.message_sent == [expected_1, expected_2]


def test_send_ping():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_ping('chat.freenode.net')
    expected = 'PING chat.freenode.net\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_pong():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_pong('chat.freenode.net')
    expected = 'PONG chat.freenode.net\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_nick():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_nick('Sopel')
    expected = 'NICK Sopel\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_user():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_user('sopel', '+iw', 'Sopel', 'Sopel (https://sopel.chat)')
    expected = 'USER sopel +iw Sopel :Sopel (https://sopel.chat)\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_pass():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_pass('secret_p4s5w0rd')
    expected = 'PASS secret_p4s5w0rd\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_join():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_join('#sopel')
    expected = 'JOIN #sopel\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_join_secret():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_join('#sopel', 'secret_p4s5w0rd')
    expected = 'JOIN #sopel secret_p4s5w0rd\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_part():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_part('#sopel')
    expected = 'PART #sopel\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_part_text():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_part('#sopel', 'Bye Sopelunkers!')
    expected = 'PART #sopel :Bye Sopelunkers!\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_quit():
    bot = BotCollector()
    backend = MockIRCBackend(bot)
    backend.connected = True

    backend.send_quit()
    expected = 'QUIT\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_quit_text():
    bot = BotCollector()
    backend = MockIRCBackend(bot)
    backend.connected = True

    backend.send_quit(reason='Bye freenode!')
    expected = 'QUIT :Bye freenode!\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_quit_disconnected():
    bot = BotCollector()
    backend = MockIRCBackend(bot)
    backend.connected = False

    backend.send_quit()
    backend.send_quit(reason='Bye freenode!')
    assert backend.message_sent == []
    assert bot.message_sent == []


def test_send_kick():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_kick('#sopel', 'spambot')
    expected = 'KICK #sopel spambot\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_kick_text():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_kick('#sopel', 'spambot', reason='Flood!')
    expected = 'KICK #sopel spambot :Flood!\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_privmsg():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_privmsg('#sopel', 'Hello world!')
    expected = 'PRIVMSG #sopel :Hello world!\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_privmsg_safe():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_privmsg('#sopel', 'Hello\r\nworld!')
    expected = 'PRIVMSG #sopel :Helloworld!\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_notice():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_notice('#sopel', 'Hello world!')
    expected = 'NOTICE #sopel :Hello world!\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]


def test_send_notice_safe():
    bot = BotCollector()
    backend = MockIRCBackend(bot)

    backend.send_notice('#sopel', 'Hello\r\nworld!')
    expected = 'NOTICE #sopel :Helloworld!\r\n'
    assert backend.message_sent == [expected.encode('utf-8')]
    assert bot.message_sent == [expected]
