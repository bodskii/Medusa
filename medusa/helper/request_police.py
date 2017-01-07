# coding=utf-8
# Author: p0psicles
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
# pylint:disable=too-many-lines
"""Request Police Class for monitoring requests responses, and throttling or breaking where needed."""

from ..bs4_parser import BS4Parser
import logging
import datetime


logger = logging.getLogger(__name__)


# Request police Exceptions.
class RequestPoliceException(Exception):
    """Generic Police Exception."""


class PoliceRequestScoreExceeded(RequestPoliceException):
    """Police Request Score Exception."""


class PoliceResponseScoreExceeded(RequestPoliceException):
    """Police Request Score Exception."""


class PoliceReservedDailyExceeded(RequestPoliceException):
    """Police Request Exception for exceeding the reserved daily search limit."""


class RequestPolice(object):
    def __init__(self):
        self.request_limit = 0
        # Keep a counter of the total number of requests for this provider.
        self.request_count = 0
        self.request_score = 0
        self.response_limit = 0
        self.response_count = 0
        self.response_score = 0
        self.api_request_count = 0
        self.api_grab_limit = None
        self.api_hit_limit_cooldown = 86400
        self.api_hit_limit_cooldown_clear = None
        self.next_allowed_request_date = None

        # request_check_newznab_daily_reserved_calls method attributes
        self.api_hit_limit = None # Moved here, as it's currently only used by daily reserve calls.
        self.daily_request_count = 0
        self.daily_reserve_calls = 0
        self.daily_reserve_calls_next_reset_date = None
        # Methods that are run before the request has been send.
        self.enabled_police_request_hooks = []
        # Methods that are run after a response has been received. Using header, status code or content checks.
        self.enabled_police_response_hooks = []

    def request_counter(self):
        self.request_count += 1

    def request_check_nzb_api_limit(self):
        """Request hook for checking if the api hit limit has been breached."""
        logger.info('Running request police request_check_nzb_api_limit.')
        if self.api_hit_limit_cooldown_clear and self.api_hit_limit_cooldown_clear > datetime.datetime.now():
            raise RequestPoliceException('Stil in api hit cooldown.')
        self.request_count = 0
        self.request_score = 0

    def response_check_nzb_api_limit(self, r):
        """Response hook for checking if the api hit limit has been breached."""
        logger.info('Running request police response_check_nzb_api_limit.')
        with BS4Parser(r.text, 'html5lib') as html:
            ## Unfortunatly this is not reliable, and does not represent the
            # try:
            #     if html.caps.limits:
            #         self.api_hit_limit = int(html.caps.limits['max'])
            # except AttributeError:
            #     pass

            try:
                err_desc = html.error.attrs['description']
                if 'Request limit reached' in err_desc:
                    self.request_count = 1
                    self.request_score = 101
                    import re
                    m = re.search('Request limit reached.*\(([0-9]+)/([0-9]+)\)', err_desc)
                    if m:
                        self.api_hit_limit = int(m.group(2))
            except (AttributeError, TypeError):
                pass

            if self.request_score > self.request_limit:
                delta = datetime.timedelta(seconds=self.api_hit_limit_cooldown)
                self.api_hit_limit_cooldown_clear = datetime.datetime.now() + delta
                raise PoliceRequestScoreExceeded(
                    'Breached the providers api hit limit of {api_hit_limit}. '
                    'Cooldown until {cooldown_clear}'
                    .format(api_hit_limit=self.api_hit_limit,
                            cooldown_clear=self.api_hit_limit_cooldown_clear.strftime('%I:%M%p on %B %d, %Y'))
                )

    def request_check_newznab_daily_reserved_calls(self, mode='daily'):
        if self.daily_reserve_calls_next_reset_date:
            if self.daily_reserve_calls_next_reset_date > datetime.datetime.now():
                raise PoliceReservedDailyExceeded(
                    'Stil in daily search reservation cooldown.'
                    'Meaning only daily searches are allowed to hit this provider at this time'
                )
            else:
                # We've reached midnight, let's reset the reset_date and the request_count, as now we need to start over
                self.daily_reserve_calls_next_reset_date = None
                self.self.daily_request_count = 0

        if (mode != 'RSS' and self.api_hit_limit and
                    self.daily_request_count > self.api_hit_limit - self.daily_reserve_calls):
            # Set next reset to coming midnight.
            next_day_time = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
            self.daily_reserve_calls_next_reset_date = datetime.datetime.combine(next_day_time, datetime.time())

            raise PoliceReservedDailyExceeded("We've exceeded the reserved [{reserved_calls}] calls for daily search, "
                                              "we're canceling this request."
                                              .format(reserved_calls=self.daily_reserve_calls))
        self.daily_request_count += 1