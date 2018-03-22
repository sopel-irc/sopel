# coding=utf8
"""
API-less Instagram module for Sopel 
"""
try:
    from ujson import loads
except ImportError:
    from json import loads
from sopel.module import rule
from sopel.tools import SopelMemory
from requests import get
from datetime import datetime
import re

instagramregex = re.compile('.*(https?:\/\/(?:www\.){0,1}instagram\.com\/p\/[a-zA-Z0-9_-]+)\s?.*')

def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = SopelMemory()
    bot.memory['url_callbacks'][instagramregex] = instaparse
    

def shutdown(bot):
    del bot.memory['url_callbacks'][instagramregex]

# TODO: Parse Instagram profile page


@rule('.*(https?:\/\/(?:www\.){0,1}instagram\.com\/p\/[a-zA-Z0-9_-]+)\s?.*')
def instaparse(bot, trigger):
    # Get the embedded JSON
    json = get_insta_json(trigger.group(1))
    bot.say(parse_insta_json(json))
    
    
def get_insta_json(url):
    headers = {"Accept-Language": "en"}
    url = url.replace("https://","http://")
    r = get(url, headers=headers)
    
    # Extract JSON from html source code
    json_start = r.text.find("window._sharedData") + 21
    json_stops = r.text.find("</script>", json_start) - 1
    json_astxt = r.text[json_start:json_stops]
    return loads(json_astxt)


def parse_insta_json(json):
    # Parse JSON content
    needed    = json['entry_data']['PostPage'][0]['graphql']['shortcode_media']
    iwidth    = needed['dimensions']['width']
    iheight    = needed['dimensions']['height']
    iuser    = needed['owner']['username']
    ifname    = needed['owner']['full_name']
    ilikes    = needed['edge_media_preview_like']['count']
    icomms    = needed['edge_media_to_comment']['count']
    idate    = needed['taken_at_timestamp']
    pubdate = datetime.utcfromtimestamp(idate).strftime('%Y-%m-%d %H:%M:%S')    
    ivideo    = needed['is_video']
    
    # Does the post have a caption?
    try:
        icap = needed['edge_media_to_caption']['edges'][0]['node']['text']
        # Strip newlines
        icap = icap.replace('\n', ' ')
        # Truncate caption
        icap = (icap[:256] + u'…') if len(icap) > 256 else icap
    except:
        icap = False
    
    # Build bot response
    if ivideo == True:
        botmessage = "[insta] Video by "
    else:
        botmessage = "[insta] Photo by "
    if ifname == None:
        botmessage += "@%s" % iuser
    else:
        botmessage += "%s (@%s)" % (ifname, iuser)
    if icap != False:
        botmessage += u" | " + icap
    botmessage += u" | " + str(iwidth) + "x" + str(iheight)
    botmessage += u" | Likes: {:,} | Comments: {:,}".format(ilikes, icomms)
    botmessage += u" | Uploaded: " + pubdate
    
    # Ta-da!
    return botmessage
