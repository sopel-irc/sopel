#!/usr/bin/env python
"""
scores.py - Score Module
Author: Michael Yanovich, yanovich.net, Matt Meinwald and Samuel Clements
Jenni (About): http://inamidst.com/jenni/
"""

import pickle
import os

class Scores:
    def __init__(self):
        self.scores_filename = os.path.expanduser('~/.jenni/scores.txt')

        try:
            scores_file = open(self.scores_filename,"r")
        except IOError:
            self.scores_dict = dict()
        else:
            self.scores_dict = pickle.load(scores_file)
            scores_file.close()
    
    def str_score(self, nick):
        return "%s: +%s/-%s, %s" % (nick, self.scores_dict[nick][0], self.scores_dict[nick][1], self.scores_dict[nick][0] - self.scores_dict[nick][1])

    def editpoints(self, jenni, input, nick, points):
        if not nick:
            jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
        elif input.nick == nick:
            jenni.reply("I'm sorry, but I can't let you do that!")
        else:
            nick = nick.lower()
            if not nick in self.scores_dict:
                self.scores_dict[nick] = [0, 0]
            
            # Add a point if points is TRUE, remove if FALSE
            if points:
                self.scores_dict[nick][0] += 1
            else:
                self.scores_dict[nick][1] += 1
                
            self.save()
            jenni.say(self.str_score(nick))
        
    def save(self):
        scores_file = open(self.scores_filename, "w")
        pickle.dump(self.scores_dict, scores_file)
        scores_file.close()
    
    def view_scores(self, jenni, input):
        nick = unicode(input.group(2))
        top_scores = [ ]
        if len(self.scores_dict) >= 1:
            if nick != "None":
                nick = nick.lower().rstrip().lstrip()
                try:
                    str_say = score(nick)
                except:
                    str_say = "Sorry no score for %s found." % (nick)
            else:
                q = 0
                str_say = "\x0300Top 10:\x03"
                for key, value in sorted(self.scores_dict.iteritems(), key=lambda (k,v): (v[0]-v[1]), reverse=True):
                    top_scores.append("%s: +%s/-%s, %s" % (key, value[0], value[1], value[0] - value[1]))
                    str_say += " %s |" % (top_scores[q])
                    q += 1
                    if q > 9:
                        break
                del top_scores[10:]
            jenni.say(str_say)
        else:
            jenni.say("There are currently no users with a score.")
    
    def setpoint(self, jenni, input, nick):
        if not nick:
            jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
        else:
            if not input.admin or input.nick == nick:
                jenni.reply("I'm sorry, but I'm afraid I can't do that!")
            else:
                stuff = nick
                stuff_split = stuff.split()
                if len(stuff_split) < 3:
                    jenni.reply("I'm sorry, but I'm afraid I don't understand what you want me to do!")
                else:
                    nick = stuff_split[0]
                    try:
                        add = int(stuff_split[1])
                        sub = int(stuff_split[2])
                    except:
                        jenni.say("I'm sorry, but I'm afraid I don't understand what you want me to do!")
                        return
                    try:
                        nick = nick.lower()
                        if nick in self.scores_dict:
                            self.scores_dict[nick] = [add, sub]
                            self.save()
                            jenni.say(self.str_score(nick))
                        else:
                            jenni.reply("The nickname does not exist!")
                    except ValueError:
                        jenni.reply("I'm sorry but I refuse to do that!")


# Jenni commands
scores = Scores()

def addpoint_command(jenni, input):
    """.addpoint <nick> - Adds 1 point to the score system for <nick>."""
    nick = input.group(2)
    if nick != None:
        nick = nick.strip().split()[0]
    scores.editpoints(jenni, input, nick, True)
addpoint_command.commands = ['addpoint']
addpoint_command.priority = 'high'

def rmpoint_command(jenni, input):
    """.rmpoint <nick> - Adds 1 point to the score system for <nick>."""
    nick = input.group(2)
    if nick != None:
        nick = nick.strip().split()[0]
    scores.editpoints(jenni, input, nick, False)
rmpoint_command.commands = ['rmpoint']
rmpoint_command.priority = 'high'

def view_scores(jenni, input):
    """.scores - Lists all users and their point values in the system."""
    scores.view_scores(jenni, input)
view_scores.commands = ['scores']
view_scores.priority = 'medium'

def setpoint(jenni, input):
    """.setpoint <nick> <number> <number> - Sets points for given user."""
    nick = input.group(2)
    if nick != None:
        nick = nick.lstrip().rstrip()
    scores.setpoint(jenni, input, nick)
setpoint.commands = ['setpoint']
setpoint.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
