#!/usr/bin/env python
"""
radio.py - ShoutCAST radio Module
Copyright 2012, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from time import sleep
from xml.dom.minidom import parseString
import web, xml.dom.minidom

def configure(config):
    chunk = ''
    if config.option('Configure radio module', True):
        config.interactive_add('radio_URL', 'URL to the ShoutCAST administration page', 'http://127.0.0.1:8000/')
        config.interactive_add('radio_sID', 'Stream ID (only required for multi-stream servers.)', '1')
        chunk = ("\nradio_URL = '%s'\nradio_sID = '%s'\n"
                 % (config.radio_URL, config.radio_sID))
    return chunk

radioURL = '' # Set once, after the first .radio request.
checkSongs = False
current_song = ''

def getAPI(willie, trigger):
    #contact the 'heavyweight' XML API
    try:
        raw = web.get(radioURL % 'stats')
    except Exception as e:
        willie.say('The radio is not responding to the stats request.')
        willie.debug('radio', 'Exception while trying to get stats: %s' % e, 'warning')
        return 0
    
    #Parse the XML
    XML = parseString(raw).documentElement
    servername = XML.getElementsByTagName('SERVERTITLE')[0].firstChild.nodeValue
    status = XML.getElementsByTagName('STREAMSTATUS')[0].firstChild.nodeValue
    if status:
        status = 'Online'
    else:
        status = 'Offline'
    curlist = XML.getElementsByTagName('CURRENTLISTENERS')[0].firstChild.nodeValue
    maxlist = XML.getElementsByTagName('MAXLISTENERS')[0].firstChild.nodeValue

    #Garbage disposal
    XML.unlink()

    #print results
    willie.say('[%s]Status: %s. Listeners: %s/%s.' % (servername, status, curlist, maxlist))
    return 1

def currentSong(willie, trigger):
    # This function uses the PLAINTEXT API to get the current song only.
    try:
        song = web.get(radioURL % 'currentsong')
    except Exception as e:
        willie.say('The radio is not responding to the song request.')
        willie.debug('radio', 'Exception while trying to get current song: %s' % e, 'warning')
    if song:
        willie.say('Now playing: '+song)
    else:
        Willie.say('The radio is currently offline.')

def nextSong(willie, trigger):
    # This function uses the PLAINTEXT API to get the next song only.
    try:
        song = web.get(radioURL % 'nextsong')
    except Exception as e:
        willie.say('The radio is not responding to the song request.')
        willie.debug('radio', 'Exception while trying to get next song: %s' % e, 'warning')
    if song:
        willie.say('Next up: '+song)
    else:
        willie.say('No songs are queued up.')

def radio(willie, trigger):
    """ Radio functions, valid parameters: on, off, song, now, next, soon, stats. """
    global checkSongs, current_song, radioURL
    if not radioURL:
        if not hasattr(willie.config, 'radio_URL') or not hasattr(willie.config, 'radio_sID'):
            willie.say('Radio module not configured, make sure radio_URL and radio_sID are defined')
            return
        else:
            radioURL = willie.config.radio_URL+'/%s?sid='+willie.config.radio_sID
    try:
        args = trigger.group(2).lower().split(' ')
    except AttributeError:
        willie.say('Usage: .radio (on|off|song|now|next|soon|stats)')
    if args[0] == 'on':
        if not trigger.isop:
            return;
        if checkSongs == True:
            willie.reply('Radio data checking is already on.')
            return
        if not getAPI(willie, trigger):
            return
        checkSongs = True
        while checkSongs:
            last = current_song
            try:
                current_song = web.get(radioURL % 'currentsong')
                nextsong = web.get(radioURL % 'nextsong')
            except Exception as e:
                willie.debug('radio', 'Exception while trying to get periodic radio data: %s' % e, 'warning')
                willie.say('The radio is not responding to the song request.')
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
    elif args[0] == 'next' or args[0] == 'soon':
        nextSong(willie, trigger)
    elif args[0] == 'stats':
        getAPI(willie, trigger)
radio.commands = ['radio']
radio.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
