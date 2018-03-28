# coding=utf-8
"""
etymology.py - Sopel Etymology Module
Copyright 2007-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division
from lxml import html
from requests import get
from sopel.module import commands, example, NOLIMIT

ETYURI = 'https://www.etymonline.com/word/%s'
ETYSEARCH = 'https://www.etymonline.com/search?q=%s'

def etymology(word):
    # @@ <nsh> sbp, would it be possible to have a flag for .ety to get 2nd/etc
    # entries? - http://swhack.com/logs/2006-07-19#T15-05-29

    if len(word) > 25:
        raise ValueError("Word too long: %s[…]" % word[:10])

    ety = get(ETYURI % word)
    if ety.status_code != 200:
        return None
    tree = html.fromstring(ety.text)
    sentence = tree.xpath("//section[contains(@class, 'word__defination')]")[0].text_content()
    maxlength = 275
    if len(sentence) > maxlength:
        sentence = sentence[:maxlength]
        words = sentence[:-5].split(' ')
        words.pop()
        sentence = ' '.join(words) + ' [...]'

    sentence = '"' + sentence.replace('"', "'") + '"'
    return sentence + ' - ' + (ETYURI % word)


@commands('ety')
@example('.ety word')
def f_etymology(bot, trigger):
    """Look up the etymology of a word"""
    word = trigger.group(2)

    try:
        result = etymology(word)
    except IOError:
        msg = "Can't connect to etymonline.com (%s)" % (ETYURI % word)
        bot.msg(trigger.sender, msg)
        return NOLIMIT
    except (AttributeError, TypeError):
        result = None
    except ValueError as ve:
        result = str(ve)

    if result is not None:
        bot.msg(trigger.sender, result)
    else:
        uri = ETYSEARCH % word
        msg = 'Can\'t find the etymology for "%s". Try %s' % (word, uri)
        bot.msg(trigger.sender, msg)
        return NOLIMIT
