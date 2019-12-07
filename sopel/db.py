# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import errno
import json
import os.path
import sys

from sopel.tools import Identifier

from sqlalchemy import create_engine, Column, ForeignKey, Integer, String
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

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


BASE = declarative_base()
MYSQL_TABLE_ARGS = {'mysql_engine': 'InnoDB',
                    'mysql_charset': 'utf8mb4',
                    'mysql_collate': 'utf8mb4_unicode_ci'}


class NickIDs(BASE):
    """
    NickIDs SQLAlchemy Class
    """
    __tablename__ = 'nick_ids'
    nick_id = Column(Integer, primary_key=True)


class Nicknames(BASE):
    """
    Nicknames SQLAlchemy Class
    """
    __tablename__ = 'nicknames'
    __table_args__ = MYSQL_TABLE_ARGS
    nick_id = Column(Integer, ForeignKey('nick_ids.nick_id'), primary_key=True)
    slug = Column(String(255), primary_key=True)
    canonical = Column(String(255))


class NickValues(BASE):
    """
    NickValues SQLAlchemy Class
    """
    __tablename__ = 'nick_values'
    __table_args__ = MYSQL_TABLE_ARGS
    nick_id = Column(Integer, ForeignKey('nick_ids.nick_id'), primary_key=True)
    key = Column(String(255), primary_key=True)
    value = Column(String(255))


class ChannelValues(BASE):
    """
    ChannelValues SQLAlchemy Class
    """
    __tablename__ = 'channel_values'
    __table_args__ = MYSQL_TABLE_ARGS
    channel = Column(String(255), primary_key=True)
    key = Column(String(255), primary_key=True)
    value = Column(String(255))


class PluginValues(BASE):
    """
    PluginValues SQLAlchemy Class
    """
    __tablename__ = 'plugin_values'
    __table_args__ = MYSQL_TABLE_ARGS
    plugin = Column(String(255), primary_key=True)
    key = Column(String(255), primary_key=True)
    value = Column(String(255))


class SopelDB(object):
    """*Availability: 5.0+*

    This defines an interface for basic, common operations on a sqlite
    database. It simplifies those common operations, and allows direct access
    to the database, wherever the user has configured it to be.

    When configured with a relative filename, it is assumed to be in the directory
    set (or defaulted to) in the core setting ``homedir``.
    """

    def __init__(self, config):
        # MySQL - mysql://username:password@localhost/db
        # SQLite - sqlite:////home/sopel/.sopel/default.db
        db_type = config.core.db_type

        # Handle SQLite explicitly as a default
        if db_type == 'sqlite':
            path = config.core.db_filename
            if path is None:
                path = os.path.join(config.core.homedir, config.basename + '.db')
            path = os.path.expanduser(path)
            if not os.path.isabs(path):
                path = os.path.normpath(os.path.join(config.core.homedir, path))
            if not os.path.isdir(os.path.dirname(path)):
                raise OSError(
                    errno.ENOENT,
                    'Cannot create database file. '
                    'No such directory: "{}". Check that configuration setting '
                    'core.db_filename is valid'.format(os.path.dirname(path)),
                    path
                )
            self.filename = path
            self.url = 'sqlite:///%s' % path
        # Otherwise, handle all other database engines
        else:
            query = {}
            if db_type == 'mysql':
                drivername = config.core.db_driver or 'mysql'
                query = {'charset': 'utf8mb4'}
            elif db_type == 'postgres':
                drivername = config.core.db_driver or 'postgresql'
            elif db_type == 'oracle':
                drivername = config.core.db_driver or 'oracle'
            elif db_type == 'mssql':
                drivername = config.core.db_driver or 'mssql+pymssql'
            elif db_type == 'firebird':
                drivername = config.core.db_driver or 'firebird+fdb'
            elif db_type == 'sybase':
                drivername = config.core.db_driver or 'sybase+pysybase'
            else:
                raise Exception('Unknown db_type')

            db_user = config.core.db_user
            db_pass = config.core.db_pass
            db_host = config.core.db_host
            db_port = config.core.db_port  # Optional
            db_name = config.core.db_name  # Optional, depending on DB

            # Ensure we have all our variables defined
            if db_user is None or db_pass is None or db_host is None:
                raise Exception('Please make sure the following core '
                                'configuration values are defined: '
                                'db_user, db_pass, db_host')
            self.url = URL(drivername=drivername, username=db_user,
                           password=db_pass, host=db_host, port=db_port,
                           database=db_name, query=query)

        self.engine = create_engine(self.url, pool_recycle=3600)

        # Catch any errors connecting to database
        try:
            self.engine.connect()
        except OperationalError:
            print("OperationalError: Unable to connect to database.")
            raise

        # Create our tables
        BASE.metadata.create_all(self.engine)

        self.ssession = scoped_session(sessionmaker(bind=self.engine))

    def connect(self):
        """Return a raw database connection object."""
        return self.engine.connect()

    def execute(self, *args, **kwargs):
        """Execute an arbitrary SQL query against the database.

        Returns a cursor object, on which things like `.fetchall()` can be
        called per PEP 249."""
        with self.connect() as conn:
            return conn.execute(*args, **kwargs)

    def get_uri(self):
        """Returns a URL for the database, usable to connect with SQLAlchemy."""
        return 'sqlite:///{}'.format(self.filename)

    # NICK FUNCTIONS

    def get_nick_id(self, nick, create=True):
        """Return the internal identifier for a given nick.

        This identifier is unique to a user, and shared across all of that
        user's aliases. If create is True, a new ID will be created if one does
        not already exist"""
        session = self.ssession()
        slug = nick.lower()
        try:
            nickname = session.query(Nicknames) \
                .filter(Nicknames.slug == slug) \
                .one_or_none()

            if nickname is None:
                if not create:
                    raise ValueError('No ID exists for the given nick')
                # Generate a new ID
                nick_id = NickIDs()
                session.add(nick_id)
                session.commit()

                # Create a new Nickname
                nickname = Nicknames(nick_id=nick_id.nick_id, slug=slug, canonical=nick)
                session.add(nickname)
                session.commit()
            return nickname.nick_id
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def alias_nick(self, nick, alias):
        """Create an alias for a nick.

        Raises ValueError if the alias already exists. If nick does not already
        exist, it will be added along with the alias."""
        nick = Identifier(nick)
        alias = Identifier(alias)
        nick_id = self.get_nick_id(nick)
        session = self.ssession()
        try:
            result = session.query(Nicknames) \
                .filter(Nicknames.slug == alias.lower()) \
                .filter(Nicknames.canonical == alias) \
                .one_or_none()
            if result:
                raise ValueError('Given alias is the only entry in its group.')
            nickname = Nicknames(nick_id=nick_id, slug=alias.lower(), canonical=alias)
            session.add(nickname)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def set_nick_value(self, nick, key, value):
        """Sets the value for a given key to be associated with the nick."""
        nick = Identifier(nick)
        value = json.dumps(value, ensure_ascii=False)
        nick_id = self.get_nick_id(nick)
        session = self.ssession()
        try:
            result = session.query(NickValues) \
                .filter(NickValues.nick_id == nick_id) \
                .filter(NickValues.key == key) \
                .one_or_none()
            # NickValue exists, update
            if result:
                result.value = value
                session.commit()
            # DNE - Insert
            else:
                new_nickvalue = NickValues(nick_id=nick_id, key=key, value=value)
                session.add(new_nickvalue)
                session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def delete_nick_value(self, nick, key):
        """Deletes the value for a given key associated with a nick."""
        nick = Identifier(nick)
        nick_id = self.get_nick_id(nick)
        session = self.ssession()
        try:
            result = session.query(NickValues) \
                .filter(NickValues.nick_id == nick_id) \
                .filter(NickValues.key == key) \
                .one_or_none()
            # NickValue exists, delete
            if result:
                session.delete(result)
                session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def get_nick_value(self, nick, key, default=None):
        """Retrieves the value for a given key associated with a nick."""
        nick = Identifier(nick)
        session = self.ssession()
        try:
            result = session.query(NickValues) \
                .filter(Nicknames.nick_id == NickValues.nick_id) \
                .filter(Nicknames.slug == nick.lower()) \
                .filter(NickValues.key == key) \
                .one_or_none()
            if result is not None:
                result = result.value
            elif default is not None:
                result = default
            return _deserialize(result)
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def unalias_nick(self, alias):
        """Removes an alias.

        Raises ValueError if there is not at least one other nick in the group.
        To delete an entire group, use `delete_group`.
        """
        alias = Identifier(alias)
        nick_id = self.get_nick_id(alias, False)
        session = self.ssession()
        try:
            count = session.query(Nicknames) \
                .filter(Nicknames.nick_id == nick_id) \
                .count()
            if count <= 1:
                raise ValueError('Given alias is the only entry in its group.')
            session.query(Nicknames).filter(Nicknames.slug == alias.lower()).delete()
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def delete_nick_group(self, nick):
        """Removes a nickname, and all associated aliases and settings."""
        nick = Identifier(nick)
        nick_id = self.get_nick_id(nick, False)
        session = self.ssession()
        try:
            session.query(Nicknames).filter(Nicknames.nick_id == nick_id).delete()
            session.query(NickValues).filter(NickValues.nick_id == nick_id).delete()
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

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
        session = self.ssession()
        try:
            # Get second_id's values
            res = session.query(NickValues).filter(NickValues.nick_id == second_id).all()
            # Update first_id with second_id values if first_id doesn't have that key
            for row in res:
                first_res = session.query(NickValues) \
                    .filter(NickValues.nick_id == first_id) \
                    .filter(NickValues.key == row.key) \
                    .one_or_none()
                if not first_res:
                    self.set_nick_value(first_nick, row.key, _deserialize(row.value))
            session.query(NickValues).filter(NickValues.nick_id == second_id).delete()
            session.query(Nicknames) \
                .filter(Nicknames.nick_id == second_id) \
                .update({'nick_id': first_id})
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    # CHANNEL FUNCTIONS

    def set_channel_value(self, channel, key, value):
        """Sets the value for a given key to be associated with the channel."""
        channel = Identifier(channel).lower()
        value = json.dumps(value, ensure_ascii=False)
        session = self.ssession()
        try:
            result = session.query(ChannelValues) \
                .filter(ChannelValues.channel == channel)\
                .filter(ChannelValues.key == key) \
                .one_or_none()
            # ChannelValue exists, update
            if result:
                result.value = value
                session.commit()
            # DNE - Insert
            else:
                new_channelvalue = ChannelValues(channel=channel, key=key, value=value)
                session.add(new_channelvalue)
                session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def delete_channel_value(self, channel, key):
        """Deletes the value for a given key associated with a channel."""
        channel = Identifier(channel).lower()
        session = self.ssession()
        try:
            result = session.query(ChannelValues) \
                .filter(ChannelValues.channel == channel)\
                .filter(ChannelValues.key == key) \
                .one_or_none()
            # ChannelValue exists, delete
            if result:
                session.delete(result)
                session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def get_channel_value(self, channel, key, default=None):
        """Retrieves the value for a given key associated with a channel."""
        channel = Identifier(channel).lower()
        session = self.ssession()
        try:
            result = session.query(ChannelValues) \
                .filter(ChannelValues.channel == channel)\
                .filter(ChannelValues.key == key) \
                .one_or_none()
            if result is not None:
                result = result.value
            elif default is not None:
                result = default
            return _deserialize(result)
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    # PLUGIN FUNCTIONS

    def set_plugin_value(self, plugin, key, value):
        """Sets the value for a given key to be associated with a plugin."""
        plugin = plugin.lower()
        value = json.dumps(value, ensure_ascii=False)
        session = self.ssession()
        try:
            result = session.query(PluginValues) \
                .filter(PluginValues.plugin == plugin)\
                .filter(PluginValues.key == key) \
                .one_or_none()
            # PluginValue exists, update
            if result:
                result.value = value
                session.commit()
            # DNE - Insert
            else:
                new_pluginvalue = PluginValues(plugin=plugin, key=key, value=value)
                session.add(new_pluginvalue)
                session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def delete_plugin_value(self, plugin, key):
        """Deletes the value for a given key associated with a plugin."""
        plugin = plugin.lower()
        session = self.ssession()
        try:
            result = session.query(PluginValues) \
                .filter(PluginValues.plugin == plugin)\
                .filter(PluginValues.key == key) \
                .one_or_none()
            # PluginValue exists, update
            if result:
                session.delete(result)
                session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def get_plugin_value(self, plugin, key, default=None):
        """Retrieves the value for a given key associated with a plugin."""
        plugin = plugin.lower()
        session = self.ssession()
        try:
            result = session.query(PluginValues) \
                .filter(PluginValues.plugin == plugin)\
                .filter(PluginValues.key == key) \
                .one_or_none()
            if result is not None:
                result = result.value
            elif default is not None:
                result = default
            return _deserialize(result)
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    # NICK AND CHANNEL FUNCTIONS

    def get_nick_or_channel_value(self, name, key, default=None):
        """Gets the value `key` associated to the nick or channel  `name`."""
        name = Identifier(name)
        if name.is_nick():
            return self.get_nick_value(name, key, default)
        else:
            return self.get_channel_value(name, key, default)

    def get_preferred_value(self, names, key):
        """Gets the value for the first name which has it set.

        `names` is a list of channel and/or user names. Returns None if none of
        the names have the key set."""
        for name in names:
            value = self.get_nick_or_channel_value(name, key)
            if value is not None:
                return value
