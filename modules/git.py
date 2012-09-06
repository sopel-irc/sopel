#!/usr/bin/env python
"""
git.py - Jenni Github Module
Copyright 2012, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from datetime import datetime
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
    return willie.say('broken feature, requires a fix in web.py, gitted for testcases in local copies.')
    #check input
    if not trigger.group(2):
        return willie.say('Please title the issue')

    #Is the Oauth token and repo available?
    gitAPI = checkConfig(willie)
    if gitAPI == False:
        return willie.say('Git module not configured, make sure git_Oath_token and git_repo are defined')

    #parse input
    now = ' '.join(str(datetime.utcnow()).split(' ')).split('.')[0]+' UTC'
    body = 'submitted by: %s\nfrom channel: %s\nat %s' % (trigger.nick, trigger.sender, now)
    data = '{"title": "%s","body": %s,"labels": ["IRC"]}' % (trigger.group(2), body)
    #submit
    try:
        raw = web.post('https://api.github.com/repos/'+gitAPI[1]+'/issues?access_token='+gitAPI[0], data)
    except Exception as e:
        print ('%s %s %s' % (type(e), e.args, e))
        return willie.say('Exception while reaching the git API.')

    print raw
    return willie.say('Issue posted')
issue.commands = ['issue']
issue.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
