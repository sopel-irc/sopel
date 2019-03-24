# coding=utf-8
"""URL title module"""
# Copyright 2010-2011, Michael Yanovich, yanovich.net, Kenneth Sham
# Copyright 2012-2013 Elsie Powell
# Copyright 2013      Lior Ramati (firerogue517@gmail.com)
# Copyright © 2014 Elad Alfassa <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import re
from sopel import web, tools, __version__
from sopel.module import commands, rule, example
from sopel.config.types import ValidatedAttribute, ListAttribute, StaticSection

import requests

USER_AGENT = 'Sopel/{} (https://sopel.chat)'.format(__version__)
default_headers = {'User-Agent': USER_AGENT}
find_urls = None
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
    exclusion_char = ValidatedAttribute('exclusion_char', default='!')
    shorten_url_length = ValidatedAttribute(
        'shorten_url_length', int, default=0)


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
    global find_urls

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

    # Ensure that url_callbacks and last_seen_url are in memory
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.SopelMemory()
    if not bot.memory.contains('last_seen_url'):
        bot.memory['last_seen_url'] = tools.SopelMemory()

    def find_func(text, clean=False):
        def trim_url(url):
            # clean trailing sentence- or clause-ending punctuation
            while url[-1] in '.,?!\'":;':
                url = url[:-1]

            # clean unmatched parentheses/braces/brackets
            for (opener, closer) in [('(', ')'), ('[', ']'), ('{', '}'), ('<', '>')]:
                if (url[-1] == closer) and (url.count(opener) < url.count(closer)):
                    url = url[:-1]

            return url

        re_url = r'(?u)((?<!%s)(?:http|https|ftp)(?::\/\/\S+))'\
            % (bot.config.url.exclusion_char)
        r = re.compile(re_url, re.IGNORECASE)

        urls = re.findall(r, text)
        if clean:
            urls = [trim_url(url) for url in urls]
        return urls

    find_urls = find_func


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
        matched = check_callbacks(bot, trigger,
                                  bot.memory['last_seen_url'][trigger.sender],
                                  True)
        if matched:
            return
        else:
            urls = [bot.memory['last_seen_url'][trigger.sender]]
    else:
        urls = find_urls(trigger)

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

    urls = find_urls(trigger, clean=True)
    if len(urls) == 0:
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
    Return a list of (title, hostname) tuples for each URL which is not handled by
    another module.
    """

    results = []
    shorten_url_length = bot.config.url.shorten_url_length
    for url in urls:
        if not url.startswith(bot.config.url.exclusion_char):
            # Magic stuff to account for international domain names
            try:
                url = web.iri_to_uri(url)
            except Exception:  # TODO: Be specific
                pass
            # First, check that the URL we got doesn't match
            matched = check_callbacks(bot, trigger, url, False)
            if matched:
                continue
            # If the URL is over bot.config.url.shorten_url_length,
            # shorten the URL
            tinyurl = None
            if (shorten_url_length > 0) and (len(url) > shorten_url_length):
                # Check bot memory to see if the shortened URL is already in
                # memory
                if not bot.memory.contains('shortened_urls'):
                    # Initialize shortened_urls as a dict if it doesn't exist.
                    bot.memory['shortened_urls'] = tools.SopelMemory()
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


def check_callbacks(bot, trigger, url, run=True):
    """
    Check the given URL against the callbacks list. If it matches, and ``run``
    is given as ``True``, run the callback function, otherwise pass. Returns
    ``True`` if the url matched anything in the callbacks list.
    """
    # Check if it matches the exclusion list first
    matched = any(regex.search(url) for regex in bot.memory['url_exclude'])
    # Then, check if there's anything in the callback list
    for regex, function in tools.iteritems(bot.memory['url_callbacks']):
        match = regex.search(url)
        if match:
            # Always run ones from @url; they don't run on their own.
            if run or hasattr(function, 'url_regex'):
                function(bot, trigger, match)
            matched = True
    return matched


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
