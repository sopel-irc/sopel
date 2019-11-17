# coding=utf-8
"""
help.py - Sopel Help Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Copyright © 2018, Adam Erdman, pandorah.org
Copyright © 2019, Tomasz Kurcz, github.com/uint
Copyright © 2019, dgw, technobabbl.es
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import collections
import logging
import socket
import textwrap

import requests

from sopel.config.types import ChoiceAttribute, ValidatedAttribute, StaticSection
from sopel.module import commands, rule, example, priority
from sopel.tools import SopelMemory


SETTING_CACHE_NAMESPACE = 'help-setting-cache'  # Set top-level memory key name
LOGGER = logging.getLogger(__name__)

# Settings that should require the help listing to be regenerated, or
# re-POSTed to paste, if they are changed during runtime.
# Keys are module names, and values are lists of setting names
# specific to that module.
TRACKED_SETTINGS = {
    'help': [
        'output',
        'show_server_host',
    ]
}


class PostingException(Exception):
    """Custom exception type for errors posting help to the chosen pastebin."""
    pass


# Pastebin handlers


def _requests_post_catch_errors(*args, **kwargs):
    try:
        response = requests.post(*args, **kwargs)
        response.raise_for_status()
    except (
            requests.exceptions.Timeout,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError
    ):
        # We re-raise all expected exception types to a generic "posting error"
        # that's easy for callers to expect, and then we pass the original
        # exception through to provide some debugging info
        LOGGER.exception('Error during POST request')
        raise PostingException('Could not communicate with remote service')

    # remaining handling (e.g. errors inside the response) is left to the caller
    return response


def post_to_clbin(msg):
    try:
        result = _requests_post_catch_errors('https://clbin.com/', data={'clbin': msg})
    except PostingException:
        raise

    result = result.text
    if re.match(r'https?://clbin\.com/', result):
        # find/replace just in case the site tries to be sneaky and save on SSL overhead,
        # though it will probably send us an HTTPS link without any tricks.
        return result.replace('http://', 'https://', 1)
    else:
        LOGGER.error("Invalid result %s", result)
        raise PostingException('clbin result did not contain expected URL base.')


def post_to_0x0(msg):
    try:
        result = _requests_post_catch_errors('https://0x0.st', files={'file': msg})
    except PostingException:
        raise

    result = result.text
    if re.match(r'https?://0x0\.st/', result):
        # find/replace just in case the site tries to be sneaky and save on SSL overhead,
        # though it will probably send us an HTTPS link without any tricks.
        return result.replace('http://', 'https://', 1)
    else:
        LOGGER.error('Invalid result %s', result)
        raise PostingException('0x0.st result did not contain expected URL base.')


def post_to_hastebin(msg):
    try:
        result = _requests_post_catch_errors('https://hastebin.com/documents', data=msg)
    except PostingException:
        raise

    try:
        result = result.json()
    except ValueError:
        LOGGER.error("Invalid Hastebin response %s", result)
        raise PostingException('Could not parse response from Hastebin!')

    if 'key' not in result:
        LOGGER.error("Invalid result %s", result)
        raise PostingException('Hastebin result did not contain expected URL base.')
    return "https://hastebin.com/" + result['key']


def post_to_termbin(msg):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)  # the bot may NOT wait forever for a response; that would be bad
    try:
        sock.connect(('termbin.com', 9999))
        sock.sendall(msg)
        sock.shutdown(socket.SHUT_WR)
        response = ""
        while 1:
            data = sock.recv(1024)
            if data == "":
                break
            response += data
        sock.close()
    except socket.error:
        LOGGER.exception('Error during communication with termbin')
        raise PostingException('Error uploading to termbin')

    # find/replace just in case the site tries to be sneaky and save on SSL overhead,
    # though it will probably send us an HTTPS link without any tricks.
    return response.strip('\x00\n').replace('http://', 'https://', 1)


def post_to_ubuntu(msg):
    data = {
        'poster': 'sopel',
        'syntax': 'text',
        'expiration': '',
        'content': msg,
    }
    result = _requests_post_catch_errors(
        'https://pastebin.ubuntu.com/', data=data)

    if not re.match(r'https://pastebin\.ubuntu\.com/p/[^/]+/', result.url):
        LOGGER.error("Invalid Ubuntu pastebin response url %s", result.url)
        raise PostingException(
            'Invalid response from Ubuntu pastebin: %s' % result.url)

    return result.url


PASTEBIN_PROVIDERS = {
    'clbin': post_to_clbin,
    '0x0': post_to_0x0,
    'hastebin': post_to_hastebin,
    'termbin': post_to_termbin,
    'ubuntu': post_to_ubuntu,
}
REPLY_METHODS = [
    'channel',
    'query',
    'notice',
]


class HelpSection(StaticSection):
    """Configuration section for this module."""
    output = ChoiceAttribute('output',
                             list(PASTEBIN_PROVIDERS),
                             default='clbin')
    """The pastebin provider to use for help output."""
    reply_method = ChoiceAttribute('reply_method',
                                   REPLY_METHODS,
                                   default='channel')
    """Where/how to reply to help commands (public/private)."""
    show_server_host = ValidatedAttribute('show_server_host', bool, default=True)
    """Show the IRC server's hostname/IP in the first line of the help listing?"""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | output | clbin | The pastebin provider to use for help output |
    | reply\\_method | channel | How/where help output should be sent |
    | show\\_server\\_host | True | Whether to show the IRC server's hostname/IP at the top of command listings |
    """
    config.define_section('help', HelpSection)
    provider_list = ', '.join(PASTEBIN_PROVIDERS)
    reply_method_list = ', '.join(REPLY_METHODS)
    config.help.configure_setting(
        'output',
        'Pick a pastebin provider: {}: '.format(provider_list)
    )
    config.help.configure_setting(
        'reply_method',
        'How/where should help command replies be sent: {}? '.format(reply_method_list)
    )
    config.help.configure_setting(
        'show_server_host',
        'Should the help command show the IRC server\'s hostname/IP in the listing?'
    )


def setup(bot):
    bot.config.define_section('help', HelpSection)

    # Initialize memory
    if SETTING_CACHE_NAMESPACE not in bot.memory:
        bot.memory[SETTING_CACHE_NAMESPACE] = SopelMemory()

    # Initialize settings cache
    for section in TRACKED_SETTINGS:
        if section not in bot.memory[SETTING_CACHE_NAMESPACE]:
            bot.memory[SETTING_CACHE_NAMESPACE][section] = SopelMemory()

    update_cache(bot)  # Populate cache

    bot.config.define_section('help', HelpSection)


def update_cache(bot):
    for section, setting_names_list in TRACKED_SETTINGS.items():
        for setting_name in setting_names_list:
            bot.memory[SETTING_CACHE_NAMESPACE][section][setting_name] = getattr(getattr(bot.config, section), setting_name)


def is_cache_valid(bot):
    for section, setting_names_list in TRACKED_SETTINGS.items():
        for setting_name in setting_names_list:
            if bot.memory[SETTING_CACHE_NAMESPACE][section][setting_name] != getattr(getattr(bot.config, section), setting_name):
                return False
    return True


@rule('$nick' r'(?i)(help|doc) +([A-Za-z]+)(?:\?+)?$')
@example('.help tell')
@commands('help', 'commands')
@priority('low')
def help(bot, trigger):
    """Shows a command's documentation, and an example if available. With no arguments, lists all commands."""
    if bot.config.help.reply_method == 'query':
        def respond(text):
            bot.say(text, trigger.nick)
    elif bot.config.help.reply_method == 'notice':
        def respond(text):
            bot.notice(text, trigger.nick)
    else:
        def respond(text):
            bot.say(text, trigger.sender)

    if trigger.group(2):
        name = trigger.group(2)
        name = name.lower()

        # number of lines of help to show
        threshold = 3

        if name in bot.doc:
            # count lines we're going to send
            # lines in command docstring, plus one line for example(s) if present (they're sent all on one line)
            if len(bot.doc[name][0]) + int(bool(bot.doc[name][1])) > threshold:
                if trigger.nick != trigger.sender:  # don't say that if asked in private
                    bot.reply('The documentation for this command is too long; '
                              'I\'m sending it to you in a private message.')

                def msgfun(l):
                    bot.say(l, trigger.nick)
            else:
                msgfun = respond

            for line in bot.doc[name][0]:
                msgfun(line)
            if bot.doc[name][1]:
                # Build a nice, grammatically-correct list of examples
                examples = ', '.join(bot.doc[name][1][:-2] + [' or '.join(bot.doc[name][1][-2:])])
                msgfun('e.g. ' + examples)
    else:
        # This'll probably catch most cases, without having to spend the time
        # actually creating the list first. Maybe worth storing the link and a
        # heuristic in the DB, too, so it persists across restarts. Would need a
        # command to regenerate, too...
        if (
            'command-list' in bot.memory and
            bot.memory['command-list'][0] == len(bot.command_groups) and
            is_cache_valid(bot)
        ):
            url = bot.memory['command-list'][1]
        else:
            respond("Hang on, I'm creating a list.")
            msgs = []

            name_length = max(6, max(len(k) for k in bot.command_groups.keys()))
            for category, cmds in collections.OrderedDict(sorted(bot.command_groups.items())).items():
                category = category.upper().ljust(name_length)
                cmds = set(cmds)  # remove duplicates
                cmds = '  '.join(cmds)
                msg = category + '  ' + cmds
                indent = ' ' * (name_length + 2)
                # Honestly not sure why this is a list here
                msgs.append('\n'.join(textwrap.wrap(msg, subsequent_indent=indent)))

            url = create_list(bot, '\n\n'.join(msgs))
            if not url:
                return
            bot.memory['command-list'] = (len(bot.command_groups), url)
            update_cache(bot)
        respond("I've posted a list of my commands at {0} - You can see "
                "more info about any of these commands by doing {1}help "
                "<command> (e.g. {1}help time)"
                .format(url, bot.config.core.help_prefix))


def create_list(bot, msg):
    """Creates & uploads the command list.

    Returns the URL from the chosen pastebin provider.
    """
    msg = 'Command listing for {}{}\n\n{}'.format(
        bot.nick,
        ('@' + bot.config.core.host) if bot.config.help.show_server_host else '',
        msg)

    try:
        result = PASTEBIN_PROVIDERS[bot.config.help.output](msg)
    except PostingException:
        bot.say("Sorry! Something went wrong.")
        LOGGER.exception("Error posting commands")
        return
    return result


@rule('$nick' r'(?i)help(?:[?!]+)?$')
@priority('low')
def help2(bot, trigger):
    response = (
        "Hi, I'm a bot. Say {1}commands to me in private for a list "
        "of my commands, or see https://sopel.chat for more "
        "general details. My owner is {0}."
        .format(bot.config.core.owner, bot.config.core.help_prefix))
    bot.reply(response)
