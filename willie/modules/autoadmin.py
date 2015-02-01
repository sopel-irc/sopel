# coding=utf8
"""
Willie module to automatically op a whitelist
Security hole: if the users in the whitelist aren't
protected by a nickserv, someone malicious could take your chat room
"""

from __future__ import unicode_literals
import willie
import time

# the whitelist is a hash of arrays
# the key for the hash is the room, the array is the whitelist of users
# for that room
OPWHITELIST = None
VOICEWHITELIST = None


def configure(config):
    config.add_option(
        'autoadmin', 'oplist',
        'Key-value pairs of users to op. Format"#channel:nick,'
        'otherchan:othernick", '
        'To op in all rooms do ALL:nick.', default="")
    config.add_option(
        'autoadmin', 'voicelist',
        'Key-value pairs of users to give voice to. Format "channel:nick, '
        'To give voice in all rooms do ALL:nick.', default="")


def create_list(oplist, whitelist):
    if len(oplist) > 0:
        parts = oplist.split(',')
        for p in parts:
            (chan, nick) = p.split(':')
            if chan is not None and nick is not None:
                chan = chan.strip()
                nick = nick.strip()
                if chan not in whitelist:
                    whitelist[chan] = []
                whitelist[chan].append(nick)


def do_setup(bot):
    """
    Create the whitelists
    """
    global OPWHITELIST
    global VOICEWHITELIST
    OPWHITELIST = {}
    VOICEWHITELIST = {}
    if bot.config.autoadmin.oplist is not None:
        create_list(bot.config.autoadmin.oplist, OPWHITELIST)
    if bot.config.autoadmin.voicelist is not None:
        create_list(bot.config.autoadmin.voicelist, VOICEWHITELIST)


def checklist(thelist, trigger):
    if trigger.sender in thelist:
        for user in thelist[trigger.sender]:
            if user == trigger.nick:
                return True
    if 'ALL' in thelist:
        for user in thelist['ALL']:
            if user == trigger.nick:
                return True
    return False


@willie.module.rule('.*')
@willie.module.event("JOIN")
@willie.module.unblockable
def check_user(bot, trigger):
    """
    Check if the user is whitelisted. OP them if they are.
    """
    if OPWHITELIST is None or VOICEWHITELIST is None:
        do_setup(bot)
    if checklist(OPWHITELIST, trigger):
        time.sleep(2)
        bot.write('Welcome back %s', trigger.nick)
        bot.write(['MODE', trigger.sender, "+o", trigger.nick])
    elif checklist(VOICEWHITELIST, trigger):
        time.sleep(2)
        bot.write('Welcome back %s', trigger.nick)
        bot.write(['MODE', trigger.sender, "+v", trigger.nick])
