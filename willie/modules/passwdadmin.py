# coding=utf8
"""
Willie module that accepts a channel and password (preferably via PM),
then ops/voices that user in that channel.
"""

import willie
import time
import re

# the list key is channel, the value is the key for that channel.
OPLIST = None
VOICELIST = None

def configure(config):
    config.add_option('passwdadmin', 'oplist',
        'Key-value pairs of users to op. Format"#channel:passwd, '
        'otherchan:betterpasswd", '
        'To allow op in all rooms (master key) do ALL:passwd.', default="")
    config.add_option('passwdadmin', 'voicelist',
        'Key-value pairs of users to give voice to. Format "channel:passwd, '
        'To allow voice in all rooms do ALL:passwd.', default="")

def create_list(oplist, roomlist):
    if len(oplist) > 0:
        parts = oplist.split(',')
        for p in parts:
            (chan,pw) = p.split(':')
            if chan is not None and pw is not None:
                chan = chan.strip()
                pw = pw.strip()
                roomlist[chan] = pw

def do_setup(bot):
    """
    Create the roomlists
    """
    global OPLIST
    global VOICELIST
    OPLIST = {}
    VOICELIST = {}
    if bot.config.passwdadmin.oplist is not None:
        create_list(bot.config.passwdadmin.oplist, OPLIST)
    if bot.config.passwdadmin.voicelist is not None:
        create_list(bot.config.passwdadmin.voicelist, VOICELIST)

def checklist(thelist, chan, passwd):
    if chan in thelist:
        if passwd == thelist[chan]:
            return True
    if 'ALL' in thelist:
        if passwd == thelist['ALL']:
            return True
    return False


@willie.module.commands('getop')
def check_user(bot, trigger):
    """ Provide the chat and the password to get op or voice """
    if OPLIST is None or VOICELIST is None:
        do_setup(bot)
    m = re.search('(?P<chan>\S+)\s+(?P<passwd>\S+)', trigger.group(2))
    if m is not None:
        d = m.groupdict()
        if checklist(OPLIST, d['chan'], d['passwd']):
            bot.say("Oping in %s"%(d['chan']))
            bot.write(['MODE', d['chan'], "+o", trigger.nick])
        elif checklist( VOICELIST, d['chan'], d['passwd']):
            bot.say("Voicing in %s"%(d['chan']))
            bot.write(['MODE', d['chan'], "+v", trigger.nick])
        else:
            bot.say('Nope.')
    else:
        bot.say("Usage: .getop #roomname password")

