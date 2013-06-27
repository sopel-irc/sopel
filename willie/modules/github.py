"""
github.py - Willie Github Module
Copyright 2012, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from datetime import datetime
from urllib2 import HTTPError
import json
from willie import web
from willie.module import commands


def checkConfig(bot):
    if not bot.config.has_option('github', 'oauth_token') or not bot.config.has_option('github', 'repo'):
        return False
    else:
        return [bot.config.github.oauth_token, bot.config.github.repo]


def configure(config):
    """
    | [github] | example | purpose |
    | -------- | ------- | ------- |
    | oauth_token | 5868e7af57496cc3ae255868e7af57496cc3ae25 | The OAuth token to connect to your github repo |
    | repo | embolalia/willie | The GitHub repo you're working from. |
    """
    chunk = ''
    if config.option('Configuring github issue reporting and searching module', False):
        config.interactive_add('github', 'oauth_token', 'Github API Oauth2 token', '')
        config.interactive_add('github', 'repo', 'Github repository', 'embolalia/willie')
    return chunk


@commands('makeissue', 'makebug')
def issue(bot, trigger):
    """Create a GitHub issue, also known as a bug report. Syntax: .makeissue Title of the bug report"""
    # check input
    if not trigger.group(2):
        return bot.say('Please title the issue')

    # Is the Oauth token and repo available?
    gitAPI = checkConfig(bot)
    if gitAPI == False:
        return bot.say('Git module not configured, make sure github.oauth_token and github.repo are defined')

    # parse input
    now = ' '.join(str(datetime.utcnow()).split(' ')).split('.')[0] + ' UTC'
    body = 'Submitted by: %s\nFrom channel: %s\nAt %s' % (trigger.nick, trigger.sender, now)
    data = {"title": trigger.group(2).encode('utf-8'), "body": body, "labels": ["IRC"]}
    # submit
    try:
        raw = web.post('https://api.github.com/repos/' + gitAPI[1] + '/issues?access_token=' + gitAPI[0], json.dumps(data))
    except HTTPError:
        return bot.say('The GitHub API returned an error.')

    data = json.loads(raw)
    bot.say('Issue #%s posted. %s' % (data['number'], data['html_url']))
    bot.debug('GitHub', 'Issue #%s created in %s' % (data['number'], trigger.sender), 'warning')


@commands('findissue', 'findbug')
def findIssue(bot, trigger):
    """Search for a GitHub issue by keyword or ID. usage: .findissue search keywords/ID (optional) You can specify the first keyword as "CLOSED" to search closed issues."""
    if not trigger.group(2):
        return bot.reply('What are you searching for?')

    # Is the Oauth token and repo available?
    gitAPI = checkConfig(bot)
    if gitAPI == False:
        return bot.say('Git module not configured, make sure github.oauth_token and github.repo are defined')
    firstParam = trigger.group(2).split(' ')[0]
    if firstParam.isdigit():
        URL = 'https://api.github.com/repos/%s/issues/%s' % (gitAPI[1], trigger.group(2))
    elif firstParam == 'CLOSED':
        if '%20'.join(trigger.group(2).split(' ')[1:]) not in ('', '\x02', '\x03'):
            URL = 'https://api.github.com/legacy/issues/search/' + gitAPI[1] + '/closed/' + '%20'.join(trigger.group(2).split(' ')[1:])
        else:
            return bot.reply('What are you searching for?')
    else:
        URL = 'https://api.github.com/legacy/issues/search/%s/open/%s' % (gitAPI[1], trigger.group(2))

    try:
        raw = web.get(URL)
    except HTTPError:
        return bot.say('The GitHub API returned an error.')

    try:
        if firstParam.isdigit():
            data = json.loads(raw)
        else:
            data = json.loads(raw)['issues'][-1]
    except (KeyError, IndexError):
        return bot.say('No search results.')
    if len(data['body'].split('\n')) > 1:
        body = data['body'].split('\n')[0] + '...'
    else:
        body = data['body'].split('\n')[0]
    bot.reply('[#%s]\x02title:\x02 %s \x02|\x02 %s' % (data['number'], data['title'], body))
    bot.say(data['html_url'])
