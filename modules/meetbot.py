#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
meetbot.py - Jenni meeting logger module
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This module is an attempt to implement at least some of the functionallity of Debian's meetbot
"""
import time
import os
import urllib2
from url import find_title
from tools import Ddict

def configure(config):
    chunk = ''
    if config.option('Configure meetbot', True):
        config.interactive_add('meeting_log_path', "Path to meeting logs storage directory (should be an absolute path, accessible on a webserver)")
        config.interactive_add('meeting_log_baseurl', "Base URL for the meeting logs directory (eg. http://example.com/logs)")
        chunk = ("\nmeeting_log_path = '%s'\nmeeting_log_baseurl = '%s'\n"
                 % (config.meeting_log_path, config.meeting_log_baseurl))
    return chunk

""" 
meetings_dict is a 2D dict.

Each meeting should have:
channel
time of start
head (can stop the meeting, plus all abilities of chairs)
chairs (can add infolines to the logs)
title
current subject

Using channel as the meeting ID as there can't be more than one meeting in a channel at the same time.
"""

meetings_dict=Ddict(dict) #Saves metadata about currently running meetings
meeting_log_path = '' #To be defined on meeting start as part of sanity checks, used by logging functions so we don't have to pass them jenni
meeting_log_baseurl = '' #To be defined on meeting start as part of sanity checks, used by logging functions so we don't have to pass them jenni

#Get the logfile name for the meeting in the requested channel
#Used by all logging functions
def figure_logfile_name(channel):
    if meetings_dict[channel]['title'] is 'Untitled meeting':
        name = 'untitled'
    else:
        name = meetings_dict[channel]['title']
    name = name.replace(' ', '-')
    timestring = time.strftime('%Y-%m-%d-%H:%M', time.gmtime(meetings_dict[channel]['start']))
    filename = timestring + '_' + name
    return filename

#Start HTML log
def logHTML_start(channel):
    logfile = open(meeting_log_path + channel + '/' + figure_logfile_name(channel) + '.html', 'a')
    timestring = time.strftime('%Y-%m-%d %H:%M', time.gmtime(meetings_dict[channel]['start']))
    title = '%s at %s, %s' % (meetings_dict[channel]['title'], channel, timestring)
    logfile.write('<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>%TITLE%</title>\n</head>\n<body>\n<h1>%TITLE%</h1>\n'.replace('%TITLE%', title))
    logfile.write('<h4>Meeting started by %s</h4><ul>\n' % meetings_dict[channel]['head'])
    logfile.close()
    
#Write a list item in the HTML log
def logHTML_listitem(item, channel):
    logfile = open(meeting_log_path + channel + '/' + figure_logfile_name(channel) + '.html', 'a')
    logfile.write('<li>'+item+'</li>\n')
    logfile.close()

#End the HTML log
def logHTML_end(channel):
    logfile = open(meeting_log_path + channel + '/' + figure_logfile_name(channel) + '.html', 'a')
    current_time = time.strftime('%H:%M:%S', time.gmtime())
    logfile.write('</ul>\n<h4>Meeting ended at %s UTC</h4>\n' % current_time)
    plainlog_url = meeting_log_baseurl + urllib2.quote(channel + '/' + figure_logfile_name(channel) + '.log')
    logfile.write('<a href="%s">Full log</a>' % plainlog_url)
    logfile.write('\n</body>\n</html>')
    logfile.close()

#Write a string to the plain text log
def logplain(item, channel):
    current_time = time.strftime('%H:%M:%S', time.gmtime())
    logfile = open(meeting_log_path + channel + '/' + figure_logfile_name(channel) + '.log', 'a')
    logfile.write('['+ current_time + '] '+item+'\r\n')
    logfile.close()

#Check if a meeting is currently running
def ismeetingrunning(channel):
    try:
        if meetings_dict[channel]['running']:
            return True
        else:
            return False
    except:
        return False

#Check if nick is a chair or head of the meeting
def ischair(nick,channel):
    try:
        if nick.lower() == meetings_dict[channel]['head'] or nick.lower() in meetings_dict[channel]['chairs']:
            return True
        else:
            return False;
    except:
        return False;

#Start meeting (also preforms all required sanity checks)
def startmeeting(jenni, input):
    if ismeetingrunning(input.sender):
        jenni.say('Can\'t do that, there is already a meeting in progress here!')
        return
    if not input.sender.startswith('#'):
        jenni.say('Can only start meetings in channels')
        return
    if not hasattr(jenni.config, 'meeting_log_path') or not hasattr(jenni.config, 'meeting_log_baseurl'):
        jenni.say('Meetbot not configured, make sure meeting_log_path and meeting_log_baseurl are defined')
        return
    #Start the meeting
    meetings_dict[input.sender]['start'] = time.time()
    if not input.group(2):
        meetings_dict[input.sender]['title'] = 'Untitled meeting'
    else:
        meetings_dict[input.sender]['title'] = input.group(2)
    meetings_dict[input.sender]['head'] = input.nick.lower()
    meetings_dict[input.sender]['running'] = True
    
    global meeting_log_path
    meeting_log_path = jenni.config.meeting_log_path
    if not meeting_log_path.endswith('/'):
        meeting_log_path = meeting_log_path + '/'
    global meeting_log_baseurl
    meeting_log_baseurl = jenni.config.meeting_log_baseurl
    if not meeting_log_baseurl.endswith('/'):
        meeting_log_baseurl = meeting_log_baseurl + '/'
    if not os.path.isdir(meeting_log_path + input.sender):
        try:
            os.makedirs(meeting_log_path + input.sender)
        except Exception as e:
            jenni.say("Can't create log directory for this channel, meeting not started!")
            jenni.say(e)
            meetings_dict[input.sender] = Ddict(dict)
            return
    #Okay, meeting started!
    logplain('Meeting started by ' + input.nick.lower(), input.sender)
    logHTML_start(input.sender)
    jenni.say('Meeting started! use .action, .agreed, .info, .chairs and .subject to control the meeting. to end the meeting, type .endmeeting')


startmeeting.commands = ['startmeeting']
startmeeting.example = '.startmeeting title or .startmeeting'

#Change the current subject (will appear as <h3> in the HTML log)
def meetingsubject(jenni, input):
    if not ismeetingrunning(input.sender):
        jenni.say('Can\'t do that, start meeting first')
        return
    if not input.group(2):
        jenni.say('what is the subject?')
        return
    if not ischair(input.nick, input.sender):
        jenni.say('Only meeting head or chairs can do that')
        return
    meetings_dict[input.sender]['current_subject'] = input.group(2)
    logfile = open(meeting_log_path + input.sender + '/' + figure_logfile_name(input.sender) + '.html', 'a')
    logfile.write('</ul><h3>'+input.group(2)+'</h3><ul>')
    logfile.close()
    logplain('Current subject: ' + input.group(2) +', (set by ' + input.nick +')', input.sender)
    jenni.say('Current subject: ' + input.group(2))
meetingsubject.commands = ['subject']
meetingsubject.example = '.subject roll call'

#End the meeting
def endmeeting(jenni, input):
    if not ismeetingrunning(input.sender):
        jenni.say('Can\'t do that, start meeting first')
        return
    if not ischair(input.nick, input.sender):
        jenni.say('Only meeting head or chairs can do that')
        return
    meeting_length = time.time() - meetings_dict[input.sender]['start'] 
    #TODO: Humanize time output
    jenni.say("Meeting ended! total meeting length %d seconds" % meeting_length)
    logHTML_end(input.sender)
    htmllog_url = meeting_log_baseurl + urllib2.quote(input.sender + '/' + figure_logfile_name(input.sender) + '.html')
    logplain('Meeting ended by %s, total meeting length %d seconds' % (input.nick, meeting_length), input.sender)
    jenni.say('Meeting minutes: ' + htmllog_url)
    meetings_dict[input.sender] = Ddict(dict)

endmeeting.commands = ['endmeeting']
endmeeting.example = '.endmeeting'

#Set meeting chairs (people who can control the meeting)
def chairs(jenni, input):
    if not ismeetingrunning(input.sender):
        jenni.say('Can\'t do that, start meeting first')
        return
    if not input.group(2):
        jenni.say('Who are the chairs?')
        return
    if input.nick.lower() == meetings_dict[input.sender]['head']:
        meetings_dict[input.sender]['chairs'] = input.group(2).lower().split(' ')
        chairs_readable = input.group(2).lower().replace(' ', ', ')
        logplain('Meeting chairs are: ' + chairs_readable, input.sender)
        logHTML_listitem('<span style="font-weight: bold">Meeting chairs are: </span>'+chairs_readable, input.sender)
        jenni.say('Meeting chairs are: ' + chairs_readable)
    else:
        jenni.say("Only meeting head can set chairs")

chairs.commands = ['chairs']
chairs.example = '.chairs Tyrope Jason elad'

#Log action item in the HTML log
def meetingaction(jenni, input):
    if not ismeetingrunning(input.sender):
        jenni.say('Can\'t do that, start meeting first')
        return
    if not input.group(2):
        jenni.say('try .action someone will do something')
        return
    if not ischair(input.nick, input.sender):
        jenni.say('Only meeting head or chairs can do that')
        return
    logplain('ACTION: ' + input.group(2), input.sender)
    logHTML_listitem('<span style="font-weight: bold">Action: </span>'+input.group(2), input.sender)
    jenni.say('ACTION: ' + input.group(2))
    
meetingaction.commands = ['action']
meetingaction.example = '.action elad will develop a meetbot'

#Log agreed item in the HTML log
def meetingagreed(jenni, input):
    if not ismeetingrunning(input.sender):
        jenni.say('Can\'t do that, start meeting first')
        return
    if not input.group(2):
        jenni.say('try .action someone will do something')
        return
    if not ischair(input.nick, input.sender):
        jenni.say('Only meeting head or chairs can do that')
        return
    logplain('AGREED: ' + input.group(2), input.sender)
    logHTML_listitem('<span style="font-weight: bold">Agreed: </span>'+input.group(2), input.sender)
    jenni.say('AGREED: ' + input.group(2))
    
meetingagreed.commands = ['agreed']
meetingagreed.example = '.agreed bowties are not cool'

#Log link item in the HTML log
def meetinglink(jenni, input):
    if not ismeetingrunning(input.sender):
        jenni.say('Can\'t do that, start meeting first')
        return
    if not input.group(2):
        jenni.say('try .action someone will do something')
        return
    if not ischair(input.nick, input.sender):
        jenni.say('Only meeting head or chairs can do that')
        return
    link = input.group(2)
    if not link.startswith("http"):
        link = "http://" + link
    try:
        title = find_title(link)
    except:
        title = ''
    logplain('LINK: %s [%s]' % (link, title), input.sender)
    logHTML_listitem('<a href="%s">%s</a>' % (link, title), input.sender)
    jenni.say('LINK: ' + link)

meetinglink.commands = ['link']
meetinglink.example = '.link http://example.com'


#Log informational item in the HTML log
def meetinginfo(jenni, input):
    if not ismeetingrunning(input.sender):
        jenni.say('Can\'t do that, start meeting first')
        return
    if not input.group(2):
        jenni.say('try .info some informative thing')
        return
    if not ischair(input.nick, input.sender):
        jenni.say('Only meeting head or chairs can do that')
        return
    logplain('INFO: ' + input.group(2), input.sender)
    logHTML_listitem(input.group(2), input.sender)
    jenni.say('INFO: ' + input.group(2))
meetinginfo.commands = ['info']
meetinginfo.example = '.info all board members present'

#called for every single message
#Will log to plain text only
def log_meeting(jenni, input): 
    if not ismeetingrunning(input.sender):
        return
    if input.startswith('.endmeeting') or input.startswith('.chairs') or input.startswith('.action') or input.startswith('.info') or input.startswith('.startmeeting') or input.startswith('.agreed') or input.startswith('.link') or input.startswith('.subject'):
        return
    logplain('<'+input.nick+'> '+input, input.sender)

log_meeting.rule = r'(.*)'
log_meeting.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
