"""
url.py - Phenny Bitly Module
Author: Michael S. Yanovich, http://opensource.osu.edu/~yanovich
About: http://inamidst.com/phenny/

This module will record all URLs to bitly via an api key and account.
It also automatically displays the "title" of any URL pasted into the channel.
"""

from BeautifulSoup import BeautifulSoup
import bitly
import re, urllib, urllib2, httplib, urlparse, time
from htmlentitydefs import name2codepoint
import web
import random
import httplib

#url_finder = re.compile(r'((?:(?:ht|f)tp(?:s?)\:\/\/|~\/|\/)?(?:\w+:\w+@)?((?:(?:[-\w\d{1-3}]+\.)+(?:com|org|net|gov|mil|biz|info|mobi|name|aero|jobs|edu|co\.uk|ac\.uk|it|fr|tv|museum|asia|local|travel|[a-z]{2})?)|((\b25[0-5]\b|\b[2][0-4][0-9]\b|\b[0-1]?[0-9]?[0-9]\b)(\.(\b25[0-5]\b|\b[2][0-4][0-9]\b|\b[0-1]?[0-9]?[0-9]\b)){3}))(?::[\d]{1,5})?(?:(?:(?:\/(?:[-\w~!$+|.,=]|%[a-f\d]{2})+)+|\/)+|\?|#)?(?:(?:\?(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=?(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)(?:&(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=?(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)*)*(?:#(?:[-\w~!$ |/.,*:;=]|%[a-f\d]{2})*)?)')
url_finder = re.compile(r'((http|https|ftp)(://\S+))')
r_title = re.compile(r'(?ims)<title[^>]*>(.*?)</title\s*>')
r_entity = re.compile(r'&[A-Za-z0-9#]+;')

def bitlystats(phenny, input):
    api = bitly.Api(login=str(input.bitly_user), apikey=str(input.bitly_api))
    text = input.group(2)
    if len(text) > 0:
        stats = api.stats(text)
        phenny.say("User clicks " + str(stats.user_clicks) + ", total clicks: " + str(stats.total_clicks) + ".")
bitlystats.commands = ['bit']
bitlystats.priority = 'medium'

def find_title(phenny, input, url):
    uri = url

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

    m = r_title.search(bytes)
    if m:
        title = m.group(1)
        title = title.strip()
        title = title.replace('\t', ' ')
        title = title.replace('\r', ' ')
        title = title.replace('\n', ' ')
        while '  ' in title:
            title = title.replace('  ', ' ')
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
            try: title.decode('utf-8')
            except:
                try: title = title.decode('iso-8859-1').encode('utf-8')
                except: title = title.decode('cp1252').encode('utf-8')
            else: pass
        else: title = 'None'

        title = title.replace('\n', '')
        title = title.replace('\r', '')
        return title

def short(phenny, input):
    try:
        api = bitly.Api(login=str(input.bitly_user), apikey=str(input.bitly_api))
        rand = random.random()
        text = input.group()
        a = re.findall(url_finder, text)
        k = len(a)
        while k > 0:
            b = str(a[k-1][0])
            if not b.startswith("http://bit.ly"):
                short1=api.shorten(b,{'history':1})
                if (len(b) >= 35):
                    #page_title = find_title(phenny, input, b)
                    #display = "[ " + str(page_title) + " ] " + str(short1)
                    if rand < 0.02:
                        phenny.say("http://bit.ly/bq1P4T")
                    else:
                        phenny.say(str(short1))
            k-=1
    except:
        return
#short.rule = r'.*(?:(?:ht|f)tp(?:s?)\:\/\/|~\/|\/)(?:\w+:\w+@)?((?:(?:[-\w\d{1-3}]+\.)+(?:com|org|net|gov|mil|biz|info|mobi|name|aero|jobs|edu|co\.uk|ac\.uk|it|fr|tv|museum|asia|local|travel|[a-z]{2})?))(?::[\d]{1,5})?(?:(?:(?:\/(?:[-\w~!$+|.,=]|%[a-f\d]{2})+)+|\/)+|\?|#)?(?:(?:\?(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=?(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)(?:&(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=?(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)*)*(?:#(?:[-\w~!$ |/.,*:;=]|%[a-f\d]{2})*)?\b'
short.rule = '.*((http|https|ftp)(://\S+)).*'
short.priority = 'high'

def title2(phenny, input, link):
    link = str(link)
    html = web.get(link)
    soup = BeautifulSoup(html)
    titles = soup.findAll('title')
    a = str(titles[0])
    b = a[7:-8]
    b = str(b)
    return b

def show_title(phenny,input):
    text = input.group()
    a = re.findall(url_finder, text)
    k = len(a)
    i = 0
    while i < k:
        url = str(a[i][0])
        try:
            try: 
                page_title = find_title(phenny, input, url)
            except:
                page_title = title2(phenny, input, url)
        except:
            return
        if page_title == None or page_title == "None":
            return
        else:
            display = "[ " + str(page_title) + " ]"
        phenny.say(display)
        i += 1
#show_title.rule = r'.*(?:(?:ht|f)tp(?:s?)\:\/\/|~\/|\/)(?:\w+:\w+@)?((?:(?:[-\w\d{1-3}]+\.)+(?:com|org|net|gov|mil|biz|info|mobi|name|aero|jobs|edu|co\.uk|ac\.uk|it|fr|tv|museum|asia|local|travel|[a-z]{2})?))(?::[\d]{1,5})?(?:(?:(?:\/(?:[-\w~!$+|.,=]|%[a-f\d]{2})+)+|\/)+|\?|#)?(?:(?:\?(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=?(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)(?:&(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=?(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)*)*(?:#(?:[-\w~!$ |/.,*:;=]|%[a-f\d]{2})*)?\b'
show_title.rule = '.*((http|https|ftp)(://\S+)).*'
show_title.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
