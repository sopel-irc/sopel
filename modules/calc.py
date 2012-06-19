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

r_result = re.compile(r'(?i)<A NAME=results>(.*?)</A>')
r_tag = re.compile(r'<\S+.*?>')

subs = [
    (' in ', ' -> '),
    (' over ', ' / '),
    (u'£', 'GBP '),
    (u'€', 'EUR '),
    ('\$', 'USD '),
    (r'\bKB\b', 'kilobytes'),
    (r'\bMB\b', 'megabytes'),
    (r'\bGB\b', 'kilobytes'),
    ('kbps', '(kilobits / second)'),
    ('mbps', '(megabits / second)')
]

def calc(jenni, input):
    """Use the Frink online calculator."""
    q = input.group(2)
    if not q:
        return jenni.say('0?')

    query = q[:]
    for a, b in subs:
        query = re.sub(a, b, query)
    query = query.rstrip(' \t')

    precision = 5
    if query[-3:] in ('GBP', 'USD', 'EUR', 'NOK'):
        precision = 2
    query = web.urllib.quote(query.encode('utf-8'))

    uri = 'http://futureboy.us/fsp/frink.fsp?fromVal='
    bytes = web.get(uri + query)
    m = r_result.search(bytes)
    if m:
        result = m.group(1)
        result = r_tag.sub('', result) # strip span.warning tags
        result = result.replace('&gt;', '>')
        result = result.replace('(undefined symbol)', '(?) ')

        if '.' in result:
            try: result = str(round(float(result), precision))
            except ValueError: pass

        if not result.strip():
            result = '?'
        elif ' in ' in q:
            result += ' ' + q.split(' in ', 1)[1]

        jenni.say(q + ' = ' + result[:350])
    else: jenni.reply("Sorry, can't calculate that.")
    jenni.say('Note that .calc is deprecated, consider using .c')
calc.commands = ['calc']
calc.example = '.calc 5 + 3'
calc.rate = 30

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
c.commands = ['c']
c.example = '.c 5 + 3'
c.rate = 30

def py(jenni, input):
    code = input.group(2)
    if not code: return
    query = code.encode('utf-8')
    uri = 'http://tumbolia.appspot.com/py/'
    answer = web.get(uri + web.urllib.quote(query))
    if answer:
        jenni.say(answer)
    else: jenni.reply('Sorry, no result.')
py.commands = ['py']
py.rate = 30

def wa(jenni, input):
    if not input.group(2):
        return jenni.reply("No search term.")
    query = input.group(2).encode('utf-8')
    uri = 'http://tumbolia.appspot.com/wa/'
    answer = web.get(uri + web.urllib.quote(query.replace('+', '%2B')))
    if answer:
        jenni.say(answer)
    else: jenni.reply('Sorry, no result.')
wa.commands = ['wa']
wa.rate = 30

if __name__ == '__main__':
    print __doc__.strip()
