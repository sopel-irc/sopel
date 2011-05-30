#!/usr/bin/env python
"""
scores.py - Score Module
Author: Michael S. Yanovich and Matt Meinwald, http://opensource.cse.ohio-state.edu/
Jenni (About): http://inamidst.com/phenny/
"""

import pickle

try:
    scores_file = open("scores.txt","r")
except IOError:
    scores_dict = dict()
else:
    scores_dict = pickle.load(scores_file)
    scores_file.close()

def addpoint(jenni, input):
    """.addpoint <nick> - Adds 1 point to the score system for <nick>."""

    nick = input.group(2)
    if nick != None:
        nick = nick.lstrip().rstrip().split()[0]

    global scores_dict
    if not nick:
        jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
    else:
        if input.nick == nick:
            jenni.reply("I'm sorry, but I'm afraid I can't do that!")
        else:
            nick = nick.lower()
            if nick in scores_dict:
                scores_dict[nick][0] += 1
            else:
                scores_dict[nick] = [1, 0]
            scores_file = open("scores.txt", "w")
            pickle.dump(scores_dict, scores_file)
            msg = "%s: +%d/-%d, %d" % (nick, scores_dict[nick][0], scores_dict[nick][1], scores_dict[nick][0] - scores_dict[nick][1])
            jenni.say(msg)
            scores_file.close()
addpoint.commands = ['addpoint']
addpoint.priority = 'high'

def rmpoint(jenni, input):
    """.rmpoint <nick> - Removes 1 point to the score system for <nick>."""

    nick = input.group(2)
    if nick != None:
        nick = nick.lstrip().rstrip().split()[0]

    global scores_dict
    if not nick:
        jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
    else:
        if input.nick == nick:
            jenni.reply("I'm sorry, but I'm afraid I can't do that!")
        else:
            nick = nick.lower()
            if nick in scores_dict:
                scores_dict[nick][1] += 1
                scores_file = open("scores.txt", "w")
                pickle.dump(scores_dict, scores_file)
                msg = "%s: +%d/-%d, %d" % (nick, scores_dict[nick][0], scores_dict[nick][1], scores_dict[nick][0] - scores_dict[nick][1])
                jenni.say(msg)
                scores_file.close()
            else:
                jenni.reply("I'm sorry, but I'm afraid I can't do that!")
rmpoint.commands = ['rmpoint']
rmpoint.priority = 'high'

def scores(jenni, input):
    """.scores - Lists all users and their point values in the system."""

    global scores_dict
    info = unicode(input.group(2))
    top_scores = [ ]
    if len(scores_dict) >= 1:
        if info != "None":
            info = info.lower().rstrip().lstrip()
            try:
                str_say = "%s: +%s/-%s, %s" % (info, scores_dict[info][0], scores_dict[info][1], scores_dict[info][0] - scores_dict[info][1])
            except:
                str_say = "Sorry no score for %s found." % (info)
        else:
            q = 0
            for key, value in sorted(scores_dict.iteritems(), key=lambda (k,v): (v[0]-v[1]), reverse=True):
                top_scores.append("%s: +%s/-%s, %s" % (key, value[0], value[1], value[0] - value[1]))
                q += 1
                if q > 9:
                    break
            del top_scores[10:]
            str_say = "\x0300Top 10:\x03 %s | %s | %s | %s | %s | %s | %s | %s | %s | %s" % (top_scores[0],top_scores[1],top_scores[2],top_scores[3],top_scores[4],top_scores[5],top_scores[6],top_scores[7],top_scores[8],top_scores[9])
        jenni.say(str_say)
    else:
        jenni.say("There are currently no users with a score.")
scores.commands = ['scores']
scores.priority = 'medium'

def rmuser(jenni, input):
    """.rmuser - Removes a user from the scores system."""

    nick = input.group(2)
    if nick != None:
        nick = nick.lstrip().rstrip().split()[0]

    global scores_dict
    if nick == "" or nick == None:
        jenni.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't remove that user!")
    else:
        if nick in scores_dict:
            if input.admin:
                scores_file = open("scores.txt", "w")
                del scores_dict[nick]
                jenni.say("User, " + str(nick) + ", has been removed.")
                pickle.dump(scores_dict, scores_file)
                scores_file.close()
            else:
                jenni.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't do that!")
        else:
            jenni.say("I'm sorry, " + str(input.nick) + ", but I can not remove a person that does not exist!")
rmuser.commands = ['rmuser']
rmuser.priority = 'medium'

def setpoint(jenni, input):
    """.setpoint <nick> <number> <number> - Sets points for given user."""

    info = input.group(2)
    if info != None:
        info = info.lstrip().rstrip()

    global scores_dict
    if not info:
        jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
    else:
        stuff = info
        stuff_split = stuff.split()
        if input.admin:
            if len(stuff_split) < 3:
                jenni.reply("I'm sorry, but I'm afraid I don't understand what you want me to do!1")
            else:
                nick = stuff_split[0]
                try:
                    add = int(stuff_split[1])
                    sub = int(stuff_split[2])
                except:
                    jenni.say("I'm sorry, but I'm afraid I don't understand what you want me to do!2")
                    return
                try:
                    if input.nick == nick:
                        jenni.reply("I'm sorry, but I'm afraid I can't do that!3")
                    else:
                        nick = nick.lower()
                        if nick in scores_dict:
                            scores_dict[nick] = [add, sub]
                            scores_file = open("scores.txt", "w")
                            pickle.dump(scores_dict, scores_file)
                            msg = "%s: +%d/-%d, %d" % (nick, scores_dict[nick][0], scores_dict[nick][1], scores_dict[nick][0] - scores_dict[nick][1])
                            jenni.say(msg)
                            scores_file.close()
                        else:
                            jenni.reply("I'm sorry, but I'm afraid I can't do that!4")
                except ValueError:
                    jenni.reply("I'm sorry but I refuse to do that!5")
        else:
            jenni.reply("I'm sorry, but you are not one of my admins.6")
setpoint.commands = ['setpoint']
setpoint.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
