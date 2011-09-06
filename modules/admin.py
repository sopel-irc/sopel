#!/usr/bin/env python
"""
admin.py - Jenni Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich (yanovich.net)
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

def join(jenni, input):
   """Join the specified channel. This is an admin-only command."""
   # Can only be done in privmsg by an admin
   if input.sender.startswith('#'): return
   if input.admin:
      channel, key = input.group(1), input.group(2)
      if not key:
         jenni.write(['JOIN'], channel)
      else: jenni.write(['JOIN', channel, key])
join.rule = r'\.join (#\S+)(?: *(\S+))?'
join.priority = 'low'
join.example = '.join #example or .join #example key'

def part(jenni, input):
   """Part the specified channel. This is an admin-only command."""
   # Can only be done in privmsg by an admin
   if input.sender.startswith('#'): return
   if input.admin:
      jenni.write(['PART'], input.group(2))
part.commands = ['part']
part.priority = 'low'
part.example = '.part #example'

def quit(jenni, input):
   """Quit from the server. This is an owner-only command."""
   # Can only be done in privmsg by the owner
   if input.sender.startswith('#'): return
   if input.owner:
      jenni.write(['QUIT'])
      __import__('os')._exit(0)
quit.commands = ['quit']
quit.priority = 'low'

def msg(jenni, input):
   # Can only be done in privmsg by an admin
   if input.sender.startswith('#'): return
   a, b = input.group(2), input.group(3)
   if (not a) or (not b): return
   if input.admin:
      jenni.msg(a, b)
msg.rule = (['msg'], r'(#?\S+) (.+)')
msg.priority = 'low'

def me(jenni, input):
   # Can only be done in privmsg by an admin
   if input.sender.startswith('#'): return
   if input.admin:
      msg = '\x01ACTION %s\x01' % input.group(3)
      jenni.msg(input.group(2), msg)
me.rule = (['me'], r'(#?\S+) (.*)')
me.priority = 'low'

def defend_ground (jenni, input):
    """
    This function monitors all kicks across all channels jenni is in. If she
    detects that she is the one kicked she'll automatically join that channel.

    WARNING: This may not needed and could cause problems if jenni becomes
    annoying. Please use this with caution.
    """
    channel = input.sender
    jenni.write(['JOIN'], channel)
defend_ground.event = 'KICK'
defend_ground.rule = '.*'
defend_ground.priority = 'low'

if __name__ == '__main__':
   print __doc__.strip()

