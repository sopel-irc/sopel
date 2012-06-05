#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
spellcheck.py - Jenni IMDB Module
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
        jenni.say('IMDB is too slow at the moment :(')
        return 'err'
    data = json.load(u) #data is a Dict containing all the information we need
    u.close()
    message = '[IMDB] Title: ' +data['Title']+ \
              ' | Year: ' +data['Year']+ \
              ' | Rating: ' +data['imdbRating']+ \
              ' | Genre: ' +data['Genre']+ \
              ' | Link: http://imdb.com/title/' + data['imdbID']
    jenni.say(message)

imdb.commands = ['imdb', 'movie']
imdb.example = '.imdb Movie Title'

if __name__ == '__main__':
    print __doc__.strip()
