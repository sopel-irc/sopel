#!/usr/bin/env python
"""
users.py - Abstracted per-user settings database for Jenni
Copyright 2012, Edward D. Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/

To use this DB
"""

class SettingsDB(object):
    def __init__(self, config):
        self.columns = set()
        if not hasattr(config, 'userdb_type'):
            print 'No user settings database specified. Ignoring.'
            return
        self.type = config.userdb_type.lower()
        
        
        if self.type == 'dict':
            self.db = config.userdb_data
        elif self.type == 'mysql':
            self.mySQL(config)
        elif self.type == 'sqlite':
            self.sqlite(config)
        else:
            print 'User settings database type is not supported. Ignoring.'
            return
            
            
    def mySQL(self, config):
        import MySQLdb
        try:
                self.__host = config.userdb_host
                self.__user = config.userdb_user
                self.__passwd = config.userdb_pass
                self.__dbname = config.userdb_name
        except AttributeError as e:
                print 'Some options are missing for your MySQL user settings DB.'
                print 'The database will not be set up.'
                return
            
        try:
            db = MySQLdb.connect(host=self.__host,
                         user=self.__user,
                         passwd=self.__passwd,
                         db=self.__dbname)
        except:
            print 'Error: Unable to connect to user settings DB.'
            return
        cur = db.cursor()
        cur.execute("SHOW tables like \"locales\";")
        if not cur.fetchone():
            print 'Error: Settings database does not have a "locales" table'
            return
            
            
        cur.execute("SHOW columns FROM locales;")
        for row in cur.fetchall():
            self.columns.add(row[0])
        db.close()

    def sqlite(self):
        print 'sqlite is not yet supported for user settings.'
        return
            
    def __len__(self):
        if self.type == 'dict':
            return len(self.db)
        if self.type == 'mysql':
            import MySQLdb
            
            db = MySQLdb.connect(host=self.__host,
                     user=self.__user,
                     passwd=self.__passwd,
                     db=self.__dbname)
            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM locales;")
            result = int(cur.fetchone()[0])
            db.close()
            return result
        else:
            return 0
            
    def __getitem__(self, key):
        if self.type == 'dict':
            return self.db[key]
        elif self.type == 'mysql':
            import MySQLdb, MySQLdb.cursors 
            db = MySQLdb.connect(host=self.__host,
                     user=self.__user,
                     passwd=self.__passwd,
                     db=self.__dbname)
            cur = MySQLdb.cursors.DictCursor(db)
            cur.execute('SELECT * FROM locales WHERE nick = "'+key+'";')
            row = cur.fetchone()
            
            if not row:
                db.close()
                raise KeyError(key+' not in database')
            db.close()
            
            return row
        else:
            return None
    
    #value is a dict {'columnName': 'value'} for each updated column        
    def __setitem__(self, key, value):
        if self.type == 'dict':
            for k, v in value:
                self.db[key][k] = v
        elif self.type == 'mysql':
            import MySQLdb, MySQLdb.cursors 
            db = MySQLdb.connect(host=self.__host,
                     user=self.__user,
                     passwd=self.__passwd,
                     db=self.__dbname)
            cur = MySQLdb.cursors.DictCursor(db)
            cur.execute('SELECT * FROM locales WHERE nick = "'+key+'";')
            if not cur.fetchone():
                cols = 'nick'
                vals = '"'+key+'"'
                for k in value:
                    cols = cols + ', ' + k
                    vals = vals + ', "' + value[k] + '"'
                command = 'INSERT INTO locales ('+cols+') VALUES (' + \
                          vals + ');'
            else:
                command = 'UPDATE locales SET '
                for k in value:
                    command = command + k + '="' + value[k] + '", '
                command = command[:-2]+' WHERE Nick = "' + key + '";'
            cur.execute(command)
            db.close()
        else: raise KeyError('User database not initialized.')
        
    def __delitem__(self, key):
        if self.type == 'dict':
            del self.db[key]
        elif self.type == 'mysql':
            import MySQLdb
            db = MySQLdb.connect(host=self.__host,
                     user=self.__user,
                     passwd=self.__passwd,
                     db=self.__dbname)
            cur = db.cursor()
            
            cur.execute('SELECT * FROM locales WHERE nick = "'+key+'";')
            if not cur.fetchone():
                db.close()
                raise KeyError(key+' not in database')
            
            cur.execute('DELETE FROM locales WHERE nick = "'+key+'";')
            db.close()
        else: raise KeyError('User database not initialized.')
    
    def __iter__(self):
        if self.type == 'dict':
            return iter(self.db)
        elif self.type == 'mysql':
            import MySQLdb
            db = MySQLdb.connect(host=self.__host,
                     user=self.__user,
                     passwd=self.__passwd,
                     db=self.__dbname)
            cur = db.cursor()
            
            cur.execute('SELECT * FROM locales')
            #TODO
            db.close()
        else: raise KeyError('User database not initialized.')
    
    def __contains__(self, item):
        if self.type == 'dict':
            return item in self.db
        elif self.type == 'mysql':
            import MySQLdb
            db = MySQLdb.connect(host=self.__host,
                     user=self.__user,
                     passwd=self.__passwd,
                     db=self.__dbname)
            cur = db.cursor()
            
            #Let's immitate actual dict behavior
            cur.execute('SELECT * FROM locales WHERE nick = "'+item+'";')
            result = cur.fetchone()
            db.close()
            if result: return True
            else: return False
            
        else: return False
            
    def hascolumn(self, column):
        return column in self.columns
