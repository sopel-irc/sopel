"""
oblique.py - Web Services Interface
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import re, urllib
import willie.web as web

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

def service(willie, trigger, command, args):
    t = o.services[command]
    template = t.replace('${args}', urllib.quote(args.encode('utf-8'), ''))
    template = template.replace('${nick}', urllib.quote(trigger.nick, ''))
    uri = template.replace('${sender}', urllib.quote(trigger.sender, ''))

    info = web.head(uri)
    if isinstance(info, list):
        info = info[0]
    if not 'text/plain' in info.get('content-type', '').lower():
        return willie.reply("Sorry, the service didn't respond in plain text.")
    bytes = web.get(uri)
    lines = bytes.splitlines()
    if not lines:
        return willie.reply("Sorry, the service didn't respond any output.")
    willie.say(lines[0][:350])

def refresh(willie):
    if hasattr(willie.config, 'services'):
        services = willie.config.services
    else: services = definitions

    old = o.services
    o.serviceURI = services
    o.services = mappings(o.serviceURI)
    return len(o.services), set(o.services) - set(old)

def o(willie, trigger):
    """Call a webservice."""
    if trigger.group(1) == 'urban':
        text = 'ud '+ trigger.group(2)
    else:
        text = trigger.group(2)

    if (not o.services) or (text == 'refresh'):
        length, added = refresh(willie)
        if text == 'refresh':
            msg = 'Okay, found %s services.' % length
            if added:
                msg += ' Added: ' + ', '.join(sorted(added)[:5])
                if len(added) > 5: msg += ', &c.'
            return willie.reply(msg)

    if not text:
        return willie.reply('Try %s for details.' % o.serviceURI)

    if ' ' in text:
        command, args = text.split(' ', 1)
    else: command, args = text, ''
    command = command.lower()

    if command == 'service':
        msg = o.services.get(args, 'No such service!')
        return willie.reply(msg)

    if not o.services.has_key(command):
        return willie.reply('Service not found in %s' % o.serviceURI)

    if hasattr(willie.config, 'external'):
        default = willie.config.external.get('*')
        manifest = willie.config.external.get(trigger.sender, default)
        if manifest:
            commands = set(manifest)
            if (command not in commands) and (manifest[0] != '!'):
                return willie.reply('Sorry, %s is not whitelisted' % command)
            elif (command in commands) and (manifest[0] == '!'):
                return willie.reply('Sorry, %s is blacklisted' % command)
    service(willie, trigger, command, args)
o.commands = ['o','urban']
o.example = '.o servicename arg1 arg2 arg3'
o.services = {}
o.serviceURI = None

def snippet(willie, trigger):
    if not o.services:
        refresh(willie)

    search = urllib.quote(trigger.group(2).encode('utf-8'))
    py = "BeautifulSoup.BeautifulSoup(re.sub('<.*?>|(?<= ) +', '', " + \
          "''.join(chr(ord(c)) for c in " + \
          "eval(urllib.urlopen('http://ajax.googleapis.com/ajax/serv" + \
          "ices/search/web?v=1.0&q=" + search + "').read()" + \
          ".replace('null', 'None'))['responseData']['resul" + \
          "ts'][0]['content'].decode('unicode-escape')).replace(" + \
          "'&quot;', '\x22')), convertEntities=True)"
    service(willie, trigger, 'py', py)
snippet.commands = ['snippet']

if __name__ == '__main__':
    print __doc__.strip()
