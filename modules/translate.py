#!/usr/bin/env python
# coding=utf-8
"""
translate.py - Jenni Translation Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import re, urllib
import web

def translate(text, input, output):
    base = "https://yanovich.net/tr/"
    if output:
        base += (output).encode('utf-8') + "/"
    if input:
        base += (input).encode('utf-8') + "/"
    lang_guess = False
    base = base.replace(" ", "%20")
    json = web.json(web.get(base + text))
    obj = json['data']['translations'][0]
    translation = (web.decode(obj['translatedText'])).encode('utf-8')
    if 'detectedSourceLanguage' in obj:
        lang_guess = obj['detectedSourceLanguage']
    return (translation, lang_guess)


def tr(jenni, context):
    """Translates a phrase, with an optional language hint."""

    input, output, phrase = context.groups()

    if input and not output:
        output = input
        input = False

    phrase = phrase.encode('utf-8')

    if (len(phrase) > 350) and (not context.admin):
        return jenni.reply('Phrase must be under 350 characters.')

    translation, from_lang = translate(phrase, input, output)

    good_response = '"{0}" ({1} to {2}, translate.google.com)'
    bad_response = "The {0} to {1} translation failed, sorry!"

    if input:
        from_lang = (input).encode('utf-8')

    if output:
        to_lang = (output).encode('utf-8')
    else:
        to_lang = 'en'

    if translation == phrase:
        jenni.reply(bad_response.format(from_lang, to_lang))
        return

    jenni.reply(good_response.format(translation, from_lang, to_lang))

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
