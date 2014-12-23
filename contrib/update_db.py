#!/usr/bin/env python
# coding=utf8
"""update_db.py - A basic migration script for 3.x/4.x databases to 5.0.

Usage: ./update_db.py /path/to/config

Note that it takes the config, rather than the db. Currently, this only
supports text fields, since that's all the stock modules used. It migrates in
place, leaving old tables there, but you should still be sure to back up
everything first to be safe."""

import sqlite3
import sys

import willie
import willie.db
import willie.config


def main():
    if willie.__version__.split('.', 1)[0] != '5':
        print('Must have Willie 5 installed to run migration script.')
        return
    if len(sys.argv) != 2:
        print('Usage: ./update_db.py /path/to/config')
    config = willie.config.Config(sys.argv[1])
    filename = config.db.userdb_file
    if not filename:
        filename = os.path.splitext(config.filename)[0] + '.db'
    elif not config.core.db_filename:
        print('Filename is only configured with old setting. Make sure you '
              'set the db_filename setting in [core].')
    print('Migrating db file {}'.format(filename))
    new_db = willie.db.WillieDB(config)
    conn = sqlite3.connect(new_db.filename)
    cur = conn.cursor()
    table_info = cur.execute('PRAGMA table_info(preferences)').fetchall()
    for column in table_info:
        old_name = column[1]
        new_name = old_name if old_name != 'tz' else 'timezone'
        if old_name == 'name':
            continue
        if column[2] != 'text':
            msg = "Can't migrate non-text field {}. Please do so manually"
            print(msg.format(old_name))
            continue
        print('Migrating column {}'.format(old_name))

        values = cur.execute(
            'SELECT name, {} FROM preferences WHERE {} NOT NULL'
            .format(old_name, old_name)).fetchall()
        for value in values:
            if value[0][0] in '+%@&~#&':
                new_db.set_channel_value(value[0], new_name, value[1])
            else:
                new_db.set_nick_value(value[0], new_name, value[1])

if __name__ == '__main__':
    main()
