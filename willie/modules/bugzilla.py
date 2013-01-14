# coding=utf-8
"""
admin.py - Willie Bugzilla Module
Copyright © 2013, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""
from lxml import etree
import re
from willie import web
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
    """Show information about a Bugzilla bug."""
    domain = trigger.group(1)
    if domain not in willie.config.bugzilla.domains:
        return
    url = 'https://%s%sctype=xml&%s' % trigger.groups()
    data = web.get(url)
    bug = etree.fromstring(data).find('bug')
    
    message = ('[BUGZILLA] Product: %s | Component: %s | Version: %s | ' +
        'Importance: %s |  Status: %s | Assigned to: %s | Reported: %s | ' +
        'Modified: %s')
    
    if bug.find('resolution') is not None:
        status = bug.find('bug_status').text + ' ' + bug.find('resolution').text
    else:
        status = bug.find('bug_status').text
    
    message = message % (bug.find('product').text, bug.find('component').text,
        bug.find('version').text, 
        (bug.find('priority').text + ' ' + bug.find('bug_severity').text), # Importance
        status, bug.find('assigned_to').text, bug.find('creation_ts').text, 
        bug.find('delta_ts').text)
    willie.say(message)
show_bug.rule = r'.*https?://(\S+?)(/show_bug.cgi\?\S*?)(id=\d+).*'

