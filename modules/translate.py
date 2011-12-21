#!/usr/bin/env python
# coding=utf-8
"""
translate.py - Jenni Translation Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import re
import web


def translate(phrase, fromlang, tolang):
    url = "http://translate.google.com/translate_a/t?client=t&text={0}"
    url = url.format(phrase)

    if tolang:
        tl = (tolang).encode('utf-8')
    else:
        tl = ('en').encode('utf-8')

    url += "&tl=" + tl

    if fromlang:
        sl = (fromlang).encode('utf-8')
        url += "&sl=" + sl

    results = web.get(url)

    re_sl = re.compile(r'\,"([a-z]{2})"\,\,')
    sl_possible = re_sl.findall(results)
    if sl_possible:
        sl = sl_possible[0]
    results = results.split('"')
    phrase = results[1]

    return (phrase, sl, tl)


def tr(jenni, context):
    """Translates a phrase, with an optional language hint."""

    input, output, phrase = context.groups()

    if input and not output:
        output = input
        input = False

    phrase = phrase.encode('utf-8')
    if (len(phrase) > 350) and (not context.admin):
        return jenni.reply('Phrase must be under 350 characters.')

    good_response = '"{0}" ({1} to {2}, translate.google.com)'
    bad_response = "The {0} to {1} translation failed, sorry!"
    dl = "Error: Source language and translation language can not be the same!"

    result = translate(phrase, input, output)

    if result[1] == result[2]:
        jenni.reply(dl)
        return

    if phrase == result[0]:
        response = (bad_response).format(result[1], result[2])
    else:
        response = (good_response).format(result[0], result[1], result[2])
    jenni.reply(response)

tr.rule = ('$nick', ur'(?:([a-z]{2}) +)?(?:([a-z]{2}) +)?["“](.+?)["”]\? *$')
tr.example = '$nickname: "mon chien"? or $nickname: fr "mon chien"?'
tr.priority = 'low'


def mangle(jenni, input):
    if not input.group(2):
        jenni.reply("What do you want me to mangle?")
        return
    phrase = input.group(2).encode('utf-8')
    for lang in ['fr', 'de', 'es', 'it', 'ja']:
        backup = phrase
        phrase = translate(phrase, 'en', lang)[0]
        if not phrase:
            phrase = backup
            break
        __import__('time').sleep(0.5)

        backup = phrase
        phrase = translate(phrase, lang, 'en')[0]
        if not phrase:
            phrase = backup
            break
        __import__('time').sleep(0.5)

    jenni.reply(phrase or 'ERRORS SRY')
mangle.commands = ['mangle']

if __name__ == '__main__':
    print __doc__.strip()
