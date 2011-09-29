#!/usr/bin/env python
"""
scores.py - Scores Module
Copyright 2010-2011, Michael Yanovich (yanovich.net), Matt Meinwald, and Samuel Clements

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import pickle
import os

class Scores:
    def __init__(self):
        self.scores_filename = os.path.expanduser('~/.jenni/scores.txt')
        self.scores_dict = dict()
        self.load()

    def str_score(self, nick, channel):
        return "%s: +%s/-%s, %s" % (nick,
                self.scores_dict[channel][nick][0], self.scores_dict[channel][nick][1], self.scores_dict[channel][nick][0] - self.scores_dict[channel][nick][1])

    def editpoints(self, jenni, input, nick, points):
        if not nick:
            jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
        elif input.nick == nick:
            jenni.reply("I'm sorry, but I can't let you do that!")
        else:
            nick = nick.lower()
            if input.sender not in self.scores_dict:
                self.scores_dict[input.sender] = {}
            if not nick in self.scores_dict[input.sender]:
                self.scores_dict[input.sender][nick] = [0, 0]

            # Add a point if points is TRUE, remove if FALSE
            if points:
                self.scores_dict[input.sender][nick][0] += 1
            else:
                self.scores_dict[input.sender][nick][1] += 1

            self.save()
            chan = input.sender
            jenni.say(self.str_score(nick, chan))

    def save(self):
        """ Save to file in comma seperated values """
        scores_file = open(self.scores_filename, "w")
        for each_chan in self.scores_dict:
            for each_nick in self.scores_dict[each_chan]:
                line = "{0},{1},{2},{3}\n".format(each_chan, each_nick,
                        self.scores_dict[each_chan][each_nick][0],
                        self.scores_dict[each_chan][each_nick][1])
                scores_file.write(line)
        scores_file.close()

    def load(self):
        try:
            sfile = open(self.scores_filename, "r")
        except:
            sfile = open(self.scores_filename, "w")
            sfile.close()
            return
        for line in sfile:
            values = line.split(",")
            if len(values) == 4:
                 if values[0] not in self.scores_dict:
                     self.scores_dict[values[0]] = dict()
                 self.scores_dict[values[0]][values[1]] = [int(values[2]),int(values[3])]
        if not self.scores_dict:
            self.scores_dict = dict()
        sfile.close()

    def view_scores(self, jenni, input):
        self.load()
        nick = unicode(input.group(2))
        top_scores = [ ]
        if len(self.scores_dict) >= 1:
            if nick != "None":
                nick = nick.lower().rstrip().lstrip()
                try:
                    chan = input.sender
                    str_say = self.str_score(nick, chan)
                except:
                    str_say = "Sorry no score for %s found." % (nick)
            else:
                if input.sender not in self.scores_dict:
                    jenni.say("There are currently no users with a score in this channel.")
                    return
                q = 0
                str_say = "\x0300Top 10 (for %s):\x03" % (input.sender)
                scores = sorted(self.scores_dict[input.sender].iteritems(),
                        key=lambda (k,v): (v[0]-v[1]), reverse=True)
                for key, value in scores:
                    top_scores.append("%s: +%s/-%s, %s" % (key, value[0], value[1], value[0] - value[1]))
                    if len(scores) == q + 1:
                        str_say += " %s" % (top_scores[q])
                    else:
                        str_say += " %s |" % (top_scores[q])
                    q += 1
                    if q > 9:
                        break
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
                        jenni.reply("I'm sorry, but I'm afraid I don't understand what you want me to do!")
                        return
                    try:
                        nick = nick.lower()
                        if nick in self.scores_dict:
                            self.scores_dict[input.sender][nick] = [add, sub]
                            self.save()
                            chan = input.sender
                            jenni.say(self.str_score(nick, chan))
                        else:
                            jenni.reply("The nickname does not exist!")
                    except ValueError:
                        jenni.reply("I'm sorry but I refuse to do that!")

    def rmuser(self, jenni, input, nick):
        if not nick:
            jenni.reply("I'm sorry, but I'm afraid I can't remove that user!")
        else:
            if nick in self.scores_dict:
                if input.admin:
                    del self.scores_dict[input.sender][nick]
                    jenni.say("User, %s, has been removed." % (nick))
                    self.save()
                else:
                    jenni.say("I'm sorry, %s. I'm afraid I can't do that!" % (input.nick))
            else:
                jenni.say("I'm sorry, %s, but I can not remove a person that does not exist!" % (input.nick))

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

def removeuser(jenni, input):
    """.rmuser <nick> -- Removes a given user from the system."""
    nick = input.group(2)
    if nick != None:
        nick = nick.lstrip().rstrip()
    scores.rmuser(jenni, input, nick)
removeuser.commands = ['rmuser']
removeuser.priority = 'medium'


if __name__ == '__main__':
    print __doc__.strip()
