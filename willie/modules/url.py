"""
url.py - Willie URL title module
Copyright 2010-2011, Michael Yanovich, yanovich.net, Kenneth Sham
Copyright 2012 Edward Powell
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import re
from htmlentitydefs import name2codepoint
import willie.web as web
import unicodedata
import urlparse

url_finder = None
r_entity = re.compile(r'&[A-Za-z0-9#]+;')
INVALID_WEBSITE = 0x01
exclusion_char = '!'

def configure(config):
    """
    
    | [url] | example | purpose |
    | ---- | ------- | ------- |
    | exclude | https?://git\.io/.* | A list of regular expressions for URLs for which the title should not be shown. |
    | exclusion_char | ! | A character (or string) which, when immediately preceding a URL, will stop the URL's title from being shown. |
    """
    if config.option('Exclude certain URLs from automatic title display', False):
        if not config.has_section('url'):
            config.add_section('url')
        config.add_list('url',  'exclude', 'Enter regular expressions for each URL you would like to exclude.',
            'Regex:')
        config.interactive_add('url', 'exclusion_char',
            'Prefix to suppress URL titling', '!')
    
def setup(willie):
    global url_finder, exclusion_char
    if willie.config.has_option('url', 'exclude'):
        regexes = [re.compile(s) for s in willie.config.url.exclude]
    else:
        regexes = []
    
    if not willie.memory.contains('url_exclude'):
        willie.memory['url_exclude'] = regexes
    else:
        exclude = willie.memory['url_exclude']
        if regexes: exclude.append(regexes)
        willie.memory['url_exclude'] = exclude
    
    if willie.config.has_option('url', 'exclusion_char'):
        exclusion_char = willie.config.url.exclusion_char
    
    url_finder = re.compile(r'(?u)(%s?(http|https|ftp)(://\S+))' %
        (exclusion_char))
    # We want the exclusion list to be pre-compiled, since url parsing gets
    # called a /lot/, and it's annoying when it's laggy.

def find_title(url):
    """
    This finds the title when provided with a string of a URL.
    """
    uri = url

    if not uri and hasattr(self, 'last_seen_uri'):
        uri = self.last_seen_uri.get(origin.sender)

    if not re.search('^((https?)|(ftp))://', uri):
        uri = 'http://' + uri

    if "twitter.com" in uri:
        uri = uri.replace('#!', '?_escaped_fragment_=')

    content = web.get(uri)
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
        title = uni_decode(title)
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

def getTLD (url):
    idx = 7
    if url.startswith('https://'): idx = 8
    elif url.startswith('ftp://'): idx = 6
    u = url[idx:]
    f = u.find('/')
    if f == -1: u = url
    else: u = url[0:idx] + u[0:f]
    return u

def get_results(willie, text):
    a = re.findall(url_finder, text)
    display = [ ]
    for match in a:
        match = match[0]
        if (match.startswith(exclusion_char) or
                any(pattern.findall(match) for pattern in willie.memory['url_exclude'])):
            continue
        url = uni_encode(match)
        url = uni_decode(url)
        url = iriToUri(url)
        try:
            page_title = find_title(url)
        except:
            page_title = None # if it can't access the site fail silently
        display.append([page_title, url])
    return display

def show_title_auto (willie, trigger):
    if trigger.startswith('.title '):
        return
    if len(re.findall("\([\d]+\sfiles\sin\s[\d]+\sdirs\)", trigger)) == 1: return
    try:
        results = get_results(willie, trigger)
    except Exception as e: raise e
    if results is None: return

    k = 1
    for r in results:
        if k > 3: break
        k += 1

        if r[0] is None:
            continue
        else: r[1] = getTLD(r[1])
        message = '[ %s ] - %s' % (r[0], r[1])
        if message != trigger:
            willie.say(message)
show_title_auto.rule = '(?u).*((http|https)(://\S+)).*'
show_title_auto.priority = 'high'

def show_title_demand (willie, trigger):
    """Show the title of a URL"""
    #try:
    results = get_results(trigger)
    #except: return
    if results is None: return

    for r in results:
        if r[0] is None: continue
        r[1] = getTLD(r[1])
        willie.say('[ %s ] - %s' % (r[0], r[1]))
show_title_demand.commands = ['title']
show_title_demand.priority = 'high'


#Tools formerly in unicode.py

def uni_decode(bytes):
    try:
        text = bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = bytes.decode('iso-8859-1')
        except UnicodeDecodeError:
            text = bytes.decode('cp1252')
    return text


def uni_encode(bytes):
    try:
        text = bytes.encode('utf-8')
    except UnicodeEncodeError:
        try:
            text = bytes.encode('iso-8859-1')
        except UnicodeEncodeError:
            text = bytes.encode('cp1252')
    return text


def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)


def iriToUri(iri):
    parts = urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti == 1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )

if __name__ == '__main__':
    print __doc__.strip()
