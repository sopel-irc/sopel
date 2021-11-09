"""Tests for Sopel's ``reddit`` plugin"""
from __future__ import generator_stop

import pytest

from sopel.trigger import PreTrigger


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    reddit
host = irc.libera.chat
"""


@pytest.fixture
def bot(botfactory, configfactory):
    settings = configfactory('default.ini', TMP_CONFIG)
    return botfactory.preloaded(settings, ['reddit'])


MATCHING_URLS = (
    # URLs the reddit plugin is expected to handle
    # Should match ONCE each, no more, no less
    'https://redd.it/123456',
    'https://redd.it/123456/',
    'https://reddit.com/123456',
    'https://reddit.com/123456/',
    'https://reddit.com/r/subname',
    'https://reddit.com/r/subname/',
    'https://www.reddit.com/r/subname',
    'https://www.reddit.com/r/subname/',
    'https://reddit.com/comments/123456',
    'https://reddit.com/comments/123456/',
    'https://www.reddit.com/comments/123456',
    'https://www.reddit.com/comments/123456/',
    'https://reddit.com/r/subname/comments/123456',
    'https://reddit.com/r/subname/comments/123456/',
    'https://www.reddit.com/comments/123456?param=value',
    'https://www.reddit.com/comments/123456/?param=value',
    'https://reddit.com/r/subname/comments/123456?param=value',
    'https://reddit.com/r/subname/comments/123456/?param=value',
    'https://www.reddit.com/r/subname/comments/123456',
    'https://www.reddit.com/r/subname/comments/123456/',
    'https://reddit.com/r/subname/comments/123456/post_title_slug/234567',
    'https://reddit.com/r/subname/comments/123456/post_title_slug/234567/',
    'https://www.reddit.com/r/subname/comments/123456/post_title_slug/234567',
    'https://www.reddit.com/r/subname/comments/123456/post_title_slug/234567/',
    'https://reddit.com/r/subname/comments/123456/post_title_slug/234567/?context=1337',
    'https://www.reddit.com/r/subname/comments/123456/post_title_slug/234567/?context=1337',
)


NON_MATCHING_URLS = (
    # we don't allow for query parameters on subreddit links (yet?)
    'https://reddit.com/r/subname?param=value',
    'https://reddit.com/r/subname/?param=value',
    'https://www.reddit.com/r/subname?param=value',
    'https://www.reddit.com/r/subname/?param=value',
)


@pytest.mark.parametrize('link', MATCHING_URLS)
def test_url_matching(link, bot):
    line = PreTrigger(bot.nick, ':User!user@irc.libera.chat PRIVMSG #channel {}'.format(link))
    matches = bot.rules.get_triggered_rules(bot, line)

    assert len([match for match in matches if match[0].get_plugin_name() == 'reddit']) == 1


@pytest.mark.parametrize('link', NON_MATCHING_URLS)
def test_url_non_matching(link, bot):
    line = PreTrigger(bot.nick, ':User!user@irc.libera.chat PRIVMSG #channel {}'.format(link))
    matches = bot.rules.get_triggered_rules(bot, line)

    assert len([match for match in matches if match[0].get_plugin_name() == 'reddit']) == 0
