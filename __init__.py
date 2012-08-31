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
import traceback
import bot
import signal

def run(config):
    if hasattr(config, 'delay'):
        delay = config.delay
    else: 
        delay = 20
    def signal_handler(sig, frame):
        if sig == signal.SIGUSR1:
            print >> sys.stderr, 'Got quit signal, shutting down.'
            p.quit('Closing')
    while True:
        try:
            p = bot.Willie(config)
            signal.signal(signal.SIGUSR1, signal_handler)
            p.run(config.host, config.port)
        except KeyboardInterrupt:
            os._exit(0)
        except Exception, e:
            trace = traceback.format_exc()
            try:
                print trace
            except:
                pass
            logfile = open(os.path.join(config.logdir, 'exceptions.log'), 'a') #todo: make not hardcoded
            logfile.write('Critical exception in core')
            logfile.write(trace)
            logfile.write('----------------------------------------\n\n')
            logfile.close()
            os._exit(1)

        if not isinstance(delay, int):
            break
        if p.hasquit:
            os.unlink(config.pid_file_path)
            os._exit(0)
        warning = 'Warning: Disconnected. Reconnecting in %s seconds...' % delay
        try:
            print >> sys.stderr, warning
        except:
            pass
        time.sleep(delay)


if __name__ == '__main__':
    print __doc__
