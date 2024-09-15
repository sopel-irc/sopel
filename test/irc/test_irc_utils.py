"""Tests for core ``sopel.irc.utils``"""
from __future__ import annotations

from itertools import permutations

import pytest

from sopel.irc import utils


@pytest.mark.parametrize('s1, s2, s3', permutations(('\n', '\r', '\x00')))
def test_safe(s1, s2, s3):
    text = 'some text'
    seq = ''.join((s1, s2, s3))

    assert utils.safe(text + seq) == text
    assert utils.safe(seq + text) == text
    assert utils.safe('some ' + seq + 'text') == text
    assert utils.safe(
        s1
        + 'some '
        + s2
        + 'text'
        + s3
    ) == text


def test_safe_empty():
    text = ''
    assert utils.safe(text) == text


def test_safe_none():
    with pytest.raises(TypeError):
        utils.safe(None)


@pytest.mark.parametrize('b1, b2, b3', permutations((b'\n', b'\r', b'\x00')))
def test_safe_bytes(b1, b2, b3):
    text = b'some text'
    seq = b''.join((b1, b2, b3))

    assert utils.safe(text + seq) == text.decode('utf-8')
    assert utils.safe(seq + text) == text.decode('utf-8')
    assert utils.safe(b'some ' + seq + b'text') == text.decode('utf-8')
    assert utils.safe(
        b1
        + b'some '
        + b2
        + b'text'
        + b3
    ) == text.decode('utf-8')
