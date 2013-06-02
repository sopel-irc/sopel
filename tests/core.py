import config, os, subprocess, sys, tempfile, threading
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
    user = None
    nick = None
    ident = None
    host = None
    msg = None

    def __init__(self, chan, user):
        self.channel = chan
        self.user = user
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
        ['GreetPub', ('msg', config.Channel, config.Willie_nick+'!'), ('msg', config.Channel, config.Nickname+': 2')],
        ['GreetPriv', ('msg', config.Willie_nick, config.Willie_nick+'!'), ('msg', config.Nickname, config.Nickname+'!')],
    ]

    def runWillies(self, bot):
        for conf in os.listdir(
                        os.path.join(
                            os.getcwd(),
                            'config')):
            print("Active config: ", conf)
            try:
                p = self.startWillie(conf)
                sleep(15)
            except Exception as e:
                print("Willie failed to run with config file "+conf)
                print e
            else:
                #Willie started.
                if p.poll() is not None:
                    #But didn't stay on.
                    print("Willie stopped before testing could begin, exit code: "+p.returncode)
                    print("Active configuration file: "+conf)
                else:
                    #Willie is still running, start testing.
                    if not self.runTests(bot):
                        print("Failed tests detected on instance with config file "+conf+". Halting tests.")
                        self.stopWillie(conf)
                        break
                    self.stopWillie(conf)
        bot.quit("Testing complete.")
        os._exit(0)

    def runTests(self, bot):
        success = True
        for test in self.tests:
            self.activeTest = test[0]
            sys.stdout.write("Test: "+test[0])
            sys.stdout.write("."*(40-len(test[0])))
            if test[1][0] == 'msg':
                bot.msg(test[1][1], test[1][2])
            elif test[1][0] == 'action':
                bot.describe(test[1][1], test[1][2])
            #Wait for result.
            for i in range(config.timeout+1):
                if not self.willieReply:
                    if i == config.timeout:
                        print "[FAILED]"
                        print "  Operation timed out."
                        break
                    sleep(1)
                else:
                    if self.willieReply != test[2]:
                        print "[FAILED]"
                        print "  Expected output: "+str(test[2])
                        print "  Received:        "+str(self.willieReply)
                        success = False
                    else:
                        print "[SUCCESS]"
                    break
            self.willieReply = None
        return success

    def startWillie(self, conf):
        command = [sys.executable,
                os.path.join(
                    os.path.dirname(os.getcwd()),
                    "willie.py",),
                    "--exit-on-error",
                    "-c",
                    os.path.join(
                        os.getcwd(),
                        "config",
                        conf)]
        for cmd in command:
            print cmd,
        print ''
        p =  subprocess.Popen(
                command,
                shell=True)
        return p

    def stopWillie(self, conf):
        #Unix-only
        p = subprocess.Popen(
                [sys.executable,
                os.path.join(
                    os.path.dirname(os.getcwd()),
                    "willie.py",),
                    "-q",
                    "-c",
                    os.path.join(
                        os.getcwd(),
                        "config",
                        conf)],
                    shell=True)

    def onJoin(self, bot, trigger):
        self.willieReply = ('join', trigger.channel, trigger.user)

    def onMsg(self, bot, trigger):
        if trigger.nick != config.Willie_nick:
            return #Message didn't originate from Willie
        if self.activeTest == None:
            return #No active tests
        else:
            self.willieReply = ('msg', trigger.channel, trigger.msg)

    def onAction(self, bot, trigger):
        if trigger.nick != config.Willie_nick:
            return #Message didn't originate from Willie
        if self.activeTest == None:
            return #No active tests
        else:
            self.willieReply = ('action', trigger.channel, trigger.msg)

class WillieTest(irc.IRCClient):
    """ IRC data handler """
    nickname = config.Nickname
    username = config.Username
    password = config.Server_Password
    realname = 'Willie test unit'
    testUnit = Tests()

    def signedOn(self):
        self.join(config.Channel)
        if config.NS_Password != '':
            self.msg('NickServ', 'IDENTIFY '+config.NS_Password)
        t=threading.Thread(target=self.testUnit.runWillies, args=(self,))
        t.daemon = True
        reactor.callLater(5, t.start)

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

# Boot sequence
if __name__ == '__main__':
    if(config.SSL):
        try:
            from twisted.internet import ssl
            reactor.connectSSL(config.Server, config.Port, testFactory(), ssl.ClientContextFactory)
        except:
            print("Error starting SSL connection. Do you have OpenSSL installed?")
            sys.exit(1)
    else:
        reactor.connectTCP(config.Server, config.Port, testFactory())
    reactor.run()

