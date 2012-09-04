#!/usr/bin/env python
"""
radio.py - ShoutCAST radio Module
Copyright 2012, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from time import sleep
import urllib2

radioURL = 'http://stream.dftba.net:8000/%s?sid=1'
checkSongs = False
current_song = ''

def PLAINreq(data):
    try:
        return urllib2.urlopen(radioURL % data).readlines()[0]
    except IndexError:
        return 'Not available'
    except Exception as e:
        if e is URLError:
            return 'Radio offline'

def currentSong(willie, trigger):
    """.cursong - Returns the song currently playing."""
    willie.say('Now playing: '+PLAINreq('currentsong'))
currentSong.commands = ['cursong']
currentSong.priority = 'medium'

def nextSong(willie, trigger):
    """.nextsong - Returns the song queued up next."""
    willie.say('Next up: '+PLAINreq('nextsong'))
nextSong.commands = ['nextsong']
nextSong.priority = 'medium'

def radio(willie, trigger):
    global checkSongs, current_song
    if not trigger.isop:
        return
    else:
        if trigger.group(2) == 'on':
            if checkSongs == True:
                willie.reply('Radio data checking is already on.')
                return
            checkSongs = True
            while checkSongs:
                last = current_song
                current_song = PLAINreq('currentsong')
                nextsong = PLAINreq('nextsong')
                if not current_song == last:
                    if current_song == 'Not available':
                        csong = 'Radio offline'
                    else:
                        csong = current_song
                    if nextsong != 'Not available':
                        willie.say('Now Playing: '+csong+' | Coming Up: '+nextsong)
                    else:
                        willie.say('Now Playing: '+csong)
                sleep(5)
        elif trigger.group(2) == 'off':
            if checkSongs == False:
                willie.reply('Radio data checking is already off.')
                return
            checkSongs = False
            current_song = ''
            willie.reply('Turning off radio data checking.')
radio.commands = ['radio']
radio.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
