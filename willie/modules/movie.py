# -*- coding: utf8 -*-
"""
imdb.py - Willie Movie Information Module
Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This module relies on imdbapi.com
"""
import json
import willie.web as web
import willie.module

try:
    import aalib
    import Image
    import cStringIO
    has_aalib = True
except ImportError:
    has_aalib = False

def get_movie_info(bot, trigger):
    if not trigger.group(2):
        return {}
    word = trigger.group(2).rstrip()
    uri = "http://www.imdbapi.com/?t=" + word
    bot.debug(__file__, "retrieving %s" % uri, 'warning')
    u = web.get(uri, 30)
    data = json.loads(u.decode('utf-8'))  # data is a Dict containing all the information we need
    if data['Response'] == 'False':
        if 'Error' in data:
            bot.say('[MOVIE] %s' % data['Error'])
        else:
            bot.debug(__file__, 'Got an error from the imdb api, search phrase was %s' % word, 'warning')
            bot.debug(__file__, str(data), 'warning')
            bot.say('[MOVIE] Got an error from imdbapi')
        return {}
    return data

@willie.module.commands('movie', 'imdb')
@willie.module.example('.movie Movie Title')
def movie(bot, trigger):
    """
    Returns some information about a movie, like Title, Year, Rating, Genre and IMDB Link.
    """
    data = get_movie_info(bot, trigger)
    if not data:
        return

    message = '[MOVIE] Title: ' + data['Title'] + \
              ' | Year: ' + data['Year'] + \
              ' | Rating: ' + data['imdbRating'] + \
              ' | Genre: ' + data['Genre'] + \
              ' | IMDB Link: http://imdb.com/title/' + data['imdbID']
    bot.say(message)

@willie.module.commands('movieposter', 'poster')
@willie.module.example('.movieposter Movie Title')
def movieposter(bot, trigger):
    """
    Prints the poster for the movie as ASCII art.
    """
    if not has_aalib:
        bot.say("[MOVIE] Sorry, I can't print movie posters!")
        return

    data = get_movie_info(bot, trigger)
    if not data:
        return

    if not 'Poster' in data or data['Poster'] == "N/A":
        bot.say('[MOVIE] No movie poster available!')
        return

    screen = aalib.AsciiScreen(width=64, height=25)
    fp = cStringIO.StringIO(web.get(data['Poster']))
    image = Image.open(fp).convert('L').resize(screen.virtual_size)
    screen.put_image((0, 0), image)
    output = screen.render()
    bot.debug(__file__, "\n" + output, 'verbose')
    for line in screen.render().splitlines():
        bot.say(line)
