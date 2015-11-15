# coding=utf-8
"""
etymology.py - Sopel Etymology Module
Copyright 2007-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
from sopel import web
from sopel.module import commands, example, NOLIMIT

etyuri = 'http://etymonline.com/?term=%s'
etysearch = 'http://etymonline.com/?search=%s'

r_definition = re.compile(r'(?ims)<dd[^>]*>.*?</dd>')
r_tag = re.compile(r'<(?!!)[^>]+>')
r_whitespace = re.compile(r'[\t\r\n ]+')

abbrs = [
    'cf', 'lit', 'etc', 'Ger', 'Du', 'Skt', 'Rus', 'Eng', 'Amer.Eng', 'Sp',
    'Fr', 'N', 'E', 'S', 'W', 'L', 'Gen', 'J.C', 'dial', 'Gk',
    '19c', '18c', '17c', '16c', 'St', 'Capt', 'obs', 'Jan', 'Feb', 'Mar',
    'Apr', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'c', 'tr', 'e', 'g'
]
t_sentence = r'^.*?(?<!%s)(?:\.(?= [A-Z0-9]|\Z)|\Z)'
r_sentence = re.compile(t_sentence % ')(?<!'.join(abbrs))


def unescape(s):
    s = s.replace('&gt;', '>')
    s = s.replace('&lt;', '<')
    s = s.replace('&amp;', '&')
    return s


def text(html):
    html = r_tag.sub('', html)
    html = r_whitespace.sub(' ', html)
    return unescape(html).strip()


def etymology(word):
    # @@ <nsh> sbp, would it be possible to have a flag for .ety to get 2nd/etc
    # entries? - http://swhack.com/logs/2006-07-19#T15-05-29

    if len(word) > 25:
        raise ValueError("Word too long: %s[...]" % word[:10])
    word = {'axe': 'ax/axe'}.get(word, word)

    bytes = web.get(etyuri % word)
    definitions = r_definition.findall(bytes)

    if not definitions:
        return None

    defn = text(definitions[0])
    m = r_sentence.match(defn)
    if not m:
        return None
    sentence = m.group(0)

    maxlength = 275
    if len(sentence) > maxlength:
        sentence = sentence[:maxlength]
        words = sentence[:-5].split(' ')
        words.pop()
        sentence = ' '.join(words) + ' [...]'

    sentence = '"' + sentence.replace('"', "'") + '"'
    return sentence + ' - ' + (etyuri % word)


@commands('ety')
@example('word')
def f_etymology(bot, trigger):
    """Look up the etymology of a word"""
    word = trigger.group(2)

    try:
        result = etymology(word)
    except IOError:
        msg = "Can't connect to etymonline.com (%s)" % (etyuri % word)
        bot.msg(trigger.sender, msg)
        return NOLIMIT
    except (AttributeError, TypeError):
        result = None

    if result is not None:
        bot.msg(trigger.sender, result)
    else:
        uri = etysearch % word
        msg = 'Can\'t find the etymology for "%s". Try %s' % (word, uri)
        bot.msg(trigger.sender, msg)
        return NOLIMIT
