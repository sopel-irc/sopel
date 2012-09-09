"""
dftba.py - Willie DFT.BA Module
Author: Edward Powell, embolalia.net

http://willie.dftba.net

This module allows for retrieving stats, shortening and lengthening dft.ba urls.
"""
import urllib
import json

def shorten(willie, trigger):
    """Shorten a URL with DFT.BA"""
    return willie.say("The dft.ba API is no longer available. Can not shorten URL.")
    args = trigger.groups()
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
    willie.say(msg)
shorten.rule = '\.shorten (\S+)( ?\S+)?'
shorten.priority = 'high'
shorten.example = '.shorten http://example.com example'


def expand(willie, trigger):
    url = trigger.group(1)
    params = urllib.urlencode({'SHORT_URL': url})
    r = urllib.urlopen('http://dft.ba/api/expand.json', params)
    response = json.loads(r.read())
    if response['api_response']['response']['status'] == 'error':
        willie.say('Uh oh. Something went wrong with your request.')
    else:
        longurl = response['api_response']['response']['long_url']
        willie.say('http://dft.ba/' + url + ' redirects to ' + longurl)
#expand.rule = '.*http://dft.ba/(\S+).*'
