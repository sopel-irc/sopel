#!/usr/bin/env python
# coding=utf-8
"""
__init__.py - Willie Init Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

import sys, os, time, threading, signal
import bot

class Watcher(object):
    # Cf. http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496735
    def __init__(self):
        self.child = os.fork()
        if self.child != 0:
            self.watch()

    def watch(self):
        try: os.wait()
        except KeyboardInterrupt:
            self.kill()
        sys.exit()

    def kill(self):
        try: os.kill(self.child, signal.SIGKILL)
        except OSError: pass

def run(config):
    if hasattr(config, 'delay'):
        delay = config.delay
    else: 
        delay = 20

    try: Watcher()
    except Exception, e:
        print >> sys.stderr, 'Warning:', e, '(in __init__.py)'

    while True:
        try: 
            p = bot.Willie(config)
            p.run(config.host, config.port)
        except KeyboardInterrupt:
            sys.exit()
        except Exception, e:
            import traceback
            trace = traceback.format_exc()
            try:
                print trace
            except:
                pass
            logfile = open('logs/exceptions.log', 'a') #todo: make not hardcoded
            logfile.write('Critical exception in core')
            logfile.write(e)
            logfile.write(trace)
            logfile.write('----------------------------------------\n\n')
            logfile.close()
            raise e

        if not isinstance(delay, int):
            break

        warning = 'Warning: Disconnected. Reconnecting in %s seconds...' % delay
        try:
            print >> sys.stderr, warning
        except:
            pass
        time.sleep(delay)

if __name__ == '__main__':
    print __doc__
