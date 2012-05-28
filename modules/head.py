#!/usr/bin/env python
"""
head.py - Jenni HTTP Metadata Utilities
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import httplib, time
from htmlentitydefs import name2codepoint
import web


def head(jenni, input):
    """Provide HTTP HEAD information."""
    uri = input.group(2)
    uri = (uri or '').encode('utf-8')
    if ' ' in uri:
        uri, header = uri.rsplit(' ', 1)
    else: uri, header = uri, None

    if not uri and hasattr(jenni, 'last_seen_uri'):
        try: uri = jenni.last_seen_uri[input.sender]
        except KeyError: return jenni.say('?')

    if not uri.startswith('htt'):
        uri = 'http://' + uri
    # uri = uri.replace('#!', '?_escaped_fragment_=')

    try: info = web.head(uri)
    except IOError: return jenni.say("Can't connect to %s" % uri)
    except httplib.InvalidURL: return jenni.say("Not a valid URI, sorry.")

    if not isinstance(info, list):
        try: info = dict(info)
        except TypeError:
            return jenni.reply('Try .head http://example.org/ [optional header]')
        info['Status'] = '200'
    else:
        newInfo = dict(info[0])
        newInfo['Status'] = str(info[1])
        info = newInfo

    if header is None:
        data = []
        if info.has_key('Status'):
            data.append(info['Status'])
        if info.has_key('content-type'):
            data.append(info['content-type'].replace('; charset=', ', '))
        if info.has_key('last-modified'):
            modified = info['last-modified']
            modified = time.strptime(modified, '%a, %d %b %Y %H:%M:%S %Z')
            data.append(time.strftime('%Y-%m-%d %H:%M:%S UTC', modified))
        if info.has_key('content-length'):
            data.append(info['content-length'] + ' bytes')
        jenni.reply(', '.join(data))
    else:
        headerlower = header.lower()
        if info.has_key(headerlower):
            jenni.say(header + ': ' + info.get(headerlower))
        else:
            msg = 'There was no %s header in the response.' % header
            jenni.say(msg)
head.commands = ['head']
head.example = '.head http://www.w3.org/'

if __name__ == '__main__':
    print __doc__.strip()
