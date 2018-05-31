# coding=utf-8
"""Tests for the new database functionality.

TODO: Most of these tests assume functionality tested in other tests. This is
enough to get everything working (and is better than nothing), but best
practice would probably be not to do that."""
from __future__ import unicode_literals, absolute_import, print_function, division

import json
import os
import sqlite3
import sys
import tempfile

import pytest

from sopel.db import SopelDB
from sopel.test_tools import MockConfig
from sopel.tools import Identifier

db_filename = tempfile.mkstemp()[1]
if sys.version_info.major >= 3:
    unicode = str
    basestring = str
    iteritems = dict.items
    itervalues = dict.values
    iterkeys = dict.keys
else:
    iteritems = dict.iteritems
    itervalues = dict.itervalues
    iterkeys = dict.iterkeys


@pytest.fixture
def db():
    config = MockConfig()
    config.core.db_filename = db_filename
    db = SopelDB(config)
    # TODO add tests to ensure db creation works properly, too.
    return db


def teardown_function(function):
    os.remove(db_filename)


def test_get_nick_id(db):
    conn = sqlite3.connect(db_filename)
    tests = [
        [None, 'embolalia', Identifier('Embolalia')],
        # Ensures case conversion is handled properly
        [None, '[][]', Identifier('[]{}')],
        # Unicode, just in case
        [None, 'embölaliå', Identifier('EmbölaliÅ')],
    ]

    for test in tests:
        test[0] = db.get_nick_id(test[2])
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
        new_id = db.get_nick_id(test[2])
        assert nick_id == new_id

    # Even if the case is different
    for test in tests:
        nick_id = test[0]
        new_id = db.get_nick_id(Identifier(test[2].upper()))
        assert nick_id == new_id


def test_alias_nick(db):
    nick = 'Embolalia'
    aliases = ['EmbölaliÅ', 'Embo`work', 'Embo']

    nick_id = db.get_nick_id(nick)
    for alias in aliases:
        db.alias_nick(nick, alias)

    for alias in aliases:
        assert db.get_nick_id(alias) == nick_id

    db.alias_nick('both', 'arenew')  # Shouldn't fail.

    with pytest.raises(ValueError):
        db.alias_nick('Eve', nick)

    with pytest.raises(ValueError):
        db.alias_nick(nick, nick)


def test_set_nick_value(db):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    nick = 'Embolalia'
    nick_id = db.get_nick_id(nick)
    data = {
        'key': 'value',
        'number_key': 1234,
        'unicode': 'EmbölaliÅ',
    }

    def check():
        for key, value in iteritems(data):
            db.set_nick_value(nick, key, value)

        for key, value in iteritems(data):
            found_value = cursor.execute(
                'SELECT value FROM nick_values WHERE nick_id = ? AND key = ?',
                [nick_id, key]
            ).fetchone()[0]
            assert json.loads(unicode(found_value)) == value
    check()

    # Test updates
    data['number_key'] = 'not a number anymore!'
    data['unicode'] = 'This is different toö!'
    check()


def test_get_nick_value(db):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    nick = 'Embolalia'
    nick_id = db.get_nick_id(nick)
    data = {
        'key': 'value',
        'number_key': 1234,
        'unicode': 'EmbölaliÅ',
    }

    for key, value in iteritems(data):
        cursor.execute('INSERT INTO nick_values VALUES (?, ?, ?)',
                       [nick_id, key, json.dumps(value, ensure_ascii=False)])
    conn.commit()

    for key, value in iteritems(data):
        found_value = db.get_nick_value(nick, key)
        assert found_value == value


def test_unalias_nick(db):
    conn = sqlite3.connect(db_filename)
    nick = 'Embolalia'
    nick_id = 42
    conn.execute('INSERT INTO nicknames VALUES (?, ?, ?)',
                 [nick_id, Identifier(nick).lower(), nick])
    aliases = ['EmbölaliÅ', 'Embo`work', 'Embo']
    for alias in aliases:
        conn.execute('INSERT INTO nicknames VALUES (?, ?, ?)',
                     [nick_id, Identifier(alias).lower(), alias])
    conn.commit()

    for alias in aliases:
        db.unalias_nick(alias)

    for alias in aliases:
        found = conn.execute(
            'SELECT * FROM nicknames WHERE nick_id = ?',
            [nick_id]).fetchall()
        assert len(found) == 1


def test_delete_nick_group(db):
    conn = sqlite3.connect(db_filename)
    aliases = ['Embolalia', 'Embo']
    nick_id = 42
    for alias in aliases:
        conn.execute('INSERT INTO nicknames VALUES (?, ?, ?)',
                     [nick_id, Identifier(alias).lower(), alias])
    conn.commit()

    db.set_nick_value(aliases[0], 'foo', 'bar')
    db.set_nick_value(aliases[1], 'spam', 'eggs')

    db.delete_nick_group(aliases[0])

    # Nothing else has created values, so we know the tables are empty
    nicks = conn.execute('SELECT * FROM nicknames').fetchall()
    assert len(nicks) == 0
    data = conn.execute('SELECT * FROM nick_values').fetchone()
    assert data is None


def test_merge_nick_groups(db):
    conn = sqlite3.connect(db_filename)
    aliases = ['Embolalia', 'Embo']
    for nick_id, alias in enumerate(aliases):
        conn.execute('INSERT INTO nicknames VALUES (?, ?, ?)',
                     [nick_id, Identifier(alias).lower(), alias])
    conn.commit()

    finals = (('foo', 'bar'), ('bar', 'blue'), ('spam', 'eggs'))

    db.set_nick_value(aliases[0], finals[0][0], finals[0][1])
    db.set_nick_value(aliases[0], finals[1][0], finals[1][1])
    db.set_nick_value(aliases[1], 'foo', 'baz')
    db.set_nick_value(aliases[1], finals[2][0], finals[2][1])

    db.merge_nick_groups(aliases[0], aliases[1])

    nick_ids = conn.execute('SELECT nick_id FROM nicknames')
    nick_id = nick_ids.fetchone()[0]
    alias_id = nick_ids.fetchone()[0]
    assert nick_id == alias_id

    for key, value in finals:
        found = conn.execute(
            'SELECT value FROM nick_values WHERE nick_id = ? AND key = ?',
            [nick_id, key]).fetchone()[0]
        assert json.loads(unicode(found)) == value


def test_set_channel_value(db):
    conn = sqlite3.connect(db_filename)
    db.set_channel_value('#asdf', 'qwer', 'zxcv')
    result = conn.execute(
        'SELECT value FROM channel_values WHERE channel = ? and key = ?',
        ['#asdf', 'qwer']).fetchone()[0]
    assert result == '"zxcv"'


def test_get_channel_value(db):
    conn = sqlite3.connect(db_filename)
    conn.execute("INSERT INTO channel_values VALUES ('#asdf', 'qwer', '\"zxcv\"')")
    conn.commit()
    result = db.get_channel_value('#asdf', 'qwer')
    assert result == 'zxcv'


def test_get_nick_or_channel_value(db):
    db.set_nick_value('asdf', 'qwer', 'poiu')
    db.set_channel_value('#asdf', 'qwer', '/.,m')
    assert db.get_nick_or_channel_value('asdf', 'qwer') == 'poiu'
    assert db.get_nick_or_channel_value('#asdf', 'qwer') == '/.,m'


def test_get_preferred_value(db):
    db.set_nick_value('asdf', 'qwer', 'poiu')
    db.set_channel_value('#asdf', 'qwer', '/.,m')
    db.set_channel_value('#asdf', 'lkjh', '1234')
    names = ['asdf', '#asdf']
    assert db.get_preferred_value(names, 'qwer') == 'poiu'
    assert db.get_preferred_value(names, 'lkjh') == '1234'
