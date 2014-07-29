import sqlite3
from willie.tools import Nick

class WillieDB(object):

    def __init__(self, filename):
        self.filename = filename

    def connect(self):
        """Return a raw database connection object."""
        return sqlite3.connect(self.filename)

    def execute(self, *args, **kwargs):
        """Execute an arbitrary SQL query against the database.

        Returns a cursor object, on which things like `.fetchall()` can be
        called per PEP 249."""
        with self.connect() as conn:
            cur = conn.cursor()
            return cur.execute(*args, **kwargs)

    def create(self):
        """Create the basic database structure."""
        self.execute(
            'CREATE TABLE nicknames '
            '(nick_id INTEGER, slug STRING PRIMARY KEY, canonical string)'
        )
        self.execute(
            'CREATE TABLE nick_values '
            '(nick_id INTEGER, key STRING, value STRING,'
            'PRIMARY KEY (nick_id, key))'
        )
        self.execute('INSERT INTO nicknames VALUES (?, ?, ?)', [0, '', ''])

    def _get_nick_id(self, nick):
        """Return the internal identifier for a given nick.

        This identifier is unique to a user, and shared across all of that
        user's aliases."""
        slug = nick.lower()
        nick_id = self.execute('SELECT nick_id from nicknames where slug = ?',
                               [slug]).fetchone()
        if nick_id is None:
            self.execute(
                'INSERT INTO nicknames (nick_id, slug, canonical) VALUES '
                '((SELECT max(nick_id) + 1 from nicknames), ?, ?)',
                [slug, nick])
            nick_id = self.execute('SELECT nick_id from nicknames where slug = ?',
                                   [slug]).fetchone()
        return nick_id[0]

    def alias_nick(self, nick, alias):
        """Create an alias for a nick.

        Raises ValueError if the alias already exists. If nick does not already
        exist, it will be added along with the alias."""
        nick = Nick(nick)
        alias = Nick(alias)
        nick_id = self._get_nick_id(nick)
        sql = 'INSERT INTO nicknames (nick_id, slug, canonical) VALUES (?, ?, ?)'
        values = [nick_id, alias.lower(), alias]
        try:
            self.execute(sql, values)
        except sqlite3.IntegrityError:  #TODO check that it's a unique violation
            raise ValueError('Alias already exists.')

    def set_nick_value(self, nick, key, value):
        """Sets the value for a given key to be associated with the nick."""
        nick = Nick(nick)
        nick_id = self._get_nick_id(nick)
        # Insert if it's not already set, otherwise update
        if not self.get_nick_value(nick, key):
            self.execute('INSERT INTO nick_values VALUES (?, ?, ?)',
                         [nick_id, key, value])
        else:
            self.execute('UPDATE nick_values SET value = ? '
                         'WHERE nick_id = ? AND key = ?',
                         [value, nick_id, key])

    def get_nick_value(self, nick, key):
        """Retrieves the value for a given key associated with a nick."""
        nick = Nick(nick)
        result = self.execute(
            'SELECT value FROM nicknames, nick_values WHERE slug = ? AND key = ?',
            [nick.lower(), key]
        ).fetchone()
        if result is not None:
            result = result[0]
        return result

    def unalias_nick(self, nick, alias):
        """Removes an alias.

        Raises ValueError if there is not at least one other nick in the group.
        """
        pass  # TODO

    def merge_nick_groups(self, nicks):
        """Merges the nick groups for the specified nicks.

        Takes an iterable of nicks, which may or may not be registered.
        Unregistered nicks will be registered. Keys which are set for only one
        of the given nicks will be preserved. Where multiple nicks have values
        for a given key, the value set for an arbitrary nick will be chosen
        (#TODO unless deterministic is just as easy to implement)."""
        pass  # TODO

# TODO settings for channels, and a method to provide a Trigger and get the
# nick setting if set, else the channel setting.
