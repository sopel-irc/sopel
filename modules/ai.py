#!/usr/bin/env python
"""
ai.py - Artificial Intelligence Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

import random, time

aistate = True
conversation = False
low = 0
high = 1
owner_gone = True

greeting = ['Hello', 'Hallo', 'Hi', 'Welcome']

## Functions that deal with the state of AI being on or off.

def off(phenny, input):
    if input.nick == phenny.config.owner:
        phenny.reply("Feature has been disabled.")
        global aistate
        aistate = False
    else:
        phenny.reply("You are not authorized to disabled this feature.")
off.commands = ['off'] 
off.priority = 'high'

def on(phenny, input):
    if input.nick == phenny.config.owner:
        phenny.reply("Feature has been enabled.")
        global aistate
        aistate = True
    else:
        phenny.reply("You are not authorized to enabled this feature.")
on.commands = ['on']
on.priority = 'high'

def state(phenny, input):
    global aistate
    if aistate == True:
        phenny.reply("It is on.")
    else:
        phenny.reply("It is off.")
state.commands = ['state']
state.priority = 'high'

## Functions that do not rely on "AISTATE"

def hello_join(phenny, input):
    well = random.random()
    if input.sender == "#osuoss":
        return
    else:
        if 0 < well < 0.02:
            if input.nick == "$nickname": 
                return
            random_greeting = random.choice(greeting)
            punctuation = random.choice(('!', ' '))
            phenny.say(random_greeting + ' ' + input.nick + punctuation)
hello_join.event = 'JOIN'
hello_join.rule = '(.*)'
hello_join.priority = 'medium'

def goodbye(phenny, input):
    byemsg = random.choice(('Bye', 'Goodbye', 'Seeya', 'Auf Wiedersehen', 'Au revoir', 'Ttyl'))
    punctuation = random.choice(('!', ' '))
    phenny.say(byemsg + ' ' + input.nick + punctuation)
goodbye.rule = r'(?i)$nickname\:\s+(bye|goodbye|seeya|cya|ttyl|g2g|gnight|goodnight)'
goodbye.thread = False

## Functions that do rely on "AISTATE"

def hau(phenny, input):
    global aistate
    global conversation
    if aistate == True:
        phenny.reply("How are you?")
        conversation = True
hau.rule = '(hey|hi|hello).*(phenny|$nickname).*$'

def hau2(phenny, input):
    hau(phenny,input)
hau2.rule = '(phenny|$nickname).*(hey|hi|hello).*$'

def gau(phenny, input):
    global aistate
    global conversation
    if aistate == True and conversation == True:
        randmsg = random.choice(["That's good to hear!", "That's great to hear!"])
        phenny.reply(randmsg)
        conversation = False
gau.rule = '.*([Gg]ood).*'

def bad(phenny, input):
    global aistate
    global conversation
    if aistate == True and conversation == True:
        randmsg = random.choice(["Sorry to hear about that."])
        phenny.reply(randmsg)
        conversation = False
bad.rule = '.*([bB]ad|[hH]orrible|[aA]wful|[Tt]errible).*$'

## ADDED Functions that do not rely on "AISTATE"

def ty(phenny, input):
    human = random.uniform(low,high)	
    time.sleep(human)
    mystr = input.group()
    mystr = str(mystr)
    if (mystr.find(" no ") == -1) and (mystr.find("no ") == -1) and (mystr.find(" no") == -1):	
        phenny.reply("You're welcome.")
ty.rule = '.*([tT]hank).*([yY]ou).*(phenny|$nickname).*$'
ty.priority = 'high'

def ty2(phenny, input):
    ty(phenny,input)
ty2.rule = '(?i)$nickname\:\s+([Tt]hank).*([Yy]ou).*'

def ty4(phenny, input):
    ty(phenny, input)
ty4.rule = '.*([Tt]hanks).*(phenny|$nickname).*'

def random_resp(phenny, input):
    # This randomly takes what someone says in the form of "phenny: <message>" and just spits it back out at the user that said it.
    human = random.random()
    if 0 <= human <= 0.025:
        strinput = input.group()
        nick = phenny.nick + ":"
        strinput = strinput.split(nick)
        phenny.reply(strinput[1][1:])
random_resp.rule = r'(?i)$nickname\:\s+(.*)'

def random_yesno(phenny, input):
    # phenny will randomly answer a yes/no answer
    human = random.random()
    wait = random.uniform(0,7)
    if 0 <= human <= .025:
        time.sleep(wait)
        choices = ["yes", "no"]
        response = random.choice(choices)
        phenny.reply(response)
random_yesno.rule = r'(?i)^(do|are|is|will|has)\b.*(\?)$'
random_yesno.priority = 'low'

def wat(phenny, input):
    phenny.say("we are team!")
wat.rule = r'(?i)(.*)\bwe\s+are\s+team\b(.*)'

def wat2(phenny,input):
    phenny.say("yes we are!")
wat2.rule = '(?i).*(we)\s(are)\s(not)\s(team).*'

def yesno(phenny,input):
    text = input.group()
    text = text.split(":")
    text = text[1].split()
    if text[0] == 'yes':
        phenny.reply("no")
    elif text[0] == 'no':
        phenny.reply("yes")
yesno.rule = '(phenny|$nickname)\:\s+(yes|no)$'

def rand_whoa (phenny,input):
    text = input.group()
    rand = random.random()
    if 0 < rand < 0.004:
        phenny.say('whoa!')
rand_whoa.rule = '.*'
rand_whoa.priority = 'low'

if __name__ == '__main__': 
    print __doc__.strip()
