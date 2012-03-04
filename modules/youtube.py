#!/usr/bin/env python
"""
youtube.py - Jenni YouTube Module
Copyright 2012, Dimitri Molenaars, Tyrope.nl.
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module will respond to .yt and .youtube commands and searches the youtubes.
"""

import urllib2, re

def ytsearch(jenni, input):
    """YouTube search module"""
    #modified from ytinfo: Copyright 2010-2011, Michael Yanovich, yanovich.net, Kenneth Sham.

    #Right now, this uses a parsing script from rscript.org. Eventually, I'd
    #like to use the YouTube API directly.

    #Before actually loading this in, let's see what input actually is so we can parse it right.

    #Grab info from rscript
    uri = 'http://rscript.org/lookup.php?type=ytinfo&term=' + input.group(2).encode('utf-8')
    uri = uri.replace(' ', '%20')
    redirects = 0
    while True:
        req = urllib2.Request(uri, headers={'Accept':'text/html'})
        req.add_header('User-Agent', 'OpenAnything/1.0 +http://diveintopython.org/')
        u = urllib2.urlopen(req)
        info = u.info()
        u.close()
        # info = web.head(uri)
        if not isinstance(info, list):
            status = '200'
        else:
            status = str(info[1])
            info = info[0]
        if status.startswith('3'):
            uri = urlparse.urljoin(uri, info['Location'])
        else: break
        redirects += 1
        if redirects >= 50:
            return "Too many re-directs."
    try: mtype = info['content-type']
    except:
        return
    if not (('/html' in mtype) or ('/xhtml' in mtype)):
        return
    u = urllib2.urlopen(req)
    bytes = u.read(262144)
    u.close()

    #Parse rscript info.
    rtitle = re.search('(TITLE: )(.*)', bytes)
    title = rtitle.group(2)

    rauthor = re.search('(AUTHOR: )(\S*) (20\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d).*', bytes)
    author = rauthor.group(2)
    if not author:
        jenni.say('I couldn\'t find information for that video.')
        return

    duration = int(re.search('(DURATION: )(.*)', bytes).group(2))
    if duration < 1: length = 'LIVE'
    else:
        hours = duration / (60 * 60)
        minutes = duration / 60 - (hours * 60)
        seconds = duration % 60

        length = ''
        if hours:
            length = str(hours) + 'hours'
            if minutes or seconds:
                length = length + ' '
        if minutes:
            length = length + str(minutes) + 'mins'
            if seconds:
                length = length + ' '
        if seconds: length = length + str(seconds) + 'secs'

    views = str('{:20,d}'.format(int(re.search('(VIEWS: )(.*)', bytes).group(2)))).lstrip(' ')

    rurl = re.search('(URL: )(.*)', bytes)
    url = rurl.group(2)

    message = '[YT Search] Title: ' +title+ \
              ' | Author: ' +author+ \
              ' | Duration: ' +length+ \
              ' | Views: ' +views+ \
              ' | Link: ' +url

    jenni.say(message)
ytsearch.commands = ['yt','youtube']
ytsearch.example = '.yt how to be a nerdfighter FAQ'

def ytinfo(jenni, input):
    #Right now, this uses a parsing script from rscript.org. Eventually, I'd
    #like to use the YouTube API directly.

    #Grab info from rscript
    uri = 'http://rscript.org/lookup.php?type=youtubeinfo&id=' + input.group(2)
    redirects = 0
    while True:
        req = urllib2.Request(uri, headers={'Accept':'text/html'})
        req.add_header('User-Agent', 'OpenAnything/1.0 +http://diveintopython.org/')
        u = urllib2.urlopen(req)
        info = u.info()
        u.close()
        # info = web.head(uri)
        if not isinstance(info, list):
            status = '200'
        else:
            status = str(info[1])
            info = info[0]
        if status.startswith('3'):
            uri = urlparse.urljoin(uri, info['Location'])
        else: break
        redirects += 1
        if redirects >= 50:
            return "Too many re-directs."
    try: mtype = info['content-type']
    except:
        return
    if not (('/html' in mtype) or ('/xhtml' in mtype)):
        return
    u = urllib2.urlopen(req)
    bytes = u.read(262144)
    u.close()

    #Parse rscript info.
    rtitle = re.search('(TITLE: )(.*)', bytes)
    title = rtitle.group(2)

    author = re.search('(AUTHOR: )(\S*) (20\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d).*', bytes)
    if not author:
        jenni.say('I couldn\'t find information for that video.')
        return
    uploader = author.group(2)
    year = author.group(3)
    month = author.group(4)
    day = author.group(5)
    hour = author.group(6)
    minute = author.group(7)
    uploaded = day + '/' + month + '/' + year + ', ' + hour + ':' + minute

    duration = int(re.search('(DURATION: )(.*)', bytes).group(2))
    if duration < 1: length = 'LIVE'
    else:
        hours = duration / (60 * 60)
        minutes = duration / 60 - (hours * 60)
        seconds = duration % 60

        length = ''
        if hours:
            length = str(hours) + 'hours'
            if minutes or seconds:
                length = length + ' '
        if minutes:
            length = length + str(minutes) + 'mins'
            if seconds:
                length = length + ' '
        if seconds: length = length + str(seconds) + 'secs'

    try:
	tempInt = int(re.search('(VIEWS: )(.*)', bytes)
    except ValueError:
	tempInt = 0
    views = str('{:20,d}'.format(tempInt.group(2)))).lstrip(' ')
    com = re.search('(COMMENTS: )(\d+)', bytes)
    if com: comments = str('{:20,d}'.format(int(com.group(2)))).lstrip(' ')
    else: comments = 'disabled'
    #Favorite, like, dislike
    favorite = re.search('(FAVORITE: )([\d,]+)( [\d,]+)?( [\d,]+)?', bytes)
    likes = favorite.group(3) or ' disabled'
    dislikes = favorite.group(4) or ' disabled'

    message = '[YouTube] Title: ' + title + ' | Uploader: ' + uploader + \
              ' | Uploaded: ' + uploaded + ' | Length: ' + length + \
              ' | Views: ' + views + ' | Comments: ' + comments + ' | Likes:'\
              + likes + ' | Dislikes:' + dislikes

    jenni.say(message)
ytinfo.rule = '.*(youtube.com/watch\S*v=|youtu.be/)([\w-]+).*'

if __name__ == '__main__':
    print __doc__.strip()
