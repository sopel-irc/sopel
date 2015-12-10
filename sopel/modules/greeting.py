# coding=utf-8
"""
greeting.py - Greeting Module
Copyright 2015, Michael Stark, <stark3@gmail.com>
Licensed under the Eiffel Forum License 2.

http://sopel.chat/

This module looks for a greeting message defined in the config
"""

from __future__ import unicode_literals, absolute_import, print_function, division
from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.module import event, rule

class GreetingSection(StaticSection):
    join_message = ValidatedAttribute('join_message', default=None)
    """A message said by the bot when joining a channel."""

def setup(bot):
    bot.config.define_section('greeting', GreetingSection)

def configure(config):
    config.define_section('greeting', GreetingSection, validate=False)
    config.greeting.configure_setting(
        'join_message',
        "Enter a message to say upon joining a channel."
    )

@event('JOIN')
@rule('.*')
def greeting(bot, trigger):
    if bot.config.core.nick == trigger.nick and bot.config.greeting.join_message:
        bot.say(bot.config.greeting.join_message)
