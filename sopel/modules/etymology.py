# coding=utf-8
"""
etymology.py - Sopel Etymology Module
Copyright 2007-9, Sean B. Palmer, inamidst.com
Copyright 2018-9, Sopel contributors
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from re import sub
from requests import get
from sopel import web
from sopel.module import commands, example, NOLIMIT
try:
    # Python 2.7
    from HTMLParser import HTMLParser
    h = HTMLParser()
    unescape = h.unescape
except ImportError:
    try:
        # Python 3.4+
        from html import unescape  # https://stackoverflow.com/a/2087433
    except ImportError:
        # Python 3.3... sigh
        from html.parser import HTMLParser
        h = HTMLParser()
        unescape = h.unescape


ETYURI = 'https://www.etymonline.com/word/%s'
ETYSEARCH = 'https://www.etymonline.com/search?q=%s'


def etymology(word):
    # @@ <nsh> sbp, would it be possible to have a flag for .ety to get 2nd/etc
    # entries? - http://swhack.com/logs/2006-07-19#T15-05-29

    if len(word) > 25:
        raise ValueError("Word too long: %s[…]" % word[:10])

    ety = get(ETYURI % web.quote(word))
    if ety.status_code != 200:
        return None

    # Let's find it
    start = ety.text.find("word__defination")
    start = ety.text.find("<p>", start)
    stop = ety.text.find("</p>", start)
    sentence = ety.text[start + 3:stop]
    # Clean up
    sentence = unescape(sentence)
    sentence = sub('<[^<]+?>', '', sentence)

    maxlength = 275
    if len(sentence) > maxlength:
        sentence = sentence[:maxlength]
        words = sentence[:-5].split(' ')
        words.pop()
        sentence = ' '.join(words) + ' […]'

    sentence = '"' + sentence.replace('"', "'") + '"'
    return sentence + ' - ' + (ETYURI % web.quote(word))


@commands('ety')
@example('.ety word')
def f_etymology(bot, trigger):
    """Look up the etymology of a word"""
    word = trigger.group(2)

    try:
        result = etymology(word)
    except IOError:
        msg = "Can't connect to etymonline.com (%s)" % (ETYURI % web.quote(word))
        bot.msg(trigger.sender, msg)
        return NOLIMIT
    except (AttributeError, TypeError):
        result = None
    except ValueError as ve:
        result = str(ve)

    if result is not None:
        bot.msg(trigger.sender, result)
    else:
        uri = ETYSEARCH % web.quote(word)
        msg = 'Can\'t find the etymology for "%s". Try %s' % (word, uri)
        bot.msg(trigger.sender, msg)
        return NOLIMIT
