#!/usr/bin/env python
"""
git.py - Jenni Github Module
Copyright 2012, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from datetime import datetime
from urllib2 import HTTPError
import json, re, web

def checkConfig(willie):
    if not hasattr(willie.config, 'git_Oath_token'):
        return False
    if not hasattr(willie.config, 'git_repo'):
        return False
    else:
        return [willie.config.git_Oath_token, willie.config.git_repo]

def configure(config):
    chunk = ''
    if config.option('Configuring git module', True):
        config.interactive_add('git_Oath_token', 'Github API Oauth2 token', '')
        config.interactive_add('git_repo', 'Github repository', 'embolalia/willie')
        chunk = ("\ngit_Oath_token = '%s'\ngit_repo = '%s'\n"
                 % (config.git_Oath_token,config.git_repo))
    return chunk

def issue(willie, trigger):
    """Create a GitHub issue, also known as a bug report. Syntax: .issue Title of the bug report"""
    #check input
    if not trigger.group(2):
        return willie.say('Please title the issue')

    #Is the Oauth token and repo available?
    gitAPI = checkConfig(willie)
    if gitAPI == False:
        return willie.say('Git module not configured, make sure git_Oath_token and git_repo are defined')

    #parse input
    now = ' '.join(str(datetime.utcnow()).split(' ')).split('.')[0]+' UTC'
    body = 'Submitted by: %s\nFrom channel: %s\nAt %s' % (trigger.nick, trigger.sender, now)
    data = {"title":trigger.group(2).encode('utf-8'), "body":body, "labels": ["IRC"]}
    #submit
    try:
        raw = web.post('https://api.github.com/repos/'+gitAPI[1]+'/issues?access_token='+gitAPI[0], json.dumps(data))
    except HTTPError as e:
        return willie.say('The GitHub API returned an error.')
    
    data = json.loads(raw)
    willie.say('Issue #%s posted. %s' % (data['number'], data['html_url']))
    willie.debug('','Issue #%s created in %s' % (data['number'],trigger.sender),'warning')
issue.commands = ['issue']
issue.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()

