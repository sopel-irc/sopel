# coding=utf-8

"""
spellcheck.py - Sopel spelling checker module
Copyright © 2016, Alan Huang
Copyright © 2019, dgw
Licensed under the Eiffel Forum License 2.
https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division
import aspell
from sopel.module import commands, example, require_admin


def setup(bot):
    bot.memory['spellcheck_pending_adds'] = []


def shutdown(bot):
    try:
        del bot.memory['spellcheck_pending_adds']
    except KeyError:
        pass


@commands('scadd')
@require_admin('I only trust admins to add words.')
def add_command(bot, trigger):
    """
    Stage a word to be added to the bot's personal dictionary.
    """
    bot.memory['spellcheck_pending_adds'].append(trigger.group(2))
    bot.say('Added "{0}". (To review pending words, use {1}scpending. '
            'To commit changes, use {1}scsave.)'
            .format(trigger.group(2), bot.config.core.help_prefix))


@commands('scpending')
def pending_command(bot, trigger):
    """
    List words that are waiting to be saved to the bot's personal dictionary.
    """
    bot.say('Ready to save: "{0}". (To remove a word before saving, use {1}scdel '
            'word, or clear the list with {1}scclear.)'
            .format('", "'.join(bot.memory['spellcheck_pending_adds']),
                    bot.config.core.help_prefix))


@commands('scdel')
@require_admin('Only admins may cancel a word-list addition.')
def del_command(bot, trigger):
    """
    Remove a word from the list of pending personal dictionary additions.
    """
    try:
        bot.memory['spellcheck_pending_adds'].remove(trigger.group(2))
    except ValueError:
        bot.say('Not in pending list: "{0}"'.format(trigger.group(2)))
    else:
        remaining = len(bot.memory['spellcheck_pending_adds'])
        if remaining == 0:
            remaining = 'No words'
        elif remaining == 1:
            remaining = 'One word'
        else:
            remaining = '{0} words'.format(remaining)
        bot.say('Removed "{0}". ({1} remaining in pending list.)'
                .format(trigger.group(2), remaining))


@commands('scclear')
@require_admin('Only admins may clear the pending word list.')
def clear_command(bot, trigger):
    """
    Clear the list of words pending addition to the bot's personal dictionary.
    """
    count = len(bot.memory['spellcheck_pending_adds'])
    del bot.memory['spellcheck_pending_adds'][:]  # list.clear() is py3.3+ only :(
    bot.say('Cleared pending word list ({0} items).'.format(count))


@commands('scsave')
@require_admin('Only admins may commit word-list changes.')
def save_command(bot, trigger):
    """
    Commit pending changes to the bot's personal dictionary. This action cannot be undone,
    except by manually editing the aspell dictionary file.
    """
    for word in bot.memory['spellcheck_pending_adds']:
        if word != word.strip() and trigger.group(2) != 'force':
            bot.say('"{0} contains extra whitespace. Amend the pending list with '
                    '{1}scdel/{1}scadd, or force saving anyway with {1}scsave force.'
                    .format(word, bot.config.core.help_prefix))
            return
    c = aspell.Speller('lang', 'en')
    for word in bot.memory['spellcheck_pending_adds']:
        c.addtoPersonal(word)
    c.saveAllwords()
    bot.say('Saved {0} pending words to my word list.'
            .format(len(bot.memory['spellcheck_pending_adds'])))
    del bot.memory['spellcheck_pending_adds'][:]  # list.clear() is py3.3+ only :(


def check_multiple(bot, words):
    mistakes = []

    c = aspell.Speller('lang', 'en')
    for word in words:
        if not c.check(word):
            mistakes.append(word)

    if len(mistakes) == 0:
        bot.say("Nothing seems to be misspelled.")
    else:
        bot.say('The following word(s) seem to be misspelled: {0}'.format(', '.join(['"{0}"'.format(w) for w in mistakes])))


def check_one(bot, word):
    c = aspell.Speller('lang', 'en')
    if c.check(word):
        bot.say("I don't see any problems with that word.")
        return
    else:
        suggestions = c.suggest(word)[:5]

    if len(suggestions) == 0:
        bot.say("That doesn't seem to be correct.")
    else:
        bot.say("That doesn't seem to be correct. Try {0}.".format(', '.join(['"{0}"'.format(s) for s in suggestions])))


@commands('spellcheck', 'spell', 'sc')
@example('.spellcheck wrod')
def spellchecker(bot, trigger):
    """
    Checks if the given word is spelled correctly, and suggests corrections.
    """
    if not trigger.group(2):
        bot.say('What word am I checking?')
        return

    if trigger.group(2) == bot.nick:
        bot.say('Hey, that\'s my name! Nothing wrong with it.')
        return

    words = trigger.group(2).split(None)

    if len(words) > 1:
        check_multiple(bot, words)
    else:
        check_one(bot, trigger.group(2))
