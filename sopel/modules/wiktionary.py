# coding=utf-8
"""
wiktionary.py - Sopel Wiktionary Module
Copyright 2009, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import requests
from sopel import web
from sopel.module import commands, example

uri = 'https://en.wiktionary.org/w/index.php?title=%s&printable=yes'
r_sup = re.compile(r'<sup[^>]+>.+</sup>')  # Superscripts that are references only, not ordinal indicators, etc...
r_tag = re.compile(r'<[^>]+>')
r_ul = re.compile(r'(?ims)<ul>.*?</ul>')


def text(html):
    text = r_sup.sub('', html)  # Remove superscripts that are references from definition
    text = r_tag.sub('', text).strip()
    text = text.replace('\n', ' ')
    text = text.replace('\r', '')
    text = text.replace('(intransitive', '(intr.')
    text = text.replace('(transitive', '(trans.')
    text = web.decode(text)
    return text


def wikt(word):
    bytes = requests.get(uri % web.quote(word)).text
    bytes = r_ul.sub('', bytes)

    mode = None
    etymology = None
    definitions = {}
    for line in bytes.splitlines():
        if 'id="Etymology"' in line:
            mode = 'etymology'
        elif 'id="Noun"' in line:
            mode = 'noun'
        elif 'id="Verb"' in line:
            mode = 'verb'
        elif 'id="Adjective"' in line:
            mode = 'adjective'
        elif 'id="Adverb"' in line:
            mode = 'adverb'
        elif 'id="Interjection"' in line:
            mode = 'interjection'
        elif 'id="Particle"' in line:
            mode = 'particle'
        elif 'id="Preposition"' in line:
            mode = 'preposition'
        elif 'id="Prefix"' in line:
            mode = 'prefix'
        elif 'id="Suffix"' in line:
            mode = 'suffix'
        # 'id="' can occur in definition lines <li> when <sup> tag is used for references;
        # make sure those are not excluded (see e.g., abecedarian).
        elif ('id="' in line) and ('<li>' not in line):
            mode = None

        elif (mode == 'etmyology') and ('<p>' in line):
            etymology = text(line)
        elif (mode is not None) and ('<li>' in line):
            definitions.setdefault(mode, []).append(text(line))

        if '<hr' in line:
            break
    return etymology, definitions


parts = ('preposition', 'particle', 'noun', 'verb',
         'adjective', 'adverb', 'interjection',
         'prefix', 'suffix')


def format(result, definitions, number=2):
    for part in parts:
        if part in definitions:
            defs = definitions[part][:number]
            result += u' — {}: '.format(part)
            n = ['%s. %s' % (i + 1, e.strip(' .')) for i, e in enumerate(defs)]
            result += ', '.join(n)
    return result.strip(' .,')


@commands('wt', 'define', 'dict')
@example('.wt bailiwick')
def wiktionary(bot, trigger):
    """Look up a word on Wiktionary."""
    word = trigger.group(2)
    if word is None:
        bot.reply('You must tell me what to look up!')
        return

    _etymology, definitions = wikt(word)
    if not definitions:
        # Cast word to lower to check in case of mismatched user input
        _etymology, definitions = wikt(word.lower())
        if not definitions:
            bot.say("Couldn't get any definitions for %s." % word)
            return

    result = format(word, definitions)
    if len(result) < 150:
        result = format(word, definitions, 3)
    if len(result) < 150:
        result = format(word, definitions, 5)

    if len(result) > 300:
        result = result[:295] + '[...]'
    bot.say(result)
