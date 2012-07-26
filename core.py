#!/usr/bin/env python
# -*- coding: utf8 -*-

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

class IRCBot(irc.IRCClient):

	def __init__(self, config):
        irc.IRCClient.__init__(self)
        self.realname = config.name
        self.nickname = config.nick
        self.username = config.username
        self.password = config.password
        self.lineRate = 0.05

    def connectionMade(self):
        #Connected, prepare client and bot system, then report connection made to console.
        irc.IRCClient.connectionMade(self)
        self.willie = Willie(self.nickname, self)
        print("connected to localhost")

    def connectionLost(self, reason):
        #WTF? Where'd my connection go?!
        irc.IRCClient.connectionLost(self, reason)
        print("disconnected from localhost:"+str(reason).split(":")[3])

    def signedOn(self):
        self.msg("NickServ", "id password") #we need to load this from config
        self.mode(self.nickname, True, "B")

    def privmsg(self, user, channel, messages):
        if(channel == self.nickname):
            #new PM!

    def userJoined(self, user, channel):
        pass #Do stuff
    def userLeft(self, user, channel):
        pass #Do stuff
    
    def userQuit(self, user, quitMessage):
        pass #Do stuff

    def userKicked(self, kickee, channel, kicker, message):
        pass #Do stuff

    def userRenamed(self, oldname, newname):
        pass #Do stuff

    def irc_unknown(self, prefix, command, params):
        #unknown command recieved, maybe a /whois response?
        pass

class IRCBotFactory(protocol.ClientFactory):
    protocol = IRCBot
    def clientConnectionLost(self, connector, reason):
        connector.connect()
    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

if __name__ == '__main__':
    print "Booting HelpBot"
    f = IRCBotFactory()
    reactor.connectTCP("localhost", 6667, f) #We need to load port and host from config
    reactor.run()


