# coding=utf-8
"""Tests for the new database functionality.

TODO: Most of these tests assume functionality tested in other tests. This is
enough to get everything working (and is better than nothing), but best
practice would probably be not to do that."""
from __future__ import unicode_literals, absolute_import, print_function, division

import json
import os
import sys
import tempfile

import pytest

from sopel.db import ChannelValues, PluginValues, Nicknames, NickValues, SopelDB
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


TMP_CONFIG = """
[core]
owner = Embolalia
db_filename = {db_filename}
"""


@pytest.fixture
def db(configfactory):
    content = TMP_CONFIG.format(db_filename=db_filename)
    settings = configfactory('default.cfg', content)
    db = SopelDB(settings)
    # TODO add tests to ensure db creation works properly, too.
    return db


def teardown_function(function):
    os.remove(db_filename)


def test_get_nick_id(db):
    session = db.ssession()
    tests = [
        [None, 'embolalia', Identifier('Embolalia')],
        # Ensures case conversion is handled properly
        [None, '{}{}', Identifier('[]{}')],
        # Unicode, just in case
        [None, 'embölaliå', Identifier('EmbölaliÅ')],
    ]

    for test in tests:
        test[0] = db.get_nick_id(test[2])
        nick_id, slug, nick = test
        registered = session.query(Nicknames) \
                            .filter(Nicknames.canonical == nick) \
                            .all()
        assert len(registered) == 1
        assert registered[0].slug == slug and registered[0].canonical == nick

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
    session.close()


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
    session = db.ssession()
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
            found_value = session.query(NickValues.value) \
                                 .filter(NickValues.nick_id == nick_id) \
                                 .filter(NickValues.key == key) \
                                 .scalar()
            assert json.loads(unicode(found_value)) == value
    check()

    # Test updates
    data['number_key'] = 'not a number anymore!'
    data['unicode'] = 'This is different toö!'
    check()
    session.close()


def test_get_nick_value(db):
    session = db.ssession()
    nick = 'Embolalia'
    nick_id = db.get_nick_id(nick)
    data = {
        'key': 'value',
        'number_key': 1234,
        'unicode': 'EmbölaliÅ',
    }

    for key, value in iteritems(data):
        nv = NickValues(nick_id=nick_id, key=key, value=json.dumps(value, ensure_ascii=False))
        session.add(nv)
        session.commit()

    for key, value in iteritems(data):
        found_value = db.get_nick_value(nick, key)
        assert found_value == value
    session.close()


def test_get_nick_value_default(db):
    assert db.get_nick_value("TestUser", "DoesntExist") is None
    assert db.get_nick_value("TestUser", "DoesntExist", "MyDefault") == "MyDefault"


def test_delete_nick_value(db):
    nick = 'Embolalia'
    db.set_nick_value(nick, 'wasd', 'uldr')
    assert db.get_nick_value(nick, 'wasd') == 'uldr'
    db.delete_nick_value(nick, 'wasd')
    assert db.get_nick_value(nick, 'wasd') is None


def test_unalias_nick(db):
    session = db.ssession()
    nick = 'Embolalia'
    nick_id = 42

    nn = Nicknames(nick_id=nick_id, slug=Identifier(nick).lower(), canonical=nick)
    session.add(nn)
    session.commit()

    aliases = ['EmbölaliÅ', 'Embo`work', 'Embo']
    for alias in aliases:
        nn = Nicknames(nick_id=nick_id, slug=Identifier(alias).lower(), canonical=alias)
        session.add(nn)
        session.commit()

    for alias in aliases:
        db.unalias_nick(alias)

    for alias in aliases:
        found = session.query(Nicknames) \
                       .filter(Nicknames.nick_id == nick_id) \
                       .all()
        assert len(found) == 1
    session.close()


def test_delete_nick_group(db):
    session = db.ssession()
    aliases = ['Embolalia', 'Embo']
    nick_id = 42
    for alias in aliases:
        nn = Nicknames(nick_id=nick_id, slug=Identifier(alias).lower(), canonical=alias)
        session.add(nn)
        session.commit()

    db.set_nick_value(aliases[0], 'foo', 'bar')
    db.set_nick_value(aliases[1], 'spam', 'eggs')

    db.delete_nick_group(aliases[0])

    # Nothing else has created values, so we know the tables are empty
    nicks = session.query(Nicknames).all()
    assert len(nicks) == 0
    data = session.query(NickValues).first()
    assert data is None
    session.close()


def test_merge_nick_groups(db):
    session = db.ssession()
    aliases = ['Embolalia', 'Embo']
    for nick_id, alias in enumerate(aliases):
        nn = Nicknames(nick_id=nick_id, slug=Identifier(alias).lower(), canonical=alias)
        session.add(nn)
        session.commit()

    finals = (('foo', 'bar'), ('bar', 'blue'), ('spam', 'eggs'))

    db.set_nick_value(aliases[0], finals[0][0], finals[0][1])
    db.set_nick_value(aliases[0], finals[1][0], finals[1][1])
    db.set_nick_value(aliases[1], 'foo', 'baz')
    db.set_nick_value(aliases[1], finals[2][0], finals[2][1])

    db.merge_nick_groups(aliases[0], aliases[1])

    nick_ids = session.query(Nicknames.nick_id).all()
    nick_id = nick_ids[0][0]
    alias_id = nick_ids[1][0]
    assert nick_id == alias_id

    for key, value in finals:
        found = session.query(NickValues.value) \
                       .filter(NickValues.nick_id == nick_id) \
                       .filter(NickValues.key == key) \
                       .scalar()
        assert json.loads(unicode(found)) == value
    session.close()


def test_set_channel_value(db):
    session = db.ssession()
    db.set_channel_value('#asdf', 'qwer', 'zxcv')
    result = session.query(ChannelValues.value) \
                    .filter(ChannelValues.channel == '#asdf') \
                    .filter(ChannelValues.key == 'qwer') \
                    .scalar()
    assert result == '"zxcv"'
    session.close()


def test_delete_channel_value(db):
    db.set_channel_value('#asdf', 'wasd', 'uldr')
    assert db.get_channel_value('#asdf', 'wasd') == 'uldr'
    db.delete_channel_value('#asdf', 'wasd')
    assert db.get_channel_value('#asdf', 'wasd') is None


def test_get_channel_value(db):
    session = db.ssession()

    cv = ChannelValues(channel='#asdf', key='qwer', value='\"zxcv\"')
    session.add(cv)
    session.commit()

    result = db.get_channel_value('#asdf', 'qwer')
    assert result == 'zxcv'
    session.close()


def test_get_channel_value_default(db):
    assert db.get_channel_value("TestChan", "DoesntExist") is None
    assert db.get_channel_value("TestChan", "DoesntExist", "MyDefault") == "MyDefault"


def test_get_nick_or_channel_value(db):
    db.set_nick_value('asdf', 'qwer', 'poiu')
    db.set_channel_value('#asdf', 'qwer', '/.,m')
    assert db.get_nick_or_channel_value('asdf', 'qwer') == 'poiu'
    assert db.get_nick_or_channel_value('#asdf', 'qwer') == '/.,m'


def test_get_nick_or_channel_value_default(db):
    assert db.get_nick_or_channel_value("Test", "DoesntExist") is None
    assert db.get_nick_or_channel_value("Test", "DoesntExist", "MyDefault") == "MyDefault"


def test_get_preferred_value(db):
    db.set_nick_value('asdf', 'qwer', 'poiu')
    db.set_channel_value('#asdf', 'qwer', '/.,m')
    db.set_channel_value('#asdf', 'lkjh', '1234')
    names = ['asdf', '#asdf']
    assert db.get_preferred_value(names, 'qwer') == 'poiu'
    assert db.get_preferred_value(names, 'lkjh') == '1234'


def test_set_plugin_value(db):
    session = db.ssession()
    db.set_plugin_value('plugname', 'qwer', 'zxcv')
    result = session.query(PluginValues.value) \
                    .filter(PluginValues.plugin == 'plugname') \
                    .filter(PluginValues.key == 'qwer') \
                    .scalar()
    assert result == '"zxcv"'
    session.close()


def test_get_plugin_value(db):
    session = db.ssession()

    pv = PluginValues(plugin='plugname', key='qwer', value='\"zxcv\"')
    session.add(pv)
    session.commit()

    result = db.get_plugin_value('plugname', 'qwer')
    assert result == 'zxcv'
    session.close()


def test_get_plugin_value_default(db):
    assert db.get_plugin_value("TestPlugin", "DoesntExist") is None
    assert db.get_plugin_value("TestPlugin", "DoesntExist", "MyDefault") == "MyDefault"


def test_delete_plugin_value(db):
    db.set_plugin_value('plugin', 'wasd', 'uldr')
    assert db.get_plugin_value('plugin', 'wasd') == 'uldr'
    db.delete_plugin_value('plugin', 'wasd')
    assert db.get_plugin_value('plugin', 'wasd') is None
