"""Tests for core ``sopel.irc.utils``"""
from __future__ import generator_stop

import pytest

from sopel.irc import utils


def test_safe():
    text = 'some text'
    assert utils.safe(text + '\r\n') == text
    assert utils.safe(text + '\n') == text
    assert utils.safe(text + '\r') == text
    assert utils.safe('\r\n' + text) == text
    assert utils.safe('\n' + text) == text
    assert utils.safe('\r' + text) == text
    assert utils.safe('some \r\ntext') == text
    assert utils.safe('some \ntext') == text
    assert utils.safe('some \rtext') == text


def test_safe_empty():
    text = ''
    assert utils.safe(text) == text


def test_safe_null():
    with pytest.raises(TypeError):
        utils.safe(None)


def test_safe_bytes():
    text = b'some text'
    assert utils.safe(text) == text.decode('utf-8')
    assert utils.safe(text + b'\r\n') == text.decode('utf-8')
    assert utils.safe(text + b'\n') == text.decode('utf-8')
    assert utils.safe(text + b'\r') == text.decode('utf-8')
    assert utils.safe(b'\r\n' + text) == text.decode('utf-8')
    assert utils.safe(b'\n' + text) == text.decode('utf-8')
    assert utils.safe(b'\r' + text) == text.decode('utf-8')
    assert utils.safe(b'some \r\ntext') == text.decode('utf-8')
    assert utils.safe(b'some \ntext') == text.decode('utf-8')
    assert utils.safe(b'some \rtext') == text.decode('utf-8')
