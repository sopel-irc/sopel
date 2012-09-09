#!/usr/bin/env python
"""
admin.py - Willie Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich (yanovich.net)
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

import os

def join(willie, trigger):
   """Join the specified channel. This is an admin-only command."""
   # Can only be done in privmsg by an admin
   if trigger.sender.startswith('#'): return
   if trigger.admin:
      channel, key = trigger.group(1), trigger.group(2)
      if not key:
         willie.write(['JOIN'], channel)
      else: willie.write(['JOIN', channel, key])
join.rule = r'\.join (#\S+)(?: *(\S+))?'
join.priority = 'low'
join.example = '.join #example or .join #example key'

def part(phenny, trigger): 
    """Part the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'): return
    if trigger.admin: 
        phenny.write(['PART'], trigger.group(2))
part.commands = ['part']
part.priority = 'low'
part.example = '.part #example'

def quit(phenny, trigger): 
    """Quit from the server. This is an owner-only command."""
    # Can only be done in privmsg by the owner
    if trigger.sender.startswith('#'): return
    if trigger.owner: 
        phenny.write(['QUIT'])
        __import__('os')._exit(0)
quit.commands = ['quit']
quit.priority = 'low'

def msg(phenny, trigger): 
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'): return
    a, b = trigger.group(2), trigger.group(3)
    if (not a) or (not b): return
    if trigger.admin: 
        phenny.msg(a, b)
msg.rule = (['msg'], r'(#?\S+) (.+)')
msg.priority = 'low'

def me(phenny, trigger): 
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'): return
    if trigger.admin: 
        msg = '\x01ACTION %s\x01' % trigger.group(3)
        phenny.msg(trigger.group(2), msg)
me.rule = (['me'], r'(#?\S+) (.*)')
me.priority = 'low'

def defend_ground(willie, trigger):
    """
    This function monitors all kicks across all channels willie is in. If she
    detects that she is the one kicked she'll automatically join that channel.

    WARNING: This may not be needed and could cause problems if willie becomes
    annoying. Please use this with caution.
    """
    channel = trigger.sender
    willie.write(['JOIN'], channel)
defend_ground.event = 'KICK'
defend_ground.rule = '.*'
defend_ground.priority = 'low'

def mode(willie, trigger):
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'): return
    if trigger.admin:
        mode = trigger.group(1)
        willie.write(('MODE ', willie.nick + ' ' + mode))
mode.rule = r'\.mode ([\+-]\S+)'
mode.priority = 'low'

def raw(phenny, trigger):
    # Can only be done in privmsg by owner
    if trigger.sender.startswith('#'): return
    if trigger.owner:
        phenny.write((trigger.group(1), trigger.group(2)))
raw.rule = '.raw (\S+) (.*)'


def blocks(willie, trigger):
    if not trigger.admin: return

    STRINGS = {
            "success_del" : "Successfully deleted block: %s",
            "success_add" : "Successfully added block: %s",
            "no_nick" : "No matching nick block found for: %s",
            "no_host" : "No matching hostmask block found for: %s",
            "invalid" : "Invalid format for %s a block. Try: .blocks add (nick|hostmask) willie",
            "invalid_display" : "Invalid input for displaying blocks.",
            "nonelisted" : "No %s listed in the blocklist.",
            'huh' : "I could not figure out what you wanted to do.",
            }

    if not os.path.isfile("blocks"):
        blocks = open("blocks", "w")
        blocks.write('\n')
        blocks.close()

    blocks = open("blocks", "r")
    contents = blocks.readlines()
    blocks.close()

    try: masks = contents[0].replace("\n", "").split(',')
    except: masks = ['']

    try: nicks = contents[1].replace("\n", "").split(',')
    except: nicks = ['']

    text = trigger.group().split()

    if len(text) == 3 and text[1] == "list":
        if text[2] == "hostmask":
            if len(masks) > 0 and masks.count("") == 0:
                for each in masks:
                    if len(each) > 0:
                        willie.say("blocked hostmask: " + each)
            else:
                willie.reply(STRINGS['nonelisted'] % ('hostmasks'))
        elif text[2] == "nick":
            if len(nicks) > 0 and nicks.count("") == 0:
                for each in nicks:
                    if len(each) > 0:
                        willie.say("blocked nick: " + each)
            else:
                willie.reply(STRINGS['nonelisted'] % ('nicks'))
        else:
            willie.reply(STRINGS['invalid_display'])

    elif len(text) == 4 and text[1] == "add":
        if text[2] == "nick":
            nicks.append(text[3])
        elif text[2] == "hostmask":
            masks.append(text[3].lower())
        else:
            willie.reply(STRINGS['invalid'] % ("adding"))
            return

        willie.reply(STRINGS['success_add'] % (text[3]))

    elif len(text) == 4 and text[1] == "del":
        if text[2] == "nick":
            try:
                nicks.remove(text[3])
                willie.reply(STRINGS['success_del'] % (text[3]))
            except:
                willie.reply(STRINGS['no_nick'] % (text[3]))
                return
        elif text[2] == "hostmask":
            try:
                masks.remove(text[3].lower())
                willie.reply(STRINGS['success_del'] % (text[3]))
            except:
                willie.reply(STRINGS['no_host'] % (text[3]))
                return
        else:
            willie.reply(STRINGS['invalid'] % ("deleting"))
            return
    else:
        willie.reply(STRINGS['huh'])

    os.remove("blocks")
    blocks = open("blocks", "w")
    masks_str = ",".join(masks)
    if len(masks_str) > 0 and "," == masks_str[0]:
        masks_str = masks_str[1:]
    blocks.write(masks_str)
    blocks.write("\n")
    nicks_str = ",".join(nicks)
    if len(nicks_str) > 0 and "," == nicks_str[0]:
        nicks_str = nicks_str[1:]
    blocks.write(nicks_str)
    blocks.close()

blocks.commands = ['blocks']
blocks.priority = 'low'
blocks.thread = False

if __name__ == '__main__':
   print __doc__.strip()

