# coding=utf-8
"""
bucket.py - willie module to emulate the behavior of #xkcd's Bucket bot
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://github.com/embolalia/willie

This module is built without using code from the original bucket, but using the same DB table format for factoids.

Things to know if you extend this module:

All inventory items are managed by the inventory class.
All runtime information is in the runtime information class

To prevent willie from outputting a "Don't Know" message when referred use the following line:

bucket_runtime_data.inhibit_reply = trigger.group(0)

and make sure the priority of your callable is medium or higher.
"""
import MySQLdb, re
from re import sub
from random import randint, seed
import willie.web as web
import os
from collections import deque
from willie.tools import Ddict
seed()

def configure(config):
    """
    It is highly recommended that you run the configuration utility on this
    module, as it will handle creating an initializing your database. More
    information on this module at https://github.com/embolalia/willie/wiki/The-Bucket-Module:-User-and-Bot-Owner-Documentation
    
    | [bucket] | example | purpose |
    | -------- | ------- | ------- |
    | db_host | example.com | The address of the MySQL server |
    | db_user | bucket | The username to log into the MySQL database |
    | db_pass | hunter2 | The password for the MySQL database |
    | db_name | bucket | The name of the database you will use |
    | literal_path | /home/willie/www/bucket | The path in which to store output of the literal command |
    | literal_baseurl | http://example.net/~willie/bucket | The base URL for literal output |
    """
    if config.option('Configure Bucket factiod DB', False):
        config.interactive_add('bucket', 'db_host', "Enter the MySQL hostname", 'localhost')
        config.interactive_add('bucket', 'db_user', "Enter the MySQL username")
        config.interactive_add('bucket', 'db_pass', "Enter the user's password")
        config.interactive_add('bucket', 'db_name', "Enter the name of the database to use")
        config.interactive_add('bucket', 'literal_path', "Enter the path in which you want to store output of the literal command")
        config.interactive_add( 'bucket','literal_baseurl', "Base URL for literal output")
        if config.option('do you want to generate bucket tables and populate them with some default data?', True):
            db = MySQLdb.connect(host=config.bucket.db_host,
                         user=config.bucket.db_user,
                         passwd=config.bucket.db_pass,
                         db=config.bucket.db_name)
            cur = db.cursor()
            #Create facts table
            cur.execute("CREATE TABLE IF NOT EXISTS `bucket_facts` (`id` int(10) unsigned NOT NULL AUTO_INCREMENT,`fact` varchar(128) COLLATE utf8_unicode_ci NOT NULL,`tidbit` text COLLATE utf8_unicode_ci NOT NULL,`verb` varchar(16) CHARACTER SET latin1 NOT NULL DEFAULT 'is',`RE` tinyint(1) NOT NULL,`protected` tinyint(1) NOT NULL,`mood` tinyint(3) unsigned DEFAULT NULL,`chance` tinyint(3) unsigned DEFAULT NULL,PRIMARY KEY (`id`),UNIQUE KEY `fact` (`fact`,`tidbit`(200),`verb`),KEY `trigger` (`fact`),KEY `RE` (`RE`)) ENGINE=MyISAM  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;")
            #Create inventory table
            cur.execute("CREATE TABLE IF NOT EXISTS `bucket_items` (`id` int(10) unsigned NOT NULL auto_increment,`channel` varchar(64) NOT NULL,`what` varchar(255) NOT NULL,`user` varchar(64) NOT NULL,PRIMARY KEY (`id`),UNIQUE KEY `what` (`what`),KEY `from` (`user`),KEY `where` (`channel`)) ENGINE=MyISAM DEFAULT CHARSET=latin1 ;")
            #Insert a Don't Know factiod
            cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', ('Don\'t Know', '++?????++ Out of Cheese Error. Redo From Start.', '<reply>', False, False, None, None))
            #Insert a pickup full factiod
            cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', ('pickup full', 'takes $item but drops $giveitem', '<action>', False, False, None, None))
            #Insert a duplicate item factiod
            cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', ('duplicate item', 'No thanks, I\'ve already got $item', '<reply>', False, False, None, None))
            #Insert a take item factiod
            cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', ('takes item', 'Oh, thanks, I\'ll keep this $item safe', '<reply>', False, False, None, None))
            db.commit()
            db.close()
    
class Inventory():
    ''' Everything inventory related '''
    avilable_items = []
    current_items = deque([]) # Max length 15
    def add_random(self):
        ''' Adds a random item to the inventory'''
        item = self.avilable_items[randint(0, len(self.avilable_items)-1)].strip()
        if item in self.current_items:
            try:
                return self.add_random()
            except RuntimeError:
                #Too much recursion, this can only mean all avilable_items are in current_items. Bananas.
                self.current_items.appendleft('bananas!')
                return 'bananas!'
        self.current_items.appendleft(item)
        return item
    def add(self, item, user, channel, willie):
        ''' Adds an item to the inventory'''
        dropped = False
        item = item.strip()
        if item.lower() not in [x.lower() for x in self.avilable_items]:
            db = connect_db(willie)
            cur = db.cursor()
            try:
                cur.execute('INSERT INTO bucket_items (`channel`, `what`, `user`) VALUES (%s, %s, %s);', (channel, item.encode('utf8'), user))
            except MySQLdb.IntegrityError, e:
                willie.debug('bucket', 'IntegrityError in inventory code', 'warning')
                willie.debug('bucket', str(e), 'warning')
            db.commit()
            db.close()
            self.avilable_items.append(item)
        if item in self.current_items:
            return '%ERROR% duplicate item %ERROR%'
        if len(self.current_items) >= 15:
            dropped = True
        self.current_items.appendleft(item)
        return dropped
    def random_item(self):
        ''' returns a random item '''
        if len(self.current_items) == 0:
            return 'bananas!'
        item = self.current_items[randint(0, len(self.current_items)-1)]
        return item
    def populate(self):
        ''' Clears the inventory and fill it with random items '''
        self.current_items = deque([])
        while (len(self.current_items)<15):
            self.add_random()
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
    shut_up = []
    special_verbs = ['<reply>', '<directreply>', '<directaction>', '<action>', '<alias>']
    factoid_search_re = re.compile('(.*).~=./(.*)/')

def remove_punctuation(string):
    return sub("[,\.\!\?\;\:]", '', string)
def setup(willie):
    print 'Setting up Bucket...'
    db = None
    cur = None
    try:
        db = connect_db(willie)
    except:
        print 'Error connecting to the bucket database.'
        raise
        return
    #caching "Don't Know" replies
    rebuild_dont_know_cache(willie)
    bucket_runtime_data.inventory = Inventory()
    cur = db.cursor()
    cur.execute('SELECT * FROM bucket_items;')
    items = cur.fetchall()
    db.close()
    for item in items:
        bucket_runtime_data.inventory.avilable_items.append(item[2])
    print 'Done setting up Bucket!'

def rebuild_dont_know_cache(willie):
        db = connect_db(willie)
        cur = db.cursor()
        cur.execute('SELECT * FROM bucket_facts WHERE fact = "Don\'t Know";')
        results = cur.fetchall()
        for result in results:
            bucket_runtime_data.dont_know_cache.append(result)
        db.close()

def add_fact(willie, trigger, fact, tidbit, verb, re, protected, mood, chance, say=True):
    db = None
    cur = None
    db = connect_db(willie)
    cur = db.cursor()
    try:
        cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', (fact, tidbit, verb, re, protected, mood, chance))
        db.commit()
    except MySQLdb.IntegrityError:
        willie.say("I already had it that way!")
        return False
    finally:
        db.close()
    bucket_runtime_data.last_teach[trigger.sender] = [fact,verb,tidbit]
    if say:
        willie.say("Okay, "+trigger.nick)
    return True

def teach_is_are(willie, trigger):
    """Teaches a is b and a are b"""
    fact = trigger.group(1)
    bucket_runtime_data.inhibit_reply = trigger
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
    
    add_fact(willie, trigger, fact, tidbit, verb, re, protected, mood, chance)
teach_is_are.rule = ('$nick', '(.*?) (is|are) (.*)')
teach_is_are.priority = 'high'

def teach_verb(willie, trigger):
    """Teaches verbs/ambiguous reply"""
    bucket_runtime_data.inhibit_reply = trigger
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
    
    if fact == tidbit and verb == '<alias>':
        willie.reply('You can\'t alias like this!')
        return
    say = True
    if verb == '<alias>':
        say = False
    success = add_fact(willie, trigger, fact, tidbit, verb, re, protected, mood, chance, say)
    if verb == '<alias>':
        db = connect_db(willie)
        cur = db.cursor()
        cur.execute('SELECT * FROM bucket_facts WHERE fact = %s;', tidbit)
        results = cur.fetchall()
        db.close()
        if len(results) == 0 and success:
            willie.say('Okay, %s. but, FYI, %s doesn\'t exist yet' % (trigger.nick, tidbit))
        if len(results) > 0 and success:
            willie.say('Okay, %s' % trigger.nick)
    if fact.lower() == 'don\'t know':
        rebuild_dont_know_cache(willie)
teach_verb.rule = ('$nick', '(.*?) (<\S+>) (.*)')
teach_verb.priority = 'high'

def save_quote(willie, trigger):
    """Saves a quote"""
    bucket_runtime_data.inhibit_reply = trigger
    quotee = trigger.group(1).lower()
    word = trigger.group(2).strip()
    fact = quotee+' quotes'
    verb = '<reply>'
    re = False
    protected = False
    mood = None
    chance = None
    try:
        memory = bucket_runtime_data.last_lines[trigger.sender][quotee]
    except KeyError:
        willie.say("Sorry, I don't remember what %s said about %s" % (quotee, word))
        return
    for line in memory:
        if remove_punctuation(word.lower()) in remove_punctuation(line[0].lower()):
            quotee = line[1]
            line = line[0]
            if line.startswith('\001ACTION'):
                line = line[len('\001ACTION '):-1]
                tidbit = '* %s %s' % (quotee, line)
            else:
                tidbit = '<%s> %s' % (quotee, line)
            result = add_fact(willie, trigger, fact, tidbit, verb, re, protected, mood, chance)
            if result:
                willie.reply("Remembered that %s <reply> %s" % (fact, tidbit))
            return
    willie.say("Sorry, I don't remember what %s said about %s" % (quotee, word))
save_quote.rule = ('$nick', 'remember (.*?) (.*)')
save_quote.priority = 'high'

def delete_factoid(willie, trigger):
    """Delets a factoid"""
    bucket_runtime_data.inhibit_reply = trigger
    was = bucket_runtime_data.what_was_that
    if not trigger.admin:
        was[trigger.sender] = dont_know(willie)
        return
    db = None
    cur = None
    db = connect_db(willie)
    cur = db.cursor()
    try:
        cur.execute('SELECT * FROM bucket_facts WHERE ID = %s;', int(trigger.group(1)))
        results = cur.fetchall()
        if len(results)>1:
            willie.debug('bucket', 'More than one factoid with the same ID?', 'warning')
            willie.debug('bucket', str(results), 'warning')
            willie.say('More than one factoid with the same ID. I refuse to continue.')
            return
        elif len(results) == 0:
            willie.reply('No such factoid')
            return
        cur.execute('DELETE FROM bucket_facts WHERE ID = %s',int(trigger.group(1)))
        db.commit()
    except:
        willie.say("Delete failed! are you sure this is a valid factoid ID?")
        return
    finally:
        db.close()
    line = results[0]
    fact, tidbit, verb = parse_factoid(line)
    willie.say("Okay, %s, forgot that %s %s %s" % (trigger.nick, fact, verb, tidbit))
    
delete_factoid.rule = ('$nick', 'delete #(.*)')
delete_factoid.priority = 'high'

def undo_teach(willie, trigger):
    """Undo teaching factoid"""
    was = bucket_runtime_data.what_was_that
    bucket_runtime_data.inhibit_reply = trigger
    if not trigger.admin:
        was[trigger.sender] = dont_know(willie)
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
        willie.reply('Nothing to undo!')
        return
    db = None
    cur = None
    db = connect_db(willie)
    cur = db.cursor()
    try:
        cur.execute('DELETE FROM bucket_facts WHERE `fact` = %s AND `verb` = %s AND `tidbit` = %s', (fact, verb, tidbit))
        db.commit()
    except:
        willie.say("Undo failed, this shouldn't have happened!")
        return
    finally:
        db.close()
    willie.say("Okay, %s. Forgot that %s %s %s" % (trigger.nick, fact, verb, tidbit))
    del last_teach[trigger.sender]
undo_teach.rule = ('$nick', 'undo last')
undo_teach.priority = 'high'

def inv_give(willie, trigger):
    ''' Called when someone gives us an item '''
    bucket_runtime_data.inhibit_reply = trigger
    was = bucket_runtime_data.what_was_that
    inventory = bucket_runtime_data.inventory
    item = trigger.group(6)
    if item.endswith('\001'):
        item = item[:-1]
    item = item.strip()

    if trigger.group(5) == 'my':
        item = '%s\'s %s' % (trigger.nick, item)
    elif trigger.group(5) == 'your':
        item = '%s\'s %s' % (willie.nick, item)
    elif trigger.group(5) != 'this' and trigger.group(5) is not None:
        item = '%s %s' % (trigger.group(5), item)
        item = re.sub(r'^me ', trigger.nick+' ', item, re.IGNORECASE)
    if trigger.group(3) is not '':
        item = re.sub(r'^his ', '%s\'s ' % trigger.nick, item, re.IGNORECASE)

    item = item.strip()
    dropped = inventory.add(item, trigger.nick, trigger.sender, willie)
    db = connect_db(willie)
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
    db.close()
    result = pick_result(results, willie)
    fact, tidbit, verb = parse_factoid(result)
    tidbit = tidbit.replace('$item', item)
    tidbit = tidbit_vars(tidbit, trigger, False)

    say_factoid(willie, fact, verb, tidbit, True)
    was = result
    return
inv_give.rule = ('((^\001ACTION (gives|hands) $nickname)|^$nickname. (take|have) (this|my|your|.*)) (.*)')
inv_give.priority = 'medium'

def inv_steal(willie, trigger):
    inventory = bucket_runtime_data.inventory
    item = trigger.group(2)
    bucket_runtime_data.inhibit_reply = trigger
    if item.endswith('\001'):
       item = item[:-1]
    if (inventory.remove(item)):
       willie.say('Hey! Give it back, it\'s mine!')
    else:
       willie.say('But I don\'t have any %s' % item)
inv_steal.rule = ('^\001ACTION (steals|takes) $nickname\'s (.*)')
inv_steal.priority = 'medium'

def inv_populate(willie, trigger):
    bucket_runtime_data.inhibit_reply = trigger
    inventory = bucket_runtime_data.inventory
    willie.action('drops all his inventory and picks up random things instead')
    inventory.populate()
inv_populate.rule = ('$nick', 'you need new things(.*|)')
inv_populate.priority = 'medium'

def say_fact(willie, trigger):
    """Response, if needed"""
    query = trigger.group(0)
    was = bucket_runtime_data.what_was_that
    db = None
    cur = None
    results = None


    if query.startswith('\001ACTION'):
        query = query[len('\001ACTION '):]
    addressed = query.lower().startswith(willie.nick.lower()) #Check if our nick was mentioned
    search_term = query.lower().strip() #What we are going to pass to MySql as our search term
    if addressed:
        search_term = search_term[(len(willie.nick)+1):].strip() #Remove our nickname from the search term
    search_term = remove_punctuation(search_term).strip()

    if len(query) < 6 and not addressed:
        return #Ignore factoids shorter than 6 chars when not addressed
    if addressed and len(search_term) is 0:
        return #Ignore 0 length queries when addressed
    if search_term == 'don\'t know' and not addressed:
        return #Ignore "don't know" when not addressed
    if not addressed and trigger.sender in bucket_runtime_data.shut_up:
        return #Don't say anything if not addressed and shutting up
    if search_term == 'shut up' and addressed:
        willie.reply('Okay...')
        bucket_runtime_data.shut_up.append(trigger.sender)
        return
    elif search_term in ['come back', 'unshutup', 'get your sorry ass back here'] and addressed:
        if trigger.sender in bucket_runtime_data.shut_up:
            bucket_runtime_data.shut_up.remove(trigger.sender)
            willie.reply('I\'m back!')
        else:
            willie.reply('Uhm, what? I was here all the time!')
        return
    literal = False
    inhibit = bucket_runtime_data.inhibit_reply
    if search_term.startswith('literal '):
        literal = True
        search_term = search_term[len('literal '):]
    elif search_term == 'what was that' and addressed:
        try:
            factoid_id = was[trigger.sender][0]
            factoid_fact = was[trigger.sender][1]
            factoid_tidbit = was[trigger.sender][2]
            factoid_verb = was[trigger.sender][3]
            willie.say('That was #%s - %s %s %s' % (factoid_id, factoid_fact, factoid_verb, factoid_tidbit))
        except KeyError:
            willie.say('I have no idea')
        return
    elif search_term.startswith('reload') or search_term.startswith('update') or inhibit == trigger:
        return #ignore commands such as reload or update, don't show 'Don't Know' responses for these 

    db = connect_db(willie)
    cur = db.cursor()
    if not addressed:
        factoid_search = None
    else:
        factoid_search = bucket_runtime_data.factoid_search_re.search(search_term)
    try:
        if search_term == 'random quote':
            cur.execute('SELECT * FROM bucket_facts WHERE fact LIKE "% quotes" ORDER BY id ASC;')
        elif factoid_search is not None:
            cur.execute('SELECT * FROM bucket_facts WHERE fact = %s AND tidbit LIKE %s ORDER BY id ASC;', (factoid_search.group(1), '%'+factoid_search.group(2)+'%'))
        else:
            cur.execute('SELECT * FROM bucket_facts WHERE fact = %s ORDER BY id ASC;', search_term)
        results = cur.fetchall()
    except UnicodeEncodeError, e:
        willie.debug('bucket','Warning, database encoding error', 'warning')
        willie.debug('bucket', e, 'warning')
    finally:
        db.close()
    if results == None:
        return
    result = pick_result(results, willie)
    if addressed and result == None and factoid_search is None:
        was[trigger.sender] = dont_know(willie)
        return
    elif factoid_search is not None and result is None:
        willie.reply('Sorry, I could\'t find anything matching your query')
        return
    elif result == None:
        return
            
    fact, tidbit, verb = parse_factoid(result)
    tidbit = tidbit_vars(tidbit, trigger)

    if literal:
        if len(results) == 1:
            result = results[0]
            number = int(result[0])
            fact, tidbit, verb = parse_factoid(result)
            willie.say ("#%d - %s %s %s" % (number, fact, verb, tidbit))
        else:
            willie.reply('just a second, I\'ll make the list!')
            bucket_literal_path = willie.config.bucket.literal_path
            bucket_literal_baseurl = willie.config.bucket.literal_baseurl
            if not bucket_literal_baseurl.endswith('/'):
                bucket_literal_baseurl = bucket_literal_baseurl + '/'
            if not os.path.isdir(bucket_literal_path):
                try:
                    os.makedirs(bucket_literal_path)
                except Exception as e:
                    willie.say("Can't create directory to store literal, sorry!")
                    willie.say(e)
                    return
            if search_term == 'random quote':
                filename = 'quotes'
            else:
                filename = fact.lower()
            f = open(os.path.join(bucket_literal_path, filename+'.txt'), 'w')
            for result in results:
                number = int(result[0])
                fact, tidbit, verb = parse_factoid(result)
                literal_line = "#%d - %s %s %s" % (number, fact, verb, tidbit)
                f.write(literal_line.encode('utf8')+'\n')
            f.close()
            willie.reply('Here you go! %s (%d factoids)' % (bucket_literal_baseurl+web.quote(filename+'.txt'), len(results)))
        result = 'Me giving you a literal link'
    else:
        say_factoid(willie, fact, verb, tidbit, addressed)
    was[trigger.sender] = result
    
    
say_fact.rule = ('(.*)')
say_fact.priority = 'low'

def pick_result(results, willie):
    try:
        if len(results) == 1:
            result = results[0]
        elif len(results) > 1:
            result = results[randint(0, len(results)-1)]
        elif len(results) == 0:
            return None
        if result[3] == '<alias>':
            #Handle alias, recursive!
            db = connect_db(willie)
            cur = db.cursor()
            search_term = result[2].strip()
            try:
                cur.execute('SELECT * FROM bucket_facts WHERE fact = %s;', search_term)
                results = cur.fetchall()
            except UnicodeEncodeError, e:
                willie.debug('bucket','Warning, database encoding error', 'warning')
                willie.debug('bucket',e , 'warning')
            finally:
                db.close()
            result = pick_result(results, willie)
        return result
    except RuntimeError, e:
        willie.debug('bucket', 'RutimeError in pick_result', 'warning')
        willie.debug('bucket', e, 'warning')
        return None

def get_inventory(willie, trigger):
    ''' get a human readable list of the bucket inventory '''

    bucket_runtime_data.inhibit_reply = trigger

    inventory = bucket_runtime_data.inventory
    
    if len(inventory.current_items)==0:
        return willie.action('is carrying nothing')

    readable_item_list = ', '.join(inventory.current_items)

    willie.action('is carrying '+readable_item_list)

get_inventory.rule = ('$nick','inventory')
get_inventory.priority = 'medium'

def connect_db(willie):
    return MySQLdb.connect(host=willie.config.bucket.db_host,
                         user=willie.config.bucket.db_user,
                         passwd=willie.config.bucket.db_pass,
                         db=willie.config.bucket.db_name,
                         charset="utf8",
                         use_unicode=True)

def tidbit_vars(tidbit, trigger, random_item=True):
    ''' Parse in-tidbit vars '''
    #Special in-tidbit vars:
    inventory = bucket_runtime_data.inventory
    tidbit = tidbit.replace('$who', trigger.nick)
    finaltidbit = ''
    for word in tidbit.split(' '):
        if '$giveitem' in word.lower():
            #we have to use replace here in case of punctuation
            word = word.replace('$giveitem', inventory.give_item())
        elif '$newitem' in word.lower():
            word = word.replace('$newitem', inventory.add_random())
        elif '$item' in word.lower() and random_item:
            word = word.replace('$item', inventory.random_item())
        if (len(finaltidbit)>0):
            word = ' ' + word
        finaltidbit = finaltidbit + word
    return finaltidbit

def dont_know(willie):
    ''' Get a Don't Know reply from the cache '''
    cache = bucket_runtime_data.dont_know_cache
    try:
        reply = cache[randint(0, len(cache)-1)]
    except ValueError:
        rebuild_dont_know_cache(willie)
        return dont_know(willie)
    fact, tidbit, verb = parse_factoid(reply)
    say_factoid(willie, fact, verb, tidbit, True)
    return reply

def say_factoid(willie, fact, verb, tidbit, addressed):
    if verb not in bucket_runtime_data.special_verbs:
        willie.say("%s %s %s" % (fact, verb, tidbit))
    elif verb == '<reply>':
        willie.say(tidbit)
    elif verb == '<action>':
        willie.action(tidbit)
    elif verb == '<directreply>' and addressed:
        willie.say(tidbit)
    elif verb == '<directaction>' and addressed:
        willie.action(tidbit)

def remember(willie, trigger):
    ''' Remember last 10 lines of each user, to use in the quote function '''
    memory = bucket_runtime_data.last_lines
    try:
        fifo = deque(memory[trigger.sender][trigger.nick.lower()])
    except KeyError:
        memory[trigger.sender][trigger.nick.lower()]=[] #Initializing the array
        return remember(willie, trigger)
    if len(fifo) == 10:
        fifo.pop()
    fifo.appendleft([trigger.group(0), trigger.nick])
    memory[trigger.sender][trigger.nick.lower()] = fifo
remember.rule = ('(.*)')
remember.priority = 'medium'

def parse_factoid(result):
    return result[1], result[2], result[3]

if __name__ == '__main__':
    print __doc__.strip()
