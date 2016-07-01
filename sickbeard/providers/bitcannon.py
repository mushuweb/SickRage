# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
#
# This file is part of Medusa.
#
# Medusa is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Medusa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Medusa. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import validators
import traceback

from requests.compat import urljoin

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class BitCannonProvider(TorrentProvider):
    """BitCannon Torrent provider"""
    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, 'BitCannon')

        # Credentials
        self.api_key = None

        # URLs
        self.custom_url = None

        # Proper Strings

        # Miscellaneous Options

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Cache
        self.cache = tvcache.TVCache(self, search_params={'RSS': ['tv', 'anime']})

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        trackers = (self.getURL(self.urls['trackers'], json=True) or {}).get(u'Trackers', [])
        if not trackers:
            logger.log(u'Could not get tracker list from BitCannon, aborting search')
        url = 'http://127.0.0.1:1337/'
        if self.custom_url:
            if not validators.url(self.custom_url):
                logger.log('Invalid custom url set, please check your settings', logger.WARNING)
                return results
            url = self.custom_url
        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                data = self.getURL(url, json=True)
                for item in data or []:
                    title = item.get(u'Title', u'')
                    info_hash = item.get(u'Btih', u'')
                    if not all([title, info_hash]):
                        continue

                    swarm = item.get(u'Swarm', {})
                    seeders = swarm.get(u'Seeders', 0)
                    leechers = swarm.get(u'Leechers', 0)
                    size = item.get(u'Size', -1)

                    #Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        continue

                    # Only build the url if we selected it
                    download_url = 'magnet:?xt=urn:btih:{0}&dn={1}&tr={2}'.format(info_hash, title, self.trackers)

                    item = title, download_url, size, seeders, leechers
                    if mode != 'RSS':
                        logger.log(u"Found result: %s " % title, logger.DEBUG)

                    items[mode].append(item)

            #For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    @staticmethod
    def _check_auth_from_data(data):
        if not all([isinstance(data, dict),
                    data.pop('status', 200) != 401,
                    data.pop('message', '') != 'Invalid API key']):

            logger.log('Invalid api key. Check your settings', logger.WARNING)
            return False

        return True


provider = BitCannonProvider()
