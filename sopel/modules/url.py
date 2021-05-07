# coding=utf-8
"""
url.py - Sopel URL Title Plugin
Copyright 2010-2011, Michael Yanovich (yanovich.net) & Kenneth Sham
Copyright 2012-2013, Elsie Powell
Copyright 2013, Lior Ramati <firerogue517@gmail.com>
Copyright 2014, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import ipaddress
import logging
import re

import dns.resolver
import requests
from urllib3.exceptions import LocationValueError

from sopel import plugin, tools
from sopel.config import types
from sopel.tools import web

# Python3 vs Python2
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

LOGGER = logging.getLogger(__name__)
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/78.0.3904.108 Safari/537.36'
)
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8',
    'Accept-Language': 'en,en-US;q=0,5',
}
# These are used to clean up the title tag before actually parsing it. Not the
# world's best way to do this, but it'll do for now.
TITLE_TAG_DATA = re.compile('<(/?)title( [^>]+)?>', re.IGNORECASE)
QUOTED_TITLE = re.compile('[\'"]<title>[\'"]', re.IGNORECASE)
# This is another regex that presumably does something important.
RE_DCC = re.compile(r'(?i)dcc\ssend')
# This sets the maximum number of bytes that should be read in order to find
# the title. We don't want it too high, or a link to a big file/stream will
# just keep downloading until there's no more memory. 640k ought to be enough
# for anybody, but the modern web begs to differ.
MAX_BYTES = 655360 * 2


class UrlSection(types.StaticSection):
    enable_auto_title = types.BooleanAttribute(
        'enable_auto_title', default=True)
    """Enable auto-title (enabled by default)"""
    # TODO some validation rules maybe?
    exclude = types.ListAttribute('exclude')
    """A list of regular expressions to match URLs for which the title should not be shown."""
    exclusion_char = types.ValidatedAttribute('exclusion_char', default='!')
    """A character (or string) which, when immediately preceding a URL, will stop that URL's title from being shown."""
    shorten_url_length = types.ValidatedAttribute(
        'shorten_url_length', int, default=0)
    """If greater than 0, the title fetcher will include a TinyURL version of links longer than this many characters."""
    enable_private_resolution = types.BooleanAttribute(
        'enable_private_resolution', default=False)
    """Enable URL lookups for RFC1918 addresses"""
    enable_dns_resolution = types.BooleanAttribute(
        'enable_dns_resolution', default=False)
    """Enable DNS resolution for all domains to validate if there are RFC1918 resolutions"""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | enable_auto_title | yes | Enable auto-title. |
    | exclude | https?://git\\\\.io/.* | A list of regular expressions for URLs for which the title should not be shown. |
    | exclusion\\_char | ! | A character (or string) which, when immediately preceding a URL, will stop the URL's title from being shown. |
    | shorten\\_url\\_length | 72 | If greater than 0, the title fetcher will include a TinyURL version of links longer than this many characters. |
    | enable\\_private\\_resolution | False | Enable URL lookups for RFC1918 addresses. |
    | enable\\_dns\\_resolution | False | Enable DNS resolution for all domains to validate if there are RFC1918 resolutions. |
    """
    config.define_section('url', UrlSection)
    config.url.configure_setting(
        'enable_auto_title',
        'Enable auto-title?'
    )
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
    # callbacks list because 1, it's easier to deal with plugins that are still
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
        bot.memory['last_seen_url'] = tools.SopelIdentifierMemory()

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


@plugin.command('urlexclude', 'urlpexclude', 'urlban', 'urlpban')
@plugin.example('.urlpexclude example\\.com/\\w+', user_help=True)
@plugin.example('.urlexclude example.com/path', user_help=True)
@plugin.output_prefix('[url] ')
def url_ban(bot, trigger):
    """Exclude a URL from auto title.

    Use ``urlpexclude`` to exclude a pattern instead of a URL.
    """
    url = trigger.group(2)

    if not url:
        bot.reply('This command requires a URL to exclude.')
        return

    if trigger.group(1) in ['urlpexclude', 'urlpban']:
        # validate regex pattern
        try:
            re.compile(url)
        except re.error as err:
            bot.reply('Invalid regex pattern: %s' % err)
            return
    else:
        # escape the URL to ensure a valid pattern
        url = re.escape(url)

    patterns = bot.settings.url.exclude

    if url in patterns:
        bot.reply('This URL is already excluded from auto title.')
        return

    # update settings
    patterns.append(url)
    bot.settings.url.exclude = patterns  # set the config option
    bot.settings.save()
    LOGGER.info('%s excluded the URL pattern "%s"', trigger.nick, url)

    # re-compile
    bot.memory['url_exclude'] = [re.compile(s) for s in patterns]

    # tell the user
    bot.reply('This URL is now excluded from auto title.')


@plugin.command('urlallow', 'urlpallow', 'urlunban', 'urlpunban')
@plugin.example('.urlpallow example\\.com/\\w+', user_help=True)
@plugin.example('.urlallow example.com/path', user_help=True)
@plugin.output_prefix('[url] ')
def url_unban(bot, trigger):
    """Allow a URL for auto title.

    Use ``urlpallow`` to allow a pattern instead of a URL.
    """
    url = trigger.group(2)

    if not url:
        bot.reply('This command requires a URL to allow.')
        return

    if trigger.group(1) in ['urlpallow', 'urlpunban']:
        # validate regex pattern
        try:
            re.compile(url)
        except re.error as err:
            bot.reply('Invalid regex pattern: %s' % err)
            return
    else:
        # escape the URL to ensure a valid pattern
        url = re.escape(url)

    patterns = bot.settings.url.exclude

    if url not in patterns:
        bot.reply('This URL was not excluded from auto title.')
        return

    # update settings
    patterns.remove(url)
    bot.settings.url.exclude = patterns  # set the config option
    bot.settings.save()
    LOGGER.info('%s allowed the URL pattern "%s"', trigger.nick, url)

    # re-compile
    bot.memory['url_exclude'] = [re.compile(s) for s in patterns]

    # tell the user
    bot.reply('This URL is not excluded from auto title anymore.')


@plugin.command('title')
@plugin.example(
    '.title https://www.google.com',
    'Google | www.google.com',
    online=True, vcr=True)
@plugin.output_prefix('[url] ')
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
        urls = list(  # needs to be a list so len() can be checked later
            web.search_urls(
                trigger,
                exclusion_char=bot.config.url.exclusion_char
            )
        )

    result_count = 0
    for url, title, domain, tinyurl in process_urls(bot, trigger, urls):
        message = '%s | %s' % (title, domain)
        if tinyurl:
            message += ' ( %s )' % tinyurl
        bot.reply(message)
        bot.memory['last_seen_url'][trigger.sender] = url
        result_count += 1

    expected_count = len(urls)
    if result_count < expected_count:
        if expected_count == 1:
            bot.reply("Sorry, fetching that title failed. Make sure the site is working.")
        elif result_count == 0:
            bot.reply("Sorry, I couldn't fetch titles for any of those.")
        else:
            bot.reply("I couldn't get all of the titles, but I fetched what I could!")


@plugin.rule(r'(?u).*(https?://\S+).*')
@plugin.output_prefix('[url] ')
def title_auto(bot, trigger):
    """
    Automatically show titles for URLs. For shortened URLs/redirects, find
    where the URL redirects to and show the title for that (or call a function
    from another plugin to give more information).
    """
    # Enabled or disabled by feature flag
    if not bot.settings.url.enable_auto_title:
        return

    # Avoid fetching links from another command
    if re.match(bot.config.core.prefix + r'\S+', trigger):
        return

    # Avoid fetching known malicious links
    if 'safety_cache' in bot.memory and trigger in bot.memory['safety_cache']:
        if bot.memory['safety_cache'][trigger]['positives'] > 1:
            return

    urls = web.search_urls(
        trigger, exclusion_char=bot.config.url.exclusion_char, clean=True)

    for url, title, domain, tinyurl in process_urls(bot, trigger, urls):
        message = '%s | %s' % (title, domain)
        if tinyurl:
            message += ' ( %s )' % tinyurl
        # Guard against responding to other instances of this bot.
        if message != trigger:
            bot.say(message)
            bot.memory['last_seen_url'][trigger.sender] = url


def process_urls(bot, trigger, urls):
    """
    For each URL in the list, ensure that it isn't handled by another plugin.
    If not, find where it redirects to, if anywhere. If that redirected URL
    should be handled by another plugin, dispatch the callback for it.
    Return a list of (title, hostname) tuples for each URL which is not handled
    by another plugin.
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
                    LOGGER.debug('Ignoring private URL: %s', url)
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
                    LOGGER.debug('Ignoring private URL: %s', url)
                    continue

        # Call the URL to get a title, if possible
        title = find_title(url)
        if not title:
            # No title found: don't handle this URL
            LOGGER.warning('No title found; ignoring URL: %s', url)
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
    :return: True if ``url`` is excluded or matches any URL callback pattern

    This function looks at the ``bot.memory`` for ``url_exclude`` patterns and
    it returns ``True`` if any matches the given ``url``. Otherwise, it looks
    at the ``bot``'s URL callback patterns, and it returns ``True`` if any
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
    return (
        matched or
        any(bot.search_url_callbacks(url)) or
        bot.rules.check_url_callback(bot, url)
    )


def find_title(url, verify=True):
    """Return the title for the given URL."""
    try:
        response = requests.get(url, stream=True, verify=verify,
                                headers=DEFAULT_HEADERS)
        content = b''
        for byte in response.iter_content(chunk_size=512):
            content += byte
            if b'</title>' in content or len(content) > MAX_BYTES:
                break
        content = content.decode('utf-8', errors='ignore')
        # Need to close the connection because we have not read all
        # the data
        response.close()
    except requests.exceptions.ConnectionError:
        LOGGER.exception('Unable to reach URL: %s', url)
        return None
    except (
        requests.exceptions.InvalidURL,  # e.g. http:///
        UnicodeError,  # e.g. http://.example.com (urllib3<1.26)
        LocationValueError,  # e.g. http://.example.com (urllib3>=1.26)
    ):
        LOGGER.debug('Invalid URL: %s', url)
        return None

    # Some cleanup that I don't really grok, but was in the original, so
    # we'll keep it (with the compiled regexes made global) for now.
    content = TITLE_TAG_DATA.sub(r'<\1title>', content)
    content = QUOTED_TITLE.sub('', content)

    start = content.rfind('<title>')
    end = content.rfind('</title>')
    if start == -1 or end == -1:
        return
    title = web.decode(content[start + 7:end])
    title = title.strip()[:200]

    title = ' '.join(title.split())  # cleanly remove multiple spaces

    # More cryptic regex substitutions. This one looks to be myano's invention.
    title = RE_DCC.sub('', title)

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
