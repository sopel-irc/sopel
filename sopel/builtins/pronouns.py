"""
pronouns.py - Sopel Pronouns Plugin
Copyright © 2016, Elsie Powell
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

import logging

import requests

from sopel import plugin
from sopel.config import types


LOGGER = logging.getLogger(__name__)


class PronounsSection(types.StaticSection):
    fetch_complete_list = types.BooleanAttribute('fetch_complete_list', default=True)
    """Whether to attempt fetching the complete list the web backend uses, at bot startup."""

    link_base_url = types.ValidatedAttribute(
        'link_base_url', default='https://pronouns.sopel.chat')
    """Base URL for links to pronoun info.

    Defaults to an instance of https://github.com/sopel-irc/pronoun-service
    hosted by the Sopel project, but it's easy to make your own instance
    available at a custom domain using one of many free static site hosts.
    """


def configure(settings):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | fetch_complete_list | True | Whether to attempt fetching the complete pronoun list from the web backend at startup. |
    | link_base_url | https://pronouns.sopel.chat | Base URL for pronoun info links. |
    """
    settings.define_section('pronouns', PronounsSection)
    settings.pronouns.configure_setting(
        'fetch_complete_list',
        'Fetch the most current list of pronoun sets at startup?')
    settings.pronouns.configure_setting(
        'link_base_url',
        'Base URL for pronoun info links:')


def setup(bot):
    bot.settings.define_section('pronouns', PronounsSection)

    # Copied from svelte-pronounisland, leaving a *lot* out.
    # If ambiguous, the earlier one will be used.
    # This basic set is hard-coded to guarantee that the ten most(ish) common sets
    # will work, even if fetching the current set from GitHub fails.
    bot.memory['pronoun_sets'] = {
        'ze/hir': 'ze/hir/hir/hirs/hirself',
        'ze/zir': 'ze/zir/zir/zirs/zirself',
        'they/.../themselves': 'they/them/their/theirs/themselves',
        'they/.../themself': 'they/them/their/theirs/themself',
        'she/her': 'she/her/her/hers/herself',
        'he/him': 'he/him/his/his/himself',
        'xey/xem': 'xey/xem/xyr/xyrs/xemself',
        'sie/hir': 'sie/hir/hir/hirs/hirself',
        'it/it': 'it/it/its/its/itself',
        'ey/em': 'ey/em/eir/eirs/eirself',
    }

    if not bot.settings.pronouns.fetch_complete_list:
        return

    # and now try to get the current list our fork of the backend uses
    # (https://github.com/sopel-irc/pronoun-service)
    try:
        r = requests.get(
            'https://github.com/sopel-irc/pronoun-service/raw/main/src/lib/data/pronouns.tab')
        r.raise_for_status()
        fetched_pairs = _process_pronoun_sets(r.text.splitlines())
    except requests.exceptions.RequestException:
        # don't do anything, just log the failure and use the hard-coded set
        LOGGER.exception("Couldn't fetch full pronouns list; using default set.")
        return
    except Exception:
        # don't care what failed, honestly, since we aren't trying to fix it
        LOGGER.exception("Couldn't parse fetched pronouns; using default set.")
        return
    else:
        bot.memory['pronoun_sets'] = dict(fetched_pairs)


def _process_pronoun_sets(set_list):
    trie = PronounTrie()
    trie.insert_list(set_list)
    yield from trie.get_pairs()


class PronounTrieNode:
    def __init__(self, source=''):
        self.children = {}
        """Child nodes are stored here."""

        self.freq = 0
        """Store how many times this node is visited during insertion."""

        self.source = source
        """The full pronoun set that caused this node's creation."""


class PronounTrie:
    def __init__(self):
        self.root = PronounTrieNode()
        """A Trie needs a root entry."""

    def insert(self, pronoun_set):
        """Insert a single pronoun set."""
        pronoun_set = pronoun_set.replace('\t', '/')
        current_node = self.root
        for pronoun in pronoun_set.split('/'):
            # create a new node if the path doesn't exist
            # and use it as the current node
            current_node = current_node.children.setdefault(pronoun, PronounTrieNode(pronoun_set))

            # increment frequency
            current_node.freq += 1

    def insert_list(self, set_list):
        """Load a list of pronoun sets all at once."""
        for item in set_list:
            self.insert(item)

    def get_pairs(self, root=None, prefix=''):
        """Yield tuples of ``(prefix, full/pronoun/set)``."""
        if root is None:
            root = self.root

        if root.freq == 1:
            yield prefix, root.source
        else:
            if prefix:
                prefix += '/'
            for word, node in root.children.items():
                yield from self.get_pairs(node, prefix + word)


@plugin.command('pronouns')
@plugin.example('.pronouns Embolalia')
def pronouns(bot, trigger):
    """Show the pronouns for a given user, defaulting to the current user if left blank."""
    if not trigger.group(3):
        pronouns = bot.db.get_nick_value(trigger.nick, 'pronouns')
        if pronouns:
            say_pronouns(bot, trigger.nick, pronouns)
        else:
            bot.reply("I don't know your pronouns! You can set them with "
                      "{}setpronouns".format(bot.settings.core.help_prefix))
    else:
        pronouns = bot.db.get_nick_value(trigger.group(3), 'pronouns')
        if pronouns:
            say_pronouns(bot, trigger.group(3), pronouns)
        elif trigger.group(3) == bot.nick:
            # You can stuff an entry into the database manually for your bot's
            # gender, but like… it's a bot.
            bot.say(
                "I am a bot. Beep boop. My pronouns are it/it/its/its/itself. "
                "See {}/it for examples.".format(bot.settings.pronouns.link_base_url)
            )
        else:
            bot.reply("I don't know {}'s pronouns. They can set them with "
                      "{}setpronouns".format(trigger.group(3),
                                             bot.settings.core.help_prefix))


def say_pronouns(bot, nick, pronouns):
    for short, set_ in bot.memory['pronoun_sets'].items():
        if pronouns == set_:
            break
        short = pronouns

    bot.say(
        "{nick}'s pronouns are {pronouns}. See {base_url}/{short} for examples."
        .format(
            nick=nick,
            pronouns=pronouns,
            base_url=bot.settings.pronouns.link_base_url,
            short=short,
        )
    )


@plugin.command('setpronouns')
@plugin.example('.setpronouns fae/faer/faer/faers/faerself')
@plugin.example('.setpronouns they/them/theirs')
@plugin.example('.setpronouns they/them')
def set_pronouns(bot, trigger):
    """Set your pronouns."""
    requested_pronouns = trigger.group(2)
    if not requested_pronouns:
        bot.reply('What pronouns do you use?')
        return

    disambig = ''
    requested_pronouns_split = requested_pronouns.split("/")
    if len(requested_pronouns_split) < 5:
        matching = []
        for known_pronoun_set in bot.memory['pronoun_sets'].values():
            known_split_set = known_pronoun_set.split("/")
            if known_pronoun_set.startswith(requested_pronouns + "/") or (
                len(requested_pronouns_split) == 3
                and (
                    (
                        # "they/.../themself"
                        requested_pronouns_split[1] == "..."
                        and requested_pronouns_split[0] == known_split_set[0]
                        and requested_pronouns_split[2] == known_split_set[4]
                    )
                    or (
                        # "they/them/theirs"
                        requested_pronouns_split[:2] == known_split_set[:2]
                        and requested_pronouns_split[2] == known_split_set[3]
                    )
                )
            ):
                matching.append(known_pronoun_set)

        if not matching:
            bot.reply(
                "I'm sorry, I don't know those pronouns. "
                "You can give me a set I don't know by formatting it "
                "subject/object/possessive-determiner/possessive-pronoun/"
                "reflexive, as in: they/them/their/theirs/themselves"
            )
            return

        requested_pronouns = matching.pop(0)
        if matching:
            disambig = " Or, if you meant one of these, please tell me: {}".format(
                ", ".join(matching)
            )

    bot.db.set_nick_value(trigger.nick, 'pronouns', requested_pronouns)
    bot.reply(
        "Thanks for telling me! I'll remember you use {}.{}".format(requested_pronouns, disambig)
    )


@plugin.command('clearpronouns')
def unset_pronouns(bot, trigger):
    """Clear pronouns for the given user."""
    bot.db.delete_nick_value(trigger.nick, 'pronouns')
    bot.reply("Okay, I'll forget your pronouns.")
