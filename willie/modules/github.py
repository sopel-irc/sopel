# coding=utf8
"""
github.py - Willie Github Module
Copyright 2012, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""
from __future__ import unicode_literals

from datetime import datetime
import sys
if sys.version_info.major < 3:
    from urllib2 import HTTPError
else:
    from urllib.error import HTTPError
import json
from willie import web, tools
from willie.module import commands, rule, NOLIMIT
import os
import re
from willie.logger import get_logger

LOGGER = get_logger(__name__)

issueURL = (r'https?://(?:www\.)?github.com/'
            '([A-z0-9\-]+/[A-z0-9\-]+)/'
            '(?:issues|pull)/'
            '([\d]+)')
regex = re.compile(issueURL)


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


def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.WillieMemory()
    bot.memory['url_callbacks'][regex] = issue_info


def shutdown(bot):
    del bot.memory['url_callbacks'][regex]


@commands('makeissue', 'makebug')
def issue(bot, trigger):
    """Create a GitHub issue, also known as a bug report. Syntax: .makeissue Title of the bug report"""
    # check input
    if not trigger.group(2):
        return bot.say('Please title the issue')

    # Is the Oauth token and repo available?
    gitAPI = checkConfig(bot)
    if not gitAPI:
        return bot.say('Git module not configured, make sure github.oauth_token and github.repo are defined')

    # parse input
    now = ' '.join(str(datetime.utcnow()).split(' ')).split('.')[0] + ' UTC'
    body = 'Submitted by: %s\nFrom channel: %s\nAt %s' % (trigger.nick, trigger.sender, now)
    data = {"title": trigger.group(2), "body": body}
    # submit
    try:
        raw = web.post('https://api.github.com/repos/' + gitAPI[1] + '/issues?access_token=' + gitAPI[0], json.dumps(data))
    except HTTPError:
        bot.say('The GitHub API returned an error.')
        return NOLIMIT

    data = json.loads(raw)
    bot.say('Issue #%s posted. %s' % (data['number'], data['html_url']))
    LOGGER.warning('Issue #%s created in %s', data['number'], trigger.sender)


@commands('addtrace', 'addtraceback')
def add_traceback(bot, trigger):
    """Add a traceback to a GitHub issue.

    This pulls the traceback from the exceptions log file. To use, put .addtrace
    followed by the issue number to add the comment to, then the signature of
    the error (the message shown to the channel when the error occured). This
    command will only work for errors from unhandled exceptions."""
    # Make sure the API is set up
    gitAPI = checkConfig(bot)
    if not gitAPI:
        return bot.say('GitHub module not configured, make sure github.oauth_token and github.repo are defined')

    if not trigger.group(2):
        bot.say('Please give both the issue number and the error message.')
        return

    # Make sure the input is valid
    args = trigger.group(2).split(None, 1)
    if len(args) != 2:
        bot.say('Please give both the issue number and the error message.')
        return
    number, trace = args

    # Make sure the given issue number exists
    issue_data = web.get('https://api.github.com/repos/%s/issues/%s' % (gitAPI[1], number))
    issue_data = json.loads(issue_data)
    if 'message' in issue_data and issue_data['message'] == 'Not Found':
        return bot.say("That issue doesn't exist.")

    # Find the relevant lines from the log file
    post = ''
    logfile = os.path.join(bot.config.logdir, 'exceptions.log')
    with open(logfile) as log:
        in_trace = False
        for data in log:
            if data == 'Signature: ' + trace + '\n':
                post = data
                in_trace = True
            elif data == '----------------------------------------\n':
                in_trace = False
            elif in_trace:
                post += data

    # Give an error if we didn't find the traceback
    if not post:
        return bot.say("I don't remember getting that error. Please post it "
                       "yourself at https://github.com/%s/issues/%s"
                       % (gitAPI[1], number))

    # Make the comment
    try:
        raw = web.post('https://api.github.com/repos/' + gitAPI[1] + '/issues/'
                       + number + '/comments?access_token=' + gitAPI[0],
                       json.dumps({'body': '``\n' + post + '``'}))
    except OSError:  # HTTPError:
        bot.say('The GitHub API returned an error.')
        return NOLIMIT

    data = json.loads(raw)
    bot.say('Added traceback to issue #%s. %s' % (number, data['html_url']))
    LOGGER.warning('Traceback added to #%s in %s.', number, trigger.sender)


@commands('findissue', 'findbug')
def findIssue(bot, trigger):
    """Search for a GitHub issue by keyword or ID. usage: .findissue search keywords/ID (optional) You can specify the first keyword as "CLOSED" to search closed issues."""
    if not trigger.group(2):
        return bot.reply('What are you searching for?')

    # Is the Oauth token and repo available?
    gitAPI = checkConfig(bot)
    if not gitAPI:
        return bot.say('Git module not configured, make sure github.oauth_token and github.repo are defined')
    firstParam = trigger.group(2).split(' ')[0]
    if firstParam.isdigit():
        URL = 'https://api.github.com/repos/%s/issues/%s' % (gitAPI[1], firstParam)
    elif firstParam == 'CLOSED':
        if '%20'.join(trigger.group(2).split(' ')[1:]) not in ('', '\x02', '\x03'):
            URL = 'https://api.github.com/legacy/issues/search/' + gitAPI[1] + '/closed/' + '%20'.join(trigger.group(2).split(' ')[1:])
        else:
            return bot.reply('What are you searching for?')
    else:
        URL = 'https://api.github.com/legacy/issues/search/%s/open/%s' % (gitAPI[1], web.quote(trigger.group(2)))

    try:
        raw = web.get(URL)
    except HTTPError:
        bot.say('The GitHub API returned an error.')
        return NOLIMIT

    try:
        if firstParam.isdigit():
            data = json.loads(raw)
        else:
            data = json.loads(raw)['issues'][-1]
    except (KeyError, IndexError):
        return bot.say('No search results.')
    try:
        if len(data['body'].split('\n')) > 1:
            body = data['body'].split('\n')[0] + '...'
        else:
            body = data['body'].split('\n')[0]
    except (KeyError):
        LOGGER.exception('API returned an invalid result on query request %s',
                      trigger.group(2))
        bot.say('Invalid result, please try again later.')
        return NOLIMIT
    bot.reply('[#%s]\x02title:\x02 %s \x02|\x02 %s' % (data['number'], data['title'], body))
    bot.say(data['html_url'])


@rule('.*%s.*' % issueURL)
def issue_info(bot, trigger, match=None):
    match = match or trigger
    URL = 'https://api.github.com/repos/%s/issues/%s' % (match.group(1), match.group(2))

    try:
        raw = web.get(URL)
    except HTTPError:
        bot.say('The GitHub API returned an error.')
        return NOLIMIT
    data = json.loads(raw)
    try:
        if len(data['body'].split('\n')) > 1:
            body = data['body'].split('\n')[0] + '...'
        else:
            body = data['body'].split('\n')[0]
    except (KeyError):
        bot.say('The API says this is an invalid issue. Please report this if you know it\'s a correct link!')
        return NOLIMIT
    bot.say('[#%s]\x02title:\x02 %s \x02|\x02 %s' % (data['number'], data['title'], body))
