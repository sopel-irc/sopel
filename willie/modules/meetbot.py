# -*- coding: utf8 -*-
"""
meetbot.py - Willie meeting logger module
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This module is an attempt to implement at least some of the functionallity of Debian's meetbot
"""
import time
import os
import urllib2
from willie.modules.url import find_title
from willie.tools import Ddict
import codecs

def configure(config):
    """
    | [meetbot] | example | purpose |
    | --------- | ------- | ------- |
    | meeting_log_path | /home/willie/www/meetings | Path to meeting logs storage directory (should be an absolute path, accessible on a webserver) |
    | meeting_log_baseurl | http://example.com/~willie/meetings | Base URL for the meeting logs directory |
    """
    if config.option('Configure meetbot', False):
        config.interactive_add('meetbot', 'meeting_log_path', "Path to meeting logs storage directory (should be an absolute path, accessible on a webserver)")
        config.interactive_add('meetbot', 'meeting_log_baseurl', "Base URL for the meeting logs directory (eg. http://example.com/logs)")

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
meeting_log_path = '' #To be defined on meeting start as part of sanity checks, used by logging functions so we don't have to pass them willie
meeting_log_baseurl = '' #To be defined on meeting start as part of sanity checks, used by logging functions so we don't have to pass them willie

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
    logfile = codecs.open(meeting_log_path + channel + '/' + figure_logfile_name(channel) + '.html', 'a', encoding='utf-8')
    timestring = time.strftime('%Y-%m-%d %H:%M', time.gmtime(meetings_dict[channel]['start']))
    title = '%s at %s, %s' % (meetings_dict[channel]['title'], channel, timestring)
    logfile.write('<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>%TITLE%</title>\n</head>\n<body>\n<h1>%TITLE%</h1>\n'.replace('%TITLE%', title))
    logfile.write('<h4>Meeting started by %s</h4><ul>\n' % meetings_dict[channel]['head'])
    logfile.close()
    
#Write a list item in the HTML log
def logHTML_listitem(item, channel):
    logfile = codecs.open(meeting_log_path + channel + '/' + figure_logfile_name(channel) + '.html', 'a', encoding='utf-8')
    logfile.write('<li>'+item+'</li>\n')
    logfile.close()

#End the HTML log
def logHTML_end(channel):
    logfile = codecs.open(meeting_log_path + channel + '/' + figure_logfile_name(channel) + '.html', 'a', encoding='utf-8')
    current_time = time.strftime('%H:%M:%S', time.gmtime())
    logfile.write('</ul>\n<h4>Meeting ended at %s UTC</h4>\n' % current_time)
    plainlog_url = meeting_log_baseurl + urllib2.quote(channel + '/' + figure_logfile_name(channel) + '.log')
    logfile.write('<a href="%s">Full log</a>' % plainlog_url)
    logfile.write('\n</body>\n</html>')
    logfile.close()

#Write a string to the plain text log
def logplain(item, channel):
    current_time = time.strftime('%H:%M:%S', time.gmtime())
    logfile = codecs.open(meeting_log_path + channel + '/' + figure_logfile_name(channel) + '.log', 'a', encoding='utf-8')
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
def startmeeting(willie, trigger):
    """
    Start a meeting.
    https://github.com/embolalia/willie/wiki/Using-the-meetbot-module
    """
    if ismeetingrunning(trigger.sender):
        willie.say('Can\'t do that, there is already a meeting in progress here!')
        return
    if not trigger.sender.startswith('#'):
        willie.say('Can only start meetings in channels')
        return
    if not willie.config.has_section('meetbot'):
        willie.say('Meetbot not configured, make sure meeting_log_path and meeting_log_baseurl are defined')
        return
    #Start the meeting
    meetings_dict[trigger.sender]['start'] = time.time()
    if not trigger.group(2):
        meetings_dict[trigger.sender]['title'] = 'Untitled meeting'
    else:
        meetings_dict[trigger.sender]['title'] = trigger.group(2)
    meetings_dict[trigger.sender]['head'] = trigger.nick.lower()
    meetings_dict[trigger.sender]['running'] = True
    
    global meeting_log_path
    meeting_log_path = willie.config.meetbot.meeting_log_path
    if not meeting_log_path.endswith('/'):
        meeting_log_path = meeting_log_path + '/'
    global meeting_log_baseurl
    meeting_log_baseurl = willie.config.meetbot.meeting_log_baseurl
    if not meeting_log_baseurl.endswith('/'):
        meeting_log_baseurl = meeting_log_baseurl + '/'
    if not os.path.isdir(meeting_log_path + trigger.sender):
        try:
            os.makedirs(meeting_log_path + trigger.sender)
        except Exception as e:
            willie.say("Can't create log directory for this channel, meeting not started!")
            meetings_dict[trigger.sender] = Ddict(dict)
            raise
            return
    #Okay, meeting started!
    logplain('Meeting started by ' + trigger.nick.lower(), trigger.sender)
    logHTML_start(trigger.sender)
    willie.say('Meeting started! use .action, .agreed, .info, .chairs and .subject to control the meeting. to end the meeting, type .endmeeting')


startmeeting.commands = ['startmeeting']
startmeeting.example = '.startmeeting title or .startmeeting'

#Change the current subject (will appear as <h3> in the HTML log)
def meetingsubject(willie, trigger):
    """
    Change the meeting subject.
    https://github.com/embolalia/willie/wiki/Using-the-meetbot-module
    """
    if not ismeetingrunning(trigger.sender):
        willie.say('Can\'t do that, start meeting first')
        return
    if not trigger.group(2):
        willie.say('what is the subject?')
        return
    if not ischair(trigger.nick, trigger.sender):
        willie.say('Only meeting head or chairs can do that')
        return
    meetings_dict[trigger.sender]['current_subject'] = trigger.group(2)
    logfile = open(meeting_log_path + trigger.sender + '/' + figure_logfile_name(trigger.sender) + '.html', 'a')
    logfile.write('</ul><h3>'+trigger.group(2)+'</h3><ul>')
    logfile.close()
    logplain('Current subject: ' + trigger.group(2) +', (set by ' + trigger.nick +')', trigger.sender)
    willie.say('Current subject: ' + trigger.group(2))
meetingsubject.commands = ['subject']
meetingsubject.example = '.subject roll call'

#End the meeting
def endmeeting(willie, trigger):
    """
    End a meeting.
    https://github.com/embolalia/willie/wiki/Using-the-meetbot-module
    """
    if not ismeetingrunning(trigger.sender):
        willie.say('Can\'t do that, start meeting first')
        return
    if not ischair(trigger.nick, trigger.sender):
        willie.say('Only meeting head or chairs can do that')
        return
    meeting_length = time.time() - meetings_dict[trigger.sender]['start'] 
    #TODO: Humanize time output
    willie.say("Meeting ended! total meeting length %d seconds" % meeting_length)
    logHTML_end(trigger.sender)
    htmllog_url = meeting_log_baseurl + urllib2.quote(trigger.sender + '/' + figure_logfile_name(trigger.sender) + '.html')
    logplain('Meeting ended by %s, total meeting length %d seconds' % (trigger.nick, meeting_length), trigger.sender)
    willie.say('Meeting minutes: ' + htmllog_url)
    meetings_dict[trigger.sender] = Ddict(dict)

endmeeting.commands = ['endmeeting']
endmeeting.example = '.endmeeting'

#Set meeting chairs (people who can control the meeting)
def chairs(willie, trigger):
    """
    Set the meeting chairs.
    https://github.com/embolalia/willie/wiki/Using-the-meetbot-module
    """
    if not ismeetingrunning(trigger.sender):
        willie.say('Can\'t do that, start meeting first')
        return
    if not trigger.group(2):
        willie.say('Who are the chairs?')
        return
    if trigger.nick.lower() == meetings_dict[trigger.sender]['head']:
        meetings_dict[trigger.sender]['chairs'] = trigger.group(2).lower().split(' ')
        chairs_readable = trigger.group(2).lower().replace(' ', ', ')
        logplain('Meeting chairs are: ' + chairs_readable, trigger.sender)
        logHTML_listitem('<span style="font-weight: bold">Meeting chairs are: </span>'+chairs_readable, trigger.sender)
        willie.say('Meeting chairs are: ' + chairs_readable)
    else:
        willie.say("Only meeting head can set chairs")

chairs.commands = ['chairs']
chairs.example = '.chairs Tyrope Jason elad'

#Log action item in the HTML log
def meetingaction(willie, trigger):
    """
    Log an action in the meeting log
    https://github.com/embolalia/willie/wiki/Using-the-meetbot-module
    """
    if not ismeetingrunning(trigger.sender):
        willie.say('Can\'t do that, start meeting first')
        return
    if not trigger.group(2):
        willie.say('try .action someone will do something')
        return
    if not ischair(trigger.nick, trigger.sender):
        willie.say('Only meeting head or chairs can do that')
        return
    logplain('ACTION: ' + trigger.group(2), trigger.sender)
    logHTML_listitem('<span style="font-weight: bold">Action: </span>'+trigger.group(2), trigger.sender)
    willie.say('ACTION: ' + trigger.group(2))
    
meetingaction.commands = ['action']
meetingaction.example = '.action elad will develop a meetbot'

#Log agreed item in the HTML log
def meetingagreed(willie, trigger):
    """
    Log an agreement in the meeting log.
    https://github.com/embolalia/willie/wiki/Using-the-meetbot-module
    """
    if not ismeetingrunning(trigger.sender):
        willie.say('Can\'t do that, start meeting first')
        return
    if not trigger.group(2):
        willie.say('try .action someone will do something')
        return
    if not ischair(trigger.nick, trigger.sender):
        willie.say('Only meeting head or chairs can do that')
        return
    logplain('AGREED: ' + trigger.group(2), trigger.sender)
    logHTML_listitem('<span style="font-weight: bold">Agreed: </span>'+trigger.group(2), trigger.sender)
    willie.say('AGREED: ' + trigger.group(2))
    
meetingagreed.commands = ['agreed']
meetingagreed.example = '.agreed bowties are not cool'

#Log link item in the HTML log
def meetinglink(willie, trigger):
    """
    Log a link in the meeing log.
    https://github.com/embolalia/willie/wiki/Using-the-meetbot-module
    """
    if not ismeetingrunning(trigger.sender):
        willie.say('Can\'t do that, start meeting first')
        return
    if not trigger.group(2):
        willie.say('try .action someone will do something')
        return
    if not ischair(trigger.nick, trigger.sender):
        willie.say('Only meeting head or chairs can do that')
        return
    link = trigger.group(2)
    if not link.startswith("http"):
        link = "http://" + link
    try:
        title = find_title(link)
    except:
        title = ''
    logplain('LINK: %s [%s]' % (link, title), trigger.sender)
    logHTML_listitem('<a href="%s">%s</a>' % (link, title), trigger.sender)
    willie.say('LINK: ' + link)

meetinglink.commands = ['link']
meetinglink.example = '.link http://example.com'


#Log informational item in the HTML log
def meetinginfo(willie, trigger):
    """
    Log an informational item in the meeting log
    https://github.com/embolalia/willie/wiki/Using-the-meetbot-module
    """
    if not ismeetingrunning(trigger.sender):
        willie.say('Can\'t do that, start meeting first')
        return
    if not trigger.group(2):
        willie.say('try .info some informative thing')
        return
    if not ischair(trigger.nick, trigger.sender):
        willie.say('Only meeting head or chairs can do that')
        return
    logplain('INFO: ' + trigger.group(2), trigger.sender)
    logHTML_listitem(trigger.group(2), trigger.sender)
    willie.say('INFO: ' + trigger.group(2))
meetinginfo.commands = ['info']
meetinginfo.example = '.info all board members present'

#called for every single message
#Will log to plain text only
def log_meeting(willie, trigger): 
    if not ismeetingrunning(trigger.sender):
        return
    if trigger.startswith('.endmeeting') or trigger.startswith('.chairs') or trigger.startswith('.action') or trigger.startswith('.info') or trigger.startswith('.startmeeting') or trigger.startswith('.agreed') or trigger.startswith('.link') or trigger.startswith('.subject'):
        return
    logplain('<'+trigger.nick+'> '+trigger, trigger.sender)

log_meeting.rule = r'(.*)'
log_meeting.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
