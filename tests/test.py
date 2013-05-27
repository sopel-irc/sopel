from time import sleep
import config, sys

class test():
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

    def executeTests(willie):
        for test in test:
            activeTest = test[0]
            if test[1][0] == 'msg':
                willie.say(config.Channel, test[1][1])
            elif test[1][0] == 'action':
                willie.describe(config.Channel, test[1][1])
            #Wait for result.
            while not willieReply:
                sleep(5)

            if willieReply != test[2]:
                print "Test "+test[0]+" failed."
                print "  Expected output: "+str(test[2])
                print "  Received:        "+str(test[2])
            else: print "Test "+test[0]+" success."
            willieReply = None
        print "Testing complete."
        willie.quit("Testing complete.")
        sys.exit(0)


    def onJoin(willie, trigger):
        if trigger.nick == config.Willie_nick:
            willie.msg('Willie detected.')
            if(activeTest == None): #We're not testing yet
                executeTests(willie) #Start testing

    def onMsg(willie, trigger):
        if trigger.nick != config.Willie_nick:
            return #Message didn't originate from Willie
        if activeTest == None:
            return #No active tests
        else:
            willieReply = ('msg', trigger.msg)

    def onAction(willie, trigger):
        if trigger.nick != config.Willie_nick:
            return #Message didn't originate from Willie
        if activeTest == None:
            return #No active tests
        else:
            willieReply = ('action', trigger.msg)
