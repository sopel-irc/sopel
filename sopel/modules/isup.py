# coding=utf-8
"""
isup.py - Sopel Website Status Check Module
Copyright 2011, Elsie Powell http://embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import requests

from sopel import module


def get_site_url(site):
    """Get a ``site`` URL

    :param str site: the site to get URL for
    :return: a valid site URL
    :raise ValueError: when site is empty, or isn't well formatted

    The ``site`` argument is checked: its scheme must be ``http`` or ``https``,
    or a :exc:`ValueError` is raised.

    If the ``site`` does not have a scheme, ``http`` is used. If it doesn't
    have a TLD, ``.com`` is used.
    """
    site = site.strip() if site else ''
    if not site:
        raise ValueError('What site do you want to check?')

    if site[:7] != 'http://' and site[:8] != 'https://':
        if '://' in site:
            protocol = site.split('://')[0] + '://'
            raise ValueError('Try it again without the %s' % protocol)

        site = 'http://' + site

    if '.' not in site:
        site += ".com"

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
        response = requests.head(site, verify=secure).headers
    except ValueError as error:
        bot.reply(str(error))
    except requests.exceptions.SSLError:
        bot.say(
            '%s looks down from here. Try using %sisupinsecure'
            % (site, bot.config.core.help_prefix))
    except requests.RequestException:
        bot.say('%s looks down from here.' % site)
    else:
        if response:
            bot.say(site + ' looks fine to me.')
        else:
            bot.say(site + ' is down from here.')


@module.commands('isupinsecure')
def isup_insecure(bot, trigger):
    """Check if a website is up (without verifying HTTPS)."""
    handle_isup(bot, trigger, secure=False)


@module.commands('isup')
def isup(bot, trigger):
    """Check if a website is up or not."""
    handle_isup(bot, trigger, secure=True)
