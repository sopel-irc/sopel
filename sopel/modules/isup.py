# coding=utf-8
"""
isup.py - Sopel Website Status Check Module
Copyright 2011, Elsie Powell http://embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import requests
from requests.exceptions import SSLError

from sopel.module import commands


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
        else:
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
    site = trigger.group(2)

    try:
        site = get_site_url(trigger.group(2))
    except ValueError as error:
        return bot.reply(str(error))

    try:
        response = requests.head(site, verify=secure).headers
    except SSLError:
        bot.say(site + ' looks down from here. Try using %sisupinsecure' % bot.config.core.help_prefix)
        return
    except Exception:
        bot.say(site + ' looks down from here.')
        return

    if response:
        bot.say(site + ' looks fine to me.')
    else:
        bot.say(site + ' is down from here.')


@commands('isupinsecure')
def isup_insecure(bot, trigger):
    """isup.me website status checker without SSL check"""
    handle_isup(bot, trigger, secure=False)


@commands('isup')
def isup(bot, trigger):
    """isup.me website status checker"""
    handle_isup(bot, trigger, secure=True)
