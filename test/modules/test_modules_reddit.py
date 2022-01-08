"""Tests for Sopel's ``reddit`` plugin"""
from __future__ import annotations

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
    ('auto_subreddit_info', 'https://reddit.com/r/subname'),
    ('auto_subreddit_info', 'https://reddit.com/r/subname/'),
    ('auto_subreddit_info', 'https://www.reddit.com/r/subname'),
    ('auto_subreddit_info', 'https://www.reddit.com/r/subname/'),
    ('post_or_comment_info', 'https://redd.it/123456'),
    ('post_or_comment_info', 'https://redd.it/123456/'),
    ('post_or_comment_info', 'https://reddit.com/123456'),
    ('post_or_comment_info', 'https://reddit.com/123456/'),
    ('post_or_comment_info', 'https://reddit.com/comments/123456'),
    ('post_or_comment_info', 'https://reddit.com/comments/123456/'),
    ('post_or_comment_info', 'https://www.reddit.com/comments/123456'),
    ('post_or_comment_info', 'https://www.reddit.com/comments/123456/'),
    ('post_or_comment_info', 'https://reddit.com/r/subname/comments/123456'),
    ('post_or_comment_info', 'https://reddit.com/r/subname/comments/123456/'),
    ('post_or_comment_info', 'https://www.reddit.com/comments/123456?param=value'),
    ('post_or_comment_info', 'https://www.reddit.com/comments/123456/?param=value'),
    ('post_or_comment_info', 'https://reddit.com/r/subname/comments/123456?param=value'),
    ('post_or_comment_info', 'https://reddit.com/r/subname/comments/123456/?param=value'),
    ('post_or_comment_info', 'https://www.reddit.com/r/subname/comments/123456'),
    ('post_or_comment_info', 'https://www.reddit.com/r/subname/comments/123456/'),
    ('post_or_comment_info', 'https://reddit.com/r/subname/comments/123456/post_title_slug/234567'),
    ('post_or_comment_info', 'https://reddit.com/r/subname/comments/123456/post_title_slug/234567/'),
    ('post_or_comment_info', 'https://www.reddit.com/r/subname/comments/123456/post_title_slug/234567'),
    ('post_or_comment_info', 'https://www.reddit.com/r/subname/comments/123456/post_title_slug/234567/'),
    ('post_or_comment_info', 'https://reddit.com/r/subname/comments/123456/post_title_slug/234567/?context=1337'),
    ('post_or_comment_info', 'https://www.reddit.com/r/subname/comments/123456/post_title_slug/234567/?context=1337'),
)


NON_MATCHING_URLS = (
    # we don't allow for query parameters on subreddit links (yet?)
    'https://reddit.com/r/subname?param=value',
    'https://reddit.com/r/subname/?param=value',
    'https://www.reddit.com/r/subname?param=value',
    'https://www.reddit.com/r/subname/?param=value',
)


@pytest.mark.parametrize('rule_name, link', MATCHING_URLS)
def test_url_matching(link, rule_name, bot):
    line = PreTrigger(bot.nick, ':User!user@irc.libera.chat PRIVMSG #channel {}'.format(link))
    matched_rules = [
        # we can ignore matches that don't come from the plugin under test
        match[0] for match in bot.rules.get_triggered_rules(bot, line)
        if match[0].get_plugin_name() == 'reddit'
    ]

    assert len(matched_rules) == 1
    assert matched_rules[0].get_rule_label() == rule_name


@pytest.mark.parametrize('link', NON_MATCHING_URLS)
def test_url_non_matching(link, bot):
    line = PreTrigger(bot.nick, ':User!user@irc.libera.chat PRIVMSG #channel {}'.format(link))
    matched_rules = [
        # we can ignore matches that don't come from the plugin under test
        match[0] for match in bot.rules.get_triggered_rules(bot, line)
        if match[0].get_plugin_name() == 'reddit'
    ]

    assert len(matched_rules) == 0
