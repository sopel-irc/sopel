# -*- coding: utf8 -*-
"""
announce.py - Send a message to all channels
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

"""
def announce(willie, trigger):
    """
    Send an announcement to all channels the bot is in
    """
    if not trigger.admin:
        willie.reply('Sorry, I can\'t let you do that')
        return
    print willie.channels
    for channel in willie.channels:
        willie.msg(channel, '[ANNOUNCMENT] %s' % trigger.group(2))
announce.commands = ['announce']
announce.example = '.announce Some important message here'
