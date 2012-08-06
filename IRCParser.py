"""
This will contain the class that inherits irc.IRCClient and actually talks to
the server. I havent decided whether or not this will be Willie, or a middleman
between Willie and the server that helps with administrative crap and just
seperates the protocol stuff from the bot stuff for ease of editing
gets data from config, but doesnt store it (assuming Willie isn't folded in)
this is really just a placeholder until we get actual code in here.
"""

from twisted.words.protocols import irc

## just a temp thing for testing purposes
class Config(object):
    def __init__(self):
        self.nickname = "TwistedWillie_Test"
        self.channels = ["#test"]
        
class IRCParser(irc.IRCClient):
    def __init__(self, config):
        self.nickname = config.nickname
        
    def signedOn(self):
        for channel in self.factory.config.channels:
            self.join(channel)
    
    def privmsg(self, user, channel, message):
        if (self.nickname == channel):
            self.willie.PM(user.split('!', 1)[0], message)
            
    def quit(self, message):
        self.factory.hasQuit = True
        irc.IRCClient.quit(self, message)
        
        
            
    
if __name__ == '__main__':
    c = Config()

