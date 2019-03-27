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

import requests

from sopel import web, tools, __version__
from sopel.config.types import ValidatedAttribute, ListAttribute, StaticSection
from sopel.module import commands, rule, example


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


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | exclude | https?://git\\\\.io/.* | A list of regular expressions for URLs for which the title should not be shown. |
    | exclusion\\_char | ! | A character (or string) which, when immediately preceding a URL, will stop the URL's title from being shown. |
    | shorten\\_url\\_length | 72 | If greater than 0, the title fetcher will include a TinyURL version of links longer than this many characters. |
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
    if not bot.memory.contains('url_exclude'):
        bot.memory['url_exclude'] = regexes
    else:
        exclude = bot.memory['url_exclude']
        if regexes:
            exclude.extend(regexes)
        bot.memory['url_exclude'] = exclude

    # Ensure last_seen_url is in memory
    if not bot.memory.contains('last_seen_url'):
        bot.memory['last_seen_url'] = tools.SopelMemory()

    # Initialize shortened_urls as a dict if it doesn't exist.
    if not bot.memory.contains('shortened_urls'):
        bot.memory['shortened_urls'] = tools.SopelMemory()


@commands('title')
@example('.title http://google.com', '[ Google ] - google.com')
def title_command(bot, trigger):
    """
    Show the title or URL information for the given URL, or the last URL seen
    in this channel.
    """
    if not trigger.group(2):
        if trigger.sender not in bot.memory['last_seen_url']:
            return
        matched = check_callbacks(
            bot, trigger, bot.memory['last_seen_url'][trigger.sender])
        if matched:
            return
        else:
            urls = [bot.memory['last_seen_url'][trigger.sender]]
    else:
        urls = list(
            web.search_urls(
                trigger,
                exclusion_char=bot.config.url.exclusion_char
            )
        )

    results = process_urls(bot, trigger, urls)
    for title, domain, tinyurl in results[:4]:
        message = '[ %s ] - %s' % (title, domain)
        if tinyurl:
            message += ' ( %s )' % tinyurl
        bot.reply(message)

    # Nice to have different failure messages for one-and-only requested URL
    # failed vs. one-of-many failed.
    if len(urls) == 1 and not results:
        bot.reply('Sorry, fetching that title failed. Make sure the site is working.')
    elif len(urls) > len(results):
        bot.reply('I couldn\'t get all of the titles, but I fetched what I could!')


@rule(r'(?u).*(https?://\S+).*')
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

    urls = list(
        web.search_urls(
            trigger,
            exclusion_char=bot.config.url.exclusion_char,
            clean=True))

    if not urls:
        return

    results = process_urls(bot, trigger, urls)
    bot.memory['last_seen_url'][trigger.sender] = urls[-1]

    for title, domain, tinyurl in results[:4]:
        message = '[ %s ] - %s' % (title, domain)
        if tinyurl:
            message += ' ( %s )' % tinyurl
        # Guard against responding to other instances of this bot.
        if message != trigger:
            bot.say(message)


def process_urls(bot, trigger, urls):
    """
    For each URL in the list, ensure that it isn't handled by another module.
    If not, find where it redirects to, if anywhere. If that redirected URL
    should be handled by another module, dispatch the callback for it.
    Return a list of (title, hostname) tuples for each URL which is not handled
    by another module.
    """
    results = []
    shorten_url_length = bot.config.url.shorten_url_length
    for url in urls:
        if not url.startswith(bot.config.url.exclusion_char):
            # First, check that the URL we got doesn't match
            if check_callbacks(bot, trigger, url):
                continue
            # If the URL is over bot.config.url.shorten_url_length,
            # shorten the URL
            tinyurl = None
            if (shorten_url_length > 0) and (len(url) > shorten_url_length):
                # Check bot memory to see if the shortened URL is already in
                # memory
                if bot.memory['shortened_urls'].contains(url):
                    tinyurl = bot.memory['shortened_urls'][url]
                else:
                    tinyurl = get_tinyurl(url)
                    bot.memory['shortened_urls'][url] = tinyurl
            # Finally, actually show the URL
            title = find_title(url, verify=bot.config.core.verify_ssl)
            if title:
                results.append((title, get_hostname(url), tinyurl))
    return results


def check_callbacks(bot, trigger, url):
    """Check if ``url`` is excluded or matches any URL callback patterns.

    :param bot: Sopel instance
    :param trigger: IRC line
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
    except requests.exceptions.ConnectionError:
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


def get_tinyurl(url):
    """ Returns a shortened tinyURL link of the URL. """
    tinyurl = "https://tinyurl.com/api-create.php?url=%s" % url
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
