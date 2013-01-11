"""
info.py - Willie Information Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

def doc(willie, trigger):
    """Shows a command's documentation, and possibly an example."""
    name = trigger.group(2)
    name = name.lower()

    if willie.doc.has_key(name):
        willie.reply(willie.doc[name][0])
        if willie.doc[name][1]:
            willie.say('e.g. ' + willie.doc[name][1])
doc.rule = ('$nick', '(?i)(help|doc) +([A-Za-z]+)(?:\?+)?$')
doc.example = '$nickname: doc tell?'
doc.priority = 'low'

def help(willie, trigger):
    """Get help for a command."""
    if not input.group(2):
	willie.reply('Say .help <command> (for example .help c) to get help for a command, or .commands for a list of commands.')
    else:
	doc(willie, trigger)
help.commands = ['help']
help.example = '.help c'

def commands(willie, trigger):
    """Return a list of Willie's commands"""
    names = ', '.join(sorted(willie.doc.iterkeys()))
    willie.reply("I am sending you a private message of all my commands!")
    willie.msg(trigger.nick, 'Commands I recognise: ' + names + '.')
    willie.msg(trigger.nick, ("For help, do '%s: help example?' where example is the " +
                    "name of the command you want help for.") % willie.nick)
commands.commands = ['commands']
commands.priority = 'low'

def help(willie, trigger):
    response = (
        'Hi, I\'m a bot. Say ".commands" to me in private for a list ' +
        'of my commands, or see http://willie.dftba.net for more ' +
        'general details. My owner is %s.'
    ) % willie.config.owner
    willie.reply(response)
help.rule = ('$nick', r'(?i)help(?:[?!]+)?$')
help.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
