#!/usr/bin/env python
"""
*Availability: 3.x+*

This class defines an interface for a semi-arbitrary database type. It is meant
to allow module writers to operate without regard to how the end user has
decided to set up the database.

The SettingsDB object itself is essentially a dict which maps channel and
user names to another dict, which maps a column name to some value. As such,
the most frequent use will be in the form `jenni.settings[user][column]`,
where table and user are strings.

A number of methods from the dict object are not implemented here. If the
method is not listed below, it has not yet been written. This may change in
future versions.
"""
"""
Copyright 2012, Edward D. Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/

To use this DB
"""

from collections import Iterable
from tools import deprecated

mysql = False
sqlite = False
try:
    import MySQLdb
    import MySQLdb.cursors
    mysql = True
except ImportError: pass

#TODO
try:
    pass
    #sqlite = True
except ImportError: pass

tablename = 'locales'

class SettingsDB(object):
    """
    Return a SettingsDB object configured with the options in the given Config
    object. The exact settgins used vary depending on the type of database
    chosen to back the SettingsDB, as determined by the ``userdb_type``
    attribute of *config*.
    
    Currently, two values for ``userdb_type`` are supported: ``dict`` and
    ``mysql``. Support for ``sqlite`` is planned.
    
    With the ``dict`` type, only one other attribute is used - ``userdb_data``.
    This attribute is a native Python dict, usually written by hand in the
    jenni config file. As such, the ``dict`` type is unique in that changes to
    it are nto persistant across restarts of the bot, or multiple instances of
    the bot.
    """
    #Note, #Python recommends using dictcursor, so you can select x in y
    #Also, PEP8 says not to import in the middle of your code. That answers that.
    def __init__(self, config):
        self.columns = set()
        if not hasattr(config, 'userdb_type'):
            print 'No user settings database specified. Ignoring.'
            return
        self.type = config.userdb_type.lower()
        
        
        if self.type == 'dict':
            self.db = config.userdb_data
        elif self.type == 'mysql' and mysql:
            self._mySQL(config)
        elif self.type == 'sqlite' and sqlite:
            self._sqlite(config)
        else:
            print 'User settings database type is not supported. You may be missing the module for it. Ignoring.'
            return
            
            
    def _mySQL(self, config):
        import MySQLdb
        try:
                self._host = config.userdb_host
                self._user = config.userdb_user
                self._passwd = config.userdb_pass
                self._dbname = config.userdb_name
        except AttributeError as e:
                print 'Some options are missing for your MySQL user settings DB.'
                print 'The database will not be set up.'
                return
            
        try:
            db = MySQLdb.connect(host=self._host,
                         user=self._user,
                         passwd=self._passwd,
                         db=self._dbname)
        except:
            print 'Error: Unable to connect to user settings DB.'
            return
        cur = db.cursor()
        #TODO this throws a warning. Do something about that.
        cur.execute("CREATE TABLE IF NOT EXISTS "+tablename+" ( name text );")
            
            
        cur.execute("SHOW columns FROM "+tablename+";")
        for row in cur.fetchall():
            self.columns.add(row[0])
        db.close()

    def _sqlite(self):
        print 'sqlite is not yet supported for user settings.'
        return
    
    def users(self):
        """
        Returns the number of users (entries not starting with # or &).
        If the database is uninitialized, returns 0.
        """
        
        if self.type == 'mysql':
            import MySQLdb
            
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM "+tablename+
                    " WHERE name LIKE \"[^#&]%;")
            result = int(cur.fetchone()[0])
            db.close()
            return result
        else:
            return 0
    
    def channels(self):
        """
        Returns the number of users (entries starting with # or &).
        If the database is uninitialized, returns 0.
        """
        
        if self.type == 'mysql':
            import MySQLdb
            
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM "+tablename+
                    " WHERE name LIKE \"[#&]%;")
            result = int(cur.fetchone()[0])
            db.close()
            return result
        else:
            return 0

    def size(self):
        """Returns the total number of users and channels in the database."""
        if self.type == 'mysql':
            
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM "+tablename+";")
            result = int(cur.fetchone()[0])
            db.close()
            return result
        else:
            return 0

    @deprecated
    def __len__(self):
        return self.size()
        
    def _get_one(self, key, value):
        """Implements get() for where values is a single string"""
        if self.type == 'dict':
            return self.db[key]
        elif self.type == 'mysql':
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = MySQLdb.cursors.DictCursor(db)
            cur.execute(
                'SELECT %s FROM '+tablename+' WHERE name = "%s";', (value, key))
            row = cur.fetchone()
            
            if not row:
                db.close()
                raise KeyError(key+' not in database')
            db.close()
            
            return row[value]
        else:
            #TODO This should be a different kind of error.
            raise KeyError('User database not initialized.')
    
    def _get_many(self, key, values):
        """Implements get() for where values is iterable"""
        if self.type == 'dict':
            return self.db[key]
        elif self.type == 'mysql':
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = MySQLdb.cursors.DictCursor(db)
            cur.execute(
                'SELECT %s FROM '+tablename+' WHERE name = "%s";', (value, key))
            row = cur.fetchone()
            
            if not row:
                db.close()
                raise KeyError(key+' not in database')
            db.close()
            
            return row[value]
        else:
            #TODO This should be a different kind of error.
            raise KeyError('User database not initialized.')

    def get(self, key, values):
        """
        Retrieve one or more ``values`` for a ``key``. 
        
        ``values`` can be either a single string or an iterable of strings. If
        it is a single string, a single string will be returned. If it is an
        iterable, a dict will be returned which maps each of the keys in 
        ``values`` to its corresponding data."""
        if isinstance(values, Iterable):
            return self._get_many(key, values)
        else:
            return self._get_one(key, values)
    
    @deprecated
    def __getitem__(self, key):
        if self.type == 'dict':
            return self.db[key]
        elif self.type == 'mysql':
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = MySQLdb.cursors.DictCursor(db)
            cur.execute('SELECT * FROM '+tablename+' WHERE name = "'+key+'";')
            row = cur.fetchone()
            
            if not row:
                db.close()
                raise KeyError(key+' not in database')
            db.close()
            
            return row
        else:
            raise KeyError('User database not initialized.')
    
    def update(self, nick, values):
        """
        Update the given values for ``nick``. ``value`` must be a dict which
        maps the names of the columns to be updated to their new values.
        """
        if self.type == 'dict':
            for k, v in values:
                self.db[key][k] = v
        elif self.type == 'mysql':
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = MySQLdb.cursors.DictCursor(db)
            cur.execute('SELECT * FROM '+tablename+' WHERE name = "'+key+'";')
            if not cur.fetchone():
                cols = 'name'
                vals = '"'+key+'"'
                for k in values:
                    cols = cols + ', ' + k
                    vals = vals + ', "' + values[k] + '"'
                command = 'INSERT INTO '+tablename+' ('+cols+') VALUES (' + \
                          vals + ');'
            else:
                command = 'UPDATE '+tablename+' SET '
                for k in values:
                    command = command + k + '="' + values[k] + '", '
                command = command[:-2]+' WHERE name = "' + key + '";'
            cur.execute(command)
            db.commit()
            db.close()
        else: raise KeyError('User database not initialized.')
        
    @deprecated    
    def __setitem__(self, key, value):
        self.update(key, value)
    
    def delete(self, key):
        """Deletes the row for *key* in the database, removing its values in all
        rows."""
        if self.type == 'dict':
            del self.db[key]
        elif self.type == 'mysql':
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = db.cursor()
            
            cur.execute('SELECT * FROM '+tablename+' WHERE name = "'+key+'";')
            if not cur.fetchone():
                db.close()
                raise KeyError(key+' not in database')
            
            cur.execute('DELETE FROM '+tablename+' WHERE name = "'+key+'";')
            db.commit()
            db.close()
        else: raise KeyError('User database not initialized.')
        
    @deprecated
    def __delitem__(self, key):
        self.delete(key)
    
    def keys(self):
        """
        Return an iterator over the nicks and channels in the database.

        In a for each loop, you can use ``for key in db:``, where key will be a
        channel or nick, and db is your SettingsDB. This may be deprecated in
        future versions.
        """
        if self.type == 'dict':
            return iter(self.db)
        elif self.type == 'mysql':
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = db.cursor()
            
            cur.execute('SELECT name FROM '+tablename+'')
            result = cur.fetchall()
            db.close()
            return result
        else: raise KeyError('User database not initialized.')
    
    def __iter__(self):
        return self.keys()
    
    def contains(self, key):
        """
        Return ``True`` if d has a key *key*, else ``False``.
        
        ``key in db`` will also work, where db is your SettingsDB object."""
        if self.type == 'dict':
            return item in self.db
        elif self.type == 'mysql':
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
            cur = db.cursor()
            
            #Let's immitate actual dict behavior
            cur.execute('SELECT * FROM '+tablename+' WHERE name = "'+item+'";')
            result = cur.fetchone()
            db.close()
            if result: return True
            else: return False
            
        else: return False
    
    def __contains__(self, item):
        return self.contains(item)
            
    def hascolumn(self, column):
        """
        The SettingsDB contains a cached list of its columns. ``hascolumn(column)``
        checks this list, and returns True if it contains ``column``. If
        ``column`` is an iterable, this returns true if all of the values in 
        ``column`` are in the column cache. Note that this will not check the
        database itself; it's meant for speed, not accuracy. However, unless
        you have multiple bots using the same database, or are adding columns
        while the bot is running, you are unlikely to encounter errors.
        """
        if isinstance(column, Iterable):
            has = True
            for column in columns:
                has = column in self.columns and has
            return has
        else:
            return column in self.columns
        
    @deprecated
    def hascolumns(self, columns):
        """
        Returns True if ``hascolumn`` evaluates to true for each column in the
        iterable ``columns``.
        """
        has = True
        for column in columns:
            has = column in self.columns and has
        return has
        
    def addcolumns(self, columns):
        """
        Insert a new column into the table, and add it to the column cache.
        This is the preferred way to add new columns to the database.
        """
        cmd = 'ALTER TABLE '+tablename+' ADD ( '
        for column in columns:
            if isinstance(column, tuple): cmd = cmd + column[0]+' '+column[1]+', '
            else: cmd = cmd + column + ' text, '
        cmd = cmd[:-2]+' );'
        
        if self.type == 'dict':
            pass #TODO this and sqlite
        elif self.type == 'mysql':
            db = MySQLdb.connect(host=self._host,
                     user=self._user,
                     passwd=self._passwd,
                     db=self._dbname)
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
        
        config.add('userdb_type',
            'What type of database would you like to use? [%s]', 'mysql')
        
        if config.userdb_type == 'dict':
            config.add('userdb_data',"""\
            Enter the data now, all on one line. If you give up, close your
            brackets and hit enter. If you'd rather edit the file later, hit
            enter now.""", """\
            {
                 'someuser':    {'tz': 'America/New_York'}
                 'anotheruser': {'icao': 'KCMH'}
                 'onemoreuser': {'tz': 'Europe/Berlin', 'icao': 'EDDT'}""")
            chunk = """\
    # ------------------  USER DATABASE CONFIGURATION  ------------------
    # Below is the user database configuration. If you want to keep the same
    # user database type, it's fine to change this. If you want to change types,
    # you should run the configuration utility (or at least consult the 
    # SettingsDB documentation page).
    
    userdb_type = 'dict'
    userdb_data = """+str(config.userdb_data)
        
        elif config.userdb_type == 'mysql':
            config.add('userdb_host', "Enter the MySQL hostname", 'localhost')
            config.add('userdb_user', "Enter the MySQL username")
            config.add('userdb_pass', "Enter the user's password", 'none')
            config.add('userdb_name', "Enter the name of the database to use")
            
            chunk = """\
    # ------------------  USER DATABASE CONFIGURATION  ------------------
    # Below is the user database configuration. If you want to keep the same
    # user database type, it's fine to change this. If you want to change types,
    # you should run the configuration utility (or at least consult the 
    # SettingsDB documentation page).

    userdb_type = '%s'
    userdb_user = '%s'
    userdb_pass = '%s'
    userdb_name = '%s'""" % (config.userdb_type, config.userdb_user,
                             config.userdb_pass, config.userdb_name)
        
        elif config.userdb_type == 'sqlite':
            config.say("This isn't currently supported. Aborting.")
        else:
            config.say("This isn't currently supported. Aborting.")
        
        return chunk

