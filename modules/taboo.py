#!/usr/bin/env python
"""a taboo extension for phenny
(c)opyleft 2008-2009 Thomas Hirsch
Licence: GPL"""

import bz2, random, time, yaml, re
from operator import itemgetter
from math import floor

dico = {}

DEFINE_NONE   = None
DEFINE_DEFINE = 1 #status codes for the define game
DEFINE_SELECT = 2

commonwords = []
#commonwords = ['SUCH', 'THAT', 'THAN', 'WHICH', 'FROM', 'WITH', 'OTHER', 'SOME', 'THEIR', 'WHOSE', 'PASS', 'WHERE', 'BEING', 'USED', 'BEEN']

words = bz2.BZ2File("wordlist/wiktionary.txt.bz2","r")
index = None
for line in words:
  line = line.strip()
  if line[0]=='?':
    index = line[1:].upper()
    if len(re.findall('[^A-Z ]',index))>0:
      index=None
  elif line[0]=="!":
    if index:
      dico[index]=line[1:]

def uniq(seq):
  "eliminates duplicates from a list"
  if len(seq)<2: 
    return seq
  rest = uniq(seq[1:])
  if seq[0] in rest:
    return rest
  else:
    return [seq[0]]+rest

def setup(self):
  try:
    yamldata = open("taboo.yaml",'r')
    self.taboo = yaml.load(yamldata.read())
  except:
    self.taboo={}
    self.taboo['run']=False   
    self.taboo['scores']={}
  try:
    yamldata = open("defind.yaml",'r')
    self.define = yaml.load(yamldata.read())
  except:
    self.define={}
    self.define['run']=False   
    self.define['status']=None   
    self.define['scores']={}
    self.define['word']=None
    self.define['defs']=[]
    self.define['selected']={}

def initgame(phenny, input):
  phenny.taboo['clue']=False  
  phenny.taboo['taboo']=False 
  phenny.taboo['run']=True
  phenny.taboo['lines']=0
  phenny.taboo['time']=time.time()
  phenny.taboo['round']={}

playtime = 301

def definescores(phenny, input):
  total = phenny.define['scores']
  msg = 'Total defind scores: '
  ordered = sorted(total.items(), key=itemgetter(1), reverse = True)
  for entry in ordered[:10]:
    msg += entry[0]+": "+str(entry[1])+"; "
  phenny.say(msg)
definescores.commands = ["dtop", "dscores", "dhof"]
definescores.thread   = True
definescores.priority = 'low'

def defind(phenny, input):
  if phenny.define['run']:
    return
  phenny.define['run'] = True
  phenny.define['status'] = DEFINE_NONE
  phenny.define['defs']   = []
  phenny.define['selected']={}
  
  while True:
    word = random.choice(dico.keys())
    if len(word.split(" "))<3 and dico[word].strip():
      break
  phenny.define['word']=word
  phenny.say("Do you all know what %s means? Quick, send me your .def[inition] via private message!" % word)
  phenny.define['defs'] = [[dico[word], "Wiktionary"]]
  phenny.define['status'] = DEFINE_DEFINE
  time.sleep(120)
  defs = phenny.define['defs'][:]
  n=1
  ordered = []
  phenny.say("Let's see, what could %s mean?." % word)
  while len(defs)>0:
    df = random.choice(defs)
    defs.remove(df)
    ordered.append([df[0], df[1], n])
    phenny.say("%i: %s" % (n,df[0]))
    n+=1
  phenny.define['defs']=ordered
  phenny.define['status'] = DEFINE_SELECT
  phenny.say("Now, .select the definition which you would expect to be the official one.")
  time.sleep(60)
  phenny.define['status'] = DEFINE_NONE
  phenny.say("Very well, let's see who has tricked whom today.")
  followers = {}
  selection = phenny.define['selected']
  for fool in selection.keys():
    id = selection[fool]
    if id in followers:
      followers[id].append(fool)
    else:
      followers[id]=[fool]
  for df in ordered:
    msg = "%s proposed: '%s'" % (df[1], df[0])
    fools = followers.get(df[2],[])
    if len(fools):
      if len(fools)==1:
        msg += " - %s was convinced." % fools[0]
      else:
        msg += " - %i were convinced." % len(fools)
      if df[1]!="Wiktionary":
        phenny.define['scores'][df[1]]=phenny.define['scores'].get(df[1],0) + len(fools)*3
      else:
        for fool in fools:
          phenny.define['scores'][fool]=phenny.define['scores'].get(fool,0) + 1
    phenny.say(msg)
  phenny.define['run'] = False
  yamldump = open("defind.yaml",'w') #save teh permanent scores
  yamldump.write(yaml.dump(phenny.define))
  yamldump.close()
  definescores(phenny, input)
defind.commands = ["defind"]
defind.thread   = True
defind.priority = 'low'

def definedef(phenny, input):
  if not phenny.define['status']==DEFINE_DEFINE:
    return
  defs = phenny.define['defs']
  for df in defs:
    if input.nick==df[1]:
      #phenny.say("You have already submitted a definition, %s" % input.nick)
      #return
      defs.remove(df)
      break
  df = input[input.find(" ")+1:]
  defs.append([df, input.nick])
  phenny.say("Thank you, %s" % input.nick)
definedef.commands = ["def","define","definition"]
definedef.thread   = False
definedef.priority = 'low'

def selectdef(phenny, input):
  if not phenny.define['status']==DEFINE_SELECT:
    return
  #if input.nick in phenny.define['selected']:
  #  phenny.say("No changing minds, %s." % input.nick)
  #  return
  try:
    par = input[input.find(" ")+1:]
    pos = int(par)
    df = phenny.define['defs'][pos-1] #throws an exception if out of bounds
    if df[1]==input.nick:
      #intentionally no message provided
      return
    phenny.define['selected'][input.nick]=pos
    phenny.say("A wise choice, %s" % input.nick)
  except:
    phenny.say("That's nothing you could choose from, %s." % input.nick)
    return
selectdef.commands = ["select"]
selectdef.thread   = True
selectdef.priority = 'low'

def tabooify(string):
  return re.sub('[^A-Z ]',' ',string.strip().upper())

def taboo(phenny, input):
  if phenny.taboo['run']:
    return
  initgame(phenny, input)
  while True:
    if not phenny.taboo['clue']:
      while True:
        clue = random.choice(dico.keys())
        boos = uniq(sorted([x for x in tabooify(dico[clue]).split() if len(x)>3]))
        for com in commonwords:
          if com in boos:
            boos.remove(com)
        phenny.taboo['clue']=clue
        phenny.taboo['boos']=boos
	if len(boos)>2: 
          break
      phenny.taboo['player']=input.nick
      phenny.bot.msg(input.nick,"describe "+clue+" without using any of "+reduce(lambda x,y:x+", "+y, boos)) #private message to originator
      tdiff = playtime - (time.time()-phenny.taboo['time']) 
      tmin  = int(floor(tdiff/60))
      tstr = str(tmin) + " minutes " + str(int(floor(tdiff-tmin*60))) + " seconds"
      phenny.say("Taboo: Off we go! "+tstr+" and counting..")
    else:
      time.sleep(1) 
    if time.time() > phenny.taboo['time'] + playtime:
      phenny.say("Time out.")
      break
    if phenny.taboo['taboo']==True: #A taboo word was said
      break
  score = phenny.taboo['round']
  if len(score)>0:
    msg = 'Taboo results: '
    for player in score:
      scr = score[player]
      phenny.taboo['scores'][player]=phenny.taboo['scores'].get(player,0)+scr
      msg += player+": "+str(scr)+"; "
    phenny.taboo['run'] = False 
    yamldump = open("taboo.yaml",'w') #save teh permanent scores
    yamldump.write(yaml.dump(phenny.taboo))
    yamldump.close()
    phenny.say(msg)
  phenny.taboo['run'] = False
taboo.commands=["taboo"]
taboo.thread=True
taboo.priority='low'

def tabooanswer(phenny, input):
  if phenny.taboo['run']==False:
    return
  if phenny.taboo['clue']==False:
    return
  answer = re.sub('[^A-Z]','',input.strip().upper())
  nospaceclue = re.sub(' ','',phenny.taboo['clue'])
  if input.nick == phenny.taboo['player']:
    phenny.taboo['lines']=phenny.taboo.get('lines',0)+1 #count the clues needed
    for boo in phenny.taboo['boos']:
      if boo in answer:
        phenny.say("TABOO!")
        phenny.taboo['taboo']=True
        return #to avoid double mentions
    if nospaceclue in answer:
      phenny.say("DOUBLE BOO!")
      phenny.taboo['taboo']=True
      phenny.taboo['round'][input.nick]=0
  else:
    if answer == nospaceclue:
      pscore = phenny.taboo['round'].get(phenny.taboo['player'],0)+1
      ascore = phenny.taboo['round'].get(input.nick,0)+1
      phenny.say(input.nick+": "+phenny.taboo['clue']+" is correct! You score "+str(ascore)+", "+phenny.taboo['player']+" scores "+str(pscore)+".")
      phenny.taboo['round'][phenny.taboo['player']]=pscore
      phenny.taboo['round'][input.nick]=ascore
      phenny.taboo['clue']=False #ok for next word

tabooanswer.rule=".*?"
tabooanswer.thread=True
tabooanswer.priority='high'

def taboopass(phenny, input):
  if phenny.taboo['run']:
    if input.nick == phenny.taboo['player']:
      phenny.taboo['clue']=False
      phenny.say("Passed.")
taboopass.commands=["pass"]
taboopass.priority='low'

def thof(phenny,input):
  total = phenny.taboo['scores']
  msg = 'Total \'taboo\' scores: '
  ordered = sorted(total.items(), key=itemgetter(1), reverse = True)
  for entry in ordered[:10]:
    msg += entry[0]+": "+str(entry[1])+"; "
  phenny.say(msg)
thof.commands=["thof","ttop","taboohof","tabootop"]
thof.priority='low'  

