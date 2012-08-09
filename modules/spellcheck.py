#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
spellcheck.py - Jenni spell check Module
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Copyright © 2012, Lior Ramati
Licensed under the Eiffel Forum License 2.

This module relies on pyenchant, on Fedora and Red Hat based system, it can be found in the package python-enchant
"""
import enchant 
def spellcheck(jenni, input):
    if not input.group(2):
        return
    word=input.group(2).rstrip()
    if " " in word:
        jenni.say("One word at a time, please")
        return;
    dictionary = enchant.Dict("en_US")
    dictionary_uk = enchant.Dict("en_GB")
    # I don't want to make anyone angry, so I check both American and British English.
    if dictionary_uk.check(word):
        if dictionary.check(word): jenni.say(word+" is spelled correctly")
        else: jenni.say(word+" is spelled correctly (British)")
    elif dictionary.check(word):
        jenni.say(word+" is spelled correctly (American)")
    else:
        msg = word+" is not spelled correctly. Maybe you want one of these spellings:"
        sugWords = []
        for suggested_word in dictionary.suggest(word):
                sugWords.append(suggested_word)
        for suggested_word in dictionary_uk.suggest(word):
                sugWords.append(suggested_word)
        for suggested_word in set(sorted(sugWords)): # removes duplicates
            msg = msg + " '"+suggested_word+"',"
        jenni.say(msg)
spellcheck.commands = ['spellcheck', 'spell']
spellcheck.example = '.spellcheck stuff'

if __name__ == '__main__':
    print __doc__.strip()
