# coding=utf-8
"""
__init__.py - Willie Init Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

import sys
import os
import time
import threading
import traceback
import bot
import signal
from tools import stderr

__version__ = '3.2.0'


def run(config):
    if config.core.delay is not None:
        delay = config.core.delay
    else:
        delay = 20

    def signal_handler(sig, frame):
        if sig == signal.SIGUSR1 or sig == signal.SIGTERM:
            stderr('Got quit signal, shutting down.')
            p.quit('Closing')
    while True:
        try:
            p = bot.Willie(config)
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, signal_handler)
            p.run(config.core.host, int(config.core.port))
        except KeyboardInterrupt:
            break
        except Exception, e:
            trace = traceback.format_exc()
            try:
                stderr(trace)
            except:
                pass
            logfile = open(os.path.join(config.logdir, 'exceptions.log'), 'a')
            logfile.write('Critical exception in core')
            logfile.write(trace)
            logfile.write('----------------------------------------\n\n')
            logfile.close()
            os.unlink(config.pid_file_path)
            os._exit(1)

        if not isinstance(delay, int):
            break
        if p.hasquit or config.exit_on_error:
            break
        stderr('Warning: Disconnected. Reconnecting in %s seconds...' % delay)
        time.sleep(delay)
    os.unlink(config.pid_file_path)
    os._exit(0)

if __name__ == '__main__':
    print __doc__
