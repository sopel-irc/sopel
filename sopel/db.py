# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import json
import os.path
import sys
import sqlite3

from sopel.tools import Identifier

if sys.version_info.major >= 3:
    unicode = str
    basestring = str


def _deserialize(value):
    if value is None:
        return None
    # sqlite likes to return ints for strings that look like ints, even though
    # the column type is string. That's how you do dynamic typing wrong.
    value = unicode(value)
    # Just in case someone's mucking with the DB in a way we can't account for,
    # ignore json parsing errors
    try:
        value = json.loads(value)
    except ValueError:
        pass
    return value


class SopelDB(object):
    """*Availability: 5.0+*

    This defines an interface for basic, common operations on a sqlite
    database. It simplifies those common operations, and allows direct access
    to the database, wherever the user has configured it to be.

    When configured with a relative filename, it is assumed to be in the same
    directory as the config."""

    def __init__(self, config):
        path = config.core.db_filename
        config_dir, config_file = os.path.split(config.filename)
        config_name, _ = os.path.splitext(config_file)
        if path is None:
            path = os.path.join(config_dir, config_name + '.db')
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(config_dir, path))
        self.filename = path
        self._create()

    def connect(self):
        """Return a raw database connection object."""
        return sqlite3.connect(self.filename, timeout=10)

    def execute(self, *args, **kwargs):
        """Execute an arbitrary SQL query against the database.

        Returns a cursor object, on which things like `.fetchall()` can be
        called per PEP 249."""
        with self.connect() as conn:
            cur = conn.cursor()
            return cur.execute(*args, **kwargs)

    def _create(self):
        """Create the basic database structure."""
        self.execute(
            'CREATE TABLE IF NOT EXISTS nick_ids (nick_id INTEGER PRIMARY KEY AUTOINCREMENT)'
        )
        self.execute(
            'CREATE TABLE IF NOT EXISTS nicknames '
            '(nick_id INTEGER REFERENCES nick_ids, '
            'slug STRING PRIMARY KEY, canonical string)'
        )
        self.execute(
            'CREATE TABLE IF NOT EXISTS nick_values '
            '(nick_id INTEGER REFERENCES nick_ids(nick_id), '
            'key STRING, value STRING, '
            'PRIMARY KEY (nick_id, key))'
        )
        self.execute(
            'CREATE TABLE IF NOT EXISTS channel_values '
            '(channel STRING, key STRING, value STRING, '
            'PRIMARY KEY (channel, key))'
        )

    def get_uri(self):
        """Returns a URL for the database, usable to connect with SQLAlchemy."""
        return 'sqlite:///{}'.format(self.filename)

    # NICK FUNCTIONS

    def get_nick_id(self, nick, create=True):
        """Return the internal identifier for a given nick.

        This identifier is unique to a user, and shared across all of that
        user's aliases. If create is True, a new ID will be created if one does
        not already exist"""
        slug = nick.lower()
        nick_id = self.execute('SELECT nick_id from nicknames where slug = ?',
                               [slug]).fetchone()
        if nick_id is None:
            if not create:
                raise ValueError('No ID exists for the given nick')
            with self.connect() as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO nick_ids VALUES (NULL)')
                nick_id = cur.execute('SELECT last_insert_rowid()').fetchone()[0]
                cur.execute(
                    'INSERT INTO nicknames (nick_id, slug, canonical) VALUES '
                    '(?, ?, ?)',
                    [nick_id, slug, nick]
                )
            nick_id = self.execute('SELECT nick_id from nicknames where slug = ?',
                                   [slug]).fetchone()
        return nick_id[0]

    def alias_nick(self, nick, alias):
        """Create an alias for a nick.

        Raises ValueError if the alias already exists. If nick does not already
        exist, it will be added along with the alias."""
        nick = Identifier(nick)
        alias = Identifier(alias)
        nick_id = self.get_nick_id(nick)
        sql = 'INSERT INTO nicknames (nick_id, slug, canonical) VALUES (?, ?, ?)'
        values = [nick_id, alias.lower(), alias]
        try:
            self.execute(sql, values)
        except sqlite3.IntegrityError:
            raise ValueError('Alias already exists.')

    def set_nick_value(self, nick, key, value):
        """Sets the value for a given key to be associated with the nick."""
        nick = Identifier(nick)
        value = json.dumps(value, ensure_ascii=False)
        nick_id = self.get_nick_id(nick)
        self.execute('INSERT OR REPLACE INTO nick_values VALUES (?, ?, ?)',
                     [nick_id, key, value])

    def get_nick_value(self, nick, key):
        """Retrieves the value for a given key associated with a nick."""
        nick = Identifier(nick)
        result = self.execute(
            'SELECT value FROM nicknames JOIN nick_values '
            'ON nicknames.nick_id = nick_values.nick_id '
            'WHERE slug = ? AND key = ?',
            [nick.lower(), key]
        ).fetchone()
        if result is not None:
            result = result[0]
        return _deserialize(result)

    def unalias_nick(self, alias):
        """Removes an alias.

        Raises ValueError if there is not at least one other nick in the group.
        To delete an entire group, use `delete_group`.
        """
        alias = Identifier(alias)
        nick_id = self.get_nick_id(alias, False)
        count = self.execute('SELECT COUNT(*) FROM nicknames WHERE nick_id = ?',
                             [nick_id]).fetchone()[0]
        if count <= 1:
            raise ValueError('Given alias is the only entry in its group.')
        self.execute('DELETE FROM nicknames WHERE slug = ?', [alias.lower()])

    def delete_nick_group(self, nick):
        """Removes a nickname, and all associated aliases and settings."""
        nick = Identifier(nick)
        nick_id = self.get_nick_id(nick, False)
        self.execute('DELETE FROM nicknames WHERE nick_id = ?', [nick_id])
        self.execute('DELETE FROM nick_values WHERE nick_id = ?', [nick_id])

    def merge_nick_groups(self, first_nick, second_nick):
        """Merges the nick groups for the specified nicks.

        Takes two nicks, which may or may not be registered.  Unregistered
        nicks will be registered. Keys which are set for only one of the given
        nicks will be preserved. Where multiple nicks have values for a given
        key, the value set for the first nick will be used.

        Note that merging of data only applies to the native key-value store.
        If modules define their own tables which rely on the nick table, they
        will need to have their merging done separately."""
        first_id = self.get_nick_id(Identifier(first_nick))
        second_id = self.get_nick_id(Identifier(second_nick))
        self.execute(
            'UPDATE OR IGNORE nick_values SET nick_id = ? WHERE nick_id = ?',
            [first_id, second_id])
        self.execute('DELETE FROM nick_values WHERE nick_id = ?', [second_id])
        self.execute('UPDATE nicknames SET nick_id = ? WHERE nick_id = ?',
                     [first_id, second_id])

    # CHANNEL FUNCTIONS

    def set_channel_value(self, channel, key, value):
        """Sets the value for a given key to be associated with the channel."""
        channel = Identifier(channel).lower()
        value = json.dumps(value, ensure_ascii=False)
        self.execute('INSERT OR REPLACE INTO channel_values VALUES (?, ?, ?)',
                     [channel, key, value])

    def get_channel_value(self, channel, key):
        """Retrieves the value for a given key associated with a channel."""
        channel = Identifier(channel).lower()
        result = self.execute(
            'SELECT value FROM channel_values WHERE channel = ? AND key = ?',
            [channel, key]
        ).fetchone()
        if result is not None:
            result = result[0]
        return _deserialize(result)

    # NICK AND CHANNEL FUNCTIONS

    def get_nick_or_channel_value(self, name, key):
        """Gets the value `key` associated to the nick or channel  `name`."""
        name = Identifier(name)
        if name.is_nick():
            return self.get_nick_value(name, key)
        else:
            return self.get_channel_value(name, key)

    def get_preferred_value(self, names, key):
        """Gets the value for the first name which has it set.

        `names` is a list of channel and/or user names. Returns None if none of
        the names have the key set."""
        for name in names:
            value = self.get_nick_or_channel_value(name, key)
            if value is not None:
                return value
