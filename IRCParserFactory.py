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

from twisted.words.protocols import ClientFactory

class IRCParserFactory(ClientFactory):
    def __init__(self, config):
        self.config = config
        # I think quitting will reconnection, and we dont want that
        self.hasQuit = False

    def buildProtocol(self, addr):
        p = IRCParser(self.config)
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        if (self.quit):
            ### quit code
        else:
            print "Disconnected from server. Trying to reconnect."
            connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:" , reason
        print "Please fix this and restart"
        reactor.stop()
