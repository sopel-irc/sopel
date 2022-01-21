"""Tests for the new database functionality.

TODO: Most of these tests assume functionality tested in other tests. This is
enough to get everything working (and is better than nothing), but best
practice would probably be not to do that."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from sopel.db import (
    ChannelValues,
    NickIDs,
    Nicknames,
    NickValues,
    PluginValues,
    SopelDB,
)
from sopel.tools import Identifier


db_filename = tempfile.mkstemp()[1]


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
    """Test get_nick_id does not create NickID by default."""
    nick = Identifier('Exirel')
    session = db.session()

    # Attempt to get nick ID: it is not created by default
    with pytest.raises(ValueError):
        db.get_nick_id(nick)

    # Create the nick ID
    nick_id = db.get_nick_id(nick, create=True)

    # Check that one and only one nickname exists with that ID
    nickname = session.query(Nicknames).filter(
        Nicknames.nick_id == nick_id,
    ).one()  # will raise if not one and exactly one
    assert nickname.canonical == 'Exirel'
    assert nickname.slug == nick.lower()

    session.close()


@pytest.mark.parametrize('name, slug, variant', (
    # Check case insensitive with ASCII only
    ('Embolalia', 'embolalia', 'eMBOLALIA'),
    # Ensures case conversion is handled properly
    ('[][]', '{}{}', '[}{]'),
    # Unicode, just in case
    ('EmbölaliÅ', 'embölaliÅ', 'EMBöLALIÅ'),
))
def test_get_nick_id_casemapping(db, name, slug, variant):
    """Test get_nick_id is case-insensitive through an Identifier."""
    session = db.session()
    nick = Identifier(name)

    # Create the nick ID
    nick_id = db.get_nick_id(nick, create=True)

    registered = session.query(Nicknames) \
                        .filter(Nicknames.canonical == name) \
                        .all()
    assert len(registered) == 1
    assert registered[0].slug == slug
    assert registered[0].canonical == name

    # Check that the retrieval actually is idempotent
    assert nick_id == db.get_nick_id(name)

    # Even if the case is different
    assert nick_id == db.get_nick_id(variant)

    # And no other nick IDs are created (even with create=True)
    assert nick_id == db.get_nick_id(name, create=True)
    assert nick_id == db.get_nick_id(variant, create=True)
    assert 1 == session.query(NickIDs).count()

    # But a truly different name means a new nick ID
    new_nick_id = db.get_nick_id(name + '_test', create=True)
    assert new_nick_id != nick_id
    assert 2 == session.query(NickIDs).count()

    session.close()


def test_alias_nick(db):
    nick = 'Embolalia'
    aliases = ['EmbölaliÅ', 'Embo`work', 'Embo']

    nick_id = db.get_nick_id(nick, create=True)
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
    data = {
        'key': 'value',
        'number_key': 1234,
        'unicode': 'EmbölaliÅ',
    }

    def check():
        for key, value in data.items():
            db.set_nick_value(nick, key, value)

        # no `create` because that should be handled in `set_nick_value()`
        nick_id = db.get_nick_id(nick)

        for key, value in data.items():
            found_value = session.query(NickValues.value) \
                                 .filter(NickValues.nick_id == nick_id) \
                                 .filter(NickValues.key == key) \
                                 .scalar()
            assert json.loads(str(found_value)) == value

        return nick_id

    nid = check()

    # Test updates
    data['number_key'] = 'not a number anymore!'
    data['unicode'] = 'This is different toö!'
    assert nid == check()
    session.close()


def test_get_nick_value(db):
    session = db.ssession()
    nick = 'Embolalia'
    nick_id = db.get_nick_id(nick, create=True)
    data = {
        'key': 'value',
        'number_key': 1234,
        'unicode': 'EmbölaliÅ',
    }

    for key, value in data.items():
        nv = NickValues(nick_id=nick_id, key=key, value=json.dumps(value, ensure_ascii=False))
        session.add(nv)
        session.commit()

    for key, value in data.items():
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

    with pytest.raises(ValueError):
        db.unalias_nick('Mister_Bradshaw')

    session.close()


def test_forget_nick_group(db):
    session = db.ssession()
    aliases = ['Embolalia', 'Embo']
    nick_id = 42
    for alias in aliases:
        nn = Nicknames(nick_id=nick_id, slug=Identifier(alias).lower(), canonical=alias)
        session.add(nn)
        session.commit()

    db.set_nick_value(aliases[0], 'foo', 'bar')
    db.set_nick_value(aliases[1], 'spam', 'eggs')

    db.forget_nick_group(aliases[0])

    with pytest.raises(ValueError):
        db.forget_nick_group('Mister_Bradshaw')

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
        assert json.loads(str(found)) == value
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


def test_forget_channel(db):
    db.set_channel_value('#testchan', 'wasd', 'uldr')
    db.set_channel_value('#testchan', 'asdf', 'hjkl')
    assert db.get_channel_value('#testchan', 'wasd') == 'uldr'
    assert db.get_channel_value('#testchan', 'asdf') == 'hjkl'
    db.forget_channel('#testchan')
    assert db.get_channel_value('#testchan', 'wasd') is None
    assert db.get_channel_value('#testchan', 'asdf') is None


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


def test_forget_plugin(db):
    db.set_plugin_value('plugin', 'wasd', 'uldr')
    db.set_plugin_value('plugin', 'asdf', 'hjkl')
    assert db.get_plugin_value('plugin', 'wasd') == 'uldr'
    assert db.get_plugin_value('plugin', 'asdf') == 'hjkl'
    db.forget_plugin('plugin')
    assert db.get_plugin_value('plugin', 'wasd') is None
    assert db.get_plugin_value('plugin', 'asdf') is None
