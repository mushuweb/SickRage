# coding=utf-8
# Author: Mr_Orange <mr_orange@hotmail.it>
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

import re
import traceback

from requests.compat import urljoin
from requests.exceptions import RequestException
from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache, ui

from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TorrentDayProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes
    """TorrentDay Torrent provider"""
    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, 'TorrentDay')

        # Credentials
        self.username = None
        self.password = None

        # URLs
        self.url = 'https://classic.torrentday.com'
        self.urls = {
            'login': urljoin(self.url, '/torrents/'),
            'search': urljoin(self.url, '/V3/API/API.php'),
            'download': urljoin(self.url, '/download.php/')
        }

        # Proper Strings

        # Miscellaneous Options
        self.freeleech = False
        self.enable_cookies = True
        self.cookies = ''

        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1},
                           'RSS': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c14': 1}}

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Cache
        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll IPTorrents every 10 minutes max

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            logger.log('Search mode: {0}'.format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log('Search string: {search}'.format
                               (search=search_string), logger.DEBUG)

                search_string = '+'.join(search_string.split())

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 8, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                if self.freeleech:
                    post_data.update({'free': 'on'})

                try:
                    response = self.get_url(self.urls['search'], post_data=post_data, returns='response')
                    response.raise_for_status()
                except RequestException as msg:
                    logger.log(u'Error while connecting to provider: {error}'.format(error=msg), logger.ERROR)
                    continue

                try:
                    jdata = response.json()
                except ValueError:  # also catches JSONDecodeError if simplejson is installed
                    logger.log('Data returned from provider is not json', logger.ERROR)
                    self.session.cookies.clear()
                    continue

                try:
                    cn = jdata.get('Fs', [dict()])[0].get('Cn', {})
                    torrents = cn.get('torrents', []) if cn else []
                except (AttributeError, TypeError, KeyError, ValueError, IndexError) as e:
                    # If TorrentDay changes their website issue will be opened so we can fix fast
                    # and not wait user notice it's not downloading torrents from there
                    logger.log('TorrentDay response: {0}. Error: {1!r}'.format(jdata, e), logger.ERROR)
                    continue

                if not torrents:
                    logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                    continue

                for torrent in torrents:
                    try:
                        title = re.sub(r'\[.*=.*\].*\[/.*\]', '', torrent['name']) if torrent['name'] else None
                        download_url = urljoin(self.urls['download'], '{}/{}'.format(torrent['id'], torrent['fname'])) if torrent['id'] and torrent['fname'] else None
                        if not all([title, download_url]):
                            continue

                        seeders = int(torrent['seed']) if torrent['seed'] else 1
                        leechers = int(torrent['leech']) if torrent['leech'] else 0

                        # Filter unseeded torrent
                        if seeders < min(self.minseed, 1):
                            if mode != 'RSS':
                                logger.log("Discarding torrent because it doesn't meet the "
                                           "minimum seeders: {0}. Seeders: {1}".format
                                           (title, seeders), logger.DEBUG)
                            continue

                        torrent_size = torrent['size']
                        size = convert_size(torrent_size) or -1

                        item = {
                            'title': title,
                            'link': download_url,
                            'size': size,
                            'seeders': seeders,
                            'leechers': leechers,
                            'pubdate': None,
                            'hash': None,
                        }
                        if mode != 'RSS':
                            logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                       (title, seeders, leechers), logger.DEBUG)

                        items.append(item)
                    except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                        logger.log('Failed parsing provider. Traceback: {0!r}'.format
                                   (traceback.format_exc()), logger.ERROR)
                        continue

            results += items

        return results

    def login(self):
        if dict_from_cookiejar(self.session.cookies).get('uid') and dict_from_cookiejar(self.session.cookies).get('pass'):
            return True

        if self.cookies:
            self.add_cookies_from_ui()
        else:
            logger.log('Failed to login, you must add your cookies in the provider settings', logger.WARNING)
            return False

            login_params = {
                'username': self.username,
                'password': self.password,
                'submit.x': 0,
                'submit.y': 0,
            }

            response = self.get_url(self.urls['login'], post_data=login_params, returns='response')
            if response.status_code != 200:
                logger.log('Unable to connect to provider', logger.WARNING)
                return False

            if re.search('You tried too often', response.text):
                logger.log('Too many login access attempts', logger.WARNING)
                return False

            if (dict_from_cookiejar(self.session.cookies).get('uid') and 
                    dict_from_cookiejar(self.session.cookies).get('uid') in response.text):
                    return True
            else:
                logger.log('Failed to login, check your cookies', logger.WARNING)
                self.session.cookies.clear()
                return False


provider = TorrentDayProvider()
