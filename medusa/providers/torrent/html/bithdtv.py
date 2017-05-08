# coding=utf-8

"""Provider code for Bithdtv."""

from __future__ import unicode_literals

import logging
import traceback

from medusa import tv
from medusa.bs4_parser import BS4Parser
from medusa.helper.common import (
    convert_size,
    try_int,
)
from medusa.logger.adapters.style import BraceAdapter
from medusa.providers.torrent.torrent_provider import TorrentProvider

from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

log = BraceAdapter(logging.getLogger(__name__))
log.logger.addHandler(logging.NullHandler())


class BithdtvProvider(TorrentProvider):
    """BIT-HDTV Torrent provider."""

    def __init__(self):
        """Initialize the class."""
        super(self.__class__, self).__init__('BITHDTV')

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0
        self.freeleech = True

        # URLs
        self.url = 'https://www.bit-hdtv.com/'
        self.urls = {
            'login': urljoin(self.url, 'takelogin.php'),
            'search': urljoin(self.url, 'torrents.php'),
        }

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        # Miscellaneous Options

        # Torrent Stats

        # Cache
        self.cache = tv.Cache(self, min_time=10)  # Only poll BitHDTV every 10 minutes max

    def search(self, search_strings, age=0, ep_obj=None):
        """
        Search a provider and parse the results.

        :param search_strings: A dict with mode (key) and the search value (value)
        :param age: Not used
        :param ep_obj: Not used
        :returns: A list of search results (structure)
        """
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            'cat': 10,
        }

        for mode in search_strings:
            log.debug('Search mode: {0}', mode)

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    log.debug('Search string: {search}',
                              {'search': search_string})
                search_params['search'] = search_string

                if mode == 'Season':
                    search_params['cat'] = 12
                response = self.get_url(self.urls['search'], params=search_params, returns='response')
                if not response or not response.text:
                    log.debug('No data returned from provider')
                    continue

                results += self.parse(response.text, mode)

        return results

    def parse(self, data, mode):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A list of items found
        """
        items = []

        with BS4Parser(data, 'html.parser') as html:  # Use html.parser, since html5parser has issues with this site.
            tables = html('table', width='750')  # Get the last table with a width of 750px.
            torrent_table = tables[-1] if tables else []
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one release is found
            if len(torrent_rows) < 2:
                log.debug('Data returned from provider does not contain any torrents')
                return items

            # Skip column headers
            for row in torrent_rows[1:]:
                cells = row('td')
                if len(cells) < 3:
                    # We must have cells[2] because it containts the title
                    continue

                if self.freeleech and not row.get('bgcolor'):
                    continue

                try:
                    title = cells[2].find('a')['title'] if cells[2] else None
                    download_url = urljoin(self.url, cells[0].find('a')['href']) if cells[0] else None
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[8].get_text(strip=True)) if len(cells) > 8 else 1
                    leechers = try_int(cells[9].get_text(strip=True)) if len(cells) > 9 else 0

                    # Filter unseeded torrent
                    if seeders < min(self.minseed, 1):
                        if mode != 'RSS':
                            log.debug("Discarding torrent because it doesn't meet the"
                                      " minimum seeders: {0}. Seeders: {1}",
                                      title, seeders)
                        continue

                    torrent_size = cells[6].get_text(' ') if len(cells) > 6 else None
                    size = convert_size(torrent_size) or -1

                    item = {
                        'title': title,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers,
                        'pubdate': None,
                    }
                    if mode != 'RSS':
                        log.debug('Found result: {0} with {1} seeders and {2} leechers',
                                  title, seeders, leechers)

                    items.append(item)
                except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                    log.error('Failed parsing provider. Traceback: {0!r}',
                              traceback.format_exc())

        return items

    def login(self):
        """Login method used for logging in before doing search and torrent downloads."""
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='response')
        if not response or not response.text:
            log.warning('Unable to connect to provider')
            self.session.cookies.clear()
            return False

        if '<h2>Login failed!</h2>' in response.text:
            log.warning('Invalid username or password. Check your settings')
            self.session.cookies.clear()
            return False

        return True


provider = BithdtvProvider()
