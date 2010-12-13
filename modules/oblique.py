#!/usr/bin/env python
"""
oblique.py - Web Services Interface
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web

definitions = 'https://github.com/nslater/oblique/wiki'

r_item = re.compile(r'(?i)<li>(.*?)</li>')
r_tag = re.compile(r'<[^>]+>')

def mappings(uri): 
    result = {}
    bytes = web.get(uri)
    for item in r_item.findall(bytes): 
        item = r_tag.sub('', item).strip(' \t\r\n')
        if not ' ' in item: continue

        command, template = item.split(' ', 1)
        if not command.isalnum(): continue
        if not template.startswith('http://'): continue
        result[command] = template.replace('&amp;', '&')
    return result

def service(jenni, input, command, args): 
    t = o.services[command]
    template = t.replace('${args}', urllib.quote(args.encode('utf-8')))
    template = template.replace('${nick}', urllib.quote(input.nick))
    uri = template.replace('${sender}', urllib.quote(input.sender))

    bytes = web.get(uri)
    lines = bytes.splitlines()
    if not lines: 
        return jenni.reply('Sorry, the service is broken.')
    jenni.say(lines[0][:350])

def refresh(jenni): 
    if hasattr(jenni.config, 'services'): 
        services = jenni.config.services
    else: services = definitions

    old = o.services
    o.serviceURI = services
    o.services = mappings(o.serviceURI)
    return len(o.services), set(o.services) - set(old)

def o(jenni, input): 
    """Call a webservice."""
    text = input.group(2)

    if (not o.services) or (text == 'refresh'): 
        length, added = refresh(jenni)
        if text == 'refresh': 
            msg = 'Okay, found %s services.' % length
            if added: 
                msg += ' Added: ' + ', '.join(sorted(added)[:5])
                if len(added) > 5: msg += ', &c.'
            return jenni.reply(msg)

    if not text: 
        return jenni.reply('Try %s for details.' % o.serviceURI)

    if ' ' in text: 
        command, args = text.split(' ', 1)
    else: command, args = text, ''
    command = command.lower()

    if command == 'service': 
        msg = o.services.get(args, 'No such service!')
        return jenni.reply(msg)

    if not o.services.has_key(command): 
        return jenni.reply('Sorry, no such service. See %s' % o.serviceURI)

    if hasattr(jenni.config, 'external'): 
        default = jenni.config.external.get('*')
        manifest = jenni.config.external.get(input.sender, default)
        if manifest: 
            commands = set(manifest)
            if (command not in commands) and (manifest[0] != '!'): 
                return jenni.reply('Sorry, %s is not whitelisted' % command)
            elif (command in commands) and (manifest[0] == '!'): 
                return jenni.reply('Sorry, %s is blacklisted' % command)
    service(jenni, input, command, args)
o.commands = ['o']
o.example = '.o servicename arg1 arg2 arg3'
o.services = {}
o.serviceURI = None

def snippet(jenni, input): 
    if not o.services: 
        refresh(jenni)

    search = urllib.quote(input.group(2).encode('utf-8'))
    py = "BeautifulSoup.BeautifulSoup(re.sub('<.*?>|(?<= ) +', '', " + \
          "''.join(chr(ord(c)) for c in " + \
          "eval(urllib.urlopen('http://ajax.googleapis.com/ajax/serv" + \
          "ices/search/web?v=1.0&q=" + search + "').read()" + \
          ".replace('null', 'None'))['responseData']['resul" + \
          "ts'][0]['content'].decode('unicode-escape')).replace(" + \
          "'&quot;', '\x22')), convertEntities=True)"
    service(jenni, input, 'py', py)
snippet.commands = ['snippet']

if __name__ == '__main__': 
    print __doc__.strip()

