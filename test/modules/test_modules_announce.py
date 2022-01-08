"""Tests for Sopel's ``announce`` plugin"""
from __future__ import annotations

from sopel.modules import announce


def test_chunks():
    """Test the `_chunks` helper for functionality and compatibility."""
    # list input
    items = ['list', 'of', 'items', 'to', 'chunk']
    r = list(announce._chunks(items, 2))

    assert len(r) == 3
    assert r[0] == tuple(items[:2])
    assert r[1] == tuple(items[2:4])
    assert r[2] == tuple(items[4:])

    # tuple input
    items = ('tuple', 'of', 'items')
    r = list(announce._chunks(items, 3))

    assert len(r) == 1
    assert r[0] == items

    # dict keys input
    keys = {'one': True, 'two': True, 'three': True}.keys()
    items = list(keys)
    r = list(announce._chunks(keys, 1))

    assert len(r) == 3
    for idx in range(len(items)):
        assert r[idx] == (items[idx],)
