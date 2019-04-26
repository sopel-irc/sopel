# coding=utf-8
"""Tests sopel.tools"""
from __future__ import unicode_literals, absolute_import, print_function, division


from datetime import timedelta
from sopel import tools
from sopel.tools.time import seconds_to_human


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


def test_time_timedelta_formatter():
    payload = 10000
    assert seconds_to_human(payload) == '2 hours, 46 minutes ago'

    payload = -2938124
    assert seconds_to_human(payload) == 'in 1 month, 3 days'

    payload = timedelta(hours=4)
    assert seconds_to_human(payload) == '4 hours ago'

    payload = timedelta(hours=-4)
    assert seconds_to_human(payload) == 'in 4 hours'
