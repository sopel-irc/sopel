# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import errno
import json
import logging
import os.path
import sys
import traceback

from sopel.tools import Identifier

from sqlalchemy import create_engine, Column, ForeignKey, Integer, String
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

if sys.version_info.major >= 3:
    unicode = str
    basestring = str


LOGGER = logging.getLogger(__name__)


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
    """Nick IDs table SQLAlchemy class."""
    __tablename__ = 'nick_ids'
    nick_id = Column(Integer, primary_key=True)


class Nicknames(BASE):
    """Nicknames table SQLAlchemy class."""
    __tablename__ = 'nicknames'
    __table_args__ = MYSQL_TABLE_ARGS
    nick_id = Column(Integer, ForeignKey('nick_ids.nick_id'), primary_key=True)
    slug = Column(String(255), primary_key=True)
    canonical = Column(String(255))


class NickValues(BASE):
    """Nick values table SQLAlchemy class."""
    __tablename__ = 'nick_values'
    __table_args__ = MYSQL_TABLE_ARGS
    nick_id = Column(Integer, ForeignKey('nick_ids.nick_id'), primary_key=True)
    key = Column(String(255), primary_key=True)
    value = Column(String(255))


class ChannelValues(BASE):
    """Channel values table SQLAlchemy class."""
    __tablename__ = 'channel_values'
    __table_args__ = MYSQL_TABLE_ARGS
    channel = Column(String(255), primary_key=True)
    key = Column(String(255), primary_key=True)
    value = Column(String(255))


class PluginValues(BASE):
    """Plugin values table SQLAlchemy class."""
    __tablename__ = 'plugin_values'
    __table_args__ = MYSQL_TABLE_ARGS
    plugin = Column(String(255), primary_key=True)
    key = Column(String(255), primary_key=True)
    value = Column(String(255))


class SopelDB(object):
    """Database object class.

    :param config: Sopel's configuration settings
    :type config: :class:`sopel.config.Config`

    This defines a simplified interface for basic, common operations on the
    bot's database. Direct access to the database is also available, to serve
    more complex plugins' needs.

    When configured to use SQLite with a relative filename, the file is assumed
    to be in the directory named by the core setting ``homedir``.

    .. versionadded:: 5.0

    .. versionchanged:: 7.0

        Switched from direct SQLite access to :ref:`SQLAlchemy
        <sqlalchemy:overview>`, allowing users more flexibility around what type
        of database they use (especially on high-load Sopel instances, which may
        run up against SQLite's concurrent-access limitations).

    """

    def __init__(self, config):
        # MySQL - mysql://username:password@localhost/db
        # SQLite - sqlite:////home/sopel/.sopel/default.db
        self.type = config.core.db_type

        # Handle SQLite explicitly as a default
        if self.type == 'sqlite':
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
            if self.type == 'mysql':
                drivername = config.core.db_driver or 'mysql'
                query = {'charset': 'utf8mb4'}
            elif self.type == 'postgres':
                drivername = config.core.db_driver or 'postgresql'
            elif self.type == 'oracle':
                drivername = config.core.db_driver or 'oracle'
            elif self.type == 'mssql':
                drivername = config.core.db_driver or 'mssql+pymssql'
            elif self.type == 'firebird':
                drivername = config.core.db_driver or 'firebird+fdb'
            elif self.type == 'sybase':
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
        """Get a direct database connection.

        :return: a proxied DBAPI connection object; see
                 :meth:`sqlalchemy.engine.Engine.raw_connection()`

        .. important::

           The :attr:`~sopel.config.core_section.CoreSection.db_type` in use
           can change how the raw connection object behaves. You probably want
           to use :meth:`session` and the SQLAlchemy ORM in new plugins, and
           officially support only Sopel 7.0+.

           Note that :meth:`session` is not available in Sopel versions prior
           to 7.0. If your plugin needs to be compatible with older Sopel
           releases, your code *should* use SQLAlchemy via :meth:`session` if
           it is available (Sopel 7.0+) and fall back to direct SQLite access
           via :meth:`connect` if it is not (Sopel 6.x).

           We discourage *publishing* plugins that don't work with all
           supported databases, but you're obviously welcome to take shortcuts
           and support only the engine(s) you need in *private* plugins.

        """
        if self.type != 'sqlite':
            # log non-sqlite uses of raw connections for troubleshooting, since
            # unless the developer had a good reason to use this instead of
            # `session()`, it indicates the plugin was written before Sopel 7.0
            # and might not work right when connected to non-sqlite DBs
            LOGGER.info(
                "Raw connection requested when 'db_type' is not 'sqlite':\n"
                "Consider using 'db.session()' to get a SQLAlchemy session "
                "instead here:\n%s",
                traceback.format_list(traceback.extract_stack()[:-1])[-1][:-1])
        return self.engine.raw_connection()

    def session(self):
        """Get a SQLAlchemy Session object.

        :rtype: :class:`sqlalchemy.orm.session.Session`

        .. versionadded:: 7.0

        .. note::

           If your plugin needs to remain compatible with Sopel versions prior
           to 7.0, you can use :meth:`connect` to get a raw connection. See
           its documentation for relevant warnings and compatibility caveats.

        """
        return self.ssession()

    def execute(self, *args, **kwargs):
        """Execute an arbitrary SQL query against the database.

        :return: the query results
        :rtype: :class:`sqlalchemy.engine.ResultProxy`

        The ``ResultProxy`` object returned is a wrapper around a ``Cursor``
        object as specified by PEP 249.
        """
        return self.engine.execute(*args, **kwargs)

    def get_uri(self):
        """Return a direct URL for the database.

        :return: the database connection URI
        :rtype: str

        This can be used to connect from a plugin using another SQLAlchemy
        instance, for example, without sharing the bot's connection.
        """
        return self.url

    # NICK FUNCTIONS

    def get_nick_id(self, nick, create=True):
        """Return the internal identifier for a given nick.

        :param nick: the nickname for which to fetch an ID
        :type nick: :class:`~sopel.tools.Identifier`
        :param bool create: whether to create an ID if one does not exist
        :raise ValueError: if no ID exists for the given ``nick`` and ``create``
                           is set to ``False``
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        The nick ID is shared across all of a user's aliases, assuming their
        nicks have been grouped together.

        .. seealso::

            Alias/group management functions: :meth:`alias_nick`,
            :meth:`unalias_nick`, :meth:`merge_nick_groups`, and
            :meth:`delete_nick_group`.

        """
        session = self.ssession()
        slug = nick.lower()
        try:
            nickname = session.query(Nicknames) \
                .filter(Nicknames.slug == slug) \
                .one_or_none()

            if nickname is None:
                # see if it needs case-mapping migration
                nickname = session.query(Nicknames) \
                    .filter(Nicknames.slug == Identifier._lower_swapped(nick)) \
                    .one_or_none()
                if nickname is not None:
                    # it does!
                    nickname.slug = slug
                    session.commit()

            if nickname is None:  # "is /* still */ None", if Python had inline comments
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

        :param str nick: an existing nickname
        :param str alias: an alias by which ``nick`` should also be known
        :raise ValueError: if the ``alias`` already exists
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. seealso::

            To merge two *existing* nick groups, use :meth:`merge_nick_groups`.

            To remove an alias created with this function, use
            :meth:`unalias_nick`.

        """
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
                raise ValueError('Alias already exists.')
            nickname = Nicknames(nick_id=nick_id, slug=alias.lower(), canonical=alias)
            session.add(nickname)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def set_nick_value(self, nick, key, value):
        """Set or update a value in the key-value store for ``nick``.

        :param str nick: the nickname with which to associate the ``value``
        :param str key: the name by which this ``value`` may be accessed later
        :param mixed value: the value to set for this ``key`` under ``nick``
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        The ``value`` can be any of a range of types; it need not be a string.
        It will be serialized to JSON before being stored and decoded
        transparently upon retrieval.

        .. seealso::

            To retrieve a value set with this method, use
            :meth:`get_nick_value`.

            To delete a value set with this method, use
            :meth:`delete_nick_value`.

        """
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
        """Delete a value from the key-value store for ``nick``.

        :param str nick: the nickname whose values to modify
        :param str key: the name of the value to delete
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. seealso::

            To set a value in the first place, use :meth:`set_nick_value`.

            To retrieve a value instead of deleting it, use
            :meth:`get_nick_value`.

        """
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
        """Get a value from the key-value store for ``nick``.

        :param str nick: the nickname whose values to access
        :param str key: the name by which the desired value was saved
        :param mixed default: value to return if ``key`` does not have a value
                              set (optional)
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. seealso::

            To set a value for later retrieval with this method, use
            :meth:`set_nick_value`.

            To delete a value instead of retrieving it, use
            :meth:`delete_nick_value`.

        """
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
        """Remove an alias.

        :param str alias: an alias with at least one other nick in its group
        :raise ValueError: if there is not at least one other nick in the group
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. seealso::

            To delete an entire group, use :meth:`delete_nick_group`.

            To *add* an alias for a nick, use :meth:`alias_nick`.

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
        """Remove a nickname, all of its aliases, and all of its stored values.

        :param str nick: one of the nicknames in the group to be deleted
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. important::

            This is otherwise known as The Nuclear Option. Be *very* sure that
            you want to do this.

        """
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
        """Merge two nick groups.

        :param str first_nick: one nick in the first group to merge
        :param str second_nick: one nick in the second group to merge
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        Takes two nicks, which may or may not be registered. Unregistered nicks
        will be registered. Keys which are set for only one of the given nicks
        will be preserved. Where both nicks have values for a given key, the
        value set for the ``first_nick`` will be used.

        A nick group can contain one or many nicknames. Groups containing more
        than one nickname can be created with this function, or by using
        :meth:`alias_nick` to add aliases.

        Note that merging of data only applies to the native key-value store.
        Plugins which define their own tables relying on the nick table will
        need to handle their own merging separately.
        """
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

    def get_channel_slug(self, chan):
        """Return the case-normalized representation of ``channel``.

        :param str channel: the channel name to normalize, with prefix
                            (required)
        :return str: the case-normalized channel name (or "slug"
                     representation)

        This is useful to make sure that a channel name is stored consistently
        in both the bot's own database and third-party plugins'
        databases/files, without regard for variation in case between
        different clients and/or servers on the network.
        """
        chan = Identifier(chan)
        slug = chan.lower()
        session = self.ssession()
        try:
            count = session.query(ChannelValues) \
                .filter(ChannelValues.channel == slug) \
                .count()

            if count == 0:
                # see if it needs case-mapping migration
                old_rows = session.query(ChannelValues) \
                    .filter(ChannelValues.channel == Identifier._lower_swapped(chan))
                old_count = old_rows.count()
                if old_count > 0:
                    # it does!
                    old_rows.update({ChannelValues.channel: slug})
                    session.commit()

            return slug
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            self.ssession.remove()

    def set_channel_value(self, channel, key, value):
        """Set or update a value in the key-value store for ``channel``.

        :param str channel: the channel with which to associate the ``value``
        :param str key: the name by which this ``value`` may be accessed later
        :param mixed value: the value to set for this ``key`` under ``channel``
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        The ``value`` can be any of a range of types; it need not be a string.
        It will be serialized to JSON before being stored and decoded
        transparently upon retrieval.

        .. seealso::

            To retrieve a value set with this method, use
            :meth:`get_channel_value`.

            To delete a value set with this method, use
            :meth:`delete_channel_value`.

        """
        channel = self.get_channel_slug(channel)
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
        """Delete a value from the key-value store for ``channel``.

        :param str channel: the channel whose values to modify
        :param str key: the name of the value to delete
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. seealso::

            To set a value in the first place, use :meth:`set_channel_value`.

            To retrieve a value instead of deleting it, use
            :meth:`get_channel_value`.

        """
        channel = self.get_channel_slug(channel)
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
        """Get a value from the key-value store for ``channel``.

        :param str channel: the channel whose values to access
        :param str key: the name by which the desired value was saved
        :param mixed default: value to return if ``key`` does not have a value
                              set (optional)
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. seealso::

            To set a value for later retrieval with this method, use
            :meth:`set_channel_value`.

            To delete a value instead of retrieving it, use
            :meth:`delete_channel_value`.

        """
        channel = self.get_channel_slug(channel)
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
        """Set or update a value in the key-value store for ``plugin``.

        :param str plugin: the plugin name with which to associate the ``value``
        :param str key: the name by which this ``value`` may be accessed later
        :param mixed value: the value to set for this ``key`` under ``plugin``
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        The ``value`` can be any of a range of types; it need not be a string.
        It will be serialized to JSON before being stored and decoded
        transparently upon retrieval.

        .. seealso::

            To retrieve a value set with this method, use
            :meth:`get_plugin_value`.

            To delete a value set with this method, use
            :meth:`delete_plugin_value`.

        """
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
        """Delete a value from the key-value store for ``plugin``.

        :param str plugin: the plugin name whose values to modify
        :param str key: the name of the value to delete
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. seealso::

            To set a value in the first place, use :meth:`set_plugin_value`.

            To retrieve a value instead of deleting it, use
            :meth:`get_plugin_value`.

        """
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
        """Get a value from the key-value store for ``plugin``.

        :param str plugin: the plugin name whose values to access
        :param str key: the name by which the desired value was saved
        :param mixed default: value to return if ``key`` does not have a value
                              set (optional)
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        .. seealso::

            To set a value for later retrieval with this method, use
            :meth:`set_plugin_value`.

            To delete a value instead of retrieving it, use
            :meth:`delete_plugin_value`.

        """
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
        """Get a value from the key-value store for ``name``.

        :param str name: nick or channel whose values to access
        :param str key: the name by which the desired value was saved
        :param mixed default: value to return if ``key`` does not have a value
                              set (optional)
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        This is useful for common logic that is shared between both users and
        channels, as it will fetch the appropriate value based on what type of
        ``name`` it is given.

        .. seealso::

            To get a value for a nick specifically, use :meth:`get_nick_value`.

            To get a value for a channel specifically, use
            :meth:`get_channel_value`.

        """
        name = Identifier(name)
        if name.is_nick():
            return self.get_nick_value(name, key, default)
        else:
            return self.get_channel_value(name, key, default)

    def get_preferred_value(self, names, key):
        """Get a value for the first name which has it set.

        :param list names: a list of channel names and/or nicknames
        :param str key: the name by which the desired value was saved
        :return: the value for ``key`` from the first ``name`` which has it set,
                 or ``None`` if none of the ``names`` has it set
        :raise ~sqlalchemy.exc.SQLAlchemyError: if there is a database error

        This is useful for logic that needs to customize its output based on
        settings stored in the database. For example, it can be used to fall
        back from the triggering user's setting to the current channel's setting
        in case the user has not configured their setting.

        .. note::

            This is the only ``get_*_value()`` method that does not support
            passing a ``default``. Try to avoid using it on ``key``\\s which
            might have ``None`` as a valid value, to avoid ambiguous logic.

        """
        for name in names:
            value = self.get_nick_or_channel_value(name, key)
            if value is not None:
                return value
