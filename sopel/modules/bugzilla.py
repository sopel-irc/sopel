# coding=utf-8
"""Bugzilla issue reporting module

Copyright 2013-2015, Embolalia, embolalia.com
Licensed under the Eiffel Forum License 2.
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import xmltodict
import re
from sopel import web, tools
from sopel.module import rule
from sopel.config.types import StaticSection, ListAttribute


regex = None


class BugzillaSection(StaticSection):
    domains = ListAttribute('domains')
    """The domains of the Bugzilla instances from which to get information."""


def configure(config):
    config.define_section('bugzilla', BugzillaSection)
    config.bugzilla.configure_setting(
        'domains',
        'Enter the domains of the Bugzillas you want extra information '
        'from (e.g. bugzilla.gnome.org)'
    )


def setup(bot):
    global regex
    bot.config.define_section('bugzilla', BugzillaSection)

    if not bot.config.bugzilla.domains:
        return
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.SopelMemory()

    domains = '|'.join(bot.config.bugzilla.domains)
    regex = re.compile((r'https?://(%s)'
                        '(/show_bug.cgi\?\S*?)'
                        '(id=\d+)')
                       % domains)
    bot.memory['url_callbacks'][regex] = show_bug


def shutdown(bot):
    del bot.memory['url_callbacks'][regex]


@rule(r'.*https?://(\S+?)'
      '(/show_bug.cgi\?\S*?)'
      '(id=\d+).*')
def show_bug(bot, trigger, match=None):
    """Show information about a Bugzilla bug."""
    match = match or trigger
    domain = match.group(1)
    if domain not in bot.config.bugzilla.domains:
        return
    url = 'https://%s%sctype=xml&%s' % match.groups()
    data = web.get(url, dont_decode=True)
    bug = xmltodict.parse(data).get('bugzilla').get('bug')

    message = ('[BUGZILLA] %s | Product: %s | Component: %s | Version: %s | ' +
               'Importance: %s |  Status: %s | Assigned to: %s | ' +
               'Reported: %s | Modified: %s')

    resolution = bug.get('resolution')
    if resolution is not None:
        status = bug.get('bug_status') + ' ' + resolution
    else:
        status = bug.get('bug_status')

    message = message % (
        bug.get('short_desc'), bug.get('product'),
        bug.get('component'), bug.get('version'),
        (bug.get('priority') + ' ' + bug.get('bug_severity')),
        status, bug.get('assigned_to').get('@name'), bug.get('creation_ts'),
        bug.get('delta_ts'))
    bot.say(message)
