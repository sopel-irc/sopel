# coding=utf-8
"""GeoIP lookup module"""
# Copyright 2011, Dimitri Molenaars, TyRope.nl,
# Copyright © 2013, Elad Alfassa <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals, absolute_import, print_function, division

import pygeoip
import socket
import os
import gzip

urlretrieve = None
try:
    from urllib import urlretrieve
except ImportError:
    try:
        # urlretrieve has been put under urllib.request in Python 3.
        # It's also deprecated so this should probably be replaced with
        # urllib2.
        from urllib.request import urlretrieve
    except ImportError:
        pass

from sopel.config.types import StaticSection, FilenameAttribute
from sopel.module import commands, example
from sopel.logger import get_logger

LOGGER = get_logger(__name__)


class GeoipSection(StaticSection):
    GeoIP_db_path = FilenameAttribute('GeoIP_db_path', directory=True)
    """Path of the directory containing the GeoIP db files."""


def configure(config):
    config.define_section('ip', GeoipSection)
    config.ip.configure_setting('GeoIP_db_path',
                                'Path of the GeoIP db files')


def setup(bot):
    bot.config.define_section('ip', GeoipSection)


def _decompress(source, target, delete_after_decompression=True):
    """ Decompress a GZip file """
    f_in = gzip.open(source, 'rb')
    f_out = open(target, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    if delete_after_decompression:
        os.remove(source)


def _find_geoip_db(bot):
    """ Find the GeoIP database """
    config = bot.config
    if config.ip.GeoIP_db_path:
        cities_db = os.path.join(config.ip.GeoIP_db_path, 'GeoLiteCity.dat')
        ipasnum_db = os.path.join(config.ip.GeoIP_db_path, 'GeoIPASNum.dat')
        citiesv6_db = os.path.join(config.ip.GeoIP_db_path, 'GeoLiteCityv6.dat')
        ipasnumv6_db = os.path.join(config.ip.GeoIP_db_path, 'GeoIPASNumv6.dat')
        if (os.path.isfile(cities_db) and
                os.path.isfile(ipasnum_db) and
                os.path.isfile(citiesv6_db) and
                os.path.isfile(ipasnumv6_db)):
            return config.ip.GeoIP_db_path
        else:
            LOGGER.warning(
                'GeoIP path configured but DB not found in configured path'
            )
    if (os.path.isfile(os.path.join(bot.config.core.homedir, 'GeoLiteCity.dat')) and
            os.path.isfile(os.path.join(bot.config.core.homedir, 'GeoIPASNum.dat')) and
            os.path.isfile(os.path.join(bot.config.core.homedir, 'GeoLiteCityv6.dat')) and
            os.path.isfile(os.path.join(bot.config.core.homedir, 'GeoIPASNumv6.dat'))):
        return bot.config.core.homedir
    elif (os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoLiteCity.dat')) and
            os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoIPASNum.dat')) and
            os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoLiteCityv6.dat')) and
            os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoIPASNumv6.dat'))):
        return '/usr/share/GeoIP'
    elif urlretrieve:
        LOGGER.warning('Downloading GeoIP database')
        bot.say('Downloading GeoIP database, please wait...')
        geolite_city_url = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz'
        geolite_ASN_url = 'http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz'
        geolite_cityv6_url = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCityv6-beta/GeoLiteCityv6.dat.gz'
        geolite_ASNv6_url = 'http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNumv6.dat.gz'
        geolite_city_filepath = os.path.join(bot.config.core.homedir, 'GeoLiteCity.dat.gz')
        geolite_ASN_filepath = os.path.join(bot.config.core.homedir, 'GeoIPASNum.dat.gz')
        geolite_cityv6_filepath = os.path.join(bot.config.core.homedir, 'GeoLiteCityv6.dat.gz')
        geolite_ASNv6_filepath = os.path.join(bot.config.core.homedir, 'GeoIPASNumv6.dat.gz')
        urlretrieve(geolite_city_url, geolite_city_filepath)
        urlretrieve(geolite_ASN_url, geolite_ASN_filepath)
        urlretrieve(geolite_cityv6_url, geolite_cityv6_filepath)
        urlretrieve(geolite_ASNv6_url, geolite_ASNv6_filepath)
        _decompress(geolite_city_filepath, geolite_city_filepath[:-3])
        _decompress(geolite_ASN_filepath, geolite_ASN_filepath[:-3])
        _decompress(geolite_cityv6_filepath, geolite_cityv6_filepath[:-3])
        _decompress(geolite_ASNv6_filepath, geolite_ASNv6_filepath[:-3])
        return bot.config.core.homedir
    else:
        return False


@commands('iplookup', 'ip')
@example('.ip 8.8.8.8',
         r'[IP/Host Lookup] Hostname: google-public-dns-a.google.com | Location: United States | ISP: AS15169 Google LLC',
         re=True,
         ignore='Downloading GeoIP database, please wait...')
def ip(bot, trigger):
    """IP Lookup tool"""
    # Check if there is input at all
    if not trigger.group(2):
        return bot.reply("No search term.")
    # Check whether the input is an IP or hostmask or a nickname
    decide = ['.', ':']
    if any(x in trigger.group(2) for x in decide):
        # It's an IP/hostname!
        query = trigger.group(2).strip()
    else:
        # Need to get the host for the username
        username = trigger.group(2).strip()
        user_in_botdb = bot.users.get(username)
        if user_in_botdb is not None:
            query = user_in_botdb.host
        else:
            return bot.say("I am not aware of this user.")

    db_path = _find_geoip_db(bot)
    if db_path is False:
        LOGGER.error('Can\'t find (or download) usable GeoIP database')
        bot.say('Sorry, I don\'t have a GeoIP database to use for this lookup')
        return False
    geolite_city_filepath = os.path.join(_find_geoip_db(bot), 'GeoLiteCity.dat')
    geolite_ASN_filepath = os.path.join(_find_geoip_db(bot), 'GeoIPASNum.dat')
    geolite_cityv6_filepath = os.path.join(_find_geoip_db(bot), 'GeoLiteCityv6.dat')
    geolite_ASNv6_filepath = os.path.join(_find_geoip_db(bot), 'GeoIPASNumv6.dat')
    try:
        addr = socket.gethostbyaddr(query)[2][0]
    except socket.herror:
        addr = query
    except socket.gaierror:
        return bot.say('[IP/Host Lookup] Unable to resolve IP/Hostname')
    if ':' not in addr:
        gi_city = pygeoip.GeoIP(geolite_city_filepath)
        gi_org = pygeoip.GeoIP(geolite_ASN_filepath)
    else:
        gi_city = pygeoip.GeoIP(geolite_cityv6_filepath)
        gi_org = pygeoip.GeoIP(geolite_ASNv6_filepath)
    host = socket.getfqdn(query)
    response = "[IP/Host Lookup] Hostname: %s" % host
    try:
        response += " | Location: %s" % gi_city.country_name_by_name(query)
    except AttributeError:
        response += ' | Location: Unknown'
    except socket.gaierror:
        return bot.say('[IP/Host Lookup] Unable to resolve IP/Hostname')

    region_data = gi_city.region_by_name(query)
    try:
        region = region_data['region_code']  # pygeoip >= 0.3.0
    except KeyError:
        region = region_data['region_name']  # pygeoip < 0.3.0
    if region:
        response += " | Region: %s" % region

    try:
        city = gi_city.record_by_name(query)['city']
    except KeyError:
        city = None
    if city:
        response += " | City: %s" % city

    isp = gi_org.org_by_name(query)
    response += " | ISP: %s" % isp

    bot.say(response)


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
