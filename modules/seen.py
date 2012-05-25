#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
seen.py - Jenni Seen Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import time
import threading

# from http://parand.com/say/index.php/2007/07/13/simple-multi-dimensional-dictionaries-in-python/
# A simple class to make mutli dimensional dict easy to use
class Ddict(dict):
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)

class DBSync(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._finished = threading.Event()
        self._interval = 20.0
    started = False
    def set_jenni(self, jenni):
        self.jenni = jenni
    def run(self):
        self.started = True
        while True:
            sync(self.jenni)
            self._finished.wait(self._interval)
def sync(jenni):
    global seen_dict
    if not jenni.settings.hascolumn("lastseentimestamp") and not jenni.settings.hascolumn("lastseenmessage") and not jenni.settings.hascolumn("lastseenchannel"):
        try:
            jenni.settings.addcolumns({"lastseentimestamp", "lastseenmessage", "lastseenchannel"})
        except:
            pass
    for nick in seen_dict:
        jenni.settings[nick] = {'lastseentimestamp': str(seen_dict[nick]['timestamp']),'lastseenmessage': seen_dict[nick]['message'],'lastseenchannel': seen_dict[nick]['channel']}
    seen_dict=Ddict(dict)


seen_dict = Ddict(dict)
sync_thread = DBSync()
def seen(jenni, input):
    start_thread(jenni)
    if not input.group(2):
        jenni.say(".seen <nick> - Reports when <nick> was last seen.")
        return
    nick = input.group(2)
    sync(jenni)
    if jenni.settings.hascolumn('lastseenmessage') and nick in jenni.settings:
        timestamp = float(jenni.settings[nick]['lastseentimestamp'])
        channel = jenni.settings[nick]['lastseenchannel']
        message = jenni.settings[nick]['lastseenmessage']
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(timestamp))

        msg = "I last saw %s at %s on %s, saying %s" % (nick, timestamp, channel, message)
        jenni.say(str(input.nick) + ': ' + msg)
    else:
        jenni.say("Sorry, I haven't seen %s around." % nick)
seen.rule = (['seen'], r'(\S+)')

def note(jenni, input):
    global seen_dict
    start_thread(jenni)
    if input.sender.startswith('#'):
        seen_dict[input.nick]['timestamp'] = time.time()
        seen_dict[input.nick]['channel'] = input.sender
        seen_dict[input.nick]['message'] = input

note.rule = r'(.*)'
note.priority = 'low'

def start_thread(jenni):
    if not sync_thread.started:
        sync_thread.set_jenni(jenni)
        sync_thread.start()



if __name__ == '__main__':
    print __doc__.strip()
