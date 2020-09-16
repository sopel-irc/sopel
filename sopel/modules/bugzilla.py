# coding=utf-8
"""
bugzilla.py - Sopel Bugzilla Plugin
Copyright 2013-2015, Embolalia, embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import re

import requests
import xmltodict

from sopel import plugin, plugins
from sopel.config import types

LOGGER = logging.getLogger(__name__)


class BugzillaSection(types.StaticSection):
    domains = types.ListAttribute('domains')
    """A list of Bugzilla issue tracker domains from which to get information."""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | domains | bugzilla.redhat.com,bugzilla.mozilla.org | A list of Bugzilla issue tracker domains |
    """
    config.define_section('bugzilla', BugzillaSection)
    config.bugzilla.configure_setting(
        'domains',
        'Enter the domains of the Bugzillas you want extra information '
        'from (e.g. bugzilla.gnome.org)'
    )


def setup(bot):
    bot.config.define_section('bugzilla', BugzillaSection)


def _bugzilla_loader(settings):
    if not settings.bugzilla.domains:
        raise plugins.exceptions.PluginSettingsError(
            'Bugzilla URL callback requires '
            '"bugzilla.domains" to be configured; check your config file.')

    domain_pattern = '|'.join(
        re.escape(domain)
        for domain in settings.bugzilla.domains)

    pattern = (
        r'https?://(%s)'
        r'(/show_bug.cgi\?\S*?)'
        r'(id=\d+).*'
    ) % domain_pattern

    return [re.compile(pattern)]


@plugin.url_lazy(_bugzilla_loader)
@plugin.output_prefix('[BUGZILLA] ')
def show_bug(bot, trigger, match=None):
    """Show information about a Bugzilla bug."""
    url = 'https://%s%sctype=xml&%s' % trigger.groups()
    data = requests.get(url).content
    bug = xmltodict.parse(data).get('bugzilla').get('bug')
    error = bug.get('@error', None)  # error="NotPermitted"

    if error:
        LOGGER.warning('Bugzilla error: %s' % error)
        bot.say('Unable to get information for '
                'linked bug (%s)' % error)
        return

    message = ('%s | Product: %s | Component: %s | Version: %s | ' +
               'Importance: %s |  Status: %s | Assigned to: %s | ' +
               'Reported: %s | Modified: %s')

    resolution = bug.get('resolution')
    if resolution is not None:
        status = bug.get('bug_status') + ' ' + resolution
    else:
        status = bug.get('bug_status')

    assigned_to = bug.get('assigned_to')
    if isinstance(assigned_to, dict):
        assigned_to = assigned_to.get('@name')

    message = message % (
        bug.get('short_desc'), bug.get('product'),
        bug.get('component'), bug.get('version'),
        (bug.get('priority') + ' ' + bug.get('bug_severity')),
        status, assigned_to, bug.get('creation_ts'),
        bug.get('delta_ts'))
    bot.say(message)
