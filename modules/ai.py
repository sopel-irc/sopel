#!/usr/bin/env python
"""
ai.py - Artificial Intelligence Module
Copyright 2009-2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import random, time

aistate = False
conversation = False
low = 0
high = 1
owner_gone = True
greet_user = ""

greeting = ['Hello', 'Hallo', 'Hi', 'Welcome']

random.seed()

def goodbye(jenni, input):
    byemsg = random.choice(('Bye', 'Goodbye', 'Seeya', 'Auf Wiedersehen', 'Au revoir', 'Ttyl'))
    punctuation = random.choice(('!', ' '))
    jenni.say(byemsg + ' ' + input.nick + punctuation)
goodbye.rule = r'(?i)$nickname\:\s+(bye|goodbye|seeya|cya|ttyl|g2g|gnight|goodnight)'
goodbye.thread = False
goodbye.rate = 30


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

def f_lol(jenni, input):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['haha', 'lol', 'rofl']
        randtime = random.uniform(0,9)
        time.sleep(randtime)
        jenni.say(random.choice(respond))
f_lol.rule = '(haha!?|lol!?)$'
f_lol.priority = 'high'

def f_bye(jenni, input):
    respond = ['bye!', 'bye', 'see ya', 'see ya!']
    jenni.say(random.choice(respond))
f_bye.rule = '(g2g!?|bye!?)$'
f_bye.priority = 'high'

def f_heh(jenni, input):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['hm']
        randtime = random.uniform(0,7)
        time.sleep(randtime)
        jenni.say(random.choice(respond))
f_heh.rule = '(heh!?)$'
f_heh.priority = 'high'

def f_really(jenni, input):
    randtime = random.uniform(10,45)
    time.sleep(randtime)
    jenni.say(str(input.nick) + ": " + "Yes, really.")
f_really.rule = r'(?i)$nickname\:\s+(really!?)'
f_really.priority = 'high'

def wb(jenni, input):
    jenni.reply("Thank you!")
wb.rule = '^(wb|welcome\sback).*$nickname\s'

if __name__ == '__main__':
    print __doc__.strip()

if __name__ == '__main__':
    print __doc__.strip()
