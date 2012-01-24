#!/usr/bin/env python
"""
startup.py - Jenni Startup Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import threading, time

def setup(jenni):
    # by clsn
    jenni.data = {}
    refresh_delay = 300.0

    if hasattr(jenni.config, 'refresh_delay'):
        try: refresh_delay = float(jenni.config.refresh_delay)
        except: pass

        def close():
            print "Nobody PONGed our PING, restarting"
            jenni.handle_close()

        def pingloop():
            timer = threading.Timer(refresh_delay, close, ())
            jenni.data['startup.setup.timer'] = timer
            jenni.data['startup.setup.timer'].start()
            # print "PING!"
            jenni.write(('PING', jenni.config.host))
        jenni.data['startup.setup.pingloop'] = pingloop

        def pong(jenni, input):
            try:
                # print "PONG!"
                jenni.data['startup.setup.timer'].cancel()
                time.sleep(refresh_delay + 60.0)
                pingloop()
            except: pass
        pong.event = 'PONG'
        pong.thread = True
        pong.rule = r'.*'
        jenni.variables['pong'] = pong

        # Need to wrap handle_connect to start the loop.
        inner_handle_connect = jenni.handle_connect

        def outer_handle_connect():
            inner_handle_connect()
            if jenni.data.get('startup.setup.pingloop'):
                jenni.data['startup.setup.pingloop']()

        jenni.handle_connect = outer_handle_connect

def startup(jenni, input):
    if hasattr(jenni.config, 'serverpass'):
        jenni.write(('PASS', jenni.config.serverpass))

    if hasattr(jenni.config, 'password'):
        jenni.msg('NickServ', 'IDENTIFY %s' % jenni.config.password)
        __import__('time').sleep(5)

    # Cf. http://swhack.com/logs/2005-12-05#T19-32-36
    for channel in jenni.channels:
        jenni.write(('JOIN', channel))
startup.rule = r'(.*)'
startup.event = '251'
startup.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
