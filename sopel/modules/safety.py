"""
safety.py - Alerts about malicious URLs
Copyright © 2014, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This plugin uses virustotal.com
"""
from __future__ import annotations

from base64 import urlsafe_b64encode
import json
import logging
import os.path
import re
import threading
import time
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.request import urlretrieve

import requests

from sopel import formatting, plugin, tools
from sopel.bot import Sopel
from sopel.config import Config, types
from sopel.trigger import Trigger


LOGGER = logging.getLogger(__name__)
PLUGIN_OUTPUT_PREFIX = '[safety] '

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
    """List of "known good" domains to ignore."""
    vt_api_key = types.ValidatedAttribute('vt_api_key')
    """Optional VirusTotal API key (improves malicious URL detection)."""
    domain_blocklist_url = types.ValidatedAttribute("domain_blocklist_url")
    """Optional hosts-file formatted domain blocklist to use instead of StevenBlack's."""


def configure(settings: Config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | default\\_mode | on | Which mode to use in channels without a mode set. |
    | known\\_good | sopel.chat,dftba.net | List of "known good" domains or regexes to ignore. This can save VT API calls. |
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
        "Enter any domains to allowlist",
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


def setup(bot: Sopel):
    bot.settings.define_section("safety", SafetySection)

    if bot.settings.safety.default_mode is None:
        bot.settings.safety.default_mode = "on"
    # migrate from enabled_by_default to default_mode. remove in v8.1 or v9
    if not bot.settings.safety.enabled_by_default:
        bot.settings.safety.default_mode = "off"
        LOGGER.info(
            "config: enabled_by_default is deprecated, please use default_mode=off",
        )

    if 'safety_cache' not in bot.memory:
        bot.memory['safety_cache'] = tools.SopelMemory()
    if 'safety_cache_lock' not in bot.memory:
        bot.memory['safety_cache_lock'] = threading.Lock()
    for item in bot.settings.safety.known_good:
        known_good.append(re.compile(item, re.I))

    update_local_cache(bot, init=True)


def update_local_cache(bot: Sopel, init: bool = False):
    """Download the current malware domain list and load it into memory.

    :param init: Load the file even if it's unchanged
    """

    malware_domains = set()

    old_file = os.path.join(bot.settings.homedir, "malwaredomains.txt")
    if os.path.exists(old_file) and os.path.isfile(old_file):
        LOGGER.info('Removing old malwaredomains file from %s', old_file)
        try:
            os.remove(old_file)
        except Exception as err:
            # for lack of a more specific error type...
            # Python on Windows throws an exception if the file is in use
            LOGGER.info('Could not delete %s: %s', old_file, str(err))

    loc = os.path.join(bot.settings.homedir, "unsafedomains.txt")
    if not os.path.isfile(loc) or os.path.getmtime(loc) < time.time() - 24 * 60 * 60:
        # File doesn't exist or is older than one day — update it
        url = bot.settings.safety.domain_blocklist_url
        if url is None or not url.startswith("http"):
            url = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
        LOGGER.info("Downloading malicious domain list from %s", url)
        # TODO: Can we use a cache header to avoid the download if it's unmodified?
        urlretrieve(url, loc)
    elif not init:
        return

    with open(loc, 'r') as f:
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
                malware_domains.add(domain)

    bot.memory["safety_cache_local"] = malware_domains


def shutdown(bot: Sopel):
    bot.memory.pop('safety_cache', None)
    bot.memory.pop('safety_cache_local', None)
    bot.memory.pop('safety_cache_lock', None)


@plugin.rule(r'(?u).*(https?://\S+).*')
@plugin.priority('high')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def url_handler(bot: Sopel, trigger: Trigger):
    """Checks for malicious URLs"""
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
        safe_url = "hxx" + url[3:]

        positives = 0  # Number of engines saying it's malicious
        total = 0  # Number of total engines

        try:
            netloc = urlparse(url).netloc.lower()
        except ValueError:
            pass  # Invalid address
        else:
            if any(regex.search(netloc) for regex in known_good):
                continue  # explicitly allowed

            if netloc in bot.memory["safety_cache_local"]:
                LOGGER.debug("[local] domain in blocklist: %r", netloc)
                positives += 1
                total += 1

        result = virustotal_lookup(bot, url, local_only=local_only)
        if result:
            positives += result["positives"]
            total += result["total"]

        if positives >= 1:
            # Possibly malicious URL detected!
            LOGGER.info(
                "Possibly malicious link (%s/%s) posted in %s by %s: %r",
                positives,
                total,
                trigger.sender,
                trigger.nick,
                safe_url,
            )
            bot.say(
                "{} {} of {} engine{} flagged a link {} posted as malicious".format(
                    formatting.bold(formatting.color("WARNING:", "red")),
                    positives,
                    total,
                    "" if total == 1 else "s",
                    formatting.bold(trigger.nick),
                )
            )
            if strict:
                bot.kick(trigger.nick, trigger.sender, "Posted a malicious link")


def virustotal_lookup(bot: Sopel, url: str, local_only: bool = False) -> Optional[Dict]:
    """Check VirusTotal for flags on a URL as malicious.

    :param url: The URL to look up
    :param local_only: If set, only check cache, do not make a new request.
    :returns: A dict containing information about findings, or None if not found.
    """
    safe_url = "hxx" + url[3:]

    if url in bot.memory["safety_cache"]:
        LOGGER.debug("[VirusTotal] Using cached data for %r", safe_url)
        return bot.memory["safety_cache"].get(url)
    if local_only:
        return None

    LOGGER.debug("[VirusTotal] Looking up %r", safe_url)
    url_id = urlsafe_b64encode(url.encode("utf-8")).rstrip(b"=").decode("ascii")
    try:
        r = requests.get(
            VT_API_URL + "/" + url_id,
            headers={"x-apikey": bot.settings.safety.vt_api_key},
        )

        if r.status_code == 404:
            # Not analyzed - submit new
            LOGGER.debug("[VirusTotal] No scan for %r, requesting", safe_url)
            # TODO: handle checking back for results from queued scans
            r = requests.post(
                VT_API_URL,
                data={"url": url},
                headers={"x-apikey": bot.settings.safety.vt_api_key},
            )
            return None
        r.raise_for_status()
        vt_data = r.json()
    except requests.exceptions.RequestException:
        # Ignoring exceptions with VT so domain list will always work
        LOGGER.debug(
            "[VirusTotal] Error obtaining response for %r", safe_url, exc_info=True
        )
    except json.JSONDecodeError:
        # Ignoring exceptions with VT so domain list will always work
        LOGGER.debug(
            "[VirusTotal] Malformed response (invalid JSON) for %r",
            safe_url,
            exc_info=True,
        )
    fetched = time.time()
    last_analysis = vt_data["data"]["attributes"]["last_analysis_stats"]
    # Only count strong opinions (ignore suspicious/timeout/undetected)
    result = {
        "positives": last_analysis["malicious"],
        "total": last_analysis["malicious"] + last_analysis["harmless"],
        "fetched": fetched,
        "virustotal_data": vt_data,
    }
    bot.memory["safety_cache"][url] = result
    if len(bot.memory["safety_cache"]) >= (2 * CACHE_LIMIT):
        _clean_cache(bot)
    return result


@plugin.command('safety')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def toggle_safety(bot: Sopel, trigger: Trigger):
    """Set safety setting for channel"""
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
def _clean_cache(bot: Sopel):
    """Cleans up old entries in URL safety cache."""

    update_local_cache(bot)

    if bot.memory['safety_cache_lock'].acquire(False):
        LOGGER.info('Starting safety cache cleanup...')
        try:
            # clean up by age first
            cutoff = time.time() - (7 * 24 * 60 * 60)  # 7 days ago
            old_keys = []
            for key, data in bot.memory['safety_cache'].items():
                if data['fetched'] <= cutoff:
                    old_keys.append(key)
            for key in old_keys:
                bot.memory['safety_cache'].pop(key, None)

            # clean up more values if the cache is still too big
            overage = len(bot.memory['safety_cache']) - CACHE_LIMIT
            if overage > 0:
                extra_keys = sorted(
                    (data.fetched, key)
                    for (key, data)
                    in bot.memory['safety_cache'].items())[:overage]
                for (_, key) in extra_keys:
                    bot.memory['safety_cache'].pop(key, None)
        finally:
            # No matter what errors happen (or not), release the lock
            bot.memory['safety_cache_lock'].release()

        LOGGER.info('Safety cache cleanup finished.')
    else:
        LOGGER.info(
            'Skipping safety cache cleanup: Cache is locked, '
            'cleanup already running.')
