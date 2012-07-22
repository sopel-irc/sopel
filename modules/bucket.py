#!/usr/bin/env python
# coding=utf-8
"""
bucket.py - Jenni module to emulate the behavior of #xkcd's Bucket bot
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://github.com/embolalia/jenni

This module is built without using code from the original bucket, but using the same DB table format for factoids.

Things to know if you extend this module:

All inventory items are managed by the inventory class.
All runtime information is in the runtime information class

To preven Jenni from outputting a "Don't Know" message when referred use the following line:

bucket_runtime_data.inhibit_reply = trigger.group(0)

and make sure the priority of your callable is medium or higher.
"""
import MySQLdb, re
from re import sub
from random import randint, seed
import web
import os
from collections import deque
from tools import Ddict
seed()

def configure(config):
    chunk = ''
    if config.option('Configure Bucket factiod DB', True):
        config.interactive_add('bucket_host', "Enter the MySQL hostname", 'localhost')
        config.interactive_add('bucket_user', "Enter the MySQL username")
        config.interactive_add('bucket_pass', "Enter the user's password")
        config.interactive_add('bucket_db', "Enter the name of the database to use")
        config.interactive_add('bucket_literal_path', "Enter the path in which you want to store output of the literal command")
        config.interactive_add('bucket_literal_baseurl', "Base URL for literal output")
        chunk = ("\nbucket_host = '%s'\nbucket_user = '%s'\nbucket_pass = '%s'\nbucket_db = '%s'\nbucket_literal_path = '%s'\nbucket_literal_baseurl = '%s'\n"
                 % (config.bucket_host, config.bucket_user, config.bucket_pass, config.bucket_db, config.bucket_literal_path, config.bucket_literal_baseurl))
    return chunk
    
class Inventory():
    ''' Everything inventory related '''
    avilable_items = []
    current_items = deque([]) #FIFO. Max length 15
    def add_random(self):
        ''' Adds a random item to the inventory'''
        item = self.avilable_items[randint(0, len(self.avilable_items)-1)]
        self.current_items.appendleft(item)
        return item
    def add(self, item, user, channel, jenni):
        ''' Adds an item to the inventory'''
        dropped = False
        if item.lower() not in [x.lower() for x in self.avilable_items]:
            db = connect_db(jenni)
            cur = db.cursor()
            try:
                cur.execute('INSERT INTO bucket_items (`channel`, `what`, `user`) VALUES (%s, %s, %s);', (channel, item, user))
            except MySQLdb.IntegrityError, e:
                jenni.debug('bucket', 'IntegrityError in inventory code', 'warning')
                jenni.debug('bucket', str(e), 'warning')
            db.commit()
            db.close()
            self.avilable_items.append(item)
        if item in self.current_items:
            return '%ERROR% duplicate item %ERROR%'
        if len(self.current_items) >= 15:
            dropped = self.current_items.pop()
        self.current_items.appendleft(item)
        return dropped
    def random_item(self):
        ''' returns a random item '''
        if len(self.current_items) == 0:
            return 'bananas!'
        item = self.current_items[randint(0, len(self.current_items)-1)]
        return item
    def give_item(self):
        ''' returns a random item and removes it from the inventory '''
        item = self.random_item()
        try:
            self.current_items.remove(item)
        except ValueError:
            pass
        return item
    def remove(self, item):
        ''' Attemt to remove an item from the inventory, returns False if failed '''
        try:
            self.current_items.remove(item)
            return True
        except ValueError:
            return False

class bucket_runtime_data():
    dont_know_cache = [] #Caching all the Don't Know factoids to reduce amount of DB reads
    what_was_that = {} #Remembering info of last DB read, per channel. for use with the "what was that" command.
    inhibit_reply = '' #Used to inhibit reply of an error message after teaching a factoid
    last_teach = {}
    last_lines = Ddict(dict) #For quotes.
    inventory = None
    shut_up = False
    special_verbs = ['<reply>', '<directreply>', '<directaction>', '<action>'] 

def remove_punctuation(string):
    return sub("[,\.\!\?\;\:]", '', string)
def setup(jenni):
    print 'Setting up Bucket...'
    db = None
    cur = None
    try:
        db = connect_db(jenni)
    except:
        print 'Error connecting to the bucket database.'
        return
    bucket_runtime_data.inventory = Inventory()
    cur = db.cursor()
    #caching "Don't Know" replies
    cur.execute('SELECT * FROM bucket_facts WHERE fact = "Don\'t Know";')
    results = cur.fetchall()
    cur.execute('SELECT * FROM bucket_items;')
    items = cur.fetchall()
    db.close()
    for result in results:
        bucket_runtime_data.dont_know_cache.append(result[2])
    for item in items:
        bucket_runtime_data.inventory.avilable_items.append(item[2])
    print 'Done setting up Bucket!'
def add_fact(jenni, trigger, fact, tidbit, verb, re, protected, mood, chance):
    db = None
    cur = None
    db = connect_db(jenni)
    cur = db.cursor()
    try:
        cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', (fact, tidbit, verb, re, protected, mood, chance))
        db.commit()
    except MySQLdb.IntegrityError:
        jenni.say("I already had it that way!")
        db.close()
        return False
    db.close()
    bucket_runtime_data.last_teach[trigger.sender] = [fact,verb,tidbit]
    jenni.say("Okay, "+trigger.nick)

def teach_is_are(jenni, trigger):
    """Teaches a is b and a are b"""
    fact = trigger.group(1)
    bucket_runtime_data.inhibit_reply = trigger.group(0)
    fact = remove_punctuation(fact)
    tidbit = trigger.group(3)
    verb = trigger.group(2)
    re = False
    protected = False
    mood = None
    chance = None
    for word in trigger.group(0).lower().split(' '):
        if word in bucket_runtime_data.special_verbs:
            return #do NOT teach is are if the trigger is similar to "Lemon, Who is the king of the derps? <reply> I am!" (contains both is|are and a special verb.
    
    add_fact(jenni, trigger, fact, tidbit, verb, re, protected, mood, chance)
teach_is_are.rule = ('$nick', '(.*?) (is|are) (.*)')
teach_is_are.priority = 'high'

def teach_verb(jenni, trigger):
    """Teaches verbs/ambiguous reply"""
    bucket_runtime_data.inhibit_reply = trigger.group(0)
    fact = trigger.group(1)
    fact = remove_punctuation(fact)
    tidbit = trigger.group(3)
    verb = trigger.group(2)
    re = False
    protected = False
    mood = None
    chance = None
    
    if verb not in bucket_runtime_data.special_verbs:
        verb = verb[1:-1]
    
    
    add_fact(jenni, trigger, fact, tidbit, verb, re, protected, mood, chance)
    if fact.lower() == 'don\'t know':
        bucket_runtime_data.dont_know_cache.append(tidbit)
teach_verb.rule = ('$nick', '(.*?) (<\S+>) (.*)')
teach_verb.priority = 'high'

def save_quote(jenni, trigger):
    """Saves a quote"""
    bucket_runtime_data.inhibit_reply = trigger.group(0)
    quotee = trigger.group(1).lower()
    word = trigger.group(2)
    fact = quotee+' quotes'
    verb = '<reply>'
    re = False
    protected = False
    mood = None
    chance = None
    
    memory = bucket_runtime_data.last_lines[trigger.sender][quotee]
    for line in memory:
        if word.lower() in line.lower():
            tidbit = '<%s> %s' % (quotee, line)
            add_fact(jenni, trigger, fact, tidbit, verb, re, protected, mood, chance)
            jenni.say("Remembered that %s <reply> %s" % (fact, tidbit))
            return
    jenni.say("Sorry, I don't remember what %s said about %s" % (quotee, word))
save_quote.rule = ('$nick', 'remember (.*?) (.*)')
save_quote.priority = 'medium'

def delete_factoid(jenni, trigger):
    """Delets a factoid"""
    bucket_runtime_data.inhibit_reply = trigger.group(0)
    was = bucket_runtime_data.what_was_that
    if not trigger.admin:
        was[trigger.sender] = dont_know(jenni)
        return
    db = None
    cur = None
    db = connect_db(jenni)
    cur = db.cursor()

    try:
        cur.execute('DELETE FROM bucket_facts WHERE ID = %s',int(trigger.group(1)))
        db.commit()
    except:
        jenni.say("Delete failed! are you sure this is a valid factoid ID?")
        db.close()
        return
    db.close()
    jenni.say("Okay, "+trigger.nick)
    
delete_factoid.rule = ('$nick', 'delete #(.*)')
delete_factoid.priority = 'high'

def undo_teach(jenni, trigger):
    """Undo teaching factoid"""
    was = bucket_runtime_data.what_was_that
    bucket_runtime_data.inhibit_reply = trigger.group(0)
    if not trigger.admin:
        was[trigger.sender] = dont_know(jenni)
        return
    last_teach = bucket_runtime_data.last_teach
    fact = ''
    verb = ''
    tidbit = ''
    try:
        fact = last_teach[trigger.sender][0]
        verb = last_teach[trigger.sender][1]
        tidbit = last_teach[trigger.sender][2]
    except KeyError:
        jenni.reply('Nothing to undo!')
        return
    db = None
    cur = None
    db = connect_db(jenni)
    cur = db.cursor()
    try:
        cur.execute('DELETE FROM bucket_facts WHERE `fact` = %s AND `verb` = %s AND `tidbit` = %s', (fact, verb, tidbit))
        db.commit()
    except:
        jenni.say("Undo failed, this shouldn't have happened!")
        db.close()
        return
    db.close()
    jenni.say("Okay, "+trigger.nick)
    
undo_teach.rule = ('$nick', 'undo last')
undo_teach.priority = 'high'

def say_fact(jenni, trigger):
    """Response, if needed"""
    query = trigger.group(0)
    was = bucket_runtime_data.what_was_that
    inventory = bucket_runtime_data.inventory
    if query.lower().startswith('\001action gives %s ' % jenni.nick.lower()) or remove_punctuation(query.lower()).startswith('%s take this ' % jenni.nick.lower()):
        #get given item to inventory
        if query.lower().startswith('\001action gives %s ' % jenni.nick.lower()):
            item = query[len('\001ACTION gives %s ' % jenni.nick):-1]
        else:
            item = query[len('%s take this  ' % jenni.nick):]

        dropped = inventory.add(item, trigger.nick, trigger.sender, jenni)
        db = None
        cur = None
        results = None
        db = connect_db(jenni)
        cur = db.cursor()
        search_term = ''
        if dropped == False:
            #Query for 'takes item'
            search_term = 'takes item'
        elif dropped == '%ERROR% duplicate item %ERROR%':
            #Query for 'duplicate item'
            search_term = 'duplicate item'
        else:
            #Query for 'pickup full'
            search_term = 'pickup full'
        cur.execute('SELECT * FROM bucket_facts WHERE fact = %s;', search_term)
        results = cur.fetchall()
        result = ''
        if len(results) == 1:
            result = results[0]
        elif len(results) > 1:
            result = results[randint(0, len(results)-1)]
        # 1 = fact
        fact = result[1]
        # 2 = tidbit
        tidbit = result[2]
        tidbit = tidbit.replace('$item', item)
        tidbit = tidbit_vars(tidbit, trigger, False)
        # 3 = verb
        verb = result[3]

        if verb not in bucket_runtime_data.special_verbs:
            jenni.say("%s %s %s" % (fact, verb, tidbit))
        elif verb == '<reply>':
            jenni.say(tidbit)
        elif verb == '<action>':
            jenni.action(tidbit)
        was = result
        return
    elif query.lower().startswith('\001action takes %s\'s ' % jenni.nick.lower()) or query.lower().startswith('\001action steals %s\'s ' % jenni.nick.lower()):
        if query.lower().startswith('\001action takes %s\'s ' % jenni.nick.lower()):
            item = remove_punctuation(query[len('\001ACTION takes %s\'s ' % jenni.nick):-1])
        else:
            item = remove_punctuation(query[len('\001ACTION steals %s\'s ' % jenni.nick):-1])
        if (inventory.remove(item)):
            jenni.say('Hey! Give it back, it\'s mine!')
        else:
            jenni.say('But I don\'t have any %s' % item)
    if query.startswith('\001ACTION'):
        query = query[len('\001ACTION '):]
    addressed = query.lower().startswith(jenni.nick.lower()) #Check if our nick was mentioned
    search_term = query.lower().strip() #What we are going to pass to MySql as our search term
    if addressed:
        search_term = search_term[(len(jenni.nick)+1):].strip() #Remove our nickname from the search term
    search_term = remove_punctuation(search_term).strip()

    if len(query) < 6 and not addressed:
        return #Ignore factoids shorter than 6 chars when not addressed
    if search_term == 'don\'t know' and not addressed:
        return #Ignore "don't know" when not addressed
    if not addressed and bucket_runtime_data.shut_up:
        return #Don't say anything if not addressed and shutting up
    if search_term == 'shut up' and addressed:
        jenni.reply('Okay...')
        bucket_runtime_data.shut_up = True
        return
    elif search_term == 'come back' and addressed:
        jenni.reply('I\'m back!')
        bucket_runtime_data.shut_up = False
        return
    literal = False
    inhibit = bucket_runtime_data.inhibit_reply
    remember(trigger)
    if search_term.startswith('literal '):
        literal = True
        search_term = str.replace(str(search_term), 'literal ','')
    elif search_term == 'what was that' and addressed:
        try:
            jenni.say('That was '+ str(was[trigger.sender]))
        except KeyError:
            jenni.say('I have no idea')
        return
    elif search_term.startswith('reload') or search_term.startswith('update') or inhibit == search_term or inhibit == trigger.group(0):
        return #ignore commands such as reload or update, don't show 'Don't Know' responses for these 
    db = None
    cur = None
    results = None
    db = connect_db(jenni)
    cur = db.cursor()

    search_term = search_term.strip()
    if search_term == 'random quote':
        try:
            cur.execute('SELECT * FROM bucket_facts WHERE fact LIKE "% quotes";')
            results = cur.fetchall()
        except UnicodeEncodeError:
            jenni.debug('bucket','Warning, database encoding error', 'warning')
        if results == None:
            return
    else:
        try:
            cur.execute('SELECT * FROM bucket_facts WHERE fact = %s;', search_term)
            results = cur.fetchall()
        except UnicodeEncodeError:
            jenni.debug('bucket','Warning, database encoding error', 'warning')
        if results == None:
            return
    db.close()
    result = output_results(jenni, trigger, results, literal, addressed)
    was[trigger.sender] = result
    
say_fact.rule = ('(.*)')
say_fact.priority = 'low'

def get_inventory(jenni, trigger):
    ''' get a human readable list of the bucket inventory '''

    bucket_runtime_data.inhibit_reply = trigger.group(0)

    inventory = bucket_runtime_data.inventory

    readable_item_list = ''
    
    if len(inventory.current_items)==0:
        return jenni.action('is carrying nothing')
    for item in inventory.current_items:
        readable_item_list = readable_item_list + ' '+str(item)+','

    jenni.action('is carrying'+readable_item_list)

get_inventory.rule = ('$nick','inventory')
get_inventory.priority = 'medium'

def output_results(jenni, trigger, results, literal=False, addressed=False):
    if len(results) == 1:
        result = results[0]
    elif len(results) > 1:
        result = results[randint(0, len(results)-1)]
    else:
        if addressed:
            return 'Don\'t know: '+dont_know(jenni)
        else:
            try:
                return bucket_runtime_data.what_was_that[trigger.sender]
            except KeyError:
                return ''
    # 1 = fact
    fact = result[1]
    # 2 = tidbit
    tidbit = tidbit_vars(result[2], trigger)
    # 3 = verb
    verb = result[3]

    if verb not in bucket_runtime_data.special_verbs and not literal:
        jenni.say("%s %s %s" % (fact, verb, tidbit))
    elif verb == '<reply>' and not literal:
        jenni.say(tidbit)
    elif verb == '<action>' and not literal:
        jenni.action(tidbit)
    elif verb == '<directreply>' and not literal and addressed:
        jenni.say(tidbit)
    elif verb == '<directaction>' and not literal and addressed:
        jenni.action(tidbit)
    elif literal:
        if len(results) == 1:
            result = results[0]
            number = int(result[0])
            fact = result[1]
            tidbit = result[2]
            verb = result[3]
            jenni.say ("#%d - %s %s %s" % (number, fact, verb, tidbit))
        else:
            jenni.reply('just a second, I\'ll make the list!')
            bucket_literal_path = jenni.config.bucket_literal_path
            bucket_literal_baseurl = jenni.config.bucket_literal_baseurl
            if not bucket_literal_baseurl.endswith('/'):
                bucket_literal_baseurl = bucket_literal_baseurl + '/'
            if not os.path.isdir(bucket_literal_path):
                try:
                    os.makedirs(bucket_literal_path)
                except Exception as e:
                    jenni.say("Can't create directory to store literal, sorry!")
                    jenni.say(e)
                    return
            f = open(os.path.join(bucket_literal_path, fact+'.txt'), 'w')
            for result in results:
                number = int(result[0])
                fact = result[1]
                tidbit = result[2]
                verb = result[3]
                literal_line = "#%d - %s %s %s" % (number, fact, verb, tidbit)
                f.write(literal_line+'\n')
            f.close()
            jenni.reply('Here you go! %s (%d factoids)' % (bucket_literal_baseurl+web.quote(fact+'.txt'), len(results)))
        return 'Me giving you a literal link'
    return result

def connect_db(jenni):
    return MySQLdb.connect(host=jenni.config.bucket_host,
                         user=jenni.config.bucket_user,
                         passwd=jenni.config.bucket_pass,
                         db=jenni.config.bucket_db)
def tidbit_vars(tidbit, trigger, random_item=True):
    ''' Parse in-tidbit vars '''
    #Special in-tidbit vars:
    inventory = bucket_runtime_data.inventory
    tidbit = tidbit.replace('$who', trigger.nick)
    if '$giveitem' in tidbit:
        tidbit = tidbit.replace('$giveitem', str(inventory.give_item()))
    if '$newitem' in tidbit:
        tidbit = tidbit.replace('$newitem', str(inventory.add_random()))
    if random_item:
        tidbit = tidbit.replace('$item', str(inventory.random_item()))
    return tidbit
def dont_know(jenni):
    ''' Get a Don't Know reply from the cache '''
    cache = bucket_runtime_data.dont_know_cache
    try:
        reply = cache[randint(0, len(cache)-1)]
    except ValueError:
        setup(jenni) #The don't know cache is empty, fill it!
        return dont_know(jenni)
    jenni.say(reply)
    return reply

def remember(trigger):
    ''' Remember last 10 lines of each user, to use in the quote function '''
    memory = bucket_runtime_data.last_lines
    try:
        fifo = deque(memory[trigger.sender][trigger.nick.lower()])
    except KeyError:
        memory[trigger.sender][trigger.nick.lower()]=[] #Initializing the array
        return remember(trigger)
    if len(fifo) == 10:
        fifo.pop()
    fifo.appendleft(trigger.group(0))
    memory[trigger.sender][trigger.nick.lower()] = fifo
    
if __name__ == '__main__':
    print __doc__.strip()
