# coding=utf8
"""
radio.py - ShoutCAST radio Module
Copyright 2012, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""
from __future__ import unicode_literals

from time import sleep
from xml.dom.minidom import parseString
import willie.web as web
from willie.module import commands, OP
from willie.logger import get_logger

LOGGER = get_logger(__name__)


def configure(config):
    """
    | [radio] | example | purpose |
    | ------- | ------- | ------- |
    | url | http://127.0.0.1:8000/ | URL to the ShoutCAST administration page |
    | sid | 1 | Stream ID (only required for multi-stream servers.) |
    """
    if config.option('Configure radio module', False):
        config.add_section('radio')
        config.interactive_add('radio', 'url', 'URL to the ShoutCAST administration page', 'http://127.0.0.1:8000/')
        config.interactive_add('radio', 'sid', 'Stream ID (only required for multi-stream servers.)', '1')

radioURL = ''  # Set once, after the first .radio request.
checkSongs = 0
current_song = ''


def getAPI(bot, trigger):
    #contact the 'heavyweight' XML API
    try:
        raw = web.get(radioURL % 'stats')
    except Exception:
        bot.say('The radio is not responding to the stats request.')
        return 0

    #Parse the XML
    XML = parseString(raw).documentElement
    status = XML.getElementsByTagName('STREAMSTATUS')[0].firstChild.nodeValue
    if status == '0':
        bot.say('The radio is currently offline.')
        return 0

    status = 'Online'
    servername = XML.getElementsByTagName('SERVERTITLE')[0].firstChild.nodeValue
    curlist = XML.getElementsByTagName('CURRENTLISTENERS')[0].firstChild.nodeValue
    maxlist = XML.getElementsByTagName('MAXLISTENERS')[0].firstChild.nodeValue

    #Garbage disposal
    XML.unlink()

    #print results
    bot.say('[%s]Status: %s. Listeners: %s/%s.' % (servername, status, curlist, maxlist))
    return 1


def currentSong(bot, trigger):
    # This function uses the PLAINTEXT API to get the current song only.
    try:
        song = web.get(radioURL % 'currentsong')
    except Exception as e:
        bot.say('The radio is not responding to the song request.')
        LOGGER.warning('Exception while trying to get current song.',
                       exc_info=True)
    if song:
        bot.say('Now playing: ' + song)
    else:
        bot.say('The radio is currently offline.')


def nextSong(bot, trigger):
    # This function uses the PLAINTEXT API to get the next song only.
    try:
        song = web.get(radioURL % 'nextsong')
    except Exception as e:
        bot.say('The radio is not responding to the song request.')
        LOGGER.exception('Exception while trying to get next song.')
    if song:
        bot.say('Next up: ' + song)
    else:
        bot.say('No songs are queued up.')


@commands('radio')
def radio(bot, trigger):
    """ Radio functions, valid parameters: on, off, song, now, next, soon, stats. """
    global checkSongs, current_song, radioURL
    if not radioURL:
        if not hasattr(bot.config, 'radio'):
            bot.say('Radio module not configured')
            return
        else:
            radioURL = bot.config.radio.url + '%s?sid=' + bot.config.radio.sid
    try:
        args = trigger.group(2).lower().split(' ')
    except AttributeError:
        bot.say('Usage: .radio (next|now|off|on|song|soon|stats)')
        return
    if args[0] == 'on':
        if bot.privileges[trigger.sender][trigger.nick] < OP:
            return
        if checkSongs != 0:
            return bot.reply('Radio data checking is already on.')
        if not getAPI(bot, trigger):
            checkSongs = 0
            return bot.say('Radio data checking not enabled.')
        checkSongs = 10
        while checkSongs:
            last = current_song
            try:
                current_song = web.get(radioURL % 'currentsong')
                nextsong = web.get(radioURL % 'nextsong')
            except Exception as e:
                checkSongs -= 1
                if checkSongs == 0:
                    LOGGER.exception(
                        'Exception while trying to get periodic radio data: %s'
                    )
                    bot.say('The radio is not responding to the song request.')
                    bot.say('Turning off radio data checking.')
                break
            if not current_song == last:
                if not current_song:
                    csong = 'The radio is currently offline.'
                else:
                    csong = 'Now Playing: ' + current_song
                if nextsong and current_song:
                    bot.say(csong + ' | Coming Up: ' + nextsong)
                else:
                    bot.say(csong)
            sleep(5)
    elif args[0] == 'off':
        if bot.privileges[trigger.sender][trigger.nick] < OP:
            return
        if checkSongs == 0:
            bot.reply('Radio data checking is already off.')
            return
        checkSongs = 0
        current_song = ''
        bot.reply('Turning off radio data checking.')
    elif args[0] == 'song' or args[0] == 'now':
        currentSong(bot, trigger)
    elif args[0] == 'next' or args[0] == 'soon':
        nextSong(bot, trigger)
    elif args[0] == 'stats':
        getAPI(bot, trigger)
