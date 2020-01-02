# coding=utf-8
"""
url.py - Sopel URL Title Module
Copyright 2010-2011, Michael Yanovich (yanovich.net) & Kenneth Sham
Copyright 2012-2013, Elsie Powell
Copyright 2013, Lior Ramati <firerogue517@gmail.com>
Copyright 2014, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re

import dns.resolver
import ipaddress
import requests

from sopel import __version__, module, tools
from sopel.config.types import ListAttribute, StaticSection, ValidatedAttribute
from sopel.tools import web

# Python3 vs Python2
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

USER_AGENT = 'Sopel/{} (https://sopel.chat)'.format(__version__)
default_headers = {'User-Agent': USER_AGENT}
# These are used to clean up the title tag before actually parsing it. Not the
# world's best way to do this, but it'll do for now.
title_tag_data = re.compile('<(/?)title( [^>]+)?>', re.IGNORECASE)
quoted_title = re.compile('[\'"]<title>[\'"]', re.IGNORECASE)
# This is another regex that presumably does something important.
re_dcc = re.compile(r'(?i)dcc\ssend')
# This sets the maximum number of bytes that should be read in order to find
# the title. We don't want it too high, or a link to a big file/stream will
# just keep downloading until there's no more memory. 640k ought to be enough
# for anybody.
max_bytes = 655360


class UrlSection(StaticSection):
    # TODO some validation rules maybe?
    exclude = ListAttribute('exclude')
    """A list of regular expressions to match URLs for which the title should not be shown."""
    exclusion_char = ValidatedAttribute('exclusion_char', default='!')
    """A character (or string) which, when immediately preceding a URL, will stop that URL's title from being shown."""
    shorten_url_length = ValidatedAttribute(
        'shorten_url_length', int, default=0)
    """If greater than 0, the title fetcher will include a TinyURL version of links longer than this many characters."""
    enable_private_resolution = ValidatedAttribute(
        'enable_private_resolution', bool, default=False)
    """Enable URL lookups for RFC1918 addresses"""
    enable_dns_resolution = ValidatedAttribute(
        'enable_dns_resolution', bool, default=False)
    """Enable DNS resolution for all domains to validate if there are RFC1918 resolutions"""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | exclude | https?://git\\\\.io/.* | A list of regular expressions for URLs for which the title should not be shown. |
    | exclusion\\_char | ! | A character (or string) which, when immediately preceding a URL, will stop the URL's title from being shown. |
    | shorten\\_url\\_length | 72 | If greater than 0, the title fetcher will include a TinyURL version of links longer than this many characters. |
    | enable\\_private\\_resolution | False | Enable URL lookups for RFC1918 addresses. |
    | enable\\_dns\\_resolution | False | Enable DNS resolution for all domains to validate if there are RFC1918 resolutions. |
    """
    config.define_section('url', UrlSection)
    config.url.configure_setting(
        'exclude',
        'Enter regular expressions for each URL you would like to exclude.'
    )
    config.url.configure_setting(
        'exclusion_char',
        'Enter a character which can be prefixed to suppress URL titling'
    )
    config.url.configure_setting(
        'shorten_url_length',
        'Enter how many characters a URL should be before the bot puts a'
        ' shorter version of the URL in the title as a TinyURL link'
        ' (0 to disable)'
    )
    config.url.configure_setting(
        'enable_private_resolution',
        'Enable URL lookups for RFC1918 addresses?'
    )
    config.url.configure_setting(
        'enable_dns_resolution',
        'Enable DNS resolution for all domains to validate if there are RFC1918 resolutions?'
    )


def setup(bot):
    bot.config.define_section('url', UrlSection)

    if bot.config.url.exclude:
        regexes = [re.compile(s) for s in bot.config.url.exclude]
    else:
        regexes = []

    # We're keeping these in their own list, rather than putting then in the
    # callbacks list because 1, it's easier to deal with modules that are still
    # using this list, and not the newer callbacks list and 2, having a lambda
    # just to pass is kinda ugly.
    if 'url_exclude' not in bot.memory:
        bot.memory['url_exclude'] = regexes
    else:
        exclude = bot.memory['url_exclude']
        if regexes:
            exclude.extend(regexes)
        bot.memory['url_exclude'] = exclude

    # Ensure last_seen_url is in memory
    if 'last_seen_url' not in bot.memory:
        bot.memory['last_seen_url'] = tools.SopelMemory()

    # Initialize shortened_urls as a dict if it doesn't exist.
    if 'shortened_urls' not in bot.memory:
        bot.memory['shortened_urls'] = tools.SopelMemory()


def shutdown(bot):
    # Unset `url_exclude` and `last_seen_url`, but not `shortened_urls`;
    # clearing `shortened_urls` will increase API calls. Leaving it in memory
    # should not lead to unexpected behavior.
    for key in ['url_exclude', 'last_seen_url']:
        try:
            del bot.memory[key]
        except KeyError:
            pass


@module.commands('title')
@module.example(
    '.title https://www.google.com',
    '[ Google ] - www.google.com',
    online=True)
def title_command(bot, trigger):
    """
    Show the title or URL information for the given URL, or the last URL seen
    in this channel.
    """
    if not trigger.group(2):
        if trigger.sender not in bot.memory['last_seen_url']:
            return
        matched = check_callbacks(
            bot, bot.memory['last_seen_url'][trigger.sender])
        if matched:
            return
        else:
            urls = [bot.memory['last_seen_url'][trigger.sender]]
    else:
        urls = web.search_urls(
            trigger,
            exclusion_char=bot.config.url.exclusion_char)

    for url, title, domain, tinyurl in process_urls(bot, trigger, urls):
        message = '[ %s ] - %s' % (title, domain)
        if tinyurl:
            message += ' ( %s )' % tinyurl
        bot.reply(message)
        bot.memory['last_seen_url'][trigger.sender] = url


@module.rule(r'(?u).*(https?://\S+).*')
def title_auto(bot, trigger):
    """
    Automatically show titles for URLs. For shortened URLs/redirects, find
    where the URL redirects to and show the title for that (or call a function
    from another module to give more information).
    """
    if re.match(bot.config.core.prefix + 'title', trigger):
        return

    # Avoid fetching known malicious links
    if 'safety_cache' in bot.memory and trigger in bot.memory['safety_cache']:
        if bot.memory['safety_cache'][trigger]['positives'] > 1:
            return

    urls = web.search_urls(
        trigger, exclusion_char=bot.config.url.exclusion_char, clean=True)

    for url, title, domain, tinyurl in process_urls(bot, trigger, urls):
        message = '[ %s ] - %s' % (title, domain)
        if tinyurl:
            message += ' ( %s )' % tinyurl
        # Guard against responding to other instances of this bot.
        if message != trigger:
            bot.say(message)
            bot.memory['last_seen_url'][trigger.sender] = url


def process_urls(bot, trigger, urls):
    """
    For each URL in the list, ensure that it isn't handled by another module.
    If not, find where it redirects to, if anywhere. If that redirected URL
    should be handled by another module, dispatch the callback for it.
    Return a list of (title, hostname) tuples for each URL which is not handled
    by another module.
    """
    shorten_url_length = bot.config.url.shorten_url_length
    for url in urls:
        # Exclude URLs that start with the exclusion char
        if url.startswith(bot.config.url.exclusion_char):
            continue

        # Check the URL does not match an existing URL callback
        if check_callbacks(bot, url):
            continue

        # Prevent private addresses from being queried if enable_private_resolution is False
        if not bot.config.url.enable_private_resolution:
            parsed = urlparse(url)
            # Check if it's an address like http://192.168.1.1
            try:
                if ipaddress.ip_address(parsed.hostname).is_private or ipaddress.ip_address(parsed.hostname).is_loopback:
                    continue
            except ValueError:
                pass

            # Check if domains are RFC1918 addresses if enable_dns_resolutions is set
            if bot.config.url.enable_dns_resolution:
                private = False
                for result in dns.resolver.query(parsed.hostname):
                    if ipaddress.ip_address(result).is_private or ipaddress.ip_address(parsed.hostname).is_loopback:
                        private = True
                        break
                if private:
                    continue

        # Call the URL to get a title, if possible
        title = find_title(url)
        if not title:
            # No title found: don't handle this URL
            continue

        # If the URL is over bot.config.url.shorten_url_length, shorten the URL
        tinyurl = None
        if (shorten_url_length > 0) and (len(url) > shorten_url_length):
            tinyurl = get_or_create_shorturl(bot, url)

        yield (url, title, get_hostname(url), tinyurl)


def check_callbacks(bot, url):
    """Check if ``url`` is excluded or matches any URL callback patterns.

    :param bot: Sopel instance
    :param str url: URL to check
    :return: True if ``url`` is excluded or matches any URL Callback pattern

    This function looks at the ``bot.memory`` for ``url_exclude`` patterns and
    it returns ``True`` if any matches the given ``url``. Otherwise, it looks
    at the ``bot``'s URL Callback patterns, and it returns ``True`` if any
    matches, ``False`` otherwise.

    .. seealso::

        The :func:`~sopel.modules.url.setup` function that defines the
        ``url_exclude`` in ``bot.memory``.

    .. versionchanged:: 7.0

        This function **does not** trigger URL callbacks anymore when ``url``
        matches a pattern.

    """
    # Check if it matches the exclusion list first
    matched = any(regex.search(url) for regex in bot.memory['url_exclude'])
    return matched or any(bot.search_url_callbacks(url))


def find_title(url, verify=True):
    """Return the title for the given URL."""
    try:
        response = requests.get(url, stream=True, verify=verify,
                                headers=default_headers)
        content = b''
        for byte in response.iter_content(chunk_size=512):
            content += byte
            if b'</title>' in content or len(content) > max_bytes:
                break
        content = content.decode('utf-8', errors='ignore')
        # Need to close the connection because we have not read all
        # the data
        response.close()
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.InvalidURL,  # e.g. http:///
        UnicodeError,  # e.g. http://.example.com
    ):
        return None

    # Some cleanup that I don't really grok, but was in the original, so
    # we'll keep it (with the compiled regexes made global) for now.
    content = title_tag_data.sub(r'<\1title>', content)
    content = quoted_title.sub('', content)

    start = content.rfind('<title>')
    end = content.rfind('</title>')
    if start == -1 or end == -1:
        return
    title = web.decode(content[start + 7:end])
    title = title.strip()[:200]

    title = ' '.join(title.split())  # cleanly remove multiple spaces

    # More cryptic regex substitutions. This one looks to be myano's invention.
    title = re_dcc.sub('', title)

    return title or None


def get_hostname(url):
    idx = 7
    if url.startswith('https://'):
        idx = 8
    elif url.startswith('ftp://'):
        idx = 6
    hostname = url[idx:]
    slash = hostname.find('/')
    if slash != -1:
        hostname = hostname[:slash]
    return hostname


def get_or_create_shorturl(bot, url):
    """Get or create a short URL for ``url``

    :param bot: Sopel instance
    :param str url: URL to get or create a short URL for
    :return: A short URL
    :rtype: str

    It gets the short URL for ``url`` from the bot's memory if it exists.
    Otherwise, it creates a short URL (see :func:`get_tinyurl`), stores it
    into the bot's memory, then returns it.
    """
    # Check bot memory to see if the shortened URL is already in
    # memory
    if url in bot.memory['shortened_urls']:
        return bot.memory['shortened_urls'][url]

    tinyurl = get_tinyurl(url)
    bot.memory['shortened_urls'][url] = tinyurl
    return tinyurl


def get_tinyurl(url):
    """Returns a shortened tinyURL link of the URL"""
    base_url = "https://tinyurl.com/api-create.php"
    tinyurl = "%s?%s" % (base_url, web.urlencode({'url': url}))
    try:
        res = requests.get(tinyurl)
        res.raise_for_status()
    except requests.exceptions.RequestException:
        return None
    # Replace text output with https instead of http to make the
    # result an HTTPS link.
    return res.text.replace("http://", "https://")


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
