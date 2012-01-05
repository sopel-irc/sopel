"""
whois.py - Retrieve WHOIS information on a user and show to the channel.
Author: Edward D. Powell http://embolalia.net
Phenny (About): http://inamidst.com/phenny/
"""
from time import sleep
import re
whois = False
got318 = False
nick = None
host = None
rl = None
chans = None
idle = None
signon = None

def sendwhois(phenny, input):
    global whois, got318, nick, host, rl, chans, idle, signon
    whois = True
    phenny.write(['WHOIS'], input.group(2))

    while not got318:
        sleep(0.5)

    #at this point, the variables are:
    #got318 = true
    #nick = None
    #host = None
    #rl = None
    #chans = unicode string of the channels the target is on.

    msg1 = '[WHOIS] Nick: ' + str(nick) + ' Host: ' + str(host) + \
           ' Real name: ' + str(rl)
    msg2 = str(nick) + ' is on the channels: ' + chans.encode('utf-8')
    phenny.say(msg1)
    phenny.say(msg2)
    #phenny.say(nick + ' has been idle ' + idle + ', signed on ' + signon)
    whois = False
    got318 = False
    nick = None
    host = None
    rl = None
    chans = None
    idle = None
    signon = None
sendwhois.commands = ['whois']

def whois311(phenny, input):
    global nick, host, rl, whois
    if whois:
        self.msg("#Embo", "[DEBUGMSG]"+phenny.raw) #What exactly are we trying to regex here?
        raw = re.match('\S+ 311 \S+ (\S+) (\S+) (\S+) (\S+) :(\S+)', \
                        phenny.raw)
        nick = raw.group(1)
        host = raw.group(2) + '@' + raw.group(3)
        rl = raw.group(5)
whois311.event = '311'
whois311.rule = '.*'

def whois319(phenny, input):
    print input.bytes
    print input.match
    print input.event
    print input.args
    print input
    if whois:
        global chans
        chans = input.group(1)
whois319.event = '319'
whois319.rule = '(.*)'

"""
#Not sure what's going on with this...
def whois317(phenny, input):
    global idle, signon
    if whois:
        raw = re.match('\S 317 (\S+) (\S+) (\d+) (\d+) (.*)', phenny.raw)
        idle = raw.groups(3)
        signon = raw.groups(4)
whois317.event = '317'
whois317.rule = '.*'
"""

def whois318(phenny, input):
    if whois:
        global got318
        got318 = True
whois318.event = '318'
whois318.rule = '.*'
