# coding=utf-8
"""Tests sopel.tools"""
from __future__ import unicode_literals, absolute_import, print_function, division


from sopel import tools


def test_get_sendable_message_default():
    initial = 'aaaa'
    text_list = tools.get_sendable_message(initial)

    assert text_list == [initial]


def test_get_sendable_message_limit():
    initial = 'a' * 400
    text_list = tools.get_sendable_message(initial)

    assert text_list == [initial]


def test_get_sendable_message_excess():
    initial = 'a' * 401
    text_list = tools.get_sendable_message(initial)

    assert text_list == ['a' * 400, 'a']


def test_get_sendable_message_excess_space():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 200, 'b' * 200])
    text_list = tools.get_sendable_message(initial)

    assert text_list == ['a' * 200, ' b' + 'b' * 199]


def test_get_sendable_message_excess_space_limit():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 400, 'b' * 200])
    text_list = tools.get_sendable_message(initial)

    assert text_list == ['a' * 400, ' b' + 'b' * 199]


def test_get_sendable_message_excess_bigger():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 401, 'b' * 1000])
    text_list = tools.get_sendable_message(initial)

    assert text_list == ['a' * 400, 'a b' + 'b' * 197, 'b' * 400, 'b' * 202]


def test_get_sendable_message_optional():
    text_list = tools.get_sendable_message('aaaa', 3)
    assert text_list == ['aaa', 'a']

    text_list = tools.get_sendable_message('aaa bbb', 3)
    assert text_list == ['aaa', 'bbb']

    text_list = tools.get_sendable_message('aa bb cc', 3)
    assert text_list == ['aa', 'bb cc']


def test_get_sendable_message_two_bytes():
    text_list = tools.get_sendable_message('αααα', 4)
    assert text_list == ['αα', 'αα']

    text_list = tools.get_sendable_message('αααα', 5)
    assert text_list == ['αα', 'αα']

    text_list = tools.get_sendable_message('α ααα', 4)
    assert text_list == ['α', 'ααα']

    text_list = tools.get_sendable_message('αα αα', 4)
    assert text_list == ['αα', 'αα']

    text_list = tools.get_sendable_message('ααα α', 4)
    assert text_list == ['αα', 'α α']
