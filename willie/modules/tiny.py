# coding=utf-8
"""
tiny.py - tinyurl shortener module
Licensed under the Eiffel Forum License 2.
Written by Om Bhallamudi (www.github.com/Ethcelon)
"""
from willie import web
import urllib2

def shorten(url):
	toOpen = 'http://tinyurl.com/api-create.php?url=' + url
	html = web.get_urllib_object(toOpen,10)
	shorturl = str(html.read())
	return shorturl

def shortenIt(willie, trigger):
	if not trigger.group(2):
		return willie.reply("No url.")
	query = trigger.group(2)
	if query.startswith('www'):
		query = 'http://' + query

	try:
		response = web.head(query)
	except ValueError, e:
		return willie.reply('something tells me thats not a real url')
	except urllib2.URLError, e:
		if hasattr(e, 'reason'):
			return willie.reply('Bad url!')
		elif hasattr(e, 'code'):
			return willie.reply('Bad url!')

	shorturl = shorten(query)
	willie.say(shorturl)

shortenIt.commands = ['tiny', 'short']
shortenIt.priority = 'low'
