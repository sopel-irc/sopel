# coding=utf-8
"""Tests for message formatting"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.formatting import colors, color, bold, underline


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


def test_underline():
    text = 'Hello World'
    assert underline(text) == '\x1f' + text + '\x1f'
