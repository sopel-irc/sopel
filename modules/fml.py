#!/usr/bin/env python
"""
fml.py - Jenni FMyLife Module
Copyright 2012, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module will reply to the .fml command, spitting out a random http://www.fmylife.com/ quote.
"""

import re, urllib2

def fml(jenni, input):
    return; //ugly hack
    #Grab info from rscript (code re-used from ytinfo)
    uri = 'http://rscript.org/lookup.php?type=fml'
    while True:
        req = urllib2.Request(uri, headers={'Accept':'text/html', 'User-Agent':'OpenAnything/1.0 +http://diveintopython.org/'})
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

    #Parse rscript info.
    rquote = re.search('(TEXT: )(.*)( FML)', bytes)
    quote = rquote.group(2)
    message = '\x02[\x02FML\x02]\x02 '+quote
    jenni.say(message)
fml.commands = ['fml']

if __name__ == '__main__':
    print __doc__.strip()