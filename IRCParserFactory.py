"""
this will contain the class that sets up the parser/willie class
and stores the config file
this is really just a placeholder until we get actual code in here.
"""
"""
This file has the class for the Factory for the whole she-bang

<copyright stuff>
made by Lior Ramati (FireRogue) copyright 2012
"""

from twisted.internet import reactor, protocol
from IRCParser import Config, IRCParser
from Willie import Willie

class IRCParserFactory(protocol.ClientFactory):
    def __init__(self, config, willie):
        self.config = config
        self.willie = willie
        # I think quitting will reconnection, and we dont want that
        self.hasQuit = False

    def buildProtocol(self, addr):
        p = IRCParser(self.config)
        p.factory = self
        self.willie.protocol = p
        p.willie = self.willie
        return p

    def clientConnectionLost(self, connector, reason):
        if (self.hasQuit):
            reactor.stop() ### quit code
        else:
            connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:" , reason
        print "Please fix this and restart"
        reactor.stop()
        
if __name__ == '__main__':
    willie = Willie()
    config = Config()
    f = IRCParserFactory(config, willie)
    reactor.connectTCP("irc.dftba.net", 6667, f)
    reactor.run()
