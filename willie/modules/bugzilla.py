# coding=utf-8
"""
admin.py - Willie Bugzilla Module
Copyright © 2013, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""
import json
import re
import urllib
import urllib2


def configure(config):
    """
    
    | [bugzilla] | example | purpose |
    | ---- | ------- | ------- |
    | domains | bugzilla.redhat.com,bugzilla.mozilla.org | A list of Bugzilla issue tracker domains |
    """
    if config.option('Show extra information about Bugzilla issues', False):
        if not config.has_section('url'):
            config.add_section('url')
        config.add_list('bugzilla', 'domains', 'Enter the domains of the Bugzillas you want extra information from. (e.g. bugzilla.mozilla.org)',
            'Domain:')

def setup(willie):
    regexes = []
    if willie.config.has_option('bugzilla', 'domains'):
        for domain in willie.config.bugzilla.domains:
            regex = re.compile('%s/show_bug.cgi\?\S*?id=(\d+)' % domain)
            regexes.append(regex)
    
    if not willie.memory.contains('url_exclude'):
        willie.memory['url_exclude'] = [regex]
    else:
        exclude = willie.memory['url_exclude']
        exclude.extend(regexes)
        willie.memory['url_exclude'] = exclude

def show_bug(willie, trigger):
    domain = trigger.group(1)
    if domain not in willie.config.bugzilla.domains:
        return
    url = 'https://api-dev.%s/1.2/bug/%s' % trigger.groups()
    header = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = urllib2.urlopen(urllib2.Request(url, headers=header))
    data = json.loads(response.read())
    
    message = ('[BUGZILLA] Product: %s | Component: %s | Version: %s | ' +
        'Importance: %s |  Status: %s | Assigned to: %s | Reported: %s | ' +
        'Modified: %s')
    
    if 'resolution' in data:
        status = data['status'] + ' ' + data['resolution']
    else:
        status = data['status']
    
    message = message % (data['product'], data['component'], data['version'], 
        (data['priority'] + ' ' + data['severity']), # Importance
        status, data['assigned_to']['name'], data['creation_time'], 
        data['last_change_time'])
    willie.say(message)
show_bug.rule = r'.*https?://(\S+?)/show_bug.cgi\?\S*?id=(\d+).*'






