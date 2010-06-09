#!/usr/bin/env python

# roulette.py - a russian roulette for phenny

import random

deaths = ("drops dead.", "looks startled.", "blasts the brains onto the wall.",
          "ruins the furniture.", "- in Soviet Russia, gun levels you.", 
          "meets his ancestors.", "ventilates the head.", "scores 1 point.",
          "meets his RNG.", "splatters across the channel.", 
          "slays two ears with one shot.", " <=|= [HEADSHOT]", 
          "learned a lesson about fortuitousness.")

def setup(self):
  self.roulette={}
  self.roulette['run']=False

def spin(phenny, input):
  gun = phenny.roulette['gun']
  pos = random.randint(0,len(gun)-1)
  gun = gun[pos:]+gun[:pos]
  phenny.roulette['gun']=gun

def rrload(phenny, input):
  if phenny.roulette['run']:
    return "It's already loaded."  
  bullets = 1
  chambers = 6
  try:
    params = input.split(" ")
    bullets = int(params[1])
    chambers = int(params[2])
  except:
    pass
  chambers = max(2,min(chambers,100))
  bullets = max(1,min(bullets,100))
  if bullets > chambers:
    bullets = chambers
  gun = [False]*chambers
  for bullet in range(0,bullets):
    gun[bullet]=True
  phenny.roulette['gun']=gun
  spin(phenny, input)
  phenny.roulette['run']=True
  strbul = str(bullets) + ((bullets == 1) and " bullet" or " bullets")
  strcha = str(chambers) + ((chambers == 1) and " chamber" or " chambers")
  phenny.say("Well met, ladies. Here's a gun with "+strbul+" in "+strcha+".")
rrload.commands=["load"]
rrload.thread=False

def rrspin(phenny, input):
  if phenny.roulette['run']:
    spin(phenny, input)
    phenny.say("RRRRR... ["+input.nick + " chooses to spin the cylinder.] ...kaCHINK!")
rrspin.commands=["spin"]
rrspin.thread=False

def rrclick(phenny, input):
  if phenny.roulette['run']:
    gun = phenny.roulette['gun']
    next = gun[0]
    if next:
      phenny.say("BLAM! "+input.nick+" "+random.choice(deaths))
      phenny.roulette['run']=False
    else:
      phenny.say("Click. Nothing happens.")
      gun = gun[1:]+gun[:1]
      phenny.roulette['gun']=gun
  else:
    phenny.say("Nothing happens.")
    phenny.say("That's because the colt isn't loaded, milksop!")
rrclick.commands=["pull","rr","suicide","die"]
rrclick.thread=False

