"""
ai.py - Artificial Intelligence Module
Copyright 2009-2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import random, time

random.seed()
limit = 3

def goodbye(willie, trigger):
    byemsg = random.choice(('Bye', 'Goodbye', 'Seeya', 'Auf Wiedersehen', 'Au revoir', 'Ttyl'))
    punctuation = random.choice(('!', ' '))
    willie.say(byemsg + ' ' + trigger.nick + punctuation)
goodbye.rule = r'(?i)$nickname\:\s+(bye|goodbye|seeya|cya|ttyl|g2g|gnight|goodnight)'
goodbye.thread = False
goodbye.rate = 30


def ty(willie, trigger):
    human = random.uniform(0,9)
    time.sleep(human)
    mystr = trigger.group()
    mystr = str(mystr)
    if (mystr.find(" no ") == -1) and (mystr.find("no ") == -1) and (mystr.find(" no") == -1):
        willie.reply("You're welcome.")
ty.rule = '(?i).*(thank).*(you).*(willie|$nickname).*$'
ty.priority = 'high'
ty.rate = 30

def ty2(willie, trigger):
    ty(willie,trigger)
ty2.rule = '(?i)$nickname\:\s+(thank).*(you).*'
ty2.rate = 30

def ty4(willie, trigger):
    ty(willie, trigger)
ty4.rule = '(?i).*(thanks).*(willie|$nickname).*'
ty4.rate = 40

def yesno(willie,trigger):
    rand = random.uniform(0,5)
    text = trigger.group()
    text = text.split(":")
    text = text[1].split()
    time.sleep(rand)
    if text[0] == 'yes':
        willie.reply("no")
    elif text[0] == 'no':
        willie.reply("yes")
yesno.rule = '(willie|$nickname)\:\s+(yes|no)$'
yesno.rate = 15

def ping_reply (willie,trigger):
    text = trigger.group().split(":")
    text = text[1].split()
    if text[0] == 'PING' or text[0] == 'ping':
        willie.reply("PONG")
ping_reply.rule = '(?i)($nickname|willie)\:\s+(ping)\s*'
ping_reply.rate = 30

def love (willie, trigger):
    willie.reply("I love you too.")
love.rule = '(?i)i.*love.*(willie|$nickname).*'
love.rate = 30

def love2 (willie, trigger):
    willie.reply("I love you too.")
love2.rule = '(?i)(willie|$nickname)\:\si.*love.*'
love2.rate = 30

def love3 (willie, trigger):
    willie.reply("I love you too.")
love3.rule = '(?i)(willie|$nickname)\,\si.*love.*'
love3.rate = 30

def f_lol(willie, trigger):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['haha', 'lol', 'rofl']
        randtime = random.uniform(0,9)
        time.sleep(randtime)
        willie.say(random.choice(respond))
f_lol.rule = '(haha!?|lol!?)$'
f_lol.priority = 'high'

def f_bye(willie, trigger):
    respond = ['bye!', 'bye', 'see ya', 'see ya!']
    willie.say(random.choice(respond))
f_bye.rule = '(g2g!?|bye!?)$'
f_bye.priority = 'high'

def f_heh(willie, trigger):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['hm']
        randtime = random.uniform(0,7)
        time.sleep(randtime)
        willie.say(random.choice(respond))
f_heh.rule = '(heh!?)$'
f_heh.priority = 'high'

def f_really(willie, trigger):
    randtime = random.uniform(10,45)
    time.sleep(randtime)
    willie.say(str(trigger.nick) + ": " + "Yes, really.")
f_really.rule = r'(?i)$nickname\:\s+(really!?)'
f_really.priority = 'high'

def wb(willie, trigger):
    willie.reply("Thank you!")
wb.rule = '^(wb|welcome\sback).*$nickname\s'

if __name__ == '__main__':
    print __doc__.strip()

if __name__ == '__main__':
    print __doc__.strip()
