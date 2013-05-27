import config, sys
from time import sleep
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

class Tests():
    """ Test handler """
    activeTest = None
    willieReply = None

    # List of tests to be executed,
    # Test syntax:
    # ['Name', (msg|action, target, message), (msg|action|raw, target, expected output (regex-enabled))]
    # To use trigger values, call as %trigger.value%
    tests = [
        #TODO: Automatically generate this list
        ['GreetPriv', ('msg', config.Willie_nick, config.Willie_nick+'!'), ('msg', config.Nickname, config.Nickname+'!')],
        ['GreetPub', ('msg', config.Channel, config.Willie_nick+'!'), ('msg', config.Channel, config.Nickname+'!')],
    ]

    def executeTests(self, willie):
        for test in self.tests:
            self.activeTest = test[0]
            print "Test: "+test[0]
            if test[1][0] == 'msg':
                willie.say(test[1][1], test[1][2])
            elif test[1][0] == 'action':
                willie.describe(test[1][1], test[1][2])
            #Wait for result.
            while not self.willieReply:
                #Bad, BAAAAAAAAAAAAAAD...
                sleep(5)

            if self.willieReply != test[2]:
                print "  FAILED"
                print "  Expected output: "+str(test[2])
                print "  Received:        "+str(test[2])
            else: print "  SUCCESS"
            self.willieReply = None
        print "Testing complete."
        willie.quit("Testing complete.")
        #TODO exit Willie
        sys.exit(0)

    def onJoin(self, willie, trigger):
        if trigger.nick == config.Willie_nick:
            if(self.activeTest == None): #We're not testing yet
                self.executeTests(willie) #Start testing

    def onMsg(self, willie, trigger):
        if trigger.nick != config.Willie_nick:
            return #Message didn't originate from Willie
        if self.activeTest == None:
            return #No active tests
        else:
            self.willieReply = ('msg', trigger.msg)

    def onAction(self, willie, trigger):
        if trigger.nick != config.Willie_nick:
            return #Message didn't originate from Willie
        if self.activeTest == None:
            return #No active tests
        else:
            self.willieReply = ('action', trigger.msg)

class WillieTest(irc.IRCClient):
    """ IRC data handler """
    nickname = config.Nickname
    username = config.Username
    password = config.Server_Password
    realname = 'Willie test unit'
    testUnit = Tests()

    def connectionLost(self, reason):
        print "Disconnected: "+str(reason).split(":")[3]

    def signedOn(self):
        self.join(config.Channel)
        if config.NS_Password != '':
            self.msg('NickServ', 'IDENTIFY '+config.NS_Password)
        #TODO: Launch Willie

    def userJoined(self, user, channel):
        trig = trigger(channel, user)
        self.testUnit.onJoin(self, trig)

    def privmsg(self, user, channel, message):
        trig = trigger(channel, user)
        trig.msg = message
        self.testUnit.onMsg(self, trig)

    def action(self, user, channel, data):
        trig = trigger(channel, user)
        trig.msg = data
        self.testUnit.onAction(self, trig)

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

