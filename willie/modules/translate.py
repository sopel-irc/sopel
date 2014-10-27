# coding=utf8
"""
translate.py - Willie Translation Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2013-2014, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals
from willie import web
from willie.module import rule, commands, priority, example
import json
import sys
import random
import os
mangle_lines = {}
if sys.version_info.major >= 3:
    unicode = str


def configure(config):
    """

    | [translate] | example | purpose |
    | ---- | ------- | ------- |
    | research | True | Enable research mode (logging) for .mangle |
    | collect_mangle_lines | False | Collect mangle lines to allow .mangle the last message in the channel |
    """
    if config.option('Configure mangle module', False):
        config.add_section('translate')
        if config.option("Enable research mode"):
            config.translate.research = True
        if config.option("Collect mangle lines"):
            config.translate.collect_mangle_lines = True


def translate(text, in_lang='auto', out_lang='en'):
    raw = False
    if unicode(out_lang).endswith('-raw'):
        out_lang = out_lang[:-4]
        raw = True

    headers = {
        'User-Agent': 'Mozilla/5.0' +
        '(X11; U; Linux i686)' +
        'Gecko/20071127 Firefox/2.0.0.11'
    }

    url_query = {
        "client": "t",
        "sl": in_lang,
        "tl": out_lang,
        "q": text,
    }
    query_string = "&".join(
        "{key}={value}".format(key=key, value=value)
        for key, value in url_query.items()
    )
    url = "http://translate.google.com/translate_a/t?{query}".format(query=query_string)
    result = web.get(url, timeout=40, headers=headers)

    while ',,' in result:
        result = result.replace(',,', ',null,')
        result = result.replace('[,', '[null,')

    data = json.loads(result)

    if raw:
        return str(data), 'en-raw'

    try:
        language = data[2]  # -2][0][0]
    except:
        language = '?'

    return ''.join(x[0] for x in data[0]), language


@rule(u'$nickname[,:]\s+(?:([a-z]{2}) +)?(?:([a-z]{2}|en-raw) +)?["“](.+?)["”]\? *$')
@example('$nickname: "mon chien"? or $nickname: fr "mon chien"?')
@priority('low')
def tr(bot, trigger):
    """Translates a phrase, with an optional language hint."""
    in_lang, out_lang, phrase = trigger.groups()

    if (len(phrase) > 350) and (not trigger.admin):
        return bot.reply('Phrase must be under 350 characters.')

    in_lang = in_lang or 'auto'
    out_lang = out_lang or 'en'

    if in_lang != out_lang:
        msg, in_lang = translate(phrase, in_lang, out_lang)
        if sys.version_info.major < 3 and isinstance(msg, str):
            msg = msg.decode('utf-8')
        if msg:
            msg = web.decode(msg)  # msg.replace('&#39;', "'")
            msg = '"%s" (%s to %s, translate.google.com)' % (msg, in_lang, out_lang)
        else:
            msg = 'The %s to %s translation failed, sorry!' % (in_lang, out_lang)

        bot.reply(msg)
    else:
        bot.reply('Language guessing failed, so try suggesting one!')


@commands('translate', 'tr')
@example('.tr :en :fr my dog', '"mon chien" (en to fr, translate.google.com)')
@example('.tr היי', '"Hi" (iw to en, translate.google.com)')
@example('.tr mon chien', '"my dog" (fr to en, translate.google.com)')
def tr2(bot, trigger):
    """Translates a phrase, with an optional language hint."""
    command = trigger.group(2)

    if not command:
        return bot.reply('You did not give me anything to translate')

    def langcode(p):
        return p.startswith(':') and (2 < len(p) < 10) and p[1:].isalpha()

    args = ['auto', 'en']

    for i in range(2):
        if ' ' not in command:
            break
        prefix, cmd = command.split(' ', 1)
        if langcode(prefix):
            args[i] = prefix[1:]
            command = cmd
    phrase = command

    if (len(phrase) > 350) and (not trigger.admin):
        return bot.reply('Phrase must be under 350 characters.')

    src, dest = args
    if src != dest:
        msg, src = translate(phrase, src, dest)
        if sys.version_info.major < 3 and isinstance(msg, str):
            msg = msg.decode('utf-8')
        if msg:
            msg = web.decode(msg)  # msg.replace('&#39;', "'")
            msg = '"%s" (%s to %s, translate.google.com)' % (msg, src, dest)
        else:
            msg = 'The %s to %s translation failed, sorry!' % (src, dest)

        bot.reply(msg)
    else:
        bot.reply('Language guessing failed, so try suggesting one!')


def get_random_lang(long_list, short_list):
    random_index = random.randint(0, len(long_list) - 1)
    random_lang = long_list[random_index]
    if random_lang not in short_list:
        short_list.append(random_lang)
    else:
        return get_random_lang(long_list, short_list)
    return short_list


@commands('mangle', 'mangle2')
def mangle(bot, trigger):
    """Repeatedly translate the input until it makes absolutely no sense."""
    global mangle_lines
    long_lang_list = ['fr', 'de', 'es', 'it', 'no', 'he', 'la', 'ja', 'cy', 'ar', 'yi', 'zh', 'nl', 'ru', 'fi', 'hi', 'af', 'jw', 'mr', 'ceb', 'cs', 'ga', 'sv', 'eo', 'el', 'ms', 'lv']
    lang_list = []
    for __ in range(0, 8):
        lang_list = get_random_lang(long_lang_list, lang_list)
    random.shuffle(lang_list)
    if trigger.group(2) is None:
        try:
            phrase = (mangle_lines[trigger.sender.lower()], '')
        except:
            bot.reply("What do you want me to mangle?")
            return
    else:
        phrase = (trigger.group(2).strip(), '')
    if phrase[0] == '':
        bot.reply("What do you want me to mangle?")
        return
    if bot.config.has_section('translate') and bot.config.translate.research:
        research_logfile = open(os.path.join(bot.config.logdir, 'mangle.log'), 'a')
        research_logfile.write('Phrase: %s\n' % str(phrase))
        research_logfile.write('Lang_list: %s\n' % lang_list)
    for lang in lang_list:
        backup = phrase
        try:
            phrase = translate(phrase[0], 'en', lang)
        except:
            phrase = False
        if not phrase:
            phrase = backup
            break

        try:
            phrase = translate(phrase[0], lang, 'en')
        except:
            phrase = backup
            continue

        if bot.config.has_section('translate') and bot.config.translate.research:
            research_logfile.write('-> %s\n' % str(phrase))
        if not phrase:
            phrase = backup
            break
    if bot.config.has_section('translate') and bot.config.translate.research:
        research_logfile.write('->[FINAL] %s\n' % str(phrase))
        research_logfile.write('----------------------------\n\n\n')
        research_logfile.close()
    bot.reply(phrase[0])


@rule('(.*)')
@priority('low')
def collect_mangle_lines(bot, trigger):
    if bot.config.has_section('translate') and bot.config.translate.collect_mangle_lines:
        global mangle_lines
        mangle_lines[trigger.sender.lower()] = "%s said '%s'" % (trigger.nick, (trigger.group(0).strip()))


if __name__ == "__main__":
    from willie.test_tools import run_example_tests
    run_example_tests(__file__)
