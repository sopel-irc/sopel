#!/usr/bin/env python
"""
wa.py - NationStates WA tools for jenni
Copyright 2011, Edward D. Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://inamidst.com/jenni/
"""

import MySQLdb, re

def configure(config):
    chunk = ''
    if config.option('Configure NationStates resolution DB', True):
        config.interactive_add('wa_host', "Enter the MySQL hostname", 'localhost')
        config.interactive_add('wa_user', "Enter the MySQL username")
        config.interactive_add('wa_pass', "Enter the user's password")
        config.interactive_add('wa_db', "Enter the name of the database to use")
        chunk = ("\nwa_db = '%s'\nwa_user = '%s'\nwa_pass = '%s'\nwa_db = '%s'\n"
                 % (config.wa_host, config.wa_user, config.wa_pass, config.wa_db))
    return chunk

def whats(jenni, input):
    """Looks up a NationStates-related abbreviation or WA resolution"""
    db = None
    cur = None
    try:
        db = MySQLdb.connect(host=jenni.config.wa_host,
                             user=jenni.config.wa_user,
                             passwd=jenni.config.wa_pass,
                             db=jenni.config.wa_db)
        cur = db.cursor()
    except:
        print "nationstates.py: WADB connection failed."
    
    givenum = 1
    #Retrieve resolution number and council
    w, abbr = input.groups()
    resd = re.match('(GA|SC|UN)(#| )*(\d*)', abbr)
    if resd:
        givenum = 0
        result = [resd.group(1), resd.group(3), abbr, None]
        if result[0] == 'GA': result[0] = 'G'
        elif result[0] == 'SC': result[0] = 'S'
        else: result[0] = 'U'
    else:        
        cur.execute("SELECT * FROM ABBRS WHERE Abbr = \"" + abbr + "\"")
        result = cur.fetchone()
    
    if result is None:
        jenni.say("Your guess is as good as mine, mate.")
    elif result[3] is not None:
        jenni.say(abbr + ' is ' + result[3])
    elif result[0] is not 'G':
        jenni.say('Sorry, ' + input.nick + ', I don\'t have data on that council yet.')
    else:
        council, number = result[0], result[1]
        num = str(number)
    
        #Look up full resolution name
        select = "SELECT * FROM RESOLUTIONS WHERE Council = \'"
        cur.execute(select + council + "\' AND Number = " +  num)
        
        message = makemessage(abbr, council, num, cur.fetchone(), givenum)
        
        jenni.say(message)
    
    db.close()
whats.rule = ('$nick', ['whats', 'what\'s'], r'(.*)')
whats.example = '$nick, what\'s GA34\n$nick, whats CoCR?'

def makemessage(abbr, council, num, result, givenum):
    if not result:
        message = 'I don\'t have a result for that yet.'
    else:
        name = result[2]
        cat = result[3]
        arg = result[4]
        auth = result[5]
        coauth = result[6]
        active = 0
        if result[7] == None: active = 1
        print active
        
        if council == 'G': council = 'GA'
        elif council == 'S': council == 'SC'
        else: council = 'UN'
        
        message = abbr + ' is '
        if givenum: message = message + council + '#' + num + ', '
        message = message + name
        if not active: message = message + ', a repealed resolution'
        message = message + ' by ' + auth
        if coauth: message = message + ' and ' + coauth
    return message
    
def authored(jenni, input):
    """.authored nation - Checks the resolution DB for resolutions authored by
    nation (or nation with any number of characters after. e.g, .authored unibot
    returns results for Unibot and Unibotian WA Mission."""
    jenni.say("Let me check.")
    name = input.group(2)
    
    db = None
    cur = None
    try:
        db = MySQLdb.connect(host=jenni.config.wa_host,
                             user=jenni.config.wa_user,
                             passwd=jenni.config.wa_pass,
                             db=jenni.config.wa_db)
        cur = db.cursor()
    except:
        print "nationstates.py: WADB connection failed."
    
    auth = 'SELECT COUNT(*) FROM RESOLUTIONS WHERE Author LIKE \''
    cur.execute(auth + name + '%\'')
    authored = cur.fetchone()[0]
    
    coauth = 'SELECT COUNT(*) FROM RESOLUTIONS WHERE Coauthor LIKE \''
    cur.execute(coauth + name + '%\'')
    coauthored = cur.fetchone()[0]
    
    db.close()
    
    message = 'I see ' + str(authored) + ' resolutions'
    if coauthored > 0:
        message = message + ', plus ' + str(coauthored) + ' coauthorships'
    jenni.say(message + ' by ' + name)
authored.commands = ['authored']
authored.example = '.authored Unibot'

def sc(jenni, input):
    """Returns a link for the requested SC resolution."""
    lnk = 'http://www.nationstates.net/page=WA_past_resolutions/council=2/start='
    jenni.say(lnk + str(int(input.group(2)) - 1))
sc.commands = ['sc']
sc.example = '.sc 3'

def ga(jenni, input):
    """Returns a link for the requested GA resolution."""
    lnk = 'http://www.nationstates.net/page=WA_past_resolutions/council=1/start='
    jenni.say(lnk + str(int(input.group(2)) - 1))
ga.commands = ['ga']
ga.example = '.ga 132'

def un(jenni, input):
    """Returns a link for the requested NSUN historical resolution."""
    lnk = 'http://www.nationstates.net/page=UN_past_resolutions/council=0/start='
    jenni.say(lnk + str(int(input.group(2)) - 1))
un.commands = ['un']
un.example = '.un 5'

def rlink(jenni, input):
     lnk = 'http://www.nationstates.net/region=' + input.group(2).rstrip(' ')
     jenni.reply(lnk)
rlink.commands = ['rlink']

def nation(jenni, input):
     lnk = 'http://www.nationstates.net/' + input.group(2).rstrip(' ')
     jenni.reply(lnk)
nation.commands = ['nation','n']

def uhoh(jenni, input):
     jenni.reply('Sorry, I\'m not FriarTuck. Eluvatar hasn\'t given me that code yet.')
uhoh.commands = ['after', 'approx']
