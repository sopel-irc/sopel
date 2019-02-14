# coding=utf-8
"""
instagram.py - API-key-less Instagram module for Sopel
Copyright 2018, Sopel contributors
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
from datetime import datetime

from requests import get

from sopel import module, tools

try:
    from ujson import loads
except ImportError:
    from json import loads


instagram_regex = r'.*(https?:\/\/(?:www\.){0,1}instagram\.com\/([a-zA-Z0-9_\.]{,30}\/)?p\/[a-zA-Z0-9_-]+)\s?.*'
instagram_pattern = re.compile(instagram_regex)


def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.SopelMemory()
    bot.memory['url_callbacks'][instagram_pattern] = instaparse


def shutdown(bot):
    del bot.memory['url_callbacks'][instagram_pattern]

# TODO: Parse Instagram profile page


@module.rule(instagram_regex)
def instaparse(bot, trigger):
    # Get the embedded JSON
    json = get_insta_json(trigger.group(1))
    bot.say(parse_insta_json(json))


def get_insta_json(url):
    headers = {"Accept-Language": "en"}
    url = url.replace("https://", "http://")
    r = get(url, headers=headers)

    # Extract JSON from html source code
    json_start = r.text.find("window._sharedData") + 21
    json_stops = r.text.find("</script>", json_start) - 1
    json_astxt = r.text[json_start:json_stops]
    return loads(json_astxt)


def parse_insta_json(json):
    # Parse JSON content
    needed = json['entry_data']['PostPage'][0]['graphql']['shortcode_media']
    iwidth = needed['dimensions']['width']
    iheight = needed['dimensions']['height']
    iuser = needed['owner']['username']
    ifname = needed['owner']['full_name']
    ilikes = needed['edge_media_preview_like']['count']
    icomms = needed['edge_media_to_comment']['count']
    idate = needed['taken_at_timestamp']
    pubdate = datetime.utcfromtimestamp(idate).strftime('%Y-%m-%d %H:%M:%S')
    ivideo = needed['is_video']

    # Does the post have a caption?
    try:
        icap = needed['edge_media_to_caption']['edges'][0]['node']['text']
        # Strip newlines
        icap = icap.replace('\n', ' ')
        # Truncate caption
        icap = (icap[:256] + '…') if len(icap) > 256 else icap
    except Exception:  # TODO: be specific
        icap = False

    # Build bot response
    if ivideo is True:
        botmessage = "[insta] Video by "
    else:
        botmessage = "[insta] Photo by "
    if ifname is None:
        botmessage += "@%s" % iuser
    else:
        botmessage += "%s (@%s)" % (ifname, iuser)
    if icap is not False:
        botmessage += " | " + icap
    botmessage += " | " + str(iwidth) + "x" + str(iheight)
    botmessage += " | Likes: {:,} | Comments: {:,}".format(ilikes, icomms)
    botmessage += " | Uploaded: " + pubdate

    # Ta-da!
    return botmessage
