import random

def gen(n):
    beeps=""
    for i in range(random.randint(1,n)):
        if random.randint(0,1)==1:
            beeps+="beep "
        else:
            beeps+="boop "
    return beeps

def bb(phenny, input):
    k = random.randint(1,5)
    phenny.say(str(gen(k)))
    
bb.rule = r'.*(beep|boop)\b.*'

#def b2(phenny, input):
#    bb(phenny,input)
#b2.rule = r'.*boop.*'

def b3(phenny,input):
    bb(phenny,input)
b3.rule = r'.*digmbot\b.*'
