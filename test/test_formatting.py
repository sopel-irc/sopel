# coding=utf-8
"""Tests for message formatting"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.formatting import colors, color, bold, italic, underline, strikethrough, monospace


def test_color():
    text = 'Hello World'
    assert color(text) == text
    assert color(text, colors.PINK) == '\x0313' + text + '\x03'
    assert color(text, colors.PINK, colors.TEAL) == '\x0313,10' + text + '\x03'
    pytest.raises(ValueError, color, text, 100)
    pytest.raises(ValueError, color, text, 'INVALID')


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
