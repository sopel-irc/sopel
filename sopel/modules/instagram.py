# coding=utf-8
"""
instagram.py - Sopel Instagram Module
Copyright 2018, Sopel contributors
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from datetime import datetime
import logging

from requests import get

from sopel import module

try:
    from ujson import loads
except ImportError:
    from json import loads


LOGGER = logging.getLogger(__name__)
INSTAGRAM_REGEX = r'(https?:\/\/(?:www\.){0,1}instagram\.com\/([a-zA-Z0-9_\.]{,30}\/)?p\/[a-zA-Z0-9_-]+)'

# TODO: Parse Instagram profile page


class ParseError(Exception):
    pass


@module.url(INSTAGRAM_REGEX)
def instaparse(bot, trigger, match):
    instagram_url = match.group(1)
    # Get the embedded JSON
    json = get_insta_json(instagram_url)
    try:
        bot.say(parse_insta_json(json))
    except ParseError:
        LOGGER.exception(
            "Unable to find Instagram's payload for URL %s", instagram_url)
        bot.say(
            "Unable to parse this Instagram URL. "
            "It's probably a temporary error; try again in a bit.")


def get_insta_json(url):
    headers = {"Accept-Language": "en"}
    url = url.replace("https://", "http://")
    r = get(url, headers=headers)

    # Extract JSON from html source code
    json_start = r.text.find("window._sharedData") + 21
    json_stops = r.text.find("</script>", json_start) - 1
    json_astxt = r.text[json_start:json_stops]
    return loads(json_astxt)


def _get_json_data(json):
    post_pages = json.get('entry_data', {}).get('PostPage', [])
    if not post_pages:
        raise ParseError('No PostPage found in %r' % json)
    post_page = post_pages[0]

    media = post_page.get('graphql', {}).get('shortcode_media', {})

    if not media:
        raise ParseError('No graphql data in %r' % post_page)

    return media


def parse_insta_json(json):
    # Parse JSON content
    needed = _get_json_data(json)

    dimensions = needed.get('dimensions', {})
    owner = needed.get('owner', {})

    # Build bot response
    parts = []

    # Title
    if needed.get('is_video'):
        title = "[insta] Video by "
    else:
        title = "[insta] Photo by "

    # Author
    iuser = owner.get('username')
    ifname = owner.get('full_name')
    if ifname and iuser:
        parts.append('%s %s (@%s)' % (title, ifname, iuser))
    elif iuser:
        parts.append('%s @%s' % (title, iuser))
    elif ifname:
        parts.append('%s %s' % (title, ifname))
    else:
        parts.append('%s unknown user' % title)

    # Media caption
    try:
        icap = needed['edge_media_to_caption']['edges'][0]['node']['text']
        # Strip newlines
        icap = icap.replace('\n', ' ')
        # Truncate caption
        icap = (icap[:256] + '…') if len(icap) > 256 else icap
    except (KeyError, IndexError):
        icap = None

    if icap:
        parts.append(icap)

    # Media width and height
    iwidth = dimensions.get('width') or None
    iheight = dimensions.get('height') or None

    if iwidth and iheight:
        parts.append('%sx%s' % (iwidth, iheight))

    # Likes
    ilikes = needed.get('edge_media_preview_like', {}).get('count')
    if ilikes:
        parts.append('Likes: {:,}'.format(ilikes))

    # Comments
    icomms = needed.get('edge_media_to_parent_comment', {}).get('count')
    if icomms:
        parts.append('Comments: {:,}'.format(icomms))

    # Publishing date
    idate = needed.get('taken_at_timestamp')
    if idate:
        dateformat = '%Y-%m-%d %H:%M:%S'
        pubdate = datetime.utcfromtimestamp(idate).strftime(dateformat)
        parts.append('Uploaded: %s' % pubdate)

    # Build the message
    return ' | '.join(parts)
