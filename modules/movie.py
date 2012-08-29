#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
imdb.py - Willie Movie Information Module
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This module relies on imdbapi.com
"""
try:
    import json
except ImportError:
    import simplejson as json
except ImportError:
    print("Either update to python 2.6+ or install simplejson")
import web

def imdb(jenni, input):
    if not input.group(2):
        return
    word=input.group(2).rstrip()
    word=word.replace(" ", "+")
    uri="http://www.imdbapi.com/?t="+word
    try: u = web.get_urllib_object(uri, 30)
    except:
        jenni.say('IMDBAPI is too slow at the moment :(')
        return 'err'
    data = json.load(u) #data is a Dict containing all the information we need
    u.close()
    if data['Response'] == 'False':
        if 'Error' in data:
            message = '[MOVIE] %s' % data['Error']
        else:
            jenni.debug('movie', 'Got an error from the imdb api, search phrase was %s' % word, 'warning')
            jenni.debug('movie', str(data), 'warning')
            message = '[MOVIE] Got an error from the IMDB api'
    else:
        message = '[MOVIE] Title: ' +data['Title']+ \
                  ' | Year: ' +data['Year']+ \
                  ' | Rating: ' +data['imdbRating']+ \
                  ' | Genre: ' +data['Genre']+ \
                  ' | IMDB Link: http://imdb.com/title/' + data['imdbID']
    jenni.say(message)

imdb.commands = ['movie', 'imdb']
imdb.example = '.movie Movie Title'

if __name__ == '__main__':
    print __doc__.strip()
