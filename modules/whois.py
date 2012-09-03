#!/usr/bin/env python
# coding=utf-8
"""
whois.py - Retrieve WHOIS information on a user and show to the channel.
Author: Edward D. Powell http://embolalia.net

Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""
from time import sleep
import re
whois, got318 = False, False
nick, host, rl, chans, idle, signon = None, None, None, None, None, None

def sendwhois(willie, trigger):
    global whois, got318, nick, host, rl, chans, idle, signon
    try:
        whois = True
        willie.write(['WHOIS'], trigger.group(2).strip()) #A whois needs a 2nd parameter to get the signon time... name+" "+name doesn't work.

        while not got318: #Wait until event 318 (End of /WHOIS list.)
            sleep(0.5)
        if nick is None:
            willie.say('[WHOIS] No such user')
            whois, got318 = False, False
            nick, host, rl, chans, idle, signon = None, None, None, None, None, None
            return
        msg1 = '[WHOIS] Nick: ' + str(nick) + ' Host: ' + str(host) + \
               ' Real name: ' + str(rl)

        #hide channels that are +s (prefixed with a ?)
        if chans is not None:
            channels = chans.split(' ')
            for chan in channels:
                if len(chan):
                    if chan[0] == "?":
                        channels.remove(chan)
            chans = ' '.join(channels)
            msg2 = str(nick) + ' is on '+str(len(channels)-1)+' channels: ' + str(chans)
        else:
            msg2 = str(nick) + ' is not in any channel!'

        willie.say(msg1)
        willie.say(msg2)
    finally:
        #reset variables.
        whois, got318 = False, False
        nick, host, rl, chans, idle, signon = None, None, None, None, None, None
sendwhois.commands = ['whois']

def whois311(willie, trigger):
    global nick, host, rl, whois
    if whois:
        raw = re.match('\S+ 311 \S+ (\S+) (\S+) (\S+) (\S+) :(.*)', \
                        willie.raw)
        nick = raw.group(1)
        host = raw.group(2) + '@' + raw.group(3)
        rl = raw.group(5)

whois311.event = '311'
whois311.rule = '.*'

def whois319(willie, trigger):
    if whois:
        global chans
        chans = trigger.group(1)
whois319.event = '319'
whois319.rule = '(.*)'

def whois318(willie, trigger):
    if whois:
        global got318
        got318 = True
whois318.event = '318'
whois318.rule = '.*'
