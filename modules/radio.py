#!/usr/bin/env python
"""
radio.py - ShoutCAST radio Module
Copyright 2012, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from time import sleep
import web

radioURL = 'http://stream.dftba.net:8000/%s?sid=1'
checkSongs = False
current_song = ''

def currentSong(willie, trigger):
    try:
        song = web.get(radioURL % 'currentsong')
    except Exception as e:
        Willie.say('The radio is not responding to the song request.')
        willie.debug('radio', 'Exception while trying to get current song: %s' % e, 'warning')
    if song:
        willie.say('Now playing: '+song)
    else:
        Willie.say('The radio is currently offline.')

def nextSong(willie, trigger):
    try:
        song = web.get(radioURL % 'nextsong')
    except Exception as e:
        Willie.say('The radio is not responding to the song request.')
        willie.debug('radio', 'Exception while trying to get next song: %s' % e, 'warning')
    if song:
        willie.say('Next up: '+song)
    else:
        willie.say('No songs are queued up.')

def radio(willie, trigger):
    """ Radio functions, valid parameters: on, off, song, now, next. """
    global checkSongs, current_song
    args = trigger.group(2).split(' ')
    if args[0] == 'on':
        if not trigger.isop:
            return;
        if checkSongs == True:
            willie.reply('Radio data checking is already on.')
            return
        checkSongs = True
        while checkSongs:
            last = current_song
            try:
                current_song = web.get(radioURL % 'currentsong')
                nextsong = web.get(radioURL % 'nextsong')
            except Exception as e:
                willie.debug('radio', 'Exception while trying to get periodic radio data: %s' % e, 'warning')
                Willie.say('The radio is not responding to the song request.')
                willie.say('Turning off radio data checking.')
                checkSongs = False
                break
            if not current_song == last:
                if not current_song:
                    csong = 'The radio is currently offline.'
                else:
                    csong = 'Now Playing: '+current_song
                if nextsong and current_song:
                    willie.say(csong+' | Coming Up: '+nextsong)
                else:
                    willie.say(csong)
            sleep(5)
    elif args[0] == 'off':
        if not trigger.isop:
            return;
        if checkSongs == False:
            willie.reply('Radio data checking is already off.')
            return
        checkSongs = False
        current_song = ''
        willie.reply('Turning off radio data checking.')
    elif args[0] == 'song' or args[0] == 'now':
        currentSong(willie, trigger)
    elif args[0] == 'next':
        nextSong(willie, trigger)
radio.commands = ['radio']
radio.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
