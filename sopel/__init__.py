# coding=utf-8
# ASCII ONLY IN THIS FILE THOUGH!!!!!!!
# Python does some stupid bullshit of respecting LC_ALL over the encoding on the
# file, so in order to undo Python's ridiculous fucking idiocy, we have to have
# our own check.

# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, http://embolalia.com
# Copyright 2012, Elad Alfassa <elad@fedoraproject.org>
#
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals, absolute_import, print_function, division

import locale
import sys
loc = locale.getlocale()
if sys.version_info.major > 2:
    if not loc[1] or 'UTF-8' not in loc[1]:
        print('WARNING!!! You are running with a non-UTF8 locale environment '
              'variables (e.g. LC_ALL is set to "C"), which makes Python 3 do '
              'stupid things. If you get strange errors, please set it to '
              'something like "en_US.UTF-8".', file=sys.stderr)


from collections import namedtuple
import os
import re
import time
import traceback
import signal

__version__ = '6.6.5'


def _version_info(version=__version__):
    regex = re.compile(r'(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?.*')
    version_groups = regex.match(__version__).groups()
    major, minor, micro = (int(piece) for piece in version_groups[0:3])
    level = version_groups[3]
    serial = int(version_groups[4] or 0)
    if level == 'a':
        level = 'alpha'
    elif level == 'b':
        level = 'beta'
    elif level == 'rc':
        level = 'candidate'
    elif not level and version_groups[4] is None:
        level = 'final'
    else:
        level = 'alpha'
    version_type = namedtuple('version_info',
                              'major, minor, micro, releaselevel, serial')
    return version_type(major, minor, micro, level, serial)


version_info = _version_info()


def run(config, pid_file, daemon=False):
    import sopel.bot as bot
    import sopel.logger
    from sopel.tools import stderr
    delay = 20
    # Inject ca_certs from config to web for SSL validation of web requests
    if not config.core.ca_certs:
        stderr('Could not open CA certificates file. SSL will not '
               'work properly.')

    def signal_handler(sig, frame):
        if sig == signal.SIGUSR1 or sig == signal.SIGTERM or sig == signal.SIGINT:
            stderr('Got quit signal, shutting down.')
            p.quit('Closing')
    while True:
        try:
            p = bot.Sopel(config, daemon=daemon)
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, signal_handler)
            if hasattr(signal, 'SIGINT'):
                signal.signal(signal.SIGINT, signal_handler)
            sopel.logger.setup_logging(p)
            p.run(config.core.host, int(config.core.port))
        except KeyboardInterrupt:
            break
        except Exception:  # TODO: Be specific
            trace = traceback.format_exc()
            try:
                stderr(trace)
            except Exception:  # TODO: Be specific
                pass
            logfile = open(os.path.join(config.core.logdir, 'exceptions.log'), 'a')
            logfile.write('Critical exception in core')
            logfile.write(trace)
            logfile.write('----------------------------------------\n\n')
            logfile.close()
            os.unlink(pid_file)
            os._exit(1)

        if not isinstance(delay, int):
            break
        if p.hasquit:
            break
        stderr('Warning: Disconnected. Reconnecting in %s seconds...' % delay)
        time.sleep(delay)
    os.unlink(pid_file)
    os._exit(0)
