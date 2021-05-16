# coding=utf-8
"""Tests for ``sopel.tests.mocks`` module"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel.tests.mocks import MockIRCBackend


def test_backend_irc_send():
    backend = MockIRCBackend(bot=None)
    backend.irc_send('a')

    assert len(backend.message_sent) == 1
    assert backend.message_sent == ['a']

    backend.irc_send('b')

    assert len(backend.message_sent) == 2
    assert backend.message_sent == ['a', 'b']

    backend.irc_send(b'c')

    assert len(backend.message_sent) == 3
    assert backend.message_sent == ['a', 'b', b'c']


def test_backend_clear_message_sent():
    items = ['a', 'b', 'c']
    backend = MockIRCBackend(bot=None)
    backend.message_sent = items

    result = backend.clear_message_sent()
    assert result == items
    assert result is not items, 'The result should be a copy.'
    assert not backend.message_sent, '`message_sent` must be empty'
