"""
info.py - Willie Information Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

def doc(willie, trigger):
    """Shows a command's documentation, and possibly an example."""
    name = trigger.group(1)
    name = name.lower()

    if willie.doc.has_key(name):
        willie.reply(willie.doc[name][0])
        if willie.doc[name][1]:
            willie.say('e.g. ' + willie.doc[name][1])
doc.rule = ('$nick', '(?i)(?:help|doc) +([A-Za-z]+)(?:\?+)?$')
doc.example = '$nickname: doc tell?'
doc.priority = 'low'

def commands(willie, trigger):
    """Return a list of Willie's commands"""
    names = ', '.join(sorted(willie.doc.iterkeys()))
    willie.reply("I am sending you a private message of all my commands!")
    willie.msg(trigger.nick, 'Commands I recognise: ' + names + '.')
    willie.msg(trigger.nick, ("For help, do '%s: help example?' where example is the " +
                    "name of the command you want help for.") % willie.nick)
commands.commands = ['commands', 'help']
commands.priority = 'low'

def help(willie, trigger):
    response = (
        'Hi, I\'m a bot. Say ".commands" to me in private for a list ' +
        'of my commands, or see http://inamidst.com/phenny/ for more ' +
        'general details. My owner is %s.'
    ) % willie.config.owner
    willie.reply(response)
help.rule = ('$nick', r'(?i)help(?:[?!]+)?$')
help.priority = 'low'

def stats(willie, trigger):
    """Show information on command usage patterns."""
    commands = {}
    users = {}
    channels = {}

    ignore = set(['f_note', 'startup', 'message', 'noteuri'])
    for (name, user), count in willie.stats.iteritems():
        if name in ignore: continue
        if not user: continue

        if not user.startswith('#'):
            try: users[user] += count
            except KeyError: users[user] = count
        else:
            try: commands[name] += count
            except KeyError: commands[name] = count

            try: channels[user] += count
            except KeyError: channels[user] = count

    comrank = sorted([(b, a) for (a, b) in commands.iteritems()], reverse=True)
    userank = sorted([(b, a) for (a, b) in users.iteritems()], reverse=True)
    charank = sorted([(b, a) for (a, b) in channels.iteritems()], reverse=True)

    # most heavily used commands
    creply = 'most used commands: '
    for count, command in comrank[:10]:
        creply += '%s (%s), ' % (command, count)
    willie.say(creply.rstrip(', '))

    # most heavy users
    reply = 'power users: '
    for count, user in userank[:10]:
        reply += '%s (%s), ' % (user, count)
    willie.say(reply.rstrip(', '))

    # most heavy channels
    chreply = 'power channels: '
    for count, channel in charank[:3]:
        chreply += '%s (%s), ' % (channel, count)
    willie.say(chreply.rstrip(', '))
stats.commands = ['stats']
stats.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
