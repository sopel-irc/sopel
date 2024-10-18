"""
url.py - Sopel URL Title Plugin
Copyright 2010-2011, Michael Yanovich (yanovich.net) & Kenneth Sham
Copyright 2012-2013, Elsie Powell
Copyright 2013, Lior Ramati <firerogue517@gmail.com>
Copyright 2014, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

from ipaddress import ip_address
import logging
import re
from typing import NamedTuple, Optional, TYPE_CHECKING
from urllib.parse import urlparse

import dns.resolver
import requests
from urllib3.exceptions import LocationValueError  # type: ignore[import]

from sopel import plugin, privileges, tools
from sopel.config import types
from sopel.tools import web

if TYPE_CHECKING:
    from collections.abc import Generator
    from sopel.bot import Sopel, SopelWrapper
    from sopel.config import Config
    from sopel.trigger import Trigger


LOGGER = logging.getLogger(__name__)
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/98.0.4758.102 Safari/537.36'
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
    exclude_required_access = types.ChoiceAttribute(
        'exclude_required_access',
        choices=privileges.__all__,
        default='OP',
    )
    """Minimum channel access level required to edit ``exclude`` list using chat commands."""
    exclusion_char = types.ValidatedAttribute('exclusion_char', default='!')
    """A character (or string) which, when immediately preceding a URL, will stop that URL's title from being shown."""
    shorten_url_length = types.ValidatedAttribute(
        'shorten_url_length', int, default=0)
    """If greater than 0, the title fetcher will include a TinyURL version of links longer than this many characters."""
    enable_private_resolution = types.BooleanAttribute(
        'enable_private_resolution', default=False)
    """Enable requests to private and local network IP addresses"""


def configure(config: Config) -> None:
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | enable_auto_title | yes | Enable auto-title. |
    | exclude | https?://git\\\\.io/.* | A list of regular expressions for URLs for which the title should not be shown. |
    | exclusion\\_char | ! | A character (or string) which, when immediately preceding a URL, will stop the URL's title from being shown. |
    | shorten\\_url\\_length | 72 | If greater than 0, the title fetcher will include a TinyURL version of links longer than this many characters. |
    | enable\\_private\\_resolution | False | Enable requests to private and local network IP addresses. |
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
        'Enable requests to private and local network IP addresses?'
    )


def setup(bot: Sopel) -> None:
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
        bot.memory['last_seen_url'] = bot.make_identifier_memory()

    # Initialize shortened_urls as a dict if it doesn't exist.
    if 'shortened_urls' not in bot.memory:
        bot.memory['shortened_urls'] = tools.SopelMemory()


def shutdown(bot: Sopel) -> None:
    # Unset `url_exclude` and `last_seen_url`, but not `shortened_urls`;
    # clearing `shortened_urls` will increase API calls. Leaving it in memory
    # should not lead to unexpected behavior.
    for key in ['url_exclude', 'last_seen_url']:
        try:
            del bot.memory[key]
        except KeyError:
            pass


def _user_can_change_excludes(bot: SopelWrapper, trigger: Trigger) -> bool:
    if trigger.admin:
        return True

    required_access = bot.config.url.exclude_required_access
    channel = bot.channels[trigger.sender]
    user_access = channel.privileges[trigger.nick]

    if user_access >= getattr(privileges, required_access):
        return True

    return False


@plugin.command('urlexclude', 'urlpexclude', 'urlban', 'urlpban')
@plugin.example('.urlpexclude example\\.com/\\w+', user_help=True)
@plugin.example('.urlexclude example.com/path', user_help=True)
@plugin.output_prefix('[url] ')
def url_ban(bot: SopelWrapper, trigger: Trigger) -> None:
    """Exclude a URL from auto title.

    Use ``urlpexclude`` to exclude a pattern instead of a URL.
    """
    url = trigger.group(2)

    if not url:
        bot.reply('This command requires a URL to exclude.')
        return

    if not _user_can_change_excludes(bot, trigger):
        bot.reply(
            'Only admins and channel members with %s access or higher may '
            'modify URL excludes.' % bot.config.url.exclude_required_access)
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
def url_unban(bot: SopelWrapper, trigger: Trigger) -> None:
    """Allow a URL for auto title.

    Use ``urlpallow`` to allow a pattern instead of a URL.
    """
    url = trigger.group(2)

    if not url:
        bot.reply('This command requires a URL to allow.')
        return

    if not _user_can_change_excludes(bot, trigger):
        bot.reply(
            'Only admins and channel members with %s access or higher may '
            'modify URL excludes.' % bot.config.url.exclude_required_access)
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
def title_command(bot: SopelWrapper, trigger: Trigger) -> None:
    """
    Show the title or URL information for the given URL, or the last URL seen
    in this channel.
    """
    result_count = 0

    if not trigger.group(2):
        if trigger.sender not in bot.memory['last_seen_url']:
            return
        urls = [bot.memory["last_seen_url"][trigger.sender]]
    else:
        # needs to be a list so len() can be checked later
        urls = list(web.search_urls(trigger))

    for url, title, domain, tinyurl, ignored in process_urls(
        bot, trigger, urls, requested=True
    ):
        if ignored:
            result_count += 1
            continue
        message = "%s | %s" % (title, domain)
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
def title_auto(bot: SopelWrapper, trigger: Trigger) -> None:
    """
    Automatically show titles for URLs. For shortened URLs/redirects, find
    where the URL redirects to and show the title for that.

    .. note::

        URLs that match (before redirection) any other registered callbacks
        will *not* have their titles shown.

    """
    # Enabled or disabled by feature flag
    if not bot.settings.url.enable_auto_title:
        return

    # Avoid fetching links from another command
    if re.match(bot.config.core.prefix + r'\S+', trigger):
        return

    unchecked_urls = web.search_urls(
        trigger, exclusion_char=bot.config.url.exclusion_char, clean=True)

    urls = []
    safety_cache = bot.memory.get("safety_cache", {})
    safety_cache_local = bot.memory.get("safety_cache_local", {})
    for url in unchecked_urls:
        # Avoid fetching known malicious links
        if url in safety_cache and safety_cache[url]["positives"] > 0:
            continue
        parsed = urlparse(url)
        if not parsed.hostname or parsed.hostname.lower() in safety_cache_local:
            continue
        urls.append(url)

    for url, title, domain, tinyurl, ignored in process_urls(bot, trigger, urls):
        if not ignored:
            message = '%s | %s' % (title, domain)
            if tinyurl:
                message += ' ( %s )' % tinyurl
            # Guard against responding to other instances of this bot.
            if message != trigger:
                bot.say(message)
        bot.memory["last_seen_url"][trigger.sender] = url


class URLInfo(NamedTuple):
    """Helper class for information about a URL handled by this plugin."""

    url: str

    title: Optional[str]
    """The title associated with ``url``, if appropriate."""

    hostname: Optional[str]
    """The hostname associated with ``url``, if appropriate."""

    tinyurl: Optional[str]
    """A shortened form of ``url``, if appropriate."""

    ignored: bool
    """Whether or not this URL matches any registered callbacks or is explicitly excluded."""


def process_urls(
    bot: SopelWrapper,
    trigger: Trigger,
    urls: list[str],
    requested: bool = False,
) -> Generator[URLInfo, None, None]:
    """
    For each URL in the list, ensure it should be titled, and do so.

    :param bot: Sopel instance
    :param trigger: The trigger object for this event
    :param urls: The URLs detected in the triggering message
    :param requested: Whether the title was explicitly requested (vs automatic)

    Yields a tuple ``(url, title, hostname, tinyurl, ignored)`` for each URL.

    .. note:

        If a URL in ``urls`` has any registered callbacks, this function will NOT
        retrieve the title, and considers the URL as dispatched to those callbacks.
        In this case, only the ``url`` and ``ignored=True`` will be set; all
        other values will be ``None``.

    .. note:

        For titles explicitly requested by the user, ``exclusion_char`` and
        exclusions from the ``.urlban``/``.urlpban`` commands are skipped.

    .. versionchanged:: 8.0

        This function **does not** notify callbacks registered for URLs
        redirected to from URLs passed to this function. See #2432, #2230.

    """
    shorten_url_length = bot.config.url.shorten_url_length
    for url in urls:
        # Exclude URLs that start with the exclusion char
        if not requested and url.startswith(bot.config.url.exclusion_char):
            continue

        parsed_url = urlparse(url)

        if check_callbacks(bot, url, use_excludes=not requested):
            # URL matches a callback OR is excluded, ignore
            yield URLInfo(url, None, None, None, True)
            continue

        # Prevent private addresses from being queried if enable_private_resolution is False
        # FIXME: This does nothing when an attacker knows how to host a 302
        # FIXME: This whole concept has a TOCTOU issue
        if not bot.config.url.enable_private_resolution:
            if not parsed_url.hostname:
                # URL like file:///path is a valid local path (i.e. private)
                LOGGER.debug("Ignoring private URL: %s", url)
                continue

            try:
                ips = [ip_address(parsed_url.hostname)]
            except ValueError:
                # Extra try/except here in case the DNS resolution fails, see #2348
                try:
                    ips = [
                        ip_address(ip.to_text())
                        for ip in dns.resolver.resolve(parsed_url.hostname)
                    ]
                except Exception as exc:
                    LOGGER.debug(
                        "Cannot resolve hostname %s, ignoring URL %s"
                        " (exception was: %r)",
                        parsed_url.hostname,
                        url,
                        exc,
                    )
                    continue

            private = False
            for ip in ips:
                if ip.is_private or ip.is_loopback:
                    private = True
                    break
            if private:
                LOGGER.debug("Ignoring private URL: %s", url)
                continue

        # Call the URL to get a title, if possible
        title = find_title(url)
        if not title:
            # No title found: don't handle this URL
            LOGGER.debug('No title found; ignoring URL: %s', url)
            continue

        # If the URL is over bot.config.url.shorten_url_length, shorten the URL
        tinyurl = None
        if (shorten_url_length > 0) and (len(url) > shorten_url_length):
            tinyurl = get_or_create_shorturl(bot, url)

        yield URLInfo(url, title, parsed_url.hostname, tinyurl, False)


def check_callbacks(
    bot: SopelWrapper,
    url: str,
    use_excludes: bool = True,
) -> bool:
    """Check if ``url`` is excluded or matches any URL callback patterns.

    :param bot: Sopel instance
    :param url: URL to check
    :param use_excludes: Use or ignore the configured exclusion lists
    :return: True if ``url`` is excluded or matches any URL callback pattern

    This function looks at the ``bot.memory`` for ``url_exclude`` patterns and
    it returns ``True`` if any matches the given ``url``. Otherwise, it looks
    at the ``bot``'s URL callback patterns, and it returns ``True`` if any
    matches, ``False`` otherwise.

    .. seealso::

        The :func:`~sopel.builtins.url.setup` function that defines the
        ``url_exclude`` in ``bot.memory``.

    .. versionchanged:: 7.0

        This function **does not** trigger URL callbacks anymore when ``url``
        matches a pattern.

    """
    # Check if it matches the exclusion list first
    excluded = use_excludes and any(
        regex.search(url) for regex in bot.memory["url_exclude"]
    )
    return (
        excluded or
        any(bot.search_url_callbacks(url)) or
        bot.rules.check_url_callback(bot, url)
    )


def find_title(url: str, verify: bool = True) -> Optional[str]:
    """Return the title for the given URL.

    :param verify: Whether to require a valid certificate when using https
    """
    try:
        response = requests.get(url, stream=True, verify=verify,
                                headers=DEFAULT_HEADERS)
        raw_content = b''
        for byte in response.iter_content(chunk_size=512):
            raw_content += byte
            if b'</title>' in raw_content or len(raw_content) > MAX_BYTES:
                break
        content = raw_content.decode('utf-8', errors='ignore')
        # Need to close the connection because we have not read all
        # the data
        response.close()
    except requests.exceptions.ConnectionError as e:
        LOGGER.debug("Unable to reach URL: %r: %s", url, e)
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
        return None

    title = web.decode(content[start + 7:end])
    title = title.strip()[:200]

    title = ' '.join(title.split())  # cleanly remove multiple spaces

    return title or None


def get_or_create_shorturl(bot: SopelWrapper, url: str) -> Optional[str]:
    """Get or create a short URL for ``url``

    :param bot: Sopel instance
    :param url: URL to get or create a short URL for
    :return: A short URL

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


def get_tinyurl(url: str) -> Optional[str]:
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
