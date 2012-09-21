#!/usr/bin/env python
"""
*Availability: 3+*

*Note:* This supersedes the ``SettingsDB`` object of v3. Within Willie modules,
simmilar functionallity can be found using ``willie.db.preferences``.

This class defines an interface for a semi-arbitrary database type. It is meant
to allow module writers to operate without regard to how the end user has
decided to set up the database.
"""
"""
Copyright 2012, Edward D. Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

from collections import Iterable
from tools import deprecated

#Attempt to import possible db modules
mysql = False
try:
    import MySQLdb
    import MySQLdb.cursors
    mysql = True
except ImportError: pass

sqlite = False
try:
    import sqlite3
    sqlite = True
except ImportError: pass

class WillieDB(object):
    """
    Return a WillieDB object configured with the options in the given Config
    object. The exact settgins used vary depending on the type of database
    chosen to back the SettingsDB, as determined by the ``userdb_type``
    attribute of *config*.
    
    Currently, two values for ``userdb_type`` are supported: ``sqlite`` and
    ``mysql``. The ``sqlite`` type requires that ``userdb_file`` be set in
    ``config``, and refer to a writeable sqlite database. The ``mysql`` type 
    requires ``userdb_host``, ``userdb_user``, ``userdb_pass``, and
    ``userdb_name`` to be set, and provide the host and name of a MySQL database,
    as well as a username and password for a user able to write to said database.
    
    Upon creation of the object, the tables currently existing in the given
    database will be registered, as though added through ``add_table``. 
    """
    def __init__(self, config):
        if not hasattr(config, 'userdb_type'):
            self.type = None
            print 'No user settings database specified. Ignoring.'
            return
        self.type = config.userdb_type.lower()
        
        
        if self.type == 'mysql' and mysql:
            self._mySQL(config)
        elif self.type == 'sqlite' and sqlite:
            self._sqlite(config)
        else:
            print 'User settings database type is not supported. You may be missing the module for it. Ignoring.'
            return
            
            
    def _mySQL(self, config):
        try:
                self._host = config.userdb_host
                self._user = config.userdb_user
                self._passwd = config.userdb_pass
                self._dbname = config.userdb_name
        except AttributeError as e:
                print 'Some options are missing for your MySQL DB. The database will not be set up.'
                return
            
        try:
            db = MySQLdb.connect(host=self._host,
                         user=self._user,
                         passwd=self._passwd,
                         db=self._dbname)
        except:
            print 'Error: Unable to connect to user settings DB.'
            return
        
        #Set up existing tables and columns
        cur = MySQLdb.cursors.DictCursor(db)
        cur.execute("SHOW tables;")
        tables = cur.fetchall()
        for table in tables:
            name = table['Tables_in_%s' % self._dbname]
            cur.execute("SHOW columns FROM %s;" % name)
            result = cur.fetchall()
            columns = []
            key = []
            for column in result:
                columns.append(column['Field'])
                if column['Key'].startswith('PRI'):
                    key.append(column['Field'])
            setattr(self, name, Table(self, name, columns, key))
        db.close()
    
    def _sqlite(self, config):
        try:
            self._file = config.userdb_file
        except AttributeError:
            print 'No file specified for SQLite DB. The database will not be set up.'
            return
            
        try:
            db = sqlite3.connect(self._file)
        except:
            print 'Error: Unable to connect to DB.'
            return
        
        #Set up existing tables and columns
        cur = db.cursor()
        cur.execute("SELECT * FROM sqlite_master;")
        tables = cur.fetchall()
        for table in tables:
            name = table[1]
            cur.execute("PRAGMA table_info(%s);" % name)
            result = cur.fetchall()
            columns = []
            key = []
            for column in result:
                columns.append(column[1])
                if column[3]:
                    key.append(column[1])
            setattr(self, name, Table(self, name, columns, key))
        db.close()

    def check_table(self, name, columns, key):
        """
        Return ``True`` if the WillieDB contains a table with the same ``name``
        and ``key``, and which contains a column with the same name as each element
        in the given list ``columns``.
        """
        if hasattr(self, name):
            table = getattr(self, name)
            return (isinstance(table, Table) and table.key == key and 
                    all(c in table.columns for c in columns))
        return False
    
    def _get_column_creation_text(self, columns, key=None):
        cols = '('
        for column in columns:
            if isinstance(column, basestring):
                if self.type == 'mysql':
                    cols = cols + column + ' VARCHAR(255)'
                elif self.type == 'sqlite':
                    cols = cols + column + ' string'
            elif isinstance(column, tuple):
                cols += '%s %s' % column
            
            if key and column in key:
                cols += ' NOT NULL'
            cols += ', '

        if key:
            if isinstance(key, basestring):
                cols += 'PRIMARY KEY (%s)' % key
            else:
                cols += 'PRIMARY KEY (%s)' % ', '.join(key)
        else:
            cols = cols[:-2]
        return cols+')'
    
    def add_table(self, name, columns, key):
        """
        Add a column with the given ``name`` and ``key``, which has the given
        ``columns``. Each element in ``columns`` may be either a string giving
        the name of the column, or a tuple containing the name of the column and
        its type (using SQL type names). If the former, the type will be assumed
        as string.
        
        This will attempt to create the table within the database. If an error
        is encountered while adding the table, it will not be added to the
        WillieDB object. If a table with the same name and key already exists,
        the given columns will be added (if they don't already exist).
        
        The given ``name`` can not be the same as any function or attribute
        (with the exception of other tables) of the ``WillieDB`` object, nor may
        it start with ``'_'``. If it does not meet this requirement, or if the
        ``name`` matches that of an existing table with a different ``key``, a
        ``ValueError`` will be thrown.
        
        When a table is created, the column ``key`` will be declared as the
        primary key of the table. If it is desired that there be no primary key,
        this can be achieved by creating the table manually, or with a custom
        query, and then creating the WillieDB object.
        """
        
        if name.startswith('_'):
            raise ValueError, 'Invalid table name %s.' % name
        elif not hasattr(self, name):
            cols = self._get_column_creation_text(columns, key)
            db = self.connect()
            cursor = db.cursor()
            cursor.execute("CREATE TABLE %s %s;" % (name, cols))
            db.close()
            setattr(self, name, Table(self, name, columns, key))
        elif isinstance(self, name, Table):
            table = getattr(self, name)
            if table.key == key:
                if not all(c in table.columns for c in columns):
                    db = self.connect()
                    cursor = db.cursor()
                    cursor.execute("ALTER TABLE %s ADD COLUMN %s;")
                    table.colums.add(columns)
                    db.close()
            else:
                raise ValueError, 'Table %s already exists with different key.' % name
        else: #Conflict with a non-table value, probably a function
            raise ValueError, 'Invalid table name %s.' % name
    
    def connect(self):
        """
        Create a database connection object. This functions essentially the same
        as the ``connect`` function of the appropriate database type, allowing
        for custom queries to be executed.
        """
        if self.type == 'mysql':
            return MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
        elif self.type == 'sqlite':
            return sqlite3.connect(self._file)

class Table(object):
    """
    Return an object which represents a table in the given WillieDB, with the
    given attributes. This will not check if ``db`` already has a table with the
    given ``name``; the ``db``'s ``add_table`` provides that functionality.
    
    ``key`` must be a string, which is in the list of strings ``columns``, or an
    Exception will be thrown. 
    """
    #Note, #Python recommends using dictcursor, so you can select x in y
    #Also, PEP8 says not to import in the middle of your code. That answers that.
    def __init__(self, db, name, columns, key):
        if not key: key = columns[0]
        self.db = db
        self.columns = set(columns)
        self.name = name
        if isinstance(key, basestring):
            if key not in columns:
                raise Exception #TODO
            self.key = key
        else:
            for k in key:
                if k not in columns:
                    raise Exception #TODO
            self.key = key
    
    def users(self):
        """
        Returns the number of users (entries not starting with # or &) in the
        table's ``key`` column.
        """
                  
        db = self.db.connect()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM "+self.name+
                " WHERE "+self.key+" LIKE \"[^#&]%;")
        result = int(cur.fetchone()[0])
        db.close()
        return result
    
    def channels(self):
        """
        Returns the number of users (entries starting with # or &) in the
        table's ``key`` column.
        """
        
        db = self.db.connect()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM "+self.name+
                " WHERE "+self.key+" LIKE \"[#&]%;")
        result = int(cur.fetchone()[0])
        db.close()
        return result

    def size(self):
        """Returns the total number of rows in the table."""
        db = self.db.connect()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM "+self.name+";")
        result = int(cur.fetchone()[0])
        db.close()
        return result
    
    def _make_where_statement(self, key, row):
        where = []
        for k in key:
            where.append(k+' = %s')
        return ' AND '.join(where) + ';'
        
    def _get_one(self, row, value, key):
        """Implements get() for where values is a single string"""
        db = self.db.connect()
        cur = db.cursor()
        where = self._make_where_statement(key, row)
        cur.execute(
            'SELECT ' + value + ' FROM ' + self.name + ' WHERE ' + where, row)
        row = cur.fetchone()[0]
        if row is None:
            db.close()
            raise KeyError(row+' not in database')
        db.close()
        
        return row
    
    def _get_many(self, row, values, key):
        """Implements get() for where values is iterable"""
        db = self.db.connect()
        cur = db.cursor()
        values = ', '.join(values)
        where = self._make_where_statement(key, row)
        cur.execute(
            'SELECT ' + values + ' FROM ' + self.name + ' WHERE ' + where, row)
        row = cur.fetchone()
        
        if row is None:
            db.close()
            raise KeyError(row+' not in database')
        db.close()
        
        return row

    def get(self, row, columns, key=None):
        """
        Retrieve the value(s) in one or more ``columns`` in the row where the
        ``key`` column(s) match the value(s) given in ``row``. This is basically
        equivalent to executing ``SELECT <columns> FROM <self> WHERE <key> =
        <row>``.
        
        The ``key`` can be either the name of one column as a string, or a tuple
        of the names of multiple columns. ``row`` is the value or values of this
        column or columns for which data will be retrieved. If multiple columns
        are being used, the order in which the columns are presented should match
        between ``row`` and ``key``. A ``KeyError`` will be raised if no have
        values matching ``row`` in ``key``. If ``key`` is not passed, it will
        default to the table's primary key.
        
        ``columns`` can either be a single column name, or a tuple of column
        names. If one name is passed, a single string will be returned. If a
        tuple of names is passed, the return value will be a tuple in the same
        order.
        """#TODO this documentation could be better.
        if not key:
            key = self.key
        print self.key
        if not (isinstance(row, basestring) and isinstance(key, basestring)):
            if not len(row) == len(key):
                print row, key
                raise ValueError, 'Unequal number of key and row columns.'
        
        if isinstance(columns, basestring):
            return self._get_one(row, columns, key)
        elif isinstance(columns, Iterable):
            return self._get_many(row, columns, key)
    
    def update(self, key, values):
        """
        Update the given values for ``key``. ``value`` must be a dict which
        maps the names of the columns to be updated to their new values.
        """
        db = self.db.connect()
        cur = db.cursor()
        where = self._make_where_statement(self.key, row)
        cur.execute('SELECT * FROM '+self.name+' WHERE ' + where, row)
        if not cur.fetchone():
            cols = self.key
            vals = '"'+key+'"'
            for k in values:
                cols = cols + ', ' + k
                vals = vals + ', "' + values[k] + '"'
            command = 'INSERT INTO '+self.name+' ('+cols+') VALUES (' + \
                      vals + ');'
        else:
            command = 'UPDATE '+self.name+' SET '
            for k in values:
                command = command + k + '="' + values[k] + '", '
            command = command[:-2]+' WHERE '+self.key+' = "' + key + '";'
        cur.execute(command)
        db.commit()
        db.close()
    
    def delete(self, key):
        """Deletes the row for *key* in the database, removing its values in all
        rows."""
        db = self.db.connect()
        cur = db.cursor()
        
        cur.execute('SELECT * FROM '+self.name+' WHERE '+self.key+' = "'+key+'";')
        if not cur.fetchone():
            db.close()
            raise KeyError(key+' not in database')
        
        cur.execute('DELETE FROM '+self.name+' WHERE '+self.key+' = "'+key+'";')
        db.commit()
        db.close()
    
    def keys(self):
        """
        Return an iterator over the keys and values in the table.

        In a for each loop, you can use ``for key in table:``, where key will be
        the value of the key column (e.g. a channel or nick), and table is the
        Table. This may be deprecated in future versions.
        """
        db = self.db.connect()
        cur = db.cursor()
        
        cur.execute('SELECT '+self.key+' FROM '+self.name+'')
        result = cur.fetchall()
        db.close()
        return result
    
    def __iter__(self):
        return self.keys()
    
    def contains(self, key):
        """
        Return ``True`` if this table has a row where the key value is equal to
        ``key``, else ``False``.
        
        ``key in db`` will also work, where db is your SettingsDB object.
        """
        db = self.db.connect()
        cur = db.cursor()
        
        #Let's immitate actual dict behavior
        cur.execute('SELECT * FROM '+self.name+' WHERE '+self.key+' = "'+key+'";')
        result = cur.fetchone()
        db.close()
        if result: return True
        else: return False
    
    def __contains__(self, item):
        return self.contains(item)
            
    def hascolumn(self, column):
        """
        Each Table contains a cached list of its columns. ``hascolumn(column)``
        checks this list, and returns True if it contains ``column``. If
        ``column`` is an iterable, this returns true if all of the values in 
        ``column`` are in the column cache. Note that this will not check the
        database itself; it's meant for speed, not accuracy. However, unless
        you have multiple bots using the same database, or are adding columns
        while the bot is running, you are unlikely to encounter errors.
        """
        if isinstance(column, basestring):
            return column in self.columns
        elif isinstance(column, Iterable):
            has = True
            for col in column:
                has = col in self.columns and has
            return has
        
    def addcolumns(self, columns):
        """
        Insert a new column into the table, and add it to the column cache.
        This is the preferred way to add new columns to the database.
        """
        cmd = 'ALTER TABLE '+self.name+' ADD ( '
        for column in columns:
            if isinstance(column, tuple): cmd = cmd + column[0]+' '+column[1]+', '
            else: cmd = cmd + column + ' text, '
        cmd = cmd[:-2]+' );'
        db = self.db.connect()
        cur = db.cursor()
        
        cur.execute(cmd)
        db.commit()
        db.close()
        #Why a second loop? because I don't want clomuns to be added to self.columns if executing the SQL command fails
        for column in columns:
            self.columns.add(column)

def write_config(config):
    """
    Interactively create configuration options and add the attributes to
    the Config object ``config``.
    """
    chunk = """\
    # ------------------  USER DATABASE CONFIGURATION  ------------------
    # The user database was not set up at install. Please consult the documentation,
    # or run the configuration utility if you wish to use it."""
    c = config.option("Would you like to set up a settings database now")
        
    if not c:
        return chunk
        
    config.interactive_add('userdb_type',
        'What type of database would you like to use? (mysql/sqlite)', 'mysql')
        
    if config.userdb_type == 'sqlite':
        config.interactive_add('userdb_file',"""Location of sqlite file""")
        chunk = """\
        # ------------------  USER DATABASE CONFIGURATION  ------------------
        # Below is the user database configuration. If you want to keep the same
        # user database type, it's fine to change this. If you want to change types,
        # you should run the configuration utility (or at least consult the 
        # SettingsDB documentation page).
    
        userdb_type = 'sqlite'
        userdb_data = '%s'""" % userdb_file
        
    elif config.userdb_type == 'mysql':
        config.interactive_add('userdb_host', "Enter the MySQL hostname", 'localhost')
        config.interactive_add('userdb_user', "Enter the MySQL username")
        config.interactive_add('userdb_pass', "Enter the user's password", 'none')
        config.interactive_add('userdb_name', "Enter the name of the database to use")
            
        chunk = """\
    # ------------------  USER DATABASE CONFIGURATION  ------------------
    # Below is the user database configuration. If you want to keep the same
    # user database type, it's fine to change this. If you want to change types,
    # you should run the configuration utility (or at least consult the 
    # SettingsDB documentation page).

    userdb_type = '%s'
    userdb_host = '%s'
    userdb_user = '%s'
    userdb_pass = '%s'
    userdb_name = '%s'""" % (config.userdb_type, config.userdb_host, config.userdb_user,
                             config.userdb_pass, config.userdb_name)
    else:
        print "This isn't currently supported. Aborting."

    return chunk

