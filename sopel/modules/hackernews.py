# coding=utf-8
"""
hackernews.py - Hacker News - news.ycombinator.com Module
Copyright © 2016, Sachin Patil, <psachin@redhat.com>
Licensed under the Eiffel Forum License 2.

This module relies on https://hacker-news.firebaseio.com
"""
from __future__ import unicode_literals, absolute_import, print_function, division
import requests
import sopel.module
from sopel.formatting import bold as bold_text
from sopel.logger import get_logger


LOGGER = get_logger(__name__)


@sopel.module.commands('hn', 'hackernews')
@sopel.module.example('.hn')
@sopel.module.example('.hn stories 3')
@sopel.module.example('.hackernews beststories 1')
@sopel.module.example('.hn newstories')
def hackernews(bot, trigger):
    items = {
        'stories': 'topstories',
        'newstories': 'newstories',
        'beststories': 'beststories',
    }

    base_uri = "https://news.ycombinator.com/item"
    base_api = "https://hacker-news.firebaseio.com/v0/"
    user_input = trigger.group().split()

    try:
        user_item = user_input[1]
    except:
        user_item = 'stories'

    try:
        count = int(user_input[2])
    except:
        count = 1

    try:
        uri = "{}{}.json".format(base_api, items[user_item])
        data = requests.get(uri)
        if 'error' not in data.json():
            for item in data.json()[:count]:
                data = requests.get("{}item/{}.json".format(
                    base_api, item)).json()
                message = "{} Title: {} | Post: {} | Url: {}".format(
                    bold_text("[Hacker News]"),
                    data['title'],
                    (base_uri + "?id=" + str(item)),
                    data['url'])
                bot.say(message)
        else:
            bot.say("[Hacker News] {}".format(data.json()['error']))
    except KeyError as err:
        message = "[Hacker News] I can't find news with the term {}. Valid \
terms are {}".format(err, ", ".join(items.keys()))
        LOGGER.warning(message)
        bot.say(message)


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
