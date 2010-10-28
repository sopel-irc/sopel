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
greet_user = ""

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
    if 0 < well < 0.02:
        if input.nick == phenny.config.nick: 
            return
        random_greeting = random.choice(greeting)
        punctuation = random.choice(('!', ' '))
        phenny.say(random_greeting + ' ' + input.nick + punctuation)
hello_join.event = 'JOIN'
hello_join.rule = '.*'
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
    global greet_user
    greet_user = input.nick
    if aistate == True and greet_user == input.nick:
        time.sleep(random.randint(0,1))
        phenny.reply("How are you?")
        conversation = True
hau.rule = r'(?i)(hey|hi|hello)\b.*(phenny|$nickname)\b.*$'

def hau2(phenny, input):
    hau(phenny,input)
hau2.rule = r'(?i)(phenny|$nickname)\b.*(hey|hi|hello)\b.*$'

def gau(phenny, input):
    global aistate
    global conversation
    global greet_user
    if aistate == True and conversation == True and greet_user == input.nick:
        randmsg = random.choice(["That's good to hear!", "That's great to hear!"])
        time.sleep(random.randint(0,1))
        phenny.reply(randmsg)
        conversation = False
#gau.rule = '(?i).*(good).*'

def bad(phenny, input):
    global aistate
    global conversation
    global greet_user
    if input.sender == "#pyohio":
        return
    if aistate == True and conversation == True and greet_user == input.nick:
        randmsg = random.choice(["Sorry to hear about that."])
        time.sleep(random.randint(0,1))
        phenny.reply(randmsg)
        conversation = False
bad.rule = '(?i).*(bad|horrible|awful|terrible).*$'

## ADDED Functions that do not rely on "AISTATE"

def ty(phenny, input):
    human = random.uniform(0,9)
    time.sleep(human)
    mystr = input.group()
    mystr = str(mystr)
    if (mystr.find(" no ") == -1) and (mystr.find("no ") == -1) and (mystr.find(" no") == -1):	
        phenny.reply("You're welcome.")
ty.rule = '(?i).*(thank).*(you).*(phenny|$nickname).*$'
ty.priority = 'high'

def ty2(phenny, input):
    ty(phenny,input)
ty2.rule = '(?i)$nickname\:\s+(thank).*(you).*'

def ty4(phenny, input):
    ty(phenny, input)
ty4.rule = '(?i).*(thanks).*(phenny|$nickname).*'

def random_resp(phenny, input):
    # This randomly takes what someone says in the form of "phenny: <message>" and just spits it back out at the user that said it.
    human = random.random()
    if 0 <= human <= 0.025:
        strinput = input.group()
        nick = phenny.nick + ":"
        strinput = strinput.split(nick)
        phenny.reply(strinput[1][1:])
random_resp.rule = r'(?i)$nickname\:\s+(.*)'

def wat(phenny, input):
    phenny.say("we are team!")
wat.rule = r'(?i)(.*)\bwe\s+are\s+team\b(.*)'

def wat2(phenny,input):
    phenny.say("yes we are!")
wat2.rule = '(?i).*(we)\s(are)\s(not)\s(team).*'

def yesno(phenny,input):
    rand = random.uniform(0,5)
    text = input.group()
    text = text.split(":")
    text = text[1].split()
    time.sleep(rand)
    if text[0] == 'yes':
        phenny.reply("no")
    elif text[0] == 'no':
        phenny.reply("yes")
yesno.rule = '(phenny|$nickname)\:\s+(yes|no)$'

def ping_reply (phenny,input):
    text = input.group().split(": ")
    if text[1] == 'PING' or text[1] == 'ping':
        phenny.reply("PONG")
ping_reply.rule = '(?i)($nickname|phenny)\:.*'

def love (phenny, input):
    phenny.reply("I love you too.")
love.rule = '(?i)i.*love.*(phenny|$nickname).*'

def love2 (phenny, input):
    phenny.reply("I love you too.")
love2.rule = '(?i)(phenny|$nickname)\:\si.*love.*'

def love3 (phenny, input):
    phenny.reply("I love you too.")
love3.rule = '(?i)(phenny|$nickname)\,\si.*love.*'

if __name__ == '__main__': 
    print __doc__.strip()
