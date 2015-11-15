# coding=utf-8
"""Tests for message parsing"""
from __future__ import unicode_literals

import pytest

from sopel.trigger import PreTrigger, Trigger
from sopel.tools import Identifier


@pytest.fixture
def nick():
    return Identifier('Sopel')


def test_basic_pretrigger(nick):
    line = ':Foo!foo@example.com PRIVMSG #octothorpe :Hello, world'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['#octothorpe', 'Hello, world']
    assert pretrigger.event == 'PRIVMSG'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == '#octothorpe'

# TODO tags, PRIVMSG to bot, intents
# TODO Trigger tests, for what little actual logic is in there
