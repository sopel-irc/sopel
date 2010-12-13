#!/usr/bin/env python
# coding=utf-8
"""
translate.py - Jenni Translation Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web

def detect(text): 
    uri = 'http://ajax.googleapis.com/ajax/services/language/detect'
    q = urllib.quote(text)
    bytes = web.get(uri + '?q=' + q + '&v=1.0')
    result = web.json(bytes)
    try: return result['responseData']['language']
    except Exception: return None

def translate(text, input, output): 
    uri = 'http://ajax.googleapis.com/ajax/services/language/translate'
    q = urllib.quote(text)
    pair = input + '%7C' + output
    bytes = web.get(uri + '?q=' + q + '&v=1.0&langpair=' + pair)
    result = web.json(bytes)
    try: return result['responseData']['translatedText'].encode('cp1252')
    except Exception: return None

def tr(jenni, context): 
    """Translates a phrase, with an optional language hint."""
    input, output, phrase = context.groups()

    phrase = phrase.encode('utf-8')

    if (len(phrase) > 350) and (not context.admin): 
        return jenni.reply('Phrase must be under 350 characters.')

    input = input or detect(phrase)
    if not input: 
        err = 'Unable to guess your crazy moon language, sorry.'
        return jenni.reply(err)
    input = input.encode('utf-8')
    output = (output or 'en').encode('utf-8')

    if input != output: 
        msg = translate(phrase, input, output)
        if msg: 
            msg = web.decode(msg) # msg.replace('&#39;', "'")
            msg = '"%s" (%s to %s, translate.google.com)' % (msg, input, output)
        else: msg = 'The %s to %s translation failed, sorry!' % (input, output)

        jenni.reply(msg)
    else: jenni.reply('Language guessing failed, so try suggesting one!')

tr.rule = ('$nick', ur'(?:([a-z]{2}) +)?(?:([a-z]{2}) +)?["“](.+?)["”]\? *$')
tr.example = '$nickname: "mon chien"? or $nickname: fr "mon chien"?'
tr.priority = 'low'

def mangle(jenni, input): 
    phrase = input.group(2).encode('utf-8')
    for lang in ['fr', 'de', 'es', 'it', 'ja']: 
        backup = phrase
        phrase = translate(phrase, 'en', lang)
        if not phrase: 
            phrase = backup
            break
        __import__('time').sleep(0.5)

        backup = phrase
        phrase = translate(phrase, lang, 'en')
        if not phrase: 
            phrase = backup
            break
        __import__('time').sleep(0.5)

    jenni.reply(phrase or 'ERRORS SRY')
mangle.commands = ['mangle']

if __name__ == '__main__': 
    print __doc__.strip()
