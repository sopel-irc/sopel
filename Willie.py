"""
Willie! either non-existant or the API and bot and whatnot, but doesnt deal
with connection crap. just gets told when stuff is going on by IRCParser (if
Willie is a standalone class. it gets its own copy of the config file in case
anything needs to be changed on the fly, but also a pointer to the factory's
file in case it needs to change anything for all times Willie is run.
"""
## this is the trigger object in the API
class Trigger(object):
    pass
    
## this is the API modules connect to
class Willie(object):
    def __init__(self):
        pass
        
    def PM(self, sender, message):
        self.msg(sender, 'You PMed me!')
        if message == ".quit":
            self.protocol.quit("bye!")
    
    ## replaces self.protocol.msg with self.msg
    def msg(self, user, message, length=None):
        self.protocol.msg(user, message, length=None)
