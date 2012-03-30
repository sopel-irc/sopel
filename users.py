#!/usr/bin/env python
"""
users.py - Abstracted per-user settings database for Jenni
Copyright 2012, Edward D. Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/

To use this DB
"""
#Is there a way to only import the DB module that's actually going to be used?
import MySQLdb

class SettingsDB(object):
    def __init__(self, config):
        if not hasattr(config, 'userdb_type'):
            print 'No user settings database specified. Ignoring.'
            return
        self.userdb_type = config.userdb_type
        
        if self.userdb_type.lower() is 'mysql':
            try:
                self.host = config.userdb_host
                self.user = config.userdb_user
                self.passwd = config.userdb_pass
                self.dbname = config.userdb_name
            except AttributeError as e:
                print 'Some options are missing for your MySQL user settings DB.'
                print 'The database will not be set up.'
                return
            
            try:
                self.db = MySQLdb.connect(host=self.host,
                             user=self.user,
                             passwd=self.passwd,
                             db=self.dbname)
                #TODO check that the DB is valid.
                self.db.close()
            except:
                print 'Error: Unable to connect to user settings DB.'
                return
            
        if userdb_type.lower() is 'sqlite':
            print 'sqlite is not yet supported for user settings.'
            return
        else:
            print 'User settings database type is not supported. Ignoring.'
            return


    def connect(self):
        if self.userdb_type.lower() is 'mysql':
            self.db = MySQLdb.connect(host=self.host,
                             user=self.user,
                             passwd=self.passwd,
                             db=self.dbname)
        else:
            return #TODO


if __name__ == '__main__':
    print "Coming soon..."
