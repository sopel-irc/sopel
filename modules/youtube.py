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
    try: u = urllib2.urlopen(req, None, 0.5)
    except:
        jenni.say('Something went wrong when accessing the rscript.org parser.')
        return
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
    #Grab info from YT API
    uri = 'http://gdata.youtube.com/feeds/api/videos/' + input.group(2) + '?v=2'
    redirects = 0
    while True:
        req = urllib2.Request(uri, headers={'Accept':'*/*', 'User-Agent':'OpenAnything/1.0 +http://diveintopython.org/'})
        try: u = urllib2.urlopen(req, None, 0.5)
        except:
            jenni.say('Something went wrong when accessing the YouTube API.')
            return
        info = u.info()
        u.close()
        # info = web.head(uri)
        if not isinstance(info, list):
            status = '200'
            info = info[0]
        else:
            status = str(info[1])
        try: info = info[0]
        except e: jenni.msg(input.devchan,"[DEVMSG]Line 120: info= "+str(info)+" exception: "+str(e))
        jenni.msg(input.devchan,"[DEVMSG]YT API Result: ["+status+"]"+info)
        if status.startswith('3'):
            uri = urlparse.urljoin(uri, info['Location'])
        else: break
        redirects += 1
        if redirects >= 50:
            return "Too many re-directs."
    try: mtype = info['content-type']
    except: return
    if not (('/html' in mtype) or ('/xhtml' in mtype)):
        return
    try: u = urllib2.urlopen(req, None, 0.5)
    except:
        jenni.say('Something went wrong when accessing the YouTube API.')
        return
    bytes = u.read(262144)
    u.close()

    #Parse YouTube API info (XML)

    #get title
    title_result = re.search('(?:<media:title type=\'plain\'>)(.*)(?:</media:title>)', bytes)
    title = title_result.group(1)

    #get youtube channel
    uploader_result = re.search('(?:<author><name>)(.*)(?:</name>)', bytes)
    uploader = uploader_result.group(1)

    #get upload time in format: yyyy-MM-ddThh:mm:ss.sssZ
    uploaded_result = re.search('(?:<yt:uploaded>)(.*)(?:</yt:uploaded>)', bytes)
    upraw = uploaded_result.group(1)
    #parse from current format to output format: DD/MM/yyyy, hh:mm
    uploaded = upraw[8:10]+"/"+upraw[5:7]+"/"+upraw[0:4]+", "+upraw[11:13]+":"+upraw[14:16]

    #get duration in seconds
    length_result = re.search('(?:<yt:duration seconds=\')(.*)(?:\'/>)', bytes)
    duration = length_result.group(1)

    #Detect liveshow + parse duration into proper time format.
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
    

    #get views
    views_result = re.search('(?:<yt:statistics favoriteCount=\')([0-9]*)(?:\' viewCount=\')([0-9]*)(?:\'/>)', bytes)
    views = views_result.group(2)

    #get favourites (for future use?)
    favs = views_result.group(1)

    #get comment count
    comments_result = re.search('(?:<gd:comments><gd:feedLink)(?:.*)(?:countHint=\')(.*)(?:\'/></gd:comments>)', bytes)
    comments = comments_result.group(1)

    #get likes & dislikes
    liking_result = re.search('(?:<yt:rating numDislikes=\')(.*)(?:\' numLikes=\')(.*)(?:\'/>)',bytes)
    likes = liking_result.group(2)
    dislikes = liking_result.group(1)

    #combine variables and print
    message = '[YouTube] Title: ' + title + ' | Uploader: ' + uploader + \
              ' | Uploaded: ' + uploaded + ' | Length: ' + length + \
              ' | Views: ' + views + ' | Comments: ' + comments + ' | Likes: '\
              + likes + ' | Dislikes: ' + dislikes

    jenni.say(message)
ytinfo.rule = '.*(youtube.com/watch\S*v=|youtu.be/)([\w-]+).*'

if __name__ == '__main__':
    print __doc__.strip()
