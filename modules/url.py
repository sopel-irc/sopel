#!/usr/bin/env python
"""
url.py - Jenni Bitly Module
Copyright 2010-2011, Michael Yanovich, yanovich.net, Kenneth Sham.
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module will record all URLs to bitly via an api key and account.
It also automatically displays the "title" of any URL pasted into the channel.
"""

import re
from htmlentitydefs import name2codepoint
import unicode
import urllib2
import web

# Place a file in your ~/jenni/ folder named, bitly.txt
# and inside this file place your API key followed by a ','
# and then your username. For example, the only line in that
# file should look like this:
# R_d67798xkjc87sdx6x8c7kjc87,myusername

# this variable is to determine when to use bitly. If the URL is more
# than this length, it'll display a bitly URL instead. To disable bit.ly, put None
# even if it's set to None, triggering .bitly command will still work!
BITLY_TRIGGER_LEN = 65
EXCLUSION_CHAR = "!"
IGNORE = ["git.io"]

# do not edit below this line unless you know what you're doing
bitly_loaded = 0

try:
    file = open("bitly.txt", "r")
    key = file.read()
    key = key.split(",")
    bitly_api_key = str(key[0].lstrip().rstrip())
    bitly_user = str(key[1].lstrip().rstrip())
    file.close()
    bitly_loaded = 1
except:
    print "ERROR: No bitly.txt found."

url_finder = re.compile(r'(?u)(%s?(http|https|ftp)(://\S+))' % (EXCLUSION_CHAR))
r_entity = re.compile(r'&[A-Za-z0-9#]+;')
INVALID_WEBSITE = 0x01

def noteuri(jenni, input):
    uri = input.group(1).encode('utf-8')
    if not hasattr(jenni.bot, 'last_seen_uri'):
        jenni.bot.last_seen_uri = {}
    jenni.bot.last_seen_uri[input.sender] = uri
noteuri.rule = r'(?u).*(http[s]?://[^<> "\x01]+)[,.]?'
noteuri.priority = 'low'

def find_title(url):
    """
    This finds the title when provided with a string of a URL."
    """
    uri = url

    if not uri and hasattr(self, 'last_seen_uri'):
        uri = self.last_seen_uri.get(origin.sender)

    for item in IGNORE:
        if item in uri:
            return

    if not re.search('^((https?)|(ftp))://', uri):
        uri = 'http://' + uri

    if "twitter.com" in uri:
        uri = uri.replace('#!', '?_escaped_fragment_=')

    redirects = 0
    ## follow re-directs, if someone pastes a bitly of a tinyurl, etc..
    while True:
        req = urllib2.Request(uri, headers={'Accept':'text/html'})
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0')
        u = urllib2.urlopen(req)
        info = u.info()
        u.close()

        if not isinstance(info, list):
            status = '200'
        else:
            status = unicode.encode(info[1])
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
    content = bytes
    regex = re.compile('<(/?)title( [^>]+)?>', re.IGNORECASE)
    content = regex.sub(r'<\1title>',content)
    regex = re.compile('[\'"]<title>[\'"]', re.IGNORECASE)
    content = regex.sub('',content)
    start = content.find('<title>')
    if start == -1: return
    end = content.find('</title>', start)
    if end == -1: return
    content = content[start+7:end]
    content = content.strip('\n').rstrip().lstrip()
    title = content

    if len(title) > 200:
        title = title[:200] + '[...]'

    def e(m):
        entity = m.group()
        if entity.startswith('&#x'):
            cp = int(entity[3:-1],16)
            return unichr(cp).encode('utf-8')
        elif entity.startswith('&#'):
            cp = int(entity[2:-1])
            return unichr(cp).encode('utf-8')
        else:
            char = name2codepoint[entity[1:-1]]
            return unichr(char).encode('utf-8')

    title = r_entity.sub(e, title)

    if title:
        title = unicode.decode(title)
    else: title = 'None'

    title = title.replace('\n', '')
    title = title.replace('\r', '')

    def remove_spaces(x):
        if "  " in x:
            x = x.replace("  ", " ")
            return remove_spaces(x)
        else:
            return x

    title = remove_spaces (title)

    re_dcc = re.compile(r'(?i)dcc\ssend')
    title = re.sub(re_dcc, '', title)

    if title:
        return title

def short(text):
    """
    This function creates a bitly url for each url in the provided "text" string.
    The return type is a list.
    """

    if not bitly_loaded: return [ ]
    bitlys = [ ]
    try:
        a = re.findall(url_finder, text)
        k = len(a)
        i = 0
        while i < k:
            b = unicode.decode(a[i][0])
            if not b.startswith("http://bit.ly") or not b.startswith("http://j.mp/"):
                # check to see if the url is valid
                try: c = web.head(b)
                except: return [[None, None]]

                url = "http://api.j.mp/v3/shorten?login=%s&apiKey=%s&longUrl=%s&format=txt" % (bitly_user, bitly_api_key, urllib2.quote(b))
                shorter = web.get(url)
                shorter.strip()
                bitlys.append([b, shorter])
            i += 1
        return bitlys
    except:
        return

def generateBitLy (jenni, input):
    if not bitly_loaded: return
    bitly = short(input)
    idx = 7
    for b in bitly:
        displayBitLy(jenni, b[0], b[1])
generateBitLy.commands = ['bitly']
generateBitLy.priority = 'high'

def displayBitLy (jenni, url, shorten):
    if url is None or shorten is None: return
    u = getTLD(url)
    jenni.say('%s  -  %s' % (u, shorten))

def getTLD (url):
    idx = 7
    if url.startswith('https://'): idx = 8
    elif url.startswith('ftp://'): idx = 6
    u = url[idx:]
    f = u.find('/')
    if f == -1: u = url
    else: u = url[0:idx] + u[0:f]
    return u

def doUseBitLy (url):
    return bitly_loaded and BITLY_TRIGGER_LEN is not None and len(url) > BITLY_TRIGGER_LEN

def get_results(text):
    a = re.findall(url_finder, text)
    k = len(a)
    i = 0
    display = [ ]
    while i < k:
        url = unicode.encode(a[i][0])
        url = unicode.decode(url)
        url = unicode.iriToUri(url)
        if not url.startswith(EXCLUSION_CHAR):
            try:
                page_title = find_title(url)
            except:
                page_title = None # if it can't access the site fail silently
            if bitly_loaded: # and (page_title is not None or page_title == INVALID_WEBSITE):
                bitly = short(url)
                bitly = bitly[0][1]
            else: bitly = url
            display.append([page_title, url, bitly])
        i += 1
    return display

def show_title_auto (jenni, input):
    if input.startswith('.title ') or input.startswith('.bitly '): return
    if len(re.findall("\([\d]+\sfiles\sin\s[\d]+\sdirs\)", input)) == 1: return
    try:
        results = get_results(input)
    except: return
    if results is None: return

    k = 1
    for r in results:
        if k > 3: break
        k += 1

        useBitLy = doUseBitLy(r[1])
        if r[0] is None:
            if useBitLy: displayBitLy(jenni, r[1], r[2])
            continue
        if useBitLy: r[1] = r[2]
        else: r[1] = getTLD(r[1])
        jenni.say('[ %s ] - %s' % (r[0], r[1]))
show_title_auto.rule = '(?u).*(%s?(http|https)(://\S+)).*' % (EXCLUSION_CHAR)
show_title_auto.priority = 'high'

def show_title_demand (jenni, input):
    #try:
    results = get_results(input)
    #except: return
    if results is None: return

    for r in results:
        if r[0] is None: continue
        if doUseBitLy(r[1]): r[1] = r[2]
        else: r[1] = getTLD(r[1])
        jenni.say('[ %s ] - %s' % (r[0], r[1]))
show_title_demand.commands = ['title']
show_title_demand.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
