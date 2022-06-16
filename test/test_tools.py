"""Tests sopel.tools"""
from __future__ import annotations

import re

from sopel import tools


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable = coretasks
"""


def test_get_sendable_message_default():
    initial = 'aaaa'
    text, excess = tools.get_sendable_message(initial)

    assert text == initial
    assert excess == ''


def test_get_sendable_message_limit():
    initial = 'a' * 400
    text, excess = tools.get_sendable_message(initial)

    assert text == initial
    assert excess == ''


def test_get_sendable_message_excess():
    initial = 'a' * 401
    text, excess = tools.get_sendable_message(initial)

    assert text == 'a' * 400
    assert excess == 'a'


def test_get_sendable_message_excess_space():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 200, 'b' * 200])
    text, excess = tools.get_sendable_message(initial)

    assert text == 'a' * 200
    assert excess == 'b' * 200


def test_get_sendable_message_excess_space_limit():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 400, 'b' * 200])
    text, excess = tools.get_sendable_message(initial)

    assert text == 'a' * 400
    assert excess == 'b' * 200


def test_get_sendable_message_excess_bigger():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 401, 'b' * 1000])
    text, excess = tools.get_sendable_message(initial)

    assert text == 'a' * 400
    assert excess == 'a ' + 'b' * 1000


def test_get_sendable_message_optional():
    text, excess = tools.get_sendable_message('aaaa', 3)
    assert text == 'aaa'
    assert excess == 'a'

    text, excess = tools.get_sendable_message('aaa bbb', 3)
    assert text == 'aaa'
    assert excess == 'bbb'

    text, excess = tools.get_sendable_message('aa bb cc', 3)
    assert text == 'aa'
    assert excess == 'bb cc'


def test_get_sendable_message_two_bytes():
    text, excess = tools.get_sendable_message('αααα', 4)
    assert text == 'αα'
    assert excess == 'αα'

    text, excess = tools.get_sendable_message('αααα', 5)
    assert text == 'αα'
    assert excess == 'αα'

    text, excess = tools.get_sendable_message('α ααα', 4)
    assert text == 'α'
    assert excess == 'ααα'

    text, excess = tools.get_sendable_message('αα αα', 4)
    assert text == 'αα'
    assert excess == 'αα'

    text, excess = tools.get_sendable_message('ααα α', 4)
    assert text == 'αα'
    assert excess == 'α α'


def test_get_sendable_message_three_bytes():
    text, excess = tools.get_sendable_message('अअअअ', 6)
    assert text == 'अअ'
    assert excess == 'अअ'

    text, excess = tools.get_sendable_message('अअअअ', 7)
    assert text == 'अअ'
    assert excess == 'अअ'

    text, excess = tools.get_sendable_message('अअअअ', 8)
    assert text == 'अअ'
    assert excess == 'अअ'

    text, excess = tools.get_sendable_message('अ अअअ', 6)
    assert text == 'अ'
    assert excess == 'अअअ'

    text, excess = tools.get_sendable_message('अअ अअ', 6)
    assert text == 'अअ'
    assert excess == 'अअ'

    text, excess = tools.get_sendable_message('अअअ अ', 6)
    assert text == 'अअ'
    assert excess == 'अ अ'


def test_get_sendable_message_four_bytes():
    text, excess = tools.get_sendable_message('𡃤𡃤𡃤𡃤', 8)
    assert text == '𡃤𡃤'
    assert excess == '𡃤𡃤'

    text, excess = tools.get_sendable_message('𡃤𡃤𡃤𡃤', 9)
    assert text == '𡃤𡃤'
    assert excess == '𡃤𡃤'

    text, excess = tools.get_sendable_message('𡃤𡃤𡃤𡃤', 10)
    assert text == '𡃤𡃤'
    assert excess == '𡃤𡃤'

    text, excess = tools.get_sendable_message('𡃤𡃤𡃤𡃤', 11)
    assert text == '𡃤𡃤'
    assert excess == '𡃤𡃤'

    text, excess = tools.get_sendable_message('𡃤 𡃤𡃤𡃤', 8)
    assert text == '𡃤'
    assert excess == '𡃤𡃤𡃤'

    text, excess = tools.get_sendable_message('𡃤𡃤 𡃤𡃤', 8)
    assert text == '𡃤𡃤'
    assert excess == '𡃤𡃤'

    text, excess = tools.get_sendable_message('𡃤𡃤𡃤 𡃤', 8)
    assert text == '𡃤𡃤'
    assert excess == '𡃤 𡃤'


def test_chain_loaders(configfactory):
    re_numeric = re.compile(r'\d+')
    re_text = re.compile(r'\w+')
    settings = configfactory('test.cfg', TMP_CONFIG)

    def loader_numeric(settings):
        return [re_numeric]

    def loader_text(settings):
        return [re_text]

    loader = tools.chain_loaders(loader_numeric, loader_text)

    assert callable(loader)
    results = loader(settings)

    assert results == [re_numeric, re_text]
