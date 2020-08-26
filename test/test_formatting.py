# coding=utf-8
"""Tests for message formatting"""
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from sopel.formatting import (
    bold,
    color,
    colors,
    CONTROL_NON_PRINTING,
    CONTROL_NORMAL,
    hex_color,
    italic,
    monospace,
    plain,
    reverse,
    strikethrough,
    underline,
)


def test_color():
    text = 'Hello World'
    assert color(text) == text
    assert color(text, colors.PINK) == '\x0313' + text + '\x03'
    assert color(text, colors.PINK, colors.TEAL) == '\x0313,10' + text + '\x03'
    pytest.raises(ValueError, color, text, 100)
    pytest.raises(ValueError, color, text, 'INVALID')


def test_hex_color():
    text = 'Hello World'
    assert hex_color(text) == text
    assert hex_color(text, '369') == '\x04336699' + text + '\x04'
    assert hex_color(text, '246', '987654') == '\x04224466,987654' + text + '\x04'
    pytest.raises(ValueError, hex_color, text, 0x224466)
    pytest.raises(ValueError, hex_color, text, '1234')
    pytest.raises(ValueError, hex_color, text, 'sixchr')


def test_bold():
    text = 'Hello World'
    assert bold(text) == '\x02' + text + '\x02'


def test_italic():
    text = 'Hello World'
    assert italic(text) == '\x1d' + text + '\x1d'


def test_underline():
    text = 'Hello World'
    assert underline(text) == '\x1f' + text + '\x1f'


def test_strikethrough():
    text = 'Hello World'
    assert strikethrough(text) == '\x1e' + text + '\x1e'


def test_monospace():
    text = 'Hello World'
    assert monospace(text) == '\x11' + text + '\x11'


def test_reverse():
    text = 'Hello World'
    assert reverse(text) == '\x16' + text + '\x16'


def test_plain_color():
    text = 'some text'
    assert plain(color(text, colors.PINK)) == text
    assert plain(color(text, colors.PINK, colors.TEAL)) == text

    tpl = 'b %s a'
    expected = tpl % text
    assert plain(tpl % color(text, colors.PINK)) == expected
    assert plain(tpl % color(text, colors.PINK, colors.TEAL)) == expected


def test_plain_hex_color():
    text = 'some text'
    assert plain(hex_color(text, 'ff0098')) == text
    assert plain(hex_color(text, 'ff0098', '00b571')) == text

    tpl = 'b %s a'
    expected = tpl % text
    assert plain(tpl % hex_color(text, 'ff0098')) == expected
    assert plain(tpl % hex_color(text, 'ff0098', '00b571')) == expected


def test_plain_bold():
    text = 'some text'
    assert plain(bold(text)) == text


def test_plain_italic():
    text = 'some text'
    assert plain(italic(text)) == text


def test_plain_underline():
    text = 'some text'
    assert plain(underline(text)) == text


def test_plain_strikethrough():
    text = 'some text'
    assert plain(strikethrough(text)) == text


def test_plain_monospace():
    text = 'some text'
    assert plain(monospace(text)) == text


def test_plain_reverse():
    text = 'some text'
    assert plain(reverse(text)) == text


def test_plain_reset():
    text = 'some%s text' % CONTROL_NORMAL
    assert plain(text) == 'some text'


@pytest.mark.parametrize('code', CONTROL_NON_PRINTING)
def test_plain_non_printing(code):
    text = 'some%s text' % code
    assert plain(text) == 'some text'


def test_plain_unknown():
    text = 'some \x99text'
    assert plain(text) == text, 'An unknown control code must not be stripped'


def test_plain_emoji():
    text = 'some emoji 💪 in here'
    assert plain(text) == text
