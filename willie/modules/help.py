"""
help.py - Dice Module
Copyright 2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from collections import deque

helpees = deque()

def addNewHelpee(willie, trigger):
    """Adds somebody who joins the channel to the helpee list."""
    if trigger.admin: return
    helpees.append({'nick': trigger.nick, 'request': None, 'active': False, 'skipped': False})
    willie.msg(trigger.nick, 'welcome to '+str(trigger)+'. Please reply here with your help request, prefixed with \'.help\'. (example: .help I lost my password.)')
addNewHelpee.event = 'JOIN'
addNewHelpee.rule = r'.*'

def help(willie, trigger):
    """Allows a helpee to add a message to their help request, and activates said request."""
    if trigger.sender.startswith("#"): return
    found = None
    for helpee in helpees:
        if trigger.nick == helpee['nick']:
            found = helpee
    if not found:
        return willie.say('You\'re not found in the list of people in the channel, are you sure you\'re in the channel?')
    else:
        if not trigger.groups()[1]:
            return willie.say('You forgot to actually state your question, example: .help Who the eff is Hank?')
        if not helpee['active']:
            helpee['active'] = True
            helpee['request'] = trigger.groups()[1].encode('UTF-8')
            willie.say('Your help request is now marked active. Your question is:')
            willie.say(helpee['request'])
            willie.say('If you have anything more to add, please use the .help command again.')
        else:
            helpee['request'] += ' '+trigger.groups()[1].encode('UTF-8')
            willie.say('You already had a question, I\'ve added this to what you\'ve asked previously. Your new question is:')
            willie.say(helpee['request'])
help.commands = ['help']

def next(willie, trigger):
    """Allows a channel operator to get the next person in the waiting list, if said person didn't activate his or her help request, it reminds them and puts them at the end of the queue."""
    if not trigger.isop: return willie.reply('You\'re not a channel operator.')
    try:
        helpee = helpees.popleft()
    except:
        return willie.reply('Nobody waiting.')
    if not helpee['active']:
        if not helpee['skipped']:
            helpee['skipped'] = True
            helpees.append(helpee)
            willie.reply('Tried assigning '+helpee['nick']+' but they didn\'t set a help request, if they\'re the only person waiting for help please give them some time to set one.')
            willie.msg(helpee['nick'], 'An operator just tried to help you but you didn\'t tell me what you need help with. I\'m putting you back at the end of the queue, please use the .help command.')
        else:
            willie.msg(helpee['nick'], 'An operator just tried to help you again. Since you seem to be inactive I\'m going to remove you from the channel. Please use the .help command after you join again.')
            willie.write(['KICK', '#help', helpee['nick'], 'Didn\'t set a help request before being assigned an operator, twice.']) #TODO: Remove hardcoded channel
    else:
        willie.reply('assigned '+helpee['nick']+' to you. Their question: '+helpee['request'])
        willie.write(['MODE', '#help', '+v', helpee['nick']]) #TODO: Remove hardcoded channel
next.commands = ['next']

if __name__ == '__main__':
    print __doc__.strip()
