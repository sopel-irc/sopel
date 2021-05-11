# coding=utf-8
"""
isup.py - Sopel Website Status Check Plugin
Copyright 2011, Elsie Powell http://embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import requests

from sopel import plugin


PLUGIN_OUTPUT_PREFIX = '[isup] '


def get_site_url(site):
    """Get a ``site`` URL

    :param str site: the site to get URL for
    :return: a valid site URL
    :raise ValueError: when site is empty, or isn't well formatted

    The ``site`` argument is checked: its scheme must be ``http`` or ``https``,
    or a :exc:`ValueError` is raised.

    If the ``site`` does not have a scheme, ``http`` is used. If it doesn't
    have a TLD, a :exc:`ValueError` is raised.
    """
    site = site.strip() if site else ''
    if not site:
        raise ValueError('What site do you want to check?')

    if not site.startswith(('http://', 'https://')):
        if '://' in site:
            protocol = site.split('://')[0] + '://'
            raise ValueError('Try it again without the %s' % protocol)

        site = 'http://' + site

    domain = site.split('/')[2].split(':')[0]
    if '.' not in domain:
        raise ValueError('I need a fully qualified domain name (with a dot).')
    if domain.endswith(('.local', '.example', '.test', '.invalid', '.localhost')):
        raise ValueError("I can't check LAN-local or invalid domains.")

    return site


def handle_isup(bot, trigger, secure=True):
    """Handle the ``bot`` command from ``trigger``

    :param bot: Sopel instance
    :type bot: :class:`sopel.bot.SopelWrapper`
    :param trigger: Command's trigger instance
    :type trigger: :class:`sopel.trigger.Trigger`
    :param bool secure: Check SSL error if ``True`` (the default)
    """
    try:
        site = get_site_url(trigger.group(2))
        response = requests.head(site, verify=secure, timeout=(10.0, 5.0))
        response.raise_for_status()
    except ValueError as error:
        bot.reply(str(error))
    except requests.exceptions.SSLError:
        bot.say(
            '{} looks down to me (SSL error). Try using `{}isupinsecure`.'
            .format(site, bot.config.core.help_prefix))
    except requests.HTTPError:
        bot.say(
            '{} looks down to me (HTTP {} "{}").'
            .format(site, response.status_code, response.reason))
    except requests.ConnectTimeout:
        bot.say(
            '{} looks down to me (timed out while connecting).'
            .format(site))
    except requests.ReadTimeout:
        bot.say(
            '{} looks down to me (timed out waiting for reply).'
            .format(site))
    except requests.ConnectionError:
        bot.say(
            '{} looks down to me (connection error).'
            .format(site))
    else:
        # If no exception happened, the request must have succeeded.
        bot.say(site + ' looks fine to me.')


@plugin.command('isupinsecure')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def isup_insecure(bot, trigger):
    """Check if a website is up (without verifying HTTPS)."""
    handle_isup(bot, trigger, secure=False)


@plugin.command('isup')
@plugin.example('.isup google.com')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def isup(bot, trigger):
    """Check if a website is up or not."""
    handle_isup(bot, trigger, secure=True)
