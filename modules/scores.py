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
        self.STRINGS = {
                "nochan" : "Channel, {0}, has no users with scores.",
                "nouser" : "{0} has no score in {1}.",
                "rmuser" : "User, {0}, has been removed from room: {1}.",
                "cantadd" : "I'm sorry, but I'm afraid I can't add that user!",
                "denied" : "I'm sorry, but I can't let you do that!",
                "invalid" : "Invalid parameters entered.",
            }

    def str_score(self, nick, channel):
        return "%s: +%s/-%s, %s" % (nick,
                self.scores_dict[channel][nick][0], self.scores_dict[channel][nick][1], self.scores_dict[channel][nick][0] - self.scores_dict[channel][nick][1])

    def editpoints(self, jenni, input, nick, points):
        if not nick:
            return
        nick = (nick).lower()
        if not nick:
            jenni.reply(self.STRINGS["cantadd"])
        elif (input.nick).lower() == nick:
            jenni.reply(self.STRINGS["denied"])
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

        def top10(channel):
            channel = channel.lower()
            if channel not in self.scores_dict:
                return self.STRINGS["nochan"].format(channel)
            q = 0
            top_scores = [ ]
            str_say = "\x02Top 10 (for %s):\x02" % (channel)
            scores = sorted(self.scores_dict[channel].iteritems(),
                    key=lambda (k,v): (v[0]-v[1]), reverse=True)
            for key, value in scores:
                top_scores.append(self.str_score(key,channel))
                if len(scores) == q + 1:
                    str_say += " %s" % (top_scores[q])
                else:
                    str_say += " %s |" % (top_scores[q])
                q += 1
                if q > 9:
                    break
            return str_say

        def given_user(nick, channel):
            nick = nick.lower()
            channel = channel.lower()
            if channel in self.scores_dict:
                if nick in self.scores_dict[channel]:
                    return self.str_score(nick, channel)
                else:
                    return self.STRINGS["nouser"].format(nick, channel)
            else:
                return self.STRINGS["nochan"].format(channel)

        self.load()
        line = input.group()[7:].split()
        current_channel = input.sender
        current_channel = current_channel.lower()

        if len(line) == 0:
            ## .scores
            t10 = top10(current_channel)
            jenni.say(t10)

        elif len(line) == 1 and not line[0].startswith("#"):
            ## .scores <nick>
            jenni.say(given_user(line[0], current_channel))

        elif len(line) == 1 and line[0].startswith("#"):
            ## .scores <channel>
            t10_chan = top10(line[0])
            jenni.say(t10_chan)

        elif len(line) == 2:
            ## .scores <channel> <nick>
            jenni.say(given_user(line[1], line[0]))

    def setpoint(self, jenni, input, line):
        if not input.admin:
            return
        line = line[10:].split()
        if len(line) != 4:
            return
        channel = line[0]
        nick = line[1].lower()
        try:
            add = int(line[2])
            sub = int(line[3])
        except:
            jenni.say(self.STRINGS["invalid"])
            return

        if channel not in self.scores_dict:
            self.scores_dict[channel] = dict()

        self.scores_dict[channel][nick] = [add, sub]
        self.save()
        jenni.say(self.str_score(nick, channel))

    def rmuser(self, jenni, input, line):
        if not input.admin or line:
            return
        line = line[8:].split()
        channel = input.sender
        nick = line[0].lower()

        def check(nick, channel):
            nick = nick.lower()
            channel = channel.lower()
            if channel in self.scores_dict:
                if nick in self.scores_dict[channel]:
                    del self.scores_dict[channel][nick]
                    return self.STRINGS["rmuser"].format(nick, channel)
                else:
                    return self.STRINGS["nouser"].format(nick, channel)
            else:
                return self.STRINGS["nochan"].format(channel)

        if len(line) == 1:
            ## .rmuser <nick>
            result = check(line[0], input.sender)
            self.save()
        elif len(line) == 2:
            ## .rumser <channel> <nick>
            result = check(line[1],line[0])
            self.save()

        jenni.say(result)

# Jenni commands
scores = Scores()

def addpoint_command(jenni, input):
    """.addpoint <nick> - Adds 1 point to the score system for <nick>."""
    nick = input.group(2)
    if nick:
        nick = nick.strip().split()[0]
    scores.editpoints(jenni, input, nick, True)
addpoint_command.commands = ['addpoint']
addpoint_command.priority = 'high'

def rmpoint_command(jenni, input):
    """.rmpoint <nick> - Adds 1 point to the score system for <nick>."""
    nick = input.group(2)
    if nick:
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
    """.setpoint <channel> <nick> <number> <number> - Sets points for given user."""
    line = input.group()
    if line:
        line = line.lstrip().rstrip()
    scores.setpoint(jenni, input, line)
setpoint.commands = ['setpoint']
setpoint.priority = 'medium'

def removeuser(jenni, input):
    """.rmuser <nick> -- Removes a given user from the system."""
    line = input.group()
    if line:
        line = line.lstrip().rstrip()
    scores.rmuser(jenni, input, line)
removeuser.commands = ['rmuser']
removeuser.priority = 'medium'


if __name__ == '__main__':
    print __doc__.strip()
