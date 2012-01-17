#!/usr/bin/env python
# coding=utf-8
"""
calc.py - Jenni Calculator Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re
import web
import string

def c(jenni, input):
    """Google calculator."""
    if not input.group(2):
        return jenni.reply("Nothing to calculate.")
    q = input.group(2).encode('utf-8')
    q = q.replace('\xcf\x95', 'phi') # utf-8 U+03D5
    q = q.replace('\xcf\x80', 'pi') # utf-8 U+03C0
    uri = 'http://www.google.com/ig/calculator?q='
    bytes = web.get(uri + web.urllib.quote(q))
    parts = bytes.split('",')
    answer = [p for p in parts if p.startswith('rhs: "')][0][6:]
    if answer:
        answer = answer.decode('unicode-escape')
        answer = ''.join(chr(ord(c)) for c in answer)
        answer = answer.decode('utf-8')
        answer = answer.replace(u'\xc2\xa0', ',')
        answer = answer.replace('<sup>', '^(')
        answer = answer.replace('</sup>', ')')
        answer = web.decode(answer)
        jenni.say(answer)
    else: jenni.say('Sorry, no result.')
c.commands = ['c', 'calc']
c.example = '.c 5 + 3'

def py(jenni, input):
    """Evaluate a Python expression. Admin-only."""
    if input.admin:
        query = input.group(2).encode('utf-8')
        uri = 'http://tumbolia.appspot.com/py/'
        answer = web.get(uri + web.urllib.quote(query))
        if answer:
            jenni.say(answer)
        else: jenni.reply('Sorry, no result.')
py.commands = ['py']
py.example = '.py len([1,2,3])'

def wa(jenni, input):
    """Wolfram Alpha calculator"""
#     if not input.group(2):
#         return jenni.reply("No search term.")
#     query = input.group(2).encode('utf-8')
#     uri = 'http://tumbolia.appspot.com/wa/'
#     answer = web.get(uri + web.urllib.quote(query.replace('+', '%2B')))
#     if answer:
#         waOutputArray = string.split(answer, ";")
#         if(len(waOutputArray) < 2):
#             jenni.say('[WOLFRAM ERROR]'+answer)
#         else:
#             jenni.say('[WOLFRAM] ' + waOutputArray[0]+" = "+waOutputArray[1])
#         waOutputArray = []
#
#     else: jenni.reply('Sorry, no result.')
    jenni.reply('This function is broken and disabled. see https://github.com/embolalia/jenni/issues/20 for more details.')
wa.commands = ['wa','wolfram']
wa.example = '.wa circumference of the sun * pi'

if __name__ == '__main__':
    print __doc__.strip()
