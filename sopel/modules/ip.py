# coding=utf-8
"""
ip.py - Sopel GeoIP Lookup Module
Copyright 2011, Dimitri Molenaars, TyRope.nl,
Copyright © 2013, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""

from __future__ import unicode_literals, absolute_import, print_function, division

import logging
import os
import socket
import tarfile

import geoip2.database

from sopel.config.types import FilenameAttribute, StaticSection
from sopel.module import commands, example
from sopel.tools import web

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


LOGGER = logging.getLogger(__name__)


class GeoipSection(StaticSection):
    GeoIP_db_path = FilenameAttribute('GeoIP_db_path', directory=True)
    """Path of the directory containing the GeoIP database files."""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | GeoIP\\_db\\_path | /home/sopel/GeoIP/ | Path to the GeoIP database files |
    """
    config.define_section('ip', GeoipSection)
    config.ip.configure_setting('GeoIP_db_path',
                                'Path of the GeoIP db files')


def setup(bot):
    bot.config.define_section('ip', GeoipSection)


def _decompress(source, target, delete_after_decompression=True):
    """Decompress just the database from the archive"""
    # https://stackoverflow.com/a/16452962
    tar = tarfile.open(source)
    for member in tar.getmembers():
        if ".mmdb" in member.name:
            member.name = os.path.basename(member.name)
            tar.extract(member, target)
    if delete_after_decompression:
        os.remove(source)


def _find_geoip_db(bot):
    """Find the GeoIP database"""
    config = bot.config
    if config.ip.GeoIP_db_path:
        cities_db = os.path.join(config.ip.GeoIP_db_path, 'GeoLite2-City.mmdb')
        ipasnum_db = os.path.join(config.ip.GeoIP_db_path, 'GeoLite2-ASN.mmdb')
        if (os.path.isfile(cities_db) and os.path.isfile(ipasnum_db)):
            return config.ip.GeoIP_db_path
        else:
            LOGGER.warning(
                'GeoIP path configured but DB not found in configured path')

    if (os.path.isfile(os.path.join(config.core.homedir, 'GeoLite2-City.mmdb')) and
            os.path.isfile(os.path.join(config.core.homedir, 'GeoLite2-ASN.mmdb'))):
        return config.core.homedir
    elif (os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoLite2-City.mmdb')) and
            os.path.isfile(os.path.join('/usr/share/GeoIP', 'GeoLite2-ASN.mmdb'))):
        return '/usr/share/GeoIP'
    elif urlretrieve:
        LOGGER.info('Downloading GeoIP database')
        bot.say('Downloading GeoIP database, please wait...')

        common_params = {'license_key': 'JXBEmLjOzislFnh4', 'suffix': 'tar.gz'}
        base_url = 'https://download.maxmind.com/app/geoip_download'
        geolite_urls = []

        for edition in ['ASN', 'City']:
            geolite_urls.append(
                '{base}?{params}'.format(
                    base=base_url,
                    params=web.urlencode(dict(common_params, **{'edition_id': 'GeoLite2-%s' % edition})),
                )
            )

        for url in geolite_urls:
            LOGGER.debug('GeoIP Source URL: %s', url)
            full_path = os.path.join(config.core.homedir, url.split("/")[-1])
            urlretrieve(url, full_path)
            _decompress(full_path, config.core.homedir)
        return bot.config.core.homedir
    else:
        return False


@commands('iplookup', 'ip')
@example('.ip 8.8.8.8',
         r'\[IP\/Host Lookup\] Hostname: \S*dns\S*\.google\S*( \| .+?: .+?)+ \| ISP: AS15169 \S+',
         re=True,
         ignore='Downloading GeoIP database, please wait...',
         online=True)
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

            # Sanity check - sometimes user information isn't populated yet
            if query is None:
                return bot.say("I don't know that user's host.")
        else:
            return bot.say("I\'m not aware of this user.")

    db_path = _find_geoip_db(bot)
    if db_path is False:
        LOGGER.error('Can\'t find (or download) usable GeoIP database.')
        bot.say('Sorry, I don\'t have a GeoIP database to use for this lookup.')
        return False

    if ':' in query:
        try:
            socket.inet_pton(socket.AF_INET6, query)
        except (OSError, socket.error):  # Python 2/3 compatibility
            return bot.say("[IP/Host Lookup] Unable to resolve IP/Hostname")
    elif '.' in query:
        try:
            socket.inet_pton(socket.AF_INET, query)
        except (socket.error, socket.herror):
            try:
                query = socket.getaddrinfo(query, None)[0][4][0]
            except socket.gaierror:
                return bot.say("[IP/Host Lookup] Unable to resolve IP/Hostname")
    else:
        return bot.say("[IP/Host Lookup] Unable to resolve IP/Hostname")

    city = geoip2.database.Reader(os.path.join(db_path, 'GeoLite2-City.mmdb'))
    asn = geoip2.database.Reader(os.path.join(db_path, 'GeoLite2-ASN.mmdb'))
    host = socket.getfqdn(query)
    try:
        city_response = city.city(query)
        asn_response = asn.asn(query)
    except geoip2.errors.AddressNotFoundError:
        return bot.say("[IP/Host Lookup] The address is not in the database.")

    response = "[IP/Host Lookup] Hostname: %s" % host
    try:
        response += " | Location: %s" % city_response.country.name
    except AttributeError:
        response += ' | Location: Unknown'

    region = city_response.subdivisions.most_specific.name
    response += " | Region: %s" % region if region else ""
    city = city_response.city.name
    response += " | City: %s" % city if city else ""
    isp = "AS" + str(asn_response.autonomous_system_number) + \
          " " + asn_response.autonomous_system_organization
    response += " | ISP: %s" % isp if isp else ""
    bot.say(response)


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
