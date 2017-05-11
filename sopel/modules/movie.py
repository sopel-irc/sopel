# coding=utf-8
"""
imdb.py - Sopel Movie Information Module
Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This module relies on omdbapi.com
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import requests
import sopel.module
from sopel.logger import get_logger
import re

LOGGER = get_logger(__name__)

yearfmt = re.compile('\((\d{4})\)')

def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.SopelMemory()
    imdb_re = re.compile(r'(imdb\.com\/title\/)(tt[0-9]+)')
    bot.memory['url_callbacks'][imdb_re] = imdb_url

def shutdown(bot):
    del bot.memory['url_callbacks'][imdb_url]

@sopel.module.commands('movie', 'imdb')
@sopel.module.example('.movie ThisTitleDoesNotExist', '[MOVIE] Movie not found!')
@sopel.module.example('.movie Citizen Kane', '[MOVIE] Title: Citizen Kane | Year: 1941 | Rating: 8.4 | Genre: Drama, Mystery | IMDB Link: http://imdb.com/title/tt0033467')
def movie(bot, trigger):
    """
    Returns some information about a movie, like Title, Year, Rating, Genre and IMDB Link.
    """
    if not trigger.group(2):
        return
    word = trigger.group(2).rstrip()
    params={}

    # check to see if there is a year e.g. (2017) at the end
    last = word.split()[-1]
    yrm = yearfmt.match(last)
    if yrm is not None:
        params['y'] = yrm.group(1)
        word = ' '.join(word.split()[:-1])

    params['t'] = word
    bot.say(run_omdb_query(params, bot.config.core.verify_ssl, True))

def run_omdb_query(params, verify_ssl, add_url=True):
    uri = "http://www.omdbapi.com/"
#    data = requests.get(uri, params={'t': word}, timeout=30,
#                        verify=bot.config.core.verify_ssl).json()
    data = requests.get(uri, params=params, timeout=30,
                        verify=verify_ssl).json()
    if data['Response'] == 'False':
        if 'Error' in data:
            message = '[MOVIE] %s' % data['Error']
        else:
            LOGGER.warning(
                'Got an error from the OMDb api, search phrase was %s; data was %s',
                word, str(data))
            message = '[MOVIE] Got an error from OMDbapi'
    else:
        message = '[MOVIE] Title: ' + data['Title'] + \
                  ' | Year: ' + data['Year'] + \
                  ' | Rating: ' + data['imdbRating'] + \
                  ' | Genre: ' + data['Genre'] + \
                  ' | Plot: {}'
        if add_url:
            message += ' | IMDB Link: http://imdb.com/title/' + data['imdbID']

        plot = data['Plot']
        if len(message.format(plot)) > 300:
            cliplen = 300 - (len(message) - 2 + 3) # remove {} add […]
            plot = plot[:cliplen] + '[…]'

    return message.format(plot)

@sopel.module.rule('.*(imdb\.com\/title\/)(tt[0-9]+).*')
def imdb_url(bot, trigger, found_match=None):
    match = found_match or trigger
    bot.say(run_omdb_query({'i': match.group(2)},
                            bot.config.core.verify_ssl, False))

if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
