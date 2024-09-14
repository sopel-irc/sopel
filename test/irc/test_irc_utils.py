"""Tests for core ``sopel.irc.utils``"""
from __future__ import annotations

from itertools import permutations

import pytest

from sopel.irc import utils


def test_safe():
    text = 'some text'
    variants = permutations(('\n', '\r', '\x00'))
    for variant in variants:
        seq = ''.join(variant)
        assert utils.safe(text + seq) == text
        assert utils.safe(seq + text) == text
        assert utils.safe('some ' + seq + 'text') == text
        assert utils.safe(
            variant[0]
            + 'some '
            + variant[1]
            + 'text'
            + variant[2]
        ) == text


def test_safe_empty():
    text = ''
    assert utils.safe(text) == text


def test_safe_none():
    with pytest.raises(TypeError):
        utils.safe(None)


def test_safe_bytes():
    text = b'some text'
    variants = permutations((b'\n', b'\r', b'\x00'))
    for variant in variants:
        seq = b''.join(variant)
        assert utils.safe(text + seq) == text.decode('utf-8')
        assert utils.safe(seq + text) == text.decode('utf-8')
        assert utils.safe(b'some ' + seq + b'text') == text.decode('utf-8')
        assert utils.safe(
            variant[0]
            + b'some '
            + variant[1]
            + b'text'
            + variant[2]
        ) == text.decode('utf-8')
