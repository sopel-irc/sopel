# -*- coding: utf8 -*-
"""
youtube.py - Willie YouTube Module
Copyright 2012, Dimitri Molenaars, Tyrope.nl.
Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net

This module will respond to .yt and .youtube commands and searches the youtubes.
"""

from willie import web, tools
from willie.module import rule, commands, example
import json
import re
from HTMLParser import HTMLParser


def setup(bot):
    regex = re.compile('(youtube.com/watch\S*v=|youtu.be/)([\w-]+)')
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.WillieMemory()
    bot.memory['url_callbacks'][regex] = ytinfo


def ytget(bot, trigger, uri):
    try:
        bytes = web.get(uri)
        result = json.loads(bytes)
        if 'feed' in result:
            video_entry = result['feed']['entry'][0]
        else:
            video_entry = result['entry']
    except:
        bot.say('Something went wrong when accessing the YouTube API.')
        return 'err'
    vid_info = {}
    try:
        # The ID format is tag:youtube.com,2008:video:RYlCVwxoL_g
        # So we need to split by : and take the last item
        vid_id = video_entry['id']['$t'].split(':')
        vid_id = vid_id[len(vid_id) - 1]  # last item is the actual ID
        vid_info['link'] = 'http://youtu.be/' + vid_id
    except KeyError:
        vid_info['link'] = 'N/A'

    try:
        vid_info['title'] = video_entry['title']['$t']
    except KeyError:
        vid_info['title'] = 'N/A'

    #get youtube channel
    try:
        vid_info['uploader'] = video_entry['author'][0]['name']['$t']
    except KeyError:
        vid_info['uploader'] = 'N/A'

    #get upload time in format: yyyy-MM-ddThh:mm:ss.sssZ
    try:
        upraw = video_entry['published']['$t']
        #parse from current format to output format: DD/MM/yyyy, hh:mm
        vid_info['uploaded'] = '{0}-{1}-{2}, {3}:{4}'.format(upraw[0:4], upraw[8:10], upraw[5:7],
                                                             upraw[11:13], upraw[14:16])
    except KeyError:
        vid_info['uploaded'] = 'N/A'

    #get duration in seconds
    try:
        duration = int(video_entry['media$group']['yt$duration']['seconds'])
        #Detect liveshow + parse duration into proper time format.
        if duration < 1:
            vid_info['length'] = 'LIVE'
        else:
            hours = duration / (60 * 60)
            minutes = duration / 60 - (hours * 60)
            seconds = duration % 60

            if hours:
                vid_info['length'] = '{0}:{1:02}:{2:02}'.format(hours, minutes, seconds)
            else:
                vid_info['length'] = '{0}:{1:02}'.format(minutes, seconds)
    except KeyError:
        vid_info['length'] = 'N/A'

    #get views
    try:
        views = video_entry['yt$statistics']['viewCount']
        vid_info['views'] = str('{0:20,d}'.format(int(views))).lstrip(' ')
    except KeyError:
        vid_info['views'] = 'N/A'

    #get comment count
    try:
        comments = video_entry['gd$comments']['gd$feedLink']['countHint']
        vid_info['comments'] = str('{0:20,d}'.format(int(comments))).lstrip(' ')
    except KeyError:
        vid_info['comments'] = 'N/A'

    #get likes & dislikes
    try:
        likes = video_entry['yt$rating']['numLikes']
        vid_info['likes'] = str('{0:20,d}'.format(int(likes))).lstrip(' ')
    except KeyError:
        vid_info['likes'] = 'N/A'
    try:
        dislikes = video_entry['yt$rating']['numDislikes']
        vid_info['dislikes'] = str('{0:20,d}'.format(int(dislikes))).lstrip(' ')
    except KeyError:
        vid_info['dislikes'] = 'N/A'
    return vid_info


@commands('yt', 'youtube')
@example('.yt how to be a nerdfighter FAQ')
def ytsearch(bot, trigger):
    """Search YouTube"""
    #modified from ytinfo: Copyright 2010-2011, Michael Yanovich, yanovich.net, Kenneth Sham.
    if not trigger.group(2):
        return
    uri = 'http://gdata.youtube.com/feeds/api/videos?v=2&alt=json&max-results=1&q=' + trigger.group(2).encode('utf-8')
    uri = uri.replace(' ', '+')
    video_info = ytget(bot, trigger, uri)

    if video_info is 'err':
        return

    if video_info['link'] == 'N/A':
        bot.say("Sorry, I couldn't find the video you are looking for")
        return

    message = ('{0} | Length: {1} | Uploader: {2} | Uploaded: {3} | Views: {4} | '
               '+{5} -{6} | Comments: {7} | {8}'
               .format(video_info['title'], video_info['length'], video_info['uploader'],
                       video_info['uploaded'], video_info['views'], video_info['likes'],
                       video_info['dislikes'], video_info['comments'], video_info['link']))
    bot.reply(HTMLParser().unescape(message))


@rule('.*(youtube.com/watch\S*v=|youtu.be/)([\w-]+).*')
def ytinfo(bot, trigger, found_match=None):
    """
    Get information about the latest video uploaded by the channel provided.
    """
    match = found_match or trigger
    #Grab info from YT API
    uri = 'http://gdata.youtube.com/feeds/api/videos/' + match.group(2) + '?v=2&alt=json'

    video_info = ytget(bot, trigger, uri)
    if video_info is 'err':
        return

    #combine variables and print
    message = ('{0} | Length: {1} | Uploader: {2} | Uploaded: {3} | Views: {4} | '
               '+{5} -{6} | Comments: {7} | {8}'
               .format(video_info['title'], video_info['length'], video_info['uploader'],
                       video_info['uploaded'], video_info['views'], video_info['likes'],
                       video_info['dislikes'], video_info['comments'], video_info['link']))
    bot.reply(HTMLParser().unescape(message))


@commands('ytlast', 'ytnew', 'ytlatest')
@example('.ytlast vlogbrothers')
def ytlast(bot, trigger):
    if not trigger.group(2):
        return
    uri = 'https://gdata.youtube.com/feeds/api/users/' + trigger.group(2).encode('utf-8') + '/uploads?max-results=1&alt=json&v=2'
    video_info = ytget(bot, trigger, uri)

    if video_info is 'err':
        return

    message = ('{0} | Length: {1} | Uploader: {2} | Uploaded: {3} | Views: {4} | '
               '+{5} -{6} | Comments: {7} | {8}'
               .format(video_info['title'], video_info['length'], video_info['uploader'],
                       video_info['uploaded'], video_info['views'], video_info['likes'],
                       video_info['dislikes'], video_info['comments'], video_info['link']))
    bot.say(HTMLParser().unescape(message))
