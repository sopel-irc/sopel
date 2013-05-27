import sys
import test, config

try:
    from twisted.words.protocols import irc
    from twisted.internet import reactor, protocol
except:
    print "Error loading twisted, are you sure you have twisted installed?"
    sys.exit(1)

class trigger():
    """ A data class to feed to tests """

    channel = None
    nick = None
    ident = None
    host = None
    msg = None

    def __init__(self, chan, user):
        self.channel = chan
        n = user.split('!')
        self.nick = n[0]
        try:
            n = n[1].split('@')
        except:
            self.ident = ''
            self.host = ''
            return
        self.ident = n[0]
        try:
            self.host = n[1]
        except:
            self.host = ''

class WillieTest(irc.IRCClient):
    """ IRC data handler """
    nickname = config.Nickname
    username = config.Username
    password = config.Server_Password
    realname = 'Willie test unit'
    testUnit = test.test()

    def connectionLost(self, reason):
        print "Disconnected: "+str(reason).split(":")[3]

    def signedOn(self):
        self.join(config.Channel)
        if config.NS_Password != '':
            self.msg('NickServ', 'IDENTIFY '+config.NS_Password)
        self.msg(config.Channel, 'Testing unit online.')

    def userJoined(self, user, channel):
        trig = trigger(channel, user)
        self.testUnit.onJoin(trig)

    def privmsg(self, user, channel, message):
        trig = trigger(channel, user)
        trig.msg = message
        self.testUnit.onMsg(trig)

    def action(self, user, channel, data):
        trig = trigger(channel, user)
        trig.msg = data
        self.testUnit.onAction(trig)

class testFactory(protocol.ClientFactory):
    """ TCP Connection handler """
    protocol = WillieTest
    def clientConnectionLost(self, connector, reason):
        print "Connection lost: ", reason
        connector.connect()
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed: ", reason
        reactor.stop()

# Boot sequence
if __name__ == '__main__':
    if(config.SSL):
        try:
            from twisted.internet import ssl
            reactor.connectSSL(config.Server, config.Port, testFactory(), ssl.ClientContextFactory)
        except:
            print ("Error starting SSL connection. Do you have OpenSSL installed?")
            sys.exit(1)
    else:
        reactor.connectTCP(config.Server, config.Port, testFactory())
    reactor.run()

