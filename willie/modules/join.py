# -*- coding: utf-8 -*-
"""
join.py - Channel Join Module
http://github.com/tcki
"""

def join(willie, trigger):
    """.join <channel> - joins specified channel"""
    if trigger.admin:
        willie.write(['JOIN'], trigger.group(2))
join.commands = ['join']
join.example = '.join #channel'
join.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
