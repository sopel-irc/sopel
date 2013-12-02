# -*- coding: utf8 -*-
"""
bitly.py - Willie Bitly Module

Copyright 2013, Tao Sauvage, depierre.tonbnc.fr
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net

This module shortens the URLs using a python bitly api. Information about
bitly-fied URLs can be retrieved with .last, .expand and .clicks.
"""


import re
import bitly_api
from willie.module import rule
from willie.module import example
from willie.module import commands
from willie.config import ConfigurationError


# Not a hack. It's a walk around.
RE_URL = r'https?://\S*'
RE_HAS_URL = r'.*(' + RE_URL + ').*'


def configure(config):
    """Provide configuration for Bitly uses.

    | [bitly] | example | purpose |
    | ---- | ------- | ------- |
    | access_token | default123 | The access token for Bitly |
    | max_length | 79 | The max length of your irc client line |

    """

    if config.option('Configure Bitly', False):
        # Access token for using Bitly's API
        # cf. https://github.com/bitly/bitly-api-python/blob/master/README.md
        config.add_section('bitly')
        config.interactive_add(
            'bitly',
            'access_token',
            'Enter the access token for Bitly:',
            'default123'
        )
        # Max length of the irc client lines
        config.interactive_add(
            'bitly',
            'max_length',
            'Enter the max length of your irc client line:',
            79
        )


def setup(bot):
    if not bot.config.has_option('bitly', 'access_token'):
        raise ConfigurationError(
            'bitly needs the access token in order to use the Bitly API'
        )
    if not bot.config.has_option('bitly', 'max_length'):
        bot.config.bitly.max_length = 79
    else:
        try:
            bot.config.bitly.max_length = int(bot.config.bitly.max_length)
        except ValueError:  # Back to the default value
            bot.config.bitly.max_length = 79

    regex = re.compile(RE_HAS_URL)
    if not bot.memory.contains(u'url_callbacks'):
        bot.memory[u'url_callbacks'] = {regex, bitly_url}
    else:
        exclude = bot.memory[u'url_callbacks']
        exclude[regex] = bitly_url
        bot.memory[u'url_callbacks'] = exclude

    if not bot.memory.contains(u'bitly_client'):
        bot.memory[u'bitly_client'] = bitly_api.Connection(
            access_token=bot.config.bitly.access_token
        )


@rule(RE_HAS_URL)
def bitly_url(bot, trigger):
    """Callback function when an URL is detected."""
    urls = [m.span() for m in re.finditer(RE_URL, trigger)]
    max_length = bot.config.bitly.max_length

    if bot.memory.contains(u'bitly_client'):
        for start, end in urls:
            # If the URL is not inline
            if start / max_length != end / max_length:
                try:
                    bot.memory[u'bitly_url'] = bot.memory[
                        u'bitly_client'
                    ].shorten(trigger[start:end])
                    bot.say(bot.memory[u'bitly_url'][u'url'])
                except bitly_api.BitlyError as e:
                    # If Bitly failed, we do nothing.
                    # Can happen when the matched url is already a bit.ly.
                    # TODO: Maybe we should log the errors
                    pass


@commands('last', 'lastest', 'new', 'newest')
@example('.last')
def bitly_last_url(bot, trigger):
    """Display the shortened version of the last URL using bitly."""

    if bot.memory.contains(u'bitly_url'):
        bot.say(trigger.nick + ': ' + bot.memory[u'bitly_url'][u'url'])


@commands('expand', 'long')
@example('.expand')
def bitly_expand_url(bot, trigger):
    """Display the expanded version of the last bitly URL."""

    if bot.memory.contains(u'bitly_url'):
        bot.say(trigger.nick + ': ' + bot.memory[u'bitly_url'][u'long_url'])


@commands('clicks')
@example('.clicks')
def bitly_clicks(bot, trigger):
    """Display the statistics about the user clicks on the last bitly URL."""

    if bot.memory.contains(u'bitly_client') and \
            bot.memory.contains(u'bitly_url'):
        bot.say(
            trigger.nick +
            ': ' +
            str(
                bot.memory[u'bitly_client'].link_clicks(
                    bot.memory[u'bitly_url'][u'url']
                )
            ) +
            ' click(s) on ' +
            bot.memory[u'bitly_url'][u'url']
        )
