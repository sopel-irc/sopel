"""
fuckingweather.py - Willie module for The Fucking Weather
Copyright 2013 Michael Yanovich
Copyright 2013 Edward Powell

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from willie import web
import re

def fucking_weather(willie, trigger):
    text = trigger.group(2)
    if not text:
        willie.reply("INVALID FUCKING PLACE. PLEASE ENTER A FUCKING ZIP CODE, OR A FUCKING CITY-STATE PAIR.")
        return
    text = web.quote(text)
    page = web.get("http://thefuckingweather.com/?where=%s" % (text))
    re_mark = re.compile('<p class="remark">(.*?)</p>')
    results = re_mark.findall(page)
    if results:
        willie.reply(results[0])
    else:
        willie.reply("I CAN'T GET THE FUCKING WEATHER.")
        return willie.NOLIMIT
fucking_weather.commands = ['fucking_weather', 'fw']
fucking_weather.rate = 30
fucking_weather.priority = 'low'
