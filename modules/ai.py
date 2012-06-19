#!/usr/bin/env python
"""
ai.py - Artificial Intelligence Module
Copyright 2010-2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import random, time

aistate = True
conversation = False
low = 0
high = 1
owner_gone = True
greet_user = ""

greeting = ['Hello', 'Hallo', 'Hi', 'Welcome']

random.seed()

## Functions that deal with the state of AI being on or off.

def off(jenni, input):
    if input.nick == jenni.config.owner:
        jenni.reply("Feature has been disabled.")
        global aistate
        aistate = False
    else:
        jenni.reply("You are not authorized to disable this feature.")
off.commands = ['off']
off.priority = 'high'

def on(jenni, input):
    if input.nick == jenni.config.owner:
        jenni.reply("Feature has been enabled.")
        global aistate
        aistate = True
    else:
        jenni.reply("You are not authorized to enable this feature.")
on.commands = ['on']
on.priority = 'high'

def state(jenni, input):
    global aistate
    if aistate == True:
        jenni.reply("It is on.")
    else:
        jenni.reply("It is off.")
state.commands = ['state']
state.priority = 'high'

## Functions that do not rely on "AISTATE"

def hello_join(jenni, input):
    well = random.random()
    if 0 < well < 0.01:
        if input.nick == jenni.config.nick:
            return
        random_greeting = random.choice(greeting)
        punctuation = random.choice(('!', ' '))
        jenni.say(random_greeting + ' ' + input.nick + punctuation)
#hello_join.event = 'JOIN'
#hello_join.rule = '.*'
#hello_join.priority = 'medium'

def goodbye(jenni, input):
    byemsg = random.choice(('Bye', 'Goodbye', 'Seeya', 'Auf Wiedersehen', 'Au revoir', 'Ttyl'))
    punctuation = random.choice(('!', ' '))
    jenni.say(byemsg + ' ' + input.nick + punctuation)
goodbye.rule = r'(?i)$nickname\:\s+(bye|goodbye|seeya|cya|ttyl|g2g|gnight|goodnight)'
goodbye.thread = False
goodbye.rate = 30

## Functions that do rely on "AISTATE"

def hau(jenni, input):
    global aistate
    global conversation
    global greet_user
    greet_user = input.nick
    if aistate == True and greet_user == input.nick:
        time.sleep(random.randint(0,1))
        jenni.reply("How are you?")
        conversation = True
hau.rule = r'(?i)(hey|hi|hello)\b.*(jenni|$nickname)\b.*$'

def hau2(jenni, input):
    hau(jenni,input)
hau2.rule = r'(?i)(jenni|$nickname)\b.*(hey|hi|hello)\b.*$'

def gau(jenni, input):
    global aistate
    global conversation
    global greet_user
    if aistate == True and conversation == True and greet_user == input.nick:
        randmsg = random.choice(["That's good to hear!", "That's great to hear!"])
        time.sleep(random.randint(0,1))
        jenni.reply(randmsg)
        conversation = False
#gau.rule = '(?i).*(good).*'

def bad(jenni, input):
    global aistate
    global conversation
    global greet_user
    if input.sender == "#pyohio":
        return
    if aistate == True and conversation == True and greet_user == input.nick:
        randmsg = random.choice(["Sorry to hear about that."])
        time.sleep(random.randint(0,1))
        jenni.reply(randmsg)
        conversation = False
bad.rule = '(?i).*(bad|horrible|awful|terrible).*$'

## ADDED Functions that do not rely on "AISTATE"

def ty(jenni, input):
    human = random.uniform(0,9)
    time.sleep(human)
    mystr = input.group()
    mystr = str(mystr)
    if (mystr.find(" no ") == -1) and (mystr.find("no ") == -1) and (mystr.find(" no") == -1):
        jenni.reply("You're welcome.")
ty.rule = '(?i).*(thank).*(you).*(jenni|$nickname).*$'
ty.priority = 'high'
ty.rate = 30

def ty2(jenni, input):
    ty(jenni,input)
ty2.rule = '(?i)$nickname\:\s+(thank).*(you).*'
ty2.rate = 30

def ty4(jenni, input):
    ty(jenni, input)
ty4.rule = '(?i).*(thanks).*(jenni|$nickname).*'
ty4.rate = 40

def random_resp(jenni, input):
    # This randomly takes what someone says in the form of "jenni: <message>" and just spits it back out at the user that said it.
    human = random.random()
    if 0 <= human <= 0.025:
        strinput = input.group()
        nick = jenni.nick + ":"
        strinput = strinput.split(nick)
        jenni.reply(strinput[1][1:])
random_resp.rule = r'(?i)$nickname\:\s+(.*)'

def yesno(jenni,input):
    rand = random.uniform(0,5)
    text = input.group()
    text = text.split(":")
    text = text[1].split()
    time.sleep(rand)
    if text[0] == 'yes':
        jenni.reply("no")
    elif text[0] == 'no':
        jenni.reply("yes")
yesno.rule = '(jenni|$nickname)\:\s+(yes|no)$'
yesno.rate = 15

def ping_reply (jenni,input):
    text = input.group().split(":")
    text = text[1].split()
    if text[0] == 'PING' or text[0] == 'ping':
        jenni.reply("PONG")
ping_reply.rule = '(?i)($nickname|jenni)\:\s+(ping)\s*'
ping_reply.rate = 30

def love (jenni, input):
    jenni.reply("I love you too.")
love.rule = '(?i)i.*love.*(jenni|$nickname).*'
love.rate = 30

def love2 (jenni, input):
    jenni.reply("I love you too.")
love2.rule = '(?i)(jenni|$nickname)\:\si.*love.*'
love2.rate = 30

def love3 (jenni, input):
    jenni.reply("I love you too.")
love3.rule = '(?i)(jenni|$nickname)\,\si.*love.*'
love3.rate = 30

if __name__ == '__main__':
    print __doc__.strip()
