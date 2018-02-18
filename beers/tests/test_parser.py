"""Tests the ability to parse from Untappd"""

import os
import datetime
from django.test import TestCase, override_settings, Client
from django.core.urlresolvers import reverse
from django.utils import timezone
from beers.utils import untappd
from beers.models import Beer, Brewery, Unvalidated_Checkin

@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class ParserTestCase(TestCase):
    """The tests on the parser"""

    def test_successful_beer_parse(self):
        """Test the ability to read a beer from the Untappd HTML"""
        url = 'file://' + os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'test-data', 
                'untappd',
                'untappd.com-b-saint-arnold-brewing-company-santo-68727')
        beer = untappd.parse_beer(url, followBrewery=False)
        self.assertEqual(beer.name, 'Santo')
        self.assertEqual(beer.brewery, 'Saint Arnold Brewing Company')
        self.assertEqual(beer.untappd_url, url)
        
    def test_successful_brewery_parse(self):
        """Test the ability to read a brewery from the Untappd HTML"""
        url = 'file://' + os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'test-data', 
                'untappd',
                'untappd.com-flyingdog')
        brewery = untappd.parse_brewery(url)
        self.assertEqual(brewery.name, 'Flying Dog Brewery')
        self.assertEqual(brewery.location, 'Frederick, MD United States')
        self.assertEqual(brewery.untappd_url, url)

    def test_successful_checkin_parse(self):
        """Test the ability to read a checkin from the Untappd HTML"""
        url = 'file://' + os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'test-data', 
                'untappd',
                'untappd.com-user-nvembar-checkin-54705629')
        checkin = untappd.parse_checkin(url)
        self.assertEqual(checkin.untappd_title,
            'Navin is drinking a Santo by Saint Arnold Brewing Company on Untappd')
        self.assertEqual(checkin.untappd_checkin, url)
        self.assertEqual(checkin.beer, 'Santo')
        self.assertTrue(checkin.beer_url.endswith(
                    '/b/santo-saint-arnold-brewing-company/68727'))
        self.assertTrue(checkin.brewery_url.endswith('/brewery/2940'))
        self.assertEqual(checkin.rating, 250)
        self.assertEqual(checkin.untappd_checkin_date, 
                         datetime.datetime(2018, 1, 3, hour=1, minute=27, second=32,
                                           tzinfo=datetime.timezone.utc))
