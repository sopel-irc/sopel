"""
url.py - Jenni Bitly Module
Author: Michael S. Yanovich, http://opensource.osu.edu/~yanovich
About: http://inamidst.com/phenny/

This module will record all URLs to bitly via an api key and account.
It also automatically displays the "title" of any URL pasted into the channel.
"""

# Change the bitly_api_key to use your api key and to have your 
# own public timeline via bitly
bitly_api_key = "R_ff9b3a798d6e5ac38efc7543a72ad4ce"
bitly_user = "phennyosu"

import re, urllib2
from htmlentitydefs import name2codepoint
import web

url_finder = re.compile(r'((http|https|ftp)(://\S+))')
r_entity = re.compile(r'&[A-Za-z0-9#]+;')

def find_title(url):
    uri = url

    if not re.search('^((https?)|(ftp))://', uri):
        uri = 'http://' + uri

    redirects = 0
    while True:
        req = urllib2.Request(uri, headers={'Accept':'text/html'})
        req.add_header('User-Agent', 'OpenAnything/1.0 +http://diveintopython.org/')
        u = urllib2.urlopen(req)
        info = u.info()
        u.close()

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
        try: title.decode('utf-8')
        except:
            try: title = title.decode('iso-8859-1').encode('utf-8')
            except: title = title.decode('cp1252').encode('utf-8')
        else: pass
    else: title = 'None'

    title = title.replace('\n', '')
    title = title.replace('\r', '')
    
    if title:
        return title

def short(text):
    bitlys = [ ]
    try:
        a = re.findall(url_finder, text)
        k = len(a)
        i = 0
        while i < k:
            b = str(a[i][0])
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
    bitly = short(input)
    idx = 7
    for b in bitly:
        displayBitLy(jenni, b[0], b[1])
generateBitLy.commands = ['bitly']
generateBitLy.priority = 'high'

def displayBitLy (jenni, url, shorten):
    if url is None or shorten is None: return
    idx = 7
    if url.startswith('https://'): idx = 8
    elif url.startswith('ftp://'): idx = 6
    u = url[idx:]
    f = u.find('/')
    if f == -1: u = url
    else: u = url[0:idx] + u[0:f]
    jenni.say('%s  -  %s' % (u, shorten))

def get_results(text):
    a = re.findall(url_finder, text)
    k = len(a)
    i = 0
    display = [ ]
    while i < k:
        url = str(a[i][0])
        try: 
            page_title = find_title(url)
        except: 
            page_title = None # if it can't access the site fail silently
        
        bitly = short(url)
        display.append([page_title, url, bitly[0][1]])
        i += 1
    return display

def show_title_auto (jenni, input):
    if input.startswith('.title ') or input.startswith('.bitly '): return
    try:
        results = get_results(input)
    except: return
    if results is None: return

    for r in results:
        if r[0] is None:
            if len(r[1]) > 50: displayBitLy(jenni, r[1], r[2])
            continue
        if len(r[1]) > 50: r[1] = r[2]
        jenni.say('[ %s ] - %s' % (r[0], r[1]))
show_title_auto.rule = '.*((http|https)(://\S+)).*'
show_title_auto.priority = 'high'

def show_title_demand (jenni, input):
    try:
        results = get_results(input)
    except: return
    if results is None: return
    
    for r in results:
        if r[0] is None: continue
        jenni.say('[ %s ] - %s' % (r[0], r[1]))
show_title_demand.commands = ['title']
show_title_demand.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
