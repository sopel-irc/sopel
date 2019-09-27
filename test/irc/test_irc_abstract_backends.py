# coding=utf-8
"""Tests for core ``sopel.irc.backends``"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.irc.abstract_backends import AbstractIRCBackend


def test_prepare_command():
    backend = AbstractIRCBackend(None)

    result = backend.prepare_command('INFO')
    assert result == 'INFO\r\n'

    result = backend.prepare_command('NICK', 'Sopel')
    assert result == 'NICK Sopel\r\n'


def test_prepare_command_text():
    backend = AbstractIRCBackend(None)

    result = backend.prepare_command('PRIVMSG', '#sopel', text='Hello world!')
    assert result == 'PRIVMSG #sopel :Hello world!\r\n'

    max_length = 510 - len('PRIVMSG #sopel :')
    text = '-' * max_length
    expected = 'PRIVMSG #sopel :%s\r\n' % text
    result = backend.prepare_command('PRIVMSG', '#sopel', text=text)
    assert result == expected


def test_prepare_command_text_too_long():
    backend = AbstractIRCBackend(None)

    max_length = 510 - len('PRIVMSG #sopel :')
    text = '-' * (max_length + 1)  # going above max length by one
    expected = 'PRIVMSG #sopel :%s\r\n' % text[:max_length]
    result = backend.prepare_command('PRIVMSG', '#sopel', text=text)
    assert result == expected
