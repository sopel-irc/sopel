# -*- coding: utf-8 -*-
"""
raw.py - Raw Command Module
http://github.com/tcki
"""

def raw(willie, trigger):
    """.raw <command> - Sends specified text to server"""
    if trigger.admin:
    	command = willie.safe(trigger.group(2))[:510] + '\r\n'
        try:
            willie.writing_lock.acquire()
            willie.log_raw(command)
            willie.send(command)
        finally:
            willie.writing_lock.release()
raw.commands = ['raw']
raw.example = '.raw COMMAND'
raw.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
