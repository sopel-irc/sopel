"""
radio.py - ShoutCAST radio Module
Copyright 2012, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from time import sleep
from xml.dom.minidom import parseString
import willie.web as web
import xml.dom.minidom

def configure(config):
    """
    | [radio] | example | purpose |
    | ------- | ------- | ------- |
    | URL | http://127.0.0.1:8000/ | URL to the ShoutCAST administration page |
    | sID | 1 | Stream ID (only required for multi-stream servers.) |
    """
    if config.option('Configure radio module', False):
        config.add_section('radio')
        config.interactive_add('radio', 'URL', 'URL to the ShoutCAST administration page', 'http://127.0.0.1:8000/')
        config.interactive_add('radio', 'sID', 'Stream ID (only required for multi-stream servers.)', '1')

radioURL = '' # Set once, after the first .radio request.
checkSongs = False
current_song = ''

def getAPI(willie, trigger):
    #contact the 'heavyweight' XML API
    try:
        raw = web.get(radioURL % 'stats')
    except Exception as e:
        willie.say('The radio is not responding to the stats request.')
        return 0
    
    #Parse the XML
    XML = parseString(raw).documentElement
    status = XML.getElementsByTagName('STREAMSTATUS')[0].firstChild.nodeValue
    if status == '0':
        willie.say('The radio is currently offline.')
        return 0

    status = 'Online'
    servername = XML.getElementsByTagName('SERVERTITLE')[0].firstChild.nodeValue
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
        willie.say('The radio is currently offline.')

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
        if not hasattr(willie.config, 'radio'):
            willie.say('Radio module not configured')
            return
        else:
            radioURL = willie.config.radio.URL+'%s?sid='+willie.config.radio.sID
    try:
        args = trigger.group(2).lower().split(' ')
    except AttributeError:
        willie.say('Usage: .radio (next|now|off|on|song|soon|stats)')
        return
    if args[0] == 'on':
        if not trigger.isop:
            return;
        if checkSongs == True:
            willie.reply('Radio data checking is already on.')
            return
        if not getAPI(willie, trigger):
            willie.say('Radio data checking not enabled.')
            checkSongs = False
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
