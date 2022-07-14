"""Tests for the new database functionality.

TODO: Most of these tests assume functionality tested in other tests. This is
enough to get everything working (and is better than nothing), but best
practice would probably be not to do that."""
from __future__ import annotations

import json

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.sql import func, select, text

from sopel.db import (
    ChannelValues,
    NickIDs,
    Nicknames,
    NickValues,
    PluginValues,
    SopelDB,
)
from sopel.tools import Identifier


TMP_CONFIG = """
[core]
owner = Pepperpots
db_filename = {db_filename}
"""


@pytest.fixture
def tmpconfig(configfactory, tmpdir):
    content = TMP_CONFIG.format(db_filename=tmpdir.join('test.sqlite'))
    return configfactory('default.cfg', content)


@pytest.fixture
def db(tmpconfig):
    db = SopelDB(tmpconfig)
    # TODO add tests to ensure db creation works properly, too.
    return db


# Test execute

def test_execute(db: SopelDB):
    # todo: remove in Sopel 8.1
    results = db.execute('SELECT * FROM nicknames')
    assert results.fetchall() == []

    results = db.execute(text('SELECT * FROM nicknames'))
    assert results.fetchall() == []


# Test connect

def test_connect(db: SopelDB):
    """Test it's possible to get a raw connection and to use it properly."""
    nick_id = db.get_nick_id('MrEricPraline', create=True)
    connection = db.connect()

    try:
        cursor_obj = connection.cursor()
        cursor_obj.execute('SELECT nick_id, canonical, slug FROM nicknames')
        results = cursor_obj.fetchall()
        cursor_obj.close()
        assert results == [(nick_id, 'MrEricPraline', 'mrericpraline')]
    finally:
        connection.close()


# Test url

def test_get_uri(db: SopelDB, tmpconfig):
    assert db.get_uri() == make_url('sqlite:///' + tmpconfig.core.db_filename)


# Test nick value

def test_get_nick_id(db: SopelDB):
    """Test get_nick_id does not create NickID by default."""
    nick = Identifier('MrEricPraline')

    # Attempt to get nick ID: it is not created by default
    with pytest.raises(ValueError):
        db.get_nick_id(nick)

    # Create the nick ID
    nick_id = db.get_nick_id(nick, create=True)

    # Check that one and only one nickname exists with that ID
    with db.session() as session:
        nickname = session.execute(
            select(Nicknames).where(Nicknames.nick_id == nick_id)
        ).scalar_one()  # will raise if not one and exactly one
    assert nickname.canonical == 'MrEricPraline'
    assert nickname.slug == nick.lower()


@pytest.mark.parametrize('name, slug, variant', (
    # Check case insensitive with ASCII only
    ('MrEricPraline', 'mrericpraline', 'mRErICPraLINE'),
    # Ensures case conversion is handled properly
    ('[][]', '{}{}', '[}{]'),
    # Unicode, just in case
    ('MrÉrïcPrâliné', 'mrÉrïcprâliné', 'MRÉRïCPRâLINé'),
))
def test_get_nick_id_casemapping(db: SopelDB, name, slug, variant):
    """Test get_nick_id is case-insensitive through an Identifier."""
    nick = Identifier(name)

    # Create the nick ID
    nick_id = db.get_nick_id(nick, create=True)

    with db.session() as session:
        registered = session.execute(
            select(Nicknames).where(Nicknames.canonical == name)
        ).scalars().fetchall()

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

    with db.session() as session:
        assert 1 == session.scalar(
            select(func.count()).select_from(NickIDs)
        )

    # But a truly different name means a new nick ID
    new_nick_id = db.get_nick_id(name + '_test', create=True)
    assert new_nick_id != nick_id

    with db.session() as session:
        assert 2 == session.scalar(
            select(func.count()).select_from(NickIDs)
        )


def test_get_nick_id_migration(db: SopelDB):
    """Test nicks with wrong casemapping are properly migrated."""
    nick = 'Test[User]'
    old_nick = Identifier._lower_swapped(nick)

    # sanity check
    assert Identifier(nick).lower() != old_nick, (
        'Previous casemapping should be different from the new one')

    # insert old version
    with db.session() as session:
        nickname = Nicknames(
            nick_id=42,
            slug=Identifier._lower_swapped(nick),
            canonical=nick,
        )
        session.add(nickname)
        session.commit()

    assert db.get_nick_id(nick) == 42, 'Old nick must be converted.'

    with db.session() as session:
        nicknames = session.execute(
            select(Nicknames)
        ).scalars().fetchall()
        assert len(nicknames) == 1, (
            'There should be only one instance of Nicknames.')
        nickname_found = nicknames[0]
        assert nickname_found.nick_id == 42
        assert nickname_found.slug == Identifier(nick).lower()
        assert nickname_found.canonical == nick


def test_alias_nick(db: SopelDB):
    nick = 'MrEricPraline'
    aliases = ['MrÉrïcPrâliné', 'John`Cleese', 'DeadParrot']

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


@pytest.mark.parametrize('value', (
    'string-value',
    123456789,
    'unicode-välûé',
    ['structured', 'value'],
))
def test_set_nick_value(db: SopelDB, value):
    nick = 'Pepperpots'
    db.set_nick_value(nick, 'testkey', value)
    assert db.get_nick_value(nick, 'testkey') == value, (
        'The value retrieved must be exactly what was stored.')


def test_set_nick_value_update(db: SopelDB):
    """Test set_nick_value can update an existing value."""
    db.set_nick_value('Pepperpots', 'testkey', 'first-value')
    db.set_nick_value('Pepperpots', 'otherkey', 'other-value')
    db.set_nick_value('Vikings', 'testkey', 'other-nick-value')

    # sanity check: ensure every (nick, key, value) is correct
    assert db.get_nick_value('Pepperpots', 'testkey') == 'first-value'
    assert db.get_nick_value('Pepperpots', 'otherkey') == 'other-value'
    assert db.get_nick_value('Vikings', 'testkey') == 'other-nick-value'

    # update only one key
    db.set_nick_value('Pepperpots', 'testkey', 'new-value')

    # check new value while old values are still the same
    assert db.get_nick_value('Pepperpots', 'testkey') == 'new-value'
    assert db.get_nick_value('Pepperpots', 'otherkey') == 'other-value'
    assert db.get_nick_value('Vikings', 'testkey') == 'other-nick-value'


def test_delete_nick_value(db: SopelDB):
    nick = 'TerryGilliam'
    db.set_nick_value(nick, 'testkey', 'test-value')

    # sanity check
    assert db.get_nick_value(nick, 'testkey') == 'test-value', (
        'Check set_nick_value: this key must contain the correct value.')

    # delete key
    db.delete_nick_value(nick, 'testkey')
    assert db.get_nick_value(nick, 'testkey') is None


def test_delete_nick_value_none(db: SopelDB):
    """Test method doesn't raise an error when there is nothing to delete."""
    nick = 'TerryGilliam'

    # this user doesn't even exist
    db.delete_nick_value(nick, 'testkey')
    assert db.get_nick_value(nick, 'testkey') is None, (
        'Trying to delete a key must not create it.')

    # create a key
    db.set_nick_value(nick, 'otherkey', 'value')

    # delete another key for that user
    db.delete_nick_value(nick, 'testkey')
    assert db.get_nick_value(nick, 'testkey') is None, (
        'Trying to delete a key must not create it.')

    # the nick still exists, and its key as well
    assert db.get_nick_value(nick, 'otherkey') == 'value', (
        'This key must not be deleted by error.')


@pytest.mark.parametrize('value', (
    'string-value',
    123456789,
    'unicode-välûé',
    ['structured', 'value'],
))
def test_get_nick_value(db: SopelDB, value):
    nick = 'TerryGilliam'
    nick_id = db.get_nick_id(nick, create=True)

    with db.session() as session:
        nick_value = NickValues(
            nick_id=nick_id,
            key='testkey',
            value=json.dumps(value, ensure_ascii=False),
        )
        session.add(nick_value)
        session.commit()

    assert db.get_nick_value(nick, 'testkey') == value
    assert db.get_nick_value(nick, 'otherkey') is None
    assert db.get_nick_value('NotTestUser', 'testkey') is None, (
        'This key must be defined for TerryGilliam only.')


def test_get_nick_value_default(db: SopelDB):
    assert db.get_nick_value('TerryGilliam', 'nokey') is None
    assert db.get_nick_value('TerryGilliam', 'nokey', 'default') == 'default'


def test_unalias_nick(db: SopelDB):
    nick = 'Embolalia'
    nick_id = 42

    with db.session() as session:
        nn = Nicknames(
            nick_id=nick_id,
            slug=Identifier(nick).lower(),
            canonical=nick,
        )
        session.add(nn)
        session.commit()

    aliases = ['EmbölaliÅ', 'Embo`work', 'Embo']
    with db.session() as session:
        for alias in aliases:
            nn = Nicknames(
                nick_id=nick_id,
                slug=Identifier(alias).lower(),
                canonical=alias,
            )
            session.add(nn)
            session.commit()

    for alias in aliases:
        db.unalias_nick(alias)

    with db.session() as session:
        found = session.scalar(
            select(func.count())
            .select_from(Nicknames)
            .where(Nicknames.nick_id == nick_id)
        )
        assert found == 1


def test_unalias_nick_one_or_none(db: SopelDB):
    # this will create the first version of the nick
    db.get_nick_id('MrEricPraline', create=True)

    # assert you can't unalias a unique nick
    with pytest.raises(ValueError):
        db.unalias_nick('MrEricPraline')

    # and you can't either with a non-existing nick
    with pytest.raises(ValueError):
        db.unalias_nick('gumbys')


def test_forget_nick_group(db: SopelDB):
    session = db.ssession()
    aliases = ['MrEricPraline', 'Praline']
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


def test_merge_nick_groups(db: SopelDB):
    session = db.ssession()
    aliases = ['MrEricPraline', 'Praline']
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


# Test channel value

def test_get_channel_slug(db: SopelDB):
    assert db.get_channel_slug('#channel') == '#channel'
    assert db.get_channel_slug('#CHANNEL') == '#channel'
    assert db.get_channel_slug('#[channel]') == '#{channel}', (
        'Default casemapping should be rfc-1459')


def test_get_channel_slug_with_migration(db: SopelDB):
    channel = db.make_identifier('#[channel]')
    db.set_channel_value(channel, 'testkey', 'cval')
    assert db.get_channel_slug(channel) == channel.lower()
    assert db.get_channel_value(channel, 'testkey') == 'cval'

    # insert a value with the wrong casemapping
    old_channel = Identifier._lower_swapped('#[channel]')
    assert old_channel == '#[channel]'
    assert channel.lower() == '#{channel}'

    with db.session() as session:
        channel_value = ChannelValues(
            channel=old_channel,
            key='oldkey',
            value='"value"'  # result from json.dumps
        )
        session.add(channel_value)
        session.commit()

    assert db.get_channel_slug(old_channel) == channel.lower(), (
        'Channel with previous casemapping must return the new version.')
    assert db.get_channel_value(old_channel, 'oldkey') == 'value', (
        'Key associated to an old version must be migrated to the new one')


def test_set_channel_value(db: SopelDB):
    # set new value
    db.set_channel_value('#channel', 'testkey', 'channel-value')

    with db.session() as session:
        result = session.query(ChannelValues.value) \
                        .filter(ChannelValues.channel == '#channel') \
                        .filter(ChannelValues.key == 'testkey') \
                        .scalar()
        assert result == '"channel-value"'

    # update pre-existing value
    db.set_channel_value('#channel', 'testkey', 'new_channel-value')

    with db.session() as session:
        result = session.query(ChannelValues.value) \
                        .filter(ChannelValues.channel == '#channel') \
                        .filter(ChannelValues.key == 'testkey') \
                        .scalar()
        assert result == '"new_channel-value"'


def test_delete_channel_value(db: SopelDB):
    # assert you can delete a non-existing key (without error)
    db.delete_channel_value('#channel', 'testkey')

    # assert you can delete an existing key
    db.set_channel_value('#channel', 'testkey', 'channel-value')
    db.delete_channel_value('#channel', 'testkey')
    assert db.get_channel_value('#channel', 'testkey') is None


def test_get_channel_value(db: SopelDB):
    with db.session() as session:
        channel_value = ChannelValues(
            channel='#channel',
            key='testkey',
            value='\"value\"',
        )
        session.add(channel_value)
        session.commit()

    result = db.get_channel_value('#channel', 'testkey')
    assert result == 'value'


def test_get_channel_value_default(db: SopelDB):
    assert db.get_channel_value('#channel', 'nokey') is None
    assert db.get_channel_value('#channel', 'nokey', 'value') == 'value'


def test_forget_channel(db: SopelDB):
    db.set_channel_value('#channel', 'testkey1', 'value1')
    db.set_channel_value('#channel', 'testkey2', 'value2')
    assert db.get_channel_value('#channel', 'testkey1') == 'value1'
    assert db.get_channel_value('#channel', 'testkey2') == 'value2'
    db.forget_channel('#channel')
    assert db.get_channel_value('#channel', 'wasd') is None
    assert db.get_channel_value('#channel', 'asdf') is None


# Test plugin value

def test_set_plugin_value(db: SopelDB):
    # set new value
    db.set_plugin_value('plugname', 'qwer', 'zxcv')
    with db.session() as session:
        result = session.query(PluginValues.value) \
                        .filter(PluginValues.plugin == 'plugname') \
                        .filter(PluginValues.key == 'qwer') \
                        .scalar()
        assert result == '"zxcv"'

    # update pre-existing value
    db.set_plugin_value('plugname', 'qwer', 'new_zxcv')

    with db.session() as session:
        result = session.query(PluginValues.value) \
                        .filter(PluginValues.plugin == 'plugname') \
                        .filter(PluginValues.key == 'qwer') \
                        .scalar()
        assert result == '"new_zxcv"'


def test_delete_plugin_value(db: SopelDB):
    db.set_plugin_value('plugin', 'testkey', 'todelete')
    db.set_plugin_value('plugin', 'nodelete', 'tokeep')
    assert db.get_plugin_value('plugin', 'testkey') == 'todelete'
    assert db.get_plugin_value('plugin', 'nodelete') == 'tokeep'
    db.delete_plugin_value('plugin', 'testkey')
    assert db.get_plugin_value('plugin', 'testkey') is None
    assert db.get_plugin_value('plugin', 'nodelete') == 'tokeep'


def test_delete_plugin_value_none(db: SopelDB):
    """Test you can delete a key even if it is not defined"""
    assert db.get_plugin_value('plugin', 'testkey') is None
    db.delete_plugin_value('plugin', 'testkey')
    assert db.get_plugin_value('plugin', 'testkey') is None


def test_get_plugin_value(db: SopelDB):
    session = db.ssession()

    pv = PluginValues(plugin='plugname', key='qwer', value='\"zxcv\"')
    session.add(pv)
    session.commit()

    result = db.get_plugin_value('plugname', 'qwer')
    assert result == 'zxcv'
    session.close()


def test_get_plugin_value_default(db: SopelDB):
    assert db.get_plugin_value('TestPlugin', 'DoesntExist') is None
    assert db.get_plugin_value('TestPlugin', 'DoesntExist', 'MyDefault') == 'MyDefault'


def test_forget_plugin(db: SopelDB):
    db.set_plugin_value('plugin', 'wasd', 'uldr')
    db.set_plugin_value('plugin', 'asdf', 'hjkl')
    assert db.get_plugin_value('plugin', 'wasd') == 'uldr'
    assert db.get_plugin_value('plugin', 'asdf') == 'hjkl'
    db.forget_plugin('plugin')
    assert db.get_plugin_value('plugin', 'wasd') is None
    assert db.get_plugin_value('plugin', 'asdf') is None


def test_forget_plugin_none(db: SopelDB):
    """Test forget_plugin works even if there is nothing to forget."""
    db.forget_plugin('plugin')
    assert db.get_plugin_value('plugin', 'wasd') is None
    assert db.get_plugin_value('plugin', 'asdf') is None


# Test nick & channel

def test_get_nick_or_channel_value(db: SopelDB):
    db.set_nick_value('asdf', 'qwer', 'poiu')
    db.set_channel_value('#asdf', 'qwer', '/.,m')
    assert db.get_nick_or_channel_value('asdf', 'qwer') == 'poiu'
    assert db.get_nick_or_channel_value('#asdf', 'qwer') == '/.,m'


def test_get_nick_or_channel_value_identifier(db: SopelDB):
    db.set_nick_value('testuser', 'testkey', 'user-value')
    db.set_channel_value('#channel', 'testkey', 'channel-value')

    nick = Identifier('testuser')
    channel = Identifier('#channel')
    assert db.get_nick_or_channel_value(nick, 'testkey') == 'user-value'
    assert db.get_nick_or_channel_value(nick, 'nokey') is None
    assert db.get_nick_or_channel_value(nick, 'nokey', 'default') == 'default'
    assert db.get_nick_or_channel_value(channel, 'testkey') == 'channel-value'
    assert db.get_nick_or_channel_value(
        channel, 'nokey', 'default'
    ) == 'default'


def test_get_nick_or_channel_value_default(db: SopelDB):
    assert db.get_nick_or_channel_value('Test', 'DoesntExist') is None
    assert db.get_nick_or_channel_value('Test', 'DoesntExist', 'MyDefault') == 'MyDefault'


def test_get_preferred_value(db: SopelDB):
    db.set_nick_value('asdf', 'qwer', 'poiu')
    db.set_channel_value('#asdf', 'qwer', '/.,m')
    db.set_channel_value('#asdf', 'lkjh', '1234')
    names = ['asdf', '#asdf']
    assert db.get_preferred_value(names, 'qwer') == 'poiu'
    assert db.get_preferred_value(names, 'lkjh') == '1234'


def test_get_preferred_value_none(db: SopelDB):
    """Test method when there is no preferred value"""
    db.set_nick_value('testuser', 'userkey', 'uservalue')
    db.set_channel_value('#channel', 'channelkey', 'channelvalue')
    names = ['notuser', '#notchannel']
    assert db.get_preferred_value(names, 'userkey') is None
    assert db.get_preferred_value(names, 'channelkey') is None
