# coding=utf8
"""Tests for the new database functionality.

TODO: Most of these tests assume functionality tested in other tests. This is
enough to get everything working (and is better than nothing), but best
practice would probably be not to do that."""
from __future__ import unicode_literals

import os
import sqlite3

import pytest

from willie.new_db import WillieDB
from willie.tools import Nick

db_filename = 'asdf'


@pytest.fixture
def db(monkeypatch):
    db = WillieDB(db_filename)
    # TODO add tests to ensure this is working properly, too.
    db.create()
    return db


def teardown_function(function):
    os.remove(db_filename)


def test_get_nick_id(db):
    conn = sqlite3.connect(db_filename)
    tests = [
        [None, 'embolalia', Nick('Embolalia')],
        # Ensures case conversion is handled properly
        [None, '[][]', Nick('[]{}')],
        # Unicode, just in case
        [None, 'embölaliå', Nick('EmbölaliÅ')],
    ]

    for test in tests:
        test[0] = db._get_nick_id(test[2])
        nick_id, slug, nick = test
        with conn:
            cursor = conn.cursor()
            registered = cursor.execute(
                'SELECT nick_id, slug, canonical FROM nicknames WHERE canonical IS ?', [nick]
            ).fetchall()
            assert len(registered) == 1
            assert registered[0][1] == slug and registered[0][2] == nick

    # Check that each nick ended up with a different id
    assert len(set(test[0] for test in tests)) == len(tests)

    # Check that the retrieval actually is idempotent
    for test in tests:
        nick_id = test[0]
        new_id = db._get_nick_id(test[2])
        assert nick_id == new_id

    # Even if the case is different
    for test in tests:
        nick_id = test[0]
        new_id = db._get_nick_id(Nick(test[2].upper()))
        assert nick_id == new_id


def test_alias_nick(db):
    conn = sqlite3.connect(db_filename)
    nick = 'Embolalia'
    aliases = ['EmbölaliÅ', 'Embo`work', 'Embo']

    nick_id = db._get_nick_id(nick)
    for alias in aliases:
        db.alias_nick(nick, alias)

    for alias in aliases:
        assert db._get_nick_id(alias) == nick_id

    with pytest.raises(ValueError):
        db.alias_nick('Eve', nick)
    # TODO what should happen with alias_nick(nick, nick), or other already-
    # existing aliases


def test_set_nick_value(db):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    nick = 'Embolalia'
    nick_id = db._get_nick_id(nick)
    data = {
        'key': 'value',
        'number_key': 1234,
        'bytes': b'value',
        'unicode': 'EmbölaliÅ',
    }

    def check():
        for key, value in data.iteritems():
            db.set_nick_value(nick, key, value)

        for key, value in data.iteritems():
            found_value = cursor.execute(
                'SELECT value FROM nick_values WHERE nick_id = ? AND key = ?',
                [nick_id, key]
            ).fetchone()[0]
            assert found_value == value
    check()

    # Test updates
    data['number_key'] = 'not a number anymore!'
    data['unicode'] = 'This is different toö!'
    check()


def test_get_nick_value(db):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    nick = 'Embolalia'
    nick_id = db._get_nick_id(nick)
    data = {
        'key': 'value',
        'number_key': 1234,
        'bytes': b'value',
        'unicode': 'EmbölaliÅ',
    }

    for key, value in data.iteritems():
        cursor.execute('INSERT INTO nick_values VALUES (?, ?, ?)',
                     [nick_id, key, value])
        conn.commit()

    for key, value in data.iteritems():
        print key, value
        found_value = db.get_nick_value(nick, key)
        assert found_value == value
