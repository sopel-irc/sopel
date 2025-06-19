"""
safety.py - Alerts about malicious URLs
Copyright © 2014, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This plugin uses virustotal.com
"""
from __future__ import annotations

from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
import json
import logging
import os.path
import re
import threading
from time import sleep
from typing import TYPE_CHECKING
from urllib.parse import urlparse, urlunparse

import requests

from sopel import plugin, tools
from sopel.config import types
from sopel.formatting import bold, color, colors


if TYPE_CHECKING:
    from typing import Optional

    from sopel.bot import Sopel, SopelWrapper
    from sopel.config import Config
    from sopel.trigger import Trigger

LOGGER = logging.getLogger(__name__)
PLUGIN_OUTPUT_PREFIX = '[safety] '

SAFETY_CACHE_KEY = "safety_cache"
SAFETY_CACHE_LOCK_KEY = SAFETY_CACHE_KEY + "_lock"
SAFETY_CACHE_LOCAL_KEY = SAFETY_CACHE_KEY + "_local"
SAFETY_MODES = ["off", "local", "local strict", "on", "strict"]
VT_API_URL = "https://www.virustotal.com/api/v3/urls"
CACHE_LIMIT = 512
known_good = []


class SafetySection(types.StaticSection):
    enabled_by_default = types.BooleanAttribute("enabled_by_default", default=True)
    """Deprecated: Sets default_mode to "off" or "on"."""
    default_mode = types.ValidatedAttribute("default_mode")
    """Which mode to use in channels without a mode set."""
    known_good = types.ListAttribute('known_good')
    """List of "known good" domains or regexes to consider trusted."""
    vt_api_key = types.ValidatedAttribute('vt_api_key')
    """Optional VirusTotal API key (improves malicious URL detection)."""
    domain_blocklist_url = types.ValidatedAttribute("domain_blocklist_url")
    """Optional hosts-file formatted domain blocklist to use instead of StevenBlack's."""


def configure(settings: Config) -> None:
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | default\\_mode | on | Which mode to use in channels without a mode set. |
    | known\\_good | sopel.chat,dftba.net | List of "known good" domains or regexes to consider trusted. This can save VT API calls. |
    | vt\\_api\\_key | 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef | Optional VirusTotal API key to improve malicious URL detection |
    | domain\\_blocklist\\_url | https://example.com/bad-hosts.txt | Optional hosts-file formatted domain blocklist to use instead of StevenBlack's. |
    """
    settings.define_section("safety", SafetySection)
    settings.safety.configure_setting(
        "default_mode",
        (
            "Which mode should be used in channels that haven't specifically set one?"
            "\n({})".format("/".join(SAFETY_MODES))
        ),
        default="on",
    )
    settings.safety.configure_setting(
        'known_good',
        "Enter any domains or regexes to consider trusted",
    )
    settings.safety.configure_setting(
        'vt_api_key',
        "Optionally, enter a VirusTotal API key to improve malicious URL "
        "protection.\nOtherwise, only the configured hosts list will be used.",
    )
    settings.safety.configure_setting(
        "domain_blocklist_url",
        "Optionally, provide the URL for a hosts-file formatted domain "
        "blocklist to use instead of StevenBlack's.",
    )


def setup(bot: Sopel) -> None:
    bot.settings.define_section("safety", SafetySection)

    if bot.settings.safety.default_mode is None:
        bot.settings.safety.default_mode = "on"
    # migrate from enabled_by_default to default_mode. TODO: remove in v8.1 or v9
    if not bot.settings.safety.enabled_by_default:
        bot.settings.safety.default_mode = "off"
        LOGGER.warning(
            "config: enabled_by_default is deprecated, please use default_mode=off",
        )

    if SAFETY_CACHE_KEY not in bot.memory:
        bot.memory[SAFETY_CACHE_KEY] = tools.SopelMemory()
    if SAFETY_CACHE_LOCK_KEY not in bot.memory:
        bot.memory[SAFETY_CACHE_LOCK_KEY] = threading.Lock()
    for item in bot.settings.safety.known_good:
        known_good.append(re.compile(item, re.I))

    # clean up old files. TODO: remove in v8.1 or 9
    old_file = os.path.join(bot.settings.homedir, "malwaredomains.txt")
    if os.path.exists(old_file) and os.path.isfile(old_file):
        LOGGER.info('Removing old malwaredomains file from %s', old_file)
        try:
            os.remove(old_file)
        except Exception as err:
            # for lack of a more specific error type...
            # Python on Windows throws an exception if the file is in use
            LOGGER.warning('Could not delete %s: %s', old_file, str(err))

    LOGGER.info('Ensuring unsafe domain list is up-to-date (safety plugin setup)')
    update_local_cache(bot, init=True)


def safeify_url(url: str) -> str:
    """Replace bits of a URL to make it hard to browse to."""
    try:
        parts = urlparse(url)
        scheme = parts.scheme.replace("t", "x")  # hxxp
        netloc = parts.netloc.replace(".", "[.]")  # google[.]com and IPv4
        netloc = netloc.replace(":", "[:]")  # IPv6 addresses (bad lazy method)
        return urlunparse((scheme, netloc) + parts[2:])
    except ValueError:
        # Still try to defang URLs that fail parsing
        return url.replace(":", "[:]").replace(".", "[.]")


def download_domain_list(bot: Sopel, path: str) -> bool:
    """Download the current unsafe domain list.

    :param path: Where to save the unsafe domain list
    :returns: True if the list was updated
    """
    url = bot.settings.safety.domain_blocklist_url
    if url is None or not url.startswith("http"):
        url = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
    LOGGER.debug("Downloading unsafe domain list from %s", url)
    old_etag = bot.db.get_plugin_value("safety", "unsafe_domain_list_etag")
    if old_etag:
        r = requests.head(url)
        if r.headers["ETag"] == old_etag and os.path.isfile(path):
            LOGGER.debug("Unsafe domain list unchanged, skipping")
            return False

    r = requests.get(url, stream=True)
    try:
        r.raise_for_status()
        with open(path + ".new", "wb") as f:
            for data in r.iter_content(None):
                f.write(data)
    except Exception:
        # don't bother handling, we'll try again tomorrow
        LOGGER.warning("Unsafe domain list download failed; using cache")
        return False
    # .new+move so we don't clobber it if the download fails in the middle
    os.rename(path + ".new", path)
    bot.db.set_plugin_value("safety", "unsafe_domain_list_etag", r.headers.get("etag"))
    return True


def update_local_cache(bot: Sopel, init: bool = False) -> None:
    """Download the current malware domain list and load it into memory.

    :param init: Load the file even if it's unchanged
    """
    path = os.path.join(bot.settings.homedir, "unsafedomains.txt")
    updated = download_domain_list(bot, path)
    if not os.path.isfile(path):
        LOGGER.warning("Could not load unsafe domain list")
        return

    if not updated and not init:
        return

    LOGGER.debug("Loading new unsafe domain list")
    unsafe_domains = set()
    with open(path, "r") as f:
        for line in f:
            clean_line = str(line).strip().lower()
            if not clean_line or clean_line[0] == '#':
                # blank line or comment
                continue

            parts = clean_line.split(' ', 1)
            try:
                domain = parts[1]
            except IndexError:
                # line does not contain a hosts entry; skip it
                continue

            if '.' in domain:
                # only publicly routable domains matter; skip loopback/link-local stuff
                unsafe_domains.add(domain)
    bot.memory[SAFETY_CACHE_LOCAL_KEY] = unsafe_domains


def shutdown(bot: Sopel) -> None:
    bot.memory.pop(SAFETY_CACHE_KEY, None)
    bot.memory.pop(SAFETY_CACHE_LOCAL_KEY, None)
    bot.memory.pop(SAFETY_CACHE_LOCK_KEY, None)


@plugin.rule(r'(?u).*(https?://\S+).*')
@plugin.priority('high')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def url_handler(bot: SopelWrapper, trigger: Trigger) -> None:
    """Checks for malicious URLs."""
    mode = bot.db.get_channel_value(
        trigger.sender,
        "safety",
        bot.settings.safety.default_mode,
    )
    if mode == "off":
        return
    local_only = "local" in mode or bot.settings.safety.vt_api_key is None
    strict = "strict" in mode

    for url in tools.web.search_urls(trigger):

        positives = 0  # Number of engines saying it's malicious
        total = 0  # Number of total engines

        try:
            hostname = urlparse(url).hostname.lower()
        except (ValueError, AttributeError):
            pass  # Invalid address
        else:
            if any(regex.search(hostname) for regex in known_good):
                continue  # explicitly trusted

            if hostname in bot.memory[SAFETY_CACHE_LOCAL_KEY]:
                LOGGER.debug("[local] domain in blocklist: %r", hostname)
                positives += 1
                total += 1

        result = virustotal_lookup(bot, url, local_only=local_only)
        if result:
            positives += result["positives"]
            total += result["total"]

        if positives >= 1:
            # Possibly malicious URL detected!
            safe_url = safeify_url(url)
            LOGGER.info(
                "Possibly malicious link (%s/%s) posted in %s by %s: %r",
                positives,
                total,
                trigger.sender,
                trigger.nick,
                safe_url,
            )
            bot.say(
                "{} {} of {} engines flagged a link {} posted as malicious".format(
                    bold(color("WARNING:", colors.RED)),
                    positives,
                    total,
                    bold(trigger.nick),
                )
            )
            if strict:
                bot.kick(trigger.nick, trigger.sender, "Posted a malicious link")


def virustotal_lookup(
    bot: SopelWrapper,
    url: str,
    local_only: bool = False,
    max_cache_age: Optional[timedelta] = None,
) -> Optional[dict]:
    """Check VirusTotal for flags on a URL as malicious.

    :param url: The URL to look up
    :param local_only: If set, only check cache, do not make a new request
    :param max_cache_age: If set, don't use cache older than this value
    :returns: A dict containing information about findings, or None if not found
    """
    if url.startswith("hxxp"):
        url = "htt" + url[3:]
    elif not url.startswith("http"):
        # VT only does http/https URLs
        return None

    safe_url = safeify_url(url)

    # default: use any cache available
    oldest_cache = datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc)
    if max_cache_age is not None:
        oldest_cache = datetime.now(timezone.utc) - max_cache_age
    cache = bot.memory[SAFETY_CACHE_KEY]
    if url in cache and cache[url]["fetched"] > oldest_cache:
        LOGGER.debug("[VirusTotal] Using cached data for %r", safe_url)
        return bot.memory[SAFETY_CACHE_KEY].get(url)
    if local_only:
        return None

    LOGGER.debug("[VirusTotal] Looking up %r", safe_url)
    url_id = urlsafe_b64encode(url.encode("utf-8")).rstrip(b"=").decode("ascii")
    attempts = 5
    requested = False
    while attempts > 0:
        attempts -= 1
        try:
            r = requests.get(
                VT_API_URL + "/" + url_id,
                headers={"x-apikey": bot.settings.safety.vt_api_key},
            )
            if r.status_code == 200:
                vt_data = r.json()
                last_analysis = vt_data["data"]["attributes"]["last_analysis_stats"]
                # VT returns 200s for recent submissions before scan results are in...
                if not requested or sum(last_analysis.values()) > 0:
                    break
            elif not requested and r.status_code == 404:
                # Not analyzed - submit new
                LOGGER.debug("[VirusTotal] No scan for %r, requesting", safe_url)
                requests.post(
                    VT_API_URL,
                    data={"url": url},
                    headers={"x-apikey": bot.settings.safety.vt_api_key},
                )
                requested = True
                sleep(2)  # Scans seem to take ~5s minimum, so add 2s
        except requests.exceptions.RequestException:
            # Ignoring exceptions with VT so domain list will always work
            LOGGER.debug(
                "[VirusTotal] Error obtaining response for %r", safe_url, exc_info=True
            )
            return None
        except json.JSONDecodeError:
            # Ignoring exceptions with VT so domain list will always work
            LOGGER.debug(
                "[VirusTotal] Malformed response (invalid JSON) for %r",
                safe_url,
                exc_info=True,
            )
            return None
        sleep(3)
    else:  # Still no results
        LOGGER.debug("[VirusTotal] Scan failed or unfinished for %r", safe_url)
        return None
    fetched = datetime.now(timezone.utc)
    # Only count strong opinions (ignore suspicious/timeout/undetected)
    result = {
        "positives": last_analysis["malicious"],
        "total": last_analysis["malicious"] + last_analysis["harmless"],
        "fetched": fetched,
        "virustotal_data": vt_data["data"]["attributes"],
    }
    bot.memory[SAFETY_CACHE_KEY][url] = result
    if len(bot.memory[SAFETY_CACHE_KEY]) >= (2 * CACHE_LIMIT):
        _clean_cache(bot)
    return result


@plugin.command("virustotal")
@plugin.example(".virustotal https://malware.wicar.org/")
@plugin.example(".virustotal hxxps://malware.wicar.org/")
@plugin.output_prefix("[safety][VirusTotal] ")
def vt_command(bot: SopelWrapper, trigger: Trigger) -> None:
    """Look up VT results on demand."""
    if not bot.settings.safety.vt_api_key:
        bot.reply("Sorry, I don't have a VirusTotal API key configured.")
        return

    url = trigger.group(2)
    safe_url = safeify_url(url)

    result = virustotal_lookup(bot, url, max_cache_age=timedelta(minutes=1))
    if not result:
        bot.reply("Sorry, an error occurred while looking that up.")
        return

    analysis = result["virustotal_data"]["last_analysis_stats"]

    result_types = {
        "malicious": colors.RED,
        "suspicious": colors.YELLOW,
        "harmless": colors.GREEN,
        "undetected": colors.GREY,
    }
    result_strs = []
    for result_type, result_color in result_types.items():
        if analysis[result_type] == 0:
            result_strs.append("0 " + result_type)
        else:
            result_strs.append(
                bold(
                    color(str(analysis[result_type]) + " " + result_type, result_color)
                )
            )
    results_str = ", ".join(result_strs)

    vt_scan_time = datetime.fromtimestamp(
        result["virustotal_data"]["last_analysis_date"],
        timezone.utc,
    )
    bot.reply(
        "Results: {} at {} for {}".format(
            results_str,
            tools.time.format_time(
                bot.db,
                bot.config,
                nick=trigger.nick,
                channel=trigger.sender,
                time=vt_scan_time,
            ),
            safe_url,
        )
    )


@plugin.command('safety')
@plugin.example(".safety on")
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def toggle_safety(bot: SopelWrapper, trigger: Trigger) -> None:
    """Set safety setting for channel."""
    if not trigger.admin and bot.channels[trigger.sender].privileges[trigger.nick] < plugin.OP:
        bot.reply('Only channel operators can change safety settings')
        return

    new_mode = None
    if trigger.group(2):
        new_mode = trigger.group(2).lower()

    if not new_mode or (new_mode != "default" and new_mode not in SAFETY_MODES):
        bot.reply(
            "Current mode: {}. Available modes: {}, or default ({})".format(
                bot.db.get_channel_value(
                    trigger.sender,
                    "safety",
                    "default",
                ),
                ", ".join(SAFETY_MODES),
                bot.settings.safety.default_mode,
            )
        )
        return

    if new_mode == "default":
        bot.db.delete_channel_value(trigger.sender, "safety")
    else:
        bot.db.set_channel_value(trigger.sender, "safety", new_mode)
    bot.say('Safety is now set to "%s" for this channel' % new_mode)


# Clean the cache every day
# Code above also calls this if there are too many cache entries
@plugin.interval(24 * 60 * 60)
def _clean_cache(bot: Sopel) -> None:
    """Cleans up old entries in URL safety cache."""

    update_local_cache(bot)

    if bot.memory[SAFETY_CACHE_LOCK_KEY].acquire(False):
        LOGGER.debug('Starting safety cache cleanup...')
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        try:
            # clean up by age first
            old_keys = []
            for key, data in bot.memory[SAFETY_CACHE_KEY].items():
                if data['fetched'] <= cutoff:
                    old_keys.append(key)
            for key in old_keys:
                bot.memory[SAFETY_CACHE_KEY].pop(key, None)

            # clean up more values if the cache is still too big
            overage = len(bot.memory[SAFETY_CACHE_KEY]) - CACHE_LIMIT
            if overage > 0:
                extra_keys = sorted(
                    (data.fetched, key)
                    for (key, data)
                    in bot.memory[SAFETY_CACHE_KEY].items())[:overage]
                for (_, key) in extra_keys:
                    bot.memory[SAFETY_CACHE_KEY].pop(key, None)
        finally:
            # No matter what errors happen (or not), release the lock
            bot.memory[SAFETY_CACHE_LOCK_KEY].release()

        LOGGER.debug('Safety cache cleanup finished.')
    else:
        LOGGER.debug(
            'Skipping safety cache cleanup: Cache is locked, '
            'cleanup already running.')
