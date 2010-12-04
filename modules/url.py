"""
url.py - Jenney Bitly Module
Author: Michael S. Yanovich, http://opensource.osu.edu/~yanovich
About: http://inamidst.com/phenny/

This module will record all URLs to bitly via an api key and account.
It also automatically displays the "title" of any URL pasted into the channel.
"""

#
# Copyright 2009 Empeeric LTD. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import simplejson
import urllib,urllib2
import urlparse
import string

BITLY_BASE_URL = "http://api.j.mp/"
BITLY_API_VERSION = "2.0.1"

VERBS_PARAM = {
         'shorten':'longUrl',
         'expand':'shortUrl',
         'info':'shortUrl',
         'stats':'shortUrl',
         'errors':'',
}

class Bit:
    class BitlyError(Exception):
        '''Base class for bitly errors'''
        @property
        def message(self):
            '''Returns the first argument used to construct this error.'''
            return self.args[0]

    class Api(object):
        """ API class for bit.ly """
        def __init__(self, login, apikey):
            self.login = login
            self.apikey = apikey
            self._urllib = urllib2

        def shorten(self,longURLs,params={}):
            """ 
                Takes either:
                A long URL string and returns shortened URL string
                Or a list of long URL strings and returns a list of shortened URL strings.
            """
            want_result_list = True
            if not isinstance(longURLs, list):
                longURLs = [longURLs]
                want_result_list = False

            for index,url in enumerate(longURLs):
                if not '://' in url:
                    longURLs[index] = "http://" + url

            request = self._getURL("shorten",longURLs,params)
            result = self._fetchUrl(request)
            json = simplejson.loads(result)
            self._CheckForError(json)

            results = json['results']
            res = [self._extract_short_url(results[url]) for url in longURLs]

            if want_result_list:
                return res
            else:
                return res[0]

        def _extract_short_url(self,item):
            if item['shortKeywordUrl'] == "":
                return item['shortUrl']
            else:
                return item['shortKeywordUrl']

        def expand(self,shortURL,params={}):
            """ Given a bit.ly url or hash, return long source url """
            request = self._getURL("expand",shortURL,params)
            result = self._fetchUrl(request)
            json = simplejson.loads(result)
            self._CheckForError(json)
            return json['results'][string.split(shortURL, '/')[-1]]['longUrl']

        def info(self,shortURL,params={}):
            """ 
            Given a bit.ly url or hash, 
            return information about that page, 
            such as the long source url
            """
            request = self._getURL("info",shortURL,params)
            result = self._fetchUrl(request)
            json = simplejson.loads(result)
            self._CheckForError(json)
            return json['results'][string.split(shortURL, '/')[-1]]

        def stats(self,shortURL,params={}):
            """ Given a bit.ly url or hash, return traffic and referrer data.  """
            request = self._getURL("stats",shortURL,params)
            result = self._fetchUrl(request)
            json = simplejson.loads(result)
            self._CheckForError(json)
            return Stats.NewFromJsonDict(json['results'])

        def errors(self,params={}):
            """ Get a list of bit.ly API error codes. """
            request = self._getURL("errors","",params)
            result = self._fetchUrl(request)
            json = simplejson.loads(result)
            self._CheckForError(json)
            return json['results']

        def setUrllib(self, urllib):
            '''Override the default urllib implementation.
        
            Args:
              urllib: an instance that supports the same API as the urllib2 module
            '''
            self._urllib = urllib

        def _getURL(self,verb,paramVal,more_params={}):
            if not isinstance(paramVal, list):
                paramVal = [paramVal]

            params = {
                      'version':BITLY_API_VERSION,
                      'format':'json',
                      'login':self.login,
                      'apiKey':self.apikey,
                }

            params.update(more_params)
            params = params.items()

            verbParam = VERBS_PARAM[verb]
            if verbParam:
                for val in paramVal:
                    params.append(( verbParam,val ))

            encoded_params = urllib.urlencode(params)
            return "%s%s?%s" % (BITLY_BASE_URL,verb,encoded_params)

        def _fetchUrl(self,url):
            '''Fetch a URL
        
            Args:
              url: The URL to retrieve
        
            Returns:
              A string containing the body of the response.
            '''

            # Open and return the URL 
            url_data = self._urllib.urlopen(url).read()
            return url_data

        def _CheckForError(self, data):
            """Raises a BitlyError if bitly returns an error message.
        
            Args:
              data: A python dict created from the bitly json response
            Raises:
              BitlyError wrapping the bitly error message if one exists.
            """
            # bitly errors are relatively unlikely, so it is faster
            # to check first, rather than try and catch the exception
            if 'ERROR' in data or data['statusCode'] == 'ERROR':
                raise BitlyError, data['errorMessage']
            for key in data['results']:
                if type(data['results']) is dict and type(data['results'][key]) is dict:
                    if 'statusCode' in data['results'][key] and data['results'][key]['statusCode'] == 'ERROR':
                        raise BitlyError, data['results'][key]['errorMessage']

    class Stats(object):
        '''A class representing the Statistics returned by the bitly api.
        
        The Stats structure exposes the following properties:
        status.user_clicks # read only
        status.clicks # read only
        '''

        def __init__(self,user_clicks=None,total_clicks=None):
            self.user_clicks = user_clicks
            self.total_clicks = total_clicks

        @staticmethod
        def NewFromJsonDict(data):
            '''Create a new instance based on a JSON dict.
        
            Args:
              data: A JSON dict, as converted from the JSON in the bitly API
            Returns:
              A bitly.Stats instance
            '''
            return Stats(user_clicks=data.get('userClicks', None),
                      total_clicks=data.get('clicks', None))

bitly = Bit()

bitly_api = "R_ff9b3a798d6e5ac38efc7543a72ad4ce"
bitly_user = "phennyosu"

import re, httplib, time
from htmlentitydefs import name2codepoint
import web

url_finder = re.compile(r'((http|https|ftp)(://\S+))')
r_title = re.compile(r'(?ims)<title[^>]*>(.*?)</title\s*>')
r_entity = re.compile(r'&[A-Za-z0-9#]+;')

def bitlystats(jenney, input):
    api = bitly.Api(login=str(bitly_user), apikey=str(bitly_api))
    text = input.group(2)
    if len(text) > 0:
        stats = api.stats(text)
        jenney.say("User clicks " + str(stats.user_clicks) + ", total clicks: " + str(stats.total_clicks) + ".")
bitlystats.commands = ['bit']
bitlystats.priority = 'medium'

def find_title(jenney, input, url):
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

def short(jenney, input):
    if input.nick == 'jenney-git':
        return
    try:
        api = bitly.Api(login=str(bitly_user), apikey=str(bitly_api))
        text = input.group()
        a = re.findall(url_finder, text)
        k = len(a)
        i = 0
        while i < k:
            b = str(a[i][0])
            if not b.startswith("http://bit.ly") or not b.startswith("http://j.mp/"):
                short1=api.shorten(b,{'history':1})
                if (len(b) >= 50):
                    #page_title = find_title(jenney, input, b)
                    #display = "[ " + str(page_title) + " ] " + str(short1)
                    jenney.say(str(short1))
            i += 1
    except:
        return
short.rule = '.*((http|https|ftp)(://\S+)).*'
short.priority = 'high'

'''
def title2(jenney, input, link):
    link = str(link)
    html = web.get(link)
    soup = BeautifulSoup(html)
    titles = soup.findAll('title')
    a = str(titles[0])
    b = a[7:-8]
    b = str(b)
    return b
'''

def show_title(jenney,input):
    if input.nick == 'jenney-git':
        return
    text = input.group()
    a = re.findall(url_finder, text)
    k = len(a)
    i = 0
    while i < k:
        url = str(a[i][0])
        try:
            try: 
                page_title = find_title(jenney, input, url)
            except:
                #page_title = title2(jenney, input, url)
                pass
        except:
            return
        if page_title == None or page_title == "None":
            return
        else:
            display = "[ " + str(page_title) + " ]"
        jenney.say(display)
        i += 1
show_title.rule = '.*((http|https|ftp)(://\S+)).*'
show_title.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
