"""
dftba.py - jenni DFT.BA Module
Author: Edward Powell, embolalia.net
About: http://inamidst.com/phenny

This module allows for retrieving stats, shortening and lengthening dft.ba urls.
"""
import urllib
import simplejson as json

def shorten(jenni, input):
    """Shorten a URL with DFT.BA"""
    args = input.groups()
    url = args[0]
    code = None
    if args[1]: code = args[1].lstrip(' ')
    if code: params = urllib.urlencode({'TARGET_URL': url, 'SOURCE_URL': code})
    else: params = urllib.urlencode({'TARGET_URL': url})
    r = urllib.urlopen('http://dft.ba/api/shorten.json', params)
    response = json.loads(r.read())['api_response']
    url = response['response']['short_url']
    if not url:
        msg = 'Uh oh. Something went wrong with your request.'
        if code: msg = msg + ' I think the code you want is already in use.'
    else:
        msg = 'http://dft.ba/' + url
    jenni.say(msg)
shorten.rule = '\.shorten (\S+)( ?\S+)?'
shorten.priority = 'high'
shorten.example = '.shorten http://example.com example'


def expand(jenni, input):
    url = input.group(1)
    params = urllib.urlencode({'SHORT_URL': url})
    r = urllib.urlopen('http://dft.ba/api/expand.json', params)
    response = json.loads(r.read())
    if response['api_response']['response']['status'] == 'error':
        jenni.say('Uh oh. Something went wrong with your request.')
    else:
        longurl = response['api_response']['response']['long_url']
        jenni.say('http://dft.ba/' + url + ' redirects to ' + longurl)
expand.rule = '.*http://dft.ba/(\S+).*'
