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
        if not hasattr(config, 'userdb_type'):
            print 'No user settings database specified. Ignoring.'
            return
        self.type = config.userdb_type.lower()
        self.columns = {}
        
        if self.type == 'mysql':
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
        if self.type == 'mysql':
            import MySQLdb, MySQLdb.cursors 
            db = MySQLdb.connect(host=self.__host,
                     user=self.__user,
                     passwd=self.__passwd,
                     db=self.__dbname)
            cur = MySQLdb.cursors.DictCursor(db)
            cur.execute('SELECT * FROM locales WHERE nick LIKE "'+key+'";')
            row = cur.fetchone()
            db.close()
            return row
        else:
            return None
            
    def __setitem__(self, key, value):
        pass
        
    def __delitem__(self, key):
        pass
    
    def __iter__(self):
        pass
    
    def __contains__(self, item):
        pass

if __name__ == '__main__':
    import MySQLdb
    
