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

LOGGER = get_logger(__name__)


@sopel.module.commands('movie', 'imdb')
@sopel.module.example('.movie ThisTitleDoesNotExist', '[MOVIE] Movie not found!', ignore=["[MOVIE] No API key provided."])
@sopel.module.example('.movie Citizen Kane', '[MOVIE] Title: Citizen Kane | Year: 1941 | Rating: 8.4 | Genre: Drama, Mystery | IMDB Link: http://imdb.com/title/tt0033467', ignore=["[MOVIE] No API key provided."])
def movie(bot, trigger):
    """
    Returns some information about a movie, like Title, Year, Rating, Genre and IMDB Link.
    """
    if not trigger.group(2):
        return
    api_key = bot.config.movie.omdb_api_key
    word = trigger.group(2).rstrip()
    uri = "http://www.omdbapi.com/"
    data = requests.get(uri, params={'t': word, 'apikey': api_key}, timeout=30,
                        verify=bot.config.core.verify_ssl).json()
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
                  ' | IMDB Link: http://imdb.com/title/' + data['imdbID']
    bot.say(message)


class MovieSection(StaticSection):
    omdb_api_key = ValidatedAttribute('omdb_api_key', default=NO_DEFAULT)
    """The OMDb API key"""


def configure(config):
    config.define_section('movie', MovieSection, validate=False)
    config.movie.configure_setting(
        'omdb_api_key',
        'Enter your OMDb API key.',
    )


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
