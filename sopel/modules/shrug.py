# -*- coding: utf-8 -*-
import sopel.module


@sopel.module.commands('shrug')
def shrug(bot, trigger):
    """Shrugs"""
    bot.say('¯\_(ツ)_/¯')
