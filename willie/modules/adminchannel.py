# coding=utf-8
"""
adminchannel.py - Willie Admin Module
Copyright 2010-2011, Michael Yanovich, Alek Rollyson, and Edward Powell
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/

"""

import re
from willie.module import commands, priority, OP

STRINGS = {'NOT_ENOUGH_ARGS': '[Error] Not enough arguments specified',
           'TOO_MANY_ARGS': '[Error] Too many arguments specified',
           'NO_PERMISSION': '[Error] You do not have permission to do this',
           'NO_CHANNEL': '[Error] The channel provided is invalid or one ' +
           'was not specified',
           'INVALID_MASK': '[Error] The mask provided is invalid or one ' +
           'was not specified',
           'NO_DATABASE': '[Error] Could not connect to the Database',
           'NO_MASK_SET': 'No mask is set for this channel',
           'DEFAULT_KICK_REASON': 'No reason specified',
           'INVALID_TOPIC_MASK': 'An invalid topic mask is in place, using' +
           'the default',
           'NO_TOPIC_MASK': 'No topic mask in place, using the default'}


def setup(bot):
    #Having a db means pref's exists. Later, we can just use `if bot.db`.
    if bot.db and not bot.db.preferences.has_columns('topic_mask'):
        bot.db.preferences.add_columns(['topic_mask'])


@commands('op')
def op(bot, trigger):
    """
    USE: .op [#channel] [nick]

    Command to op users in a room. If no nick is given,
    willie will op the nick who sent the command in the
    channel it was issues in. This can also be issued via
    PM.

    Note: Bot must be OP
    """

    # If there are no arguments then return the USE statement
    if len(trigger.group().split()) < 2:
        bot.say('%s' % cleanDoc(op))
        return

    # Let's make sure we are not trying to op the bot, since it should
    # already be op and if it is not, the command will not work anyway.
    if bot.config.nick not in trigger.group().split():
        setMode(bot, trigger, '+o')


@commands('deop')
def deop(bot, trigger):
    """
    USE: .deop [#channel] [nick]

    Command to deop users in a room. If no nick is given,
    willie will deop the nick who sent the command in the
    channel it was issues in. This can also be issued via
    PM.

    Note: Bot must be OP
    """

    # If there are no arguments then return the USE statement
    if len(trigger.group().split()) < 2:
        bot.say('%s' % cleanDoc(deop))
        return

    setMode(bot, trigger, '-o')


@commands('voice')
def voice(bot, trigger):
    """
    USE: .voice [#channel] [nick]

    Command to voice users in a room. If no nick is given,
    willie will voice the nick who sent the command in the
    channel it was issues in. This can also be issued via
    PM.

    Note: Bot must be OP
    """

    # If there are no arguments then return the USE statement
    if len(trigger.group().split()) < 2:
        bot.say('%s' % cleanDoc(voice))
        return

    setMode(bot, trigger, '+v')


@commands('devoice')
def devoice(bot, trigger):
    """
    USE: .devoice [#channel] [nick]

    Command to devoice users in a room. If no nick is given,
    willie will voice the nick who sent the command in the
    channel it was issues in. This can also be issued via
    PM.

    Note: Bot must be OP
    """

    # If there are no arguments then return the USE statement
    if len(trigger.group().split()) < 2:
        bot.say('%s' % cleanDoc(devoice))
        return

    setMode(bot, trigger, '-v')


@commands('kick')
@priority('high')
def kick(bot, trigger):
    """
    USE: .kick [#channel] nick

    Command to Kick a user from a room.

    Note: Bot must be OP
    """

    args = trigger.group().split()
    argc = len(args) - 1
    reasonidx = 1

    # If there are no arguments then return the USE statement
    if argc < 1:
        bot.say('%s' % cleanDoc(kick))
        return

    if trigger.is_privmsg:
        if argc <= 1:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        elif args >= 2:
            if isChannel(args[1]):
                channel, nick = args[1:3]
                reasonidx = 3
            elif isChannel(args[2]):
                nick, channel = args[1:3]
                reasonidx = 3
            else:
                bot.reply(STRINGS['NO_CHANNEL'])
                return
    else:
        if argc < 1:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        elif argc == 1:
            if isChannel(args[1]):
                bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
                return
            else:
                nick = args[1]
                channel = trigger.sender
        elif argc >= 2:
            if isChannel(args[1]):
                channel, nick = args[1:3]
                reasonidx = 3
            elif isChannel(args[2]):
                nick, channel = args[1:3]
                reasonidx = 3
            else:
                nick = args[1]
                channel = trigger.sender
                reasonidx = 2

    channel = channel.lower()

    reason = ' '.join(args[reasonidx:])
    if reason.strip() == '':
        reason = STRINGS['DEFAULT_KICK_REASON']

    if not permissionsCheck(bot, channel, trigger.nick):
        bot.reply(STRINGS['NO_PERMISSION'])
        return

    if nick != bot.config.nick:
        bot.write(['KICK', channel, nick], text=reason)


@commands('ban')
@priority('high')
def ban(bot, trigger):
    """
    USE: .ban [#channel] banmask

    Command to ban a user from a room.

    Note: Bot must be OP
    """

    # If there are no arguments then return the USE statement
    if len(trigger.group().split()) < 2:
        bot.say('%s' % cleanDoc(ban))
        return

    setMaskMode(bot, trigger, '+b')


@commands('unban')
def unban(bot, trigger):
    """
    USE: .ban [#channel] banmask

    Command to ban a user from a room.

    Note: Bot must be OP
    """

    # If there are no arguments then return the USE statement
    if len(trigger.group().split()) < 2:
        bot.say('%s' % cleanDoc(unban))
        return

    setMaskMode(bot, trigger, '-b')


@commands('quiet')
def quiet(bot, trigger):
    """
    USE: .quiet [#channel] quietmask

    Command to quiet a user in a room.

    Note: Bot must be OP
    """

    # If there are no arguments then return the USE statement
    if len(trigger.group().split()) < 2:
        bot.say('%s' % cleanDoc(quiet))
        return

    setMaskMode(bot, trigger, '+q')


@commands('unquiet')
def unquiet(bot, trigger):
    """
    USE: .unquiet [#channel] quietmask

    Command to unquiet a user in a room.

    Note: Bot must be OP
    """

    # If there are no arguments then return the USE statement
    if len(trigger.group().split()) < 2:
        bot.say('%s' % cleanDoc(unquiet))
        return

    setMaskMode(bot, trigger, '-q')


@commands('kickban', 'kb')
@priority('high')
def kickban(bot, trigger):
    """
    USE: .kickban|.kb [#channel] nick banmask [reason]

    Command to kick and ban a user from a room.

    Note: Bot must be OP
    """

    args = trigger.group().split()
    argc = len(args) - 1
    reasonidx = 1

    # If there are no arguments then return the USE statement
    if argc < 1:
        bot.say('%s' % cleanDoc(kickban))
        return

    if trigger.is_privmsg:
        if argc <= 2:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        elif argc >= 3:
            if isChannel(args[1]):
                channel, nick, banmask = args[1:4]
                reasonidx = 4
            else:
                bot.replay(STRINGS['NO_CHANNEL'])
                return
    else:
        if argc < 2:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        elif argc == 2:
            if isChannel(args[1]) or isChannel(args[2]):
                bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
                return
            else:
                nick, banmask = args[1:3]
                channel = trigger.sender
                reasonidx = 3
        elif argc >= 3:
            if isChannel(args[1]):
                channel, nick, banmask = args[1:4]
                reasonidx = 4
            else:
                channel = trigger.sender
                nick, banmask = args[1:3]
                reasonidx = 3

    reason = ' '.join(args[reasonidx:])
    if reason == '' or reason is None:
        reason = STRINGS['DEFAULT_KICK_REASON']

    channel = channel.lower()

    banmask = configureHostMask(banmask)

    if banmask == '':
        bot.reply(STRINGS['INVALID_MASK'])
        return

    if not permissionsCheck(bot, channel, trigger.nick):
        bot.reply(STRINGS['NO_PERMISSION'])
        return

    bot.write(['MODE', channel, '+b', banmask])
    bot.write(['KICK', channel, nick], text=reason)


@commands('topic')
def topic(bot, trigger):
    """
    USE: .topic [#channel] Channel Topic

    Command to change an channel's topic, the Channel Topic can use '~' as a
    delimiter, showing that there are multiple arguments to be provided for the
    topic mask to use.

    Note: Bot must be OP
    """
    purple, green, bold = '\x0306', '\x0310', '\x02'

    args = trigger.group().split()
    argc = len(args) - 1

    # If there are no arguments then return the USE statement
    if argc < 1:
        bot.say('%s' % cleanDoc(topic))
        return

    if trigger.is_privmsg:
        if argc < 2:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        if argc >= 2:
            if isChannel(args[1]):
                channel = args[1]
                topicidx = 2
            else:
                bot.reply(STRINGS['NO_CHANNEL'])
                return
    else:
        if argc == 1:
            topicidx = 1
            channel = trigger.sender
        if argc >= 2:
            if isChannel(args[1]):
                channel = args[1]
                topicidx = 2
            else:
                channel = trigger.sender
                topicidx = 1

    channel = channel.lower()

    default_mask = purple + 'Welcome to: ' + green + channel + purple \
        + ' | ' + bold + 'Topic: ' + bold + green + '%s'

    if bot.db and channel in bot.db.preferences:
        mask = bot.db.preferences.get(channel, 'topic_mask')
    else:
        bot.reply(STRINGS['NO_TOPIC_MASK'])
        mask = default_mask

    nargs = len(re.findall('%s', mask))

    # If the number of '%s' encountered in the mask is 0 or the mask is
    # empty then we should use the default mask
    if nargs < 1 or mask is None or mask == '':
        bot.reply(STRINGS['INVALID_TOPIC_MASK'])
        mask = default_mask

    # Attempt to get a list of arguments. This can be a single string
    # delimited by '~'
    new_topic = ' '.join(args[topicidx:])
    topic_args = tuple(new_topic.split('~', nargs))

    # Make sure we have enough arguments
    if len(topic_args) < nargs:
        message = str('Not enough arguments. You gave %s, it requires %s.' %
                      (str(len(topic_args)), str(nargs)))
        bot.reply(message)
        return

    new_topic = mask % topic_args

    if not permissionsCheck(bot, channel, trigger.nick):
        bot.reply(STRINGS['NO_PERMISSION'])
        return

    bot.write(('TOPIC', channel), text=new_topic)


@commands('tmask')
def set_mask(bot, trigger):
    """
    USE: .tmask [#channel] Channel Topic

    Command to change an channel's topic mask, the topic mask is used to help
    format the channel's topic in a uniform manner upon updating. %s is used to
    allow substituting in chunks of text.

    Note: Bot must be OP
    """
    args = trigger.group().split()
    argc = len(args) - 1
    topicidx = 1

    # If there are no arguments then return the USE statement
    if argc < 1:
        bot.say('%s' % cleanDoc(set_mask))
        return

    if trigger.is_privmsg:
        if argc < 2:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        elif argc >= 2:
            if isChannel(args[1]):
                channel = args[1]
                topicidx = 2
            else:
                bot.reply(STRINGS['NO_CHANNEL'])
                return
    else:
        if argc >= 1:
            if isChannel(args[1]):
                channel = args[1]
                topicidx = 2
            else:
                channel = trigger.sender
                topicidx = 1

    channel = channel.lower()

    topic_mask = ' '.join(args[topicidx:])

    if not permissionsCheck(bot, channel, trigger.nick):
        bot.reply(STRINGS['NO_PERMISSION'])
        return

    if not bot.db:
        bot.reply(STRINGS['NO_DATABASE'])
        return

    bot.db.preferences.update(channel.lower(), {'topic_mask': topic_mask})
    bot.reply('Topic mask updated!')


@commands('showmask')
def show_mask(bot, trigger):
    """
    USE: .showmask [#channel]

    Command to show the topic mask of a given channel.

    Note: Bot must be OP
    """

    args = trigger.group().split()
    argc = len(args) - 1

    if trigger.is_privmsg:
        if argc < 1:
            bot.reply(STRINGS['NO_CHANNEL'])
            return
        elif argc == 1:
            if isChannel(args[1]):
                channel = args[1]
            else:
                bot.reply(STRINGS['NO_CHANNEL'])
                return
        elif argc > 1:
            bot.reply(STRINGS['TOO_MANY_ARGS'])
            return
    else:
        if argc < 1:
            channel = trigger.sender
        elif argc == 1:
            if isChannel(args[1]):
                channel = args[1]
            else:
                bot.reply(STRINGS['NO_CHANNEL'])
                return
        elif argc > 1:
            bot.reply(STRINGS['TOO_MANY_ARGS'])
            return

    channel = channel.lower()

    if not bot.db:
        bot.reply(STRINGS['NO_DATABASE'])
        return

    if channel not in bot.db.preferences:
        bot.reply(STRINGS['NO_MASK_SET'])
        return

    if not permissionsCheck(bot, channel, trigger.nick):
        bot.reply(STRINGS['NO_PERMISSION'])
        return

    topic = bot.db.preferences.get(channel, 'topic_mask')

    bot.reply('The topic mask is:')
    bot.say('%s' % topic)


def configureHostMask(mask):
    """
    Allows for short form bans to be used

    nick!user@host.domain
    """
    if mask == '*!*@*':
        return mask

    # Nick
    if re.match('^[^.@!/]+$', mask) is not None:
        return '%s!*@*' % mask

    # Host.Domain
    if re.match('^[^@!]+$', mask) is not None:
        return '*!*@%s' % mask

    # User@
    m = re.match('^([^!@]+)@$', mask)
    if m is not None:
        return '*!%s@*' % m.group(1)

    # User@Host.Domain
    m = re.match('^([^!@]+)@([^@!]+)$', mask)
    if m is not None:
        return '*!%s@%s' % (m.group(1), m.group(2))

    # Nick!User@
    m = re.match('^([^!@]+)!([^!@]+)@?$', mask)
    if m is not None:
        return '%s!%s@*' % (m.group(1), m.group(2))

    # Nick!User@Host.Domain
    m = re.match('^([^!@]+)!([^!@]+)@([^!@]+)$', mask)
    if m is not None:
        return '%s!%s@%s' % (m.group(1), m.group(2), m.group(3))

    return ''


def permissionsCheck(bot, channel, nick):
    """
    Checks to see if the provided user has OP access to the channel

    Returns:
        False if they do not
        True if they do
    """
    if channel not in bot.privileges or \
            nick not in bot.privileges[channel] or \
            bot.privileges[channel][nick] < OP:
        return False
    return True


def setMaskMode(bot, trigger, mode):
    """
    Takes a bot, trigger and mode as arguments and applies
    the needed mode change on the channel/nick. Used by (un)ban/(un)quiet

    Note: These Require the bot to be OP
    """
    args = trigger.group().split()
    argc = len(args) - 1

    if trigger.is_privmsg:
        if argc < 2:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        elif argc == 2:
            if isChannel(args[1]):
                channel = args[1]
                banmask = args[2]
            else:
                bot.reply(STRINGS['NO_CHANNEL'])
                return
        elif argc > 2:
            bot.reply(STRINGS['TOO_MANY_ARGS'])
            return
    else:
        if argc < 1:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        elif argc == 1:
            if isChannel(args[1]):
                bot.reply(STRINGS['INVALID_MASK'])
                return
            else:
                banmask = args[1]
                channel = trigger.sender
        elif argc == 2:
            if isChannel(args[1]):
                channel, banmask = args[1:3]
            elif isChannel(args[2]):
                banmask, channel = args[1:3]
            else:
                bot.reply(STRINGS['NO_CHANNEL'])
                return
        elif argc > 2:
            bot.reply(STRINGS['TOO_MANY_ARGS'])
            return

    channel = channel.lower()

    if not permissionsCheck(bot, channel, trigger.nick):
        bot.reply(STRINGS['NO_PERMISSION'])
        return

    banmask = configureHostMask(banmask)

    if banmask == '':
        bot.reply(STRINGS['INVALID_MASK'])
        return

    bot.write(['MODE', channel, mode, banmask])


def setMode(bot, trigger, mode):
    """
    Takes a bot, trigger and mode as arguments and applies
    the needed mode change on the channel/nick. Used by (de)op/(de)voice

    Note: These Require the bot to be OP
    """
    args = trigger.group().split()
    argc = len(args) - 1

    if trigger.is_privmsg:
        if argc <= 1:
            bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
            return
        elif argc == 2:
            # Order [channel] [nick]
            if isChannel(args[1]):
                channel, nick = args[1:3]
            elif isChannel(args[2]):
                nick, channel = args[1:3]
            else:
                bot.reply(STRINGS['NO_CHANNEL'])
                return
        else:
            bot.reply(STRINGS['TOO_MANY_ARGS'])
            return
    else:
        if argc == 0:
            nick = trigger.nick
            channel = trigger.sender
        elif argc == 1:
            nick = args[1]
            channel = trigger.sender
            if isChannel(nick):
                bot.reply(STRINGS['NOT_ENOUGH_ARGS'])
                return
        elif argc == 2:
            # Order [channel] [nick]
            if isChannel(args[1]):
                channel, nick = args[1:3]
            elif isChannel(args[2]):
                nick, channel = args[1:3]
            else:
                bot.reply(STRINGS['TOO_MANY_ARGS'])
                return
        else:
            bot.reply(STRINGS['TOO_MANY_ARGS'])
            return

    channel = channel.lower()

    if not permissionsCheck(bot, channel, trigger.nick):
        bot.reply(STRINGS['NO_PERMISSION'])
        return

    bot.write(['MODE', channel, mode, nick])


def cleanDoc(doc):
    """
    Try to find the first newline and truncate, we skip the first two
    lines to avoid docs that start with \r\n
    """
    for line in doc.__doc__.replace('\r', '').split('\n'):
        if line != '':
            return line


def isChannel(value):
    """
    Check if the given string is a channel or not
    """
    if value is not None and value[0] in '&#~!':
        return True
    else:
        return False
