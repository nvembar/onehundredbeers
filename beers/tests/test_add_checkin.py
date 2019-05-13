import datetime
import json
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from unittest import mock
from beers.views.checkin import add_unvalidated_checkin

from beers.models import Beer, Brewery, Contest, Contest_Player, \
                         Unvalidated_Checkin, Contest_Checkin, Contest_Beer, \
                         Contest_Brewery, Player


def outer_mock_parse_checkin(url):
    return AddCheckinTestCase.mock_parse_checkin(url)

@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class AddCheckinTestCase(TestCase):

    CHECKINS = {}

    fixtures = ['permissions',
                'users',
                'contest_tests',
                'unvalidated_checkins',
                ]

    @classmethod
    def mock_parse_checkin(clz, url):
        print("Mock parse: {}".format(url))
        return clz.CHECKINS[url]

    @classmethod
    def setUpTestData(clz):
        checkin = Unvalidated_Checkin()
        checkin.untappd_checkin = 'https://example.com/unvalidated_checkin_new'
        checkin.untappd_title = 'New Untappd Title'
        checkin.untappd_user = 'untapped1'
        checkin.untappd_checkin_date = datetime.datetime.fromisoformat('2016-01-04T00:00:00+00:00')
        checkin.brewery = 'Brewery 7'
        checkin.beer = 'Beer 7'
        checkin.beer_url = 'https://test.com/beers/beer7'
        checkin.brewery_url = 'https://test.com/brewery/brewery7'
        clz.CHECKINS['https://example.com/unvalidated_checkin_new'] = checkin

    @mock.patch('beers.views.checkin.parse_checkin', side_effect=outer_mock_parse_checkin)
    def test_successful_add_checkin(self, mocked_function):
        c = Client()
        untappd_url = 'https://example.com/unvalidated_checkin_new'
        _ = Player.objects.get(user__username='runner1')
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.post(reverse('unvalidated-checkins-json', args=[1]), data={'untappd_url': untappd_url})
        self.assertEqual(response.status_code, 200)
        uv = Unvalidated_Checkin.objects.get(untappd_checkin=untappd_url)
        checkin = AddCheckinTestCase.CHECKINS[untappd_url]
        self.assertEqual(uv.untappd_checkin, untappd_url)
        self.assertEqual(uv.untappd_title, checkin.untappd_title)
        self.assertEqual(uv.contest_player.player.untappd_username, checkin.untappd_user)
        self.assertEqual(uv.brewery, checkin.brewery)
        self.assertEqual(uv.beer, checkin.beer)
        self.assertEqual(uv.beer_url, checkin.beer_url)
        self.assertEqual(uv.brewery_url, checkin.brewery_url)

    @mock.patch('beers.views.checkin.parse_checkin', side_effect=outer_mock_parse_checkin)
    def test_failed_duplicate_url(self, mocked_function):
        c = Client()
        untappd_url = 'https://example.com/unvalidated_1'
        _ = Player.objects.get(user__username='runner1')
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.post(reverse('unvalidated-checkins-json', args=[1]), data={'untappd_url': untappd_url})
        self.assertEqual(response.status_code, 400)

    @mock.patch('beers.api.views.untappd.parse_checkin', side_effect=outer_mock_parse_checkin)
    def test_unvalidated_api_create(self, mocked_function):
        """Tests if the JSON API gets the right values for a single request"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.post(reverse('unvalidated-checkin-list',
                                  kwargs={'contest_id': 1}),
                                  data={'untappd_checkin': 'https://example.com/unvalidated_checkin_new'})
        self.assertEqual(response.status_code, 201)
        checkin = json.loads(response.content)
        print('New checkin url {}'.format(checkin['url']))
        self.assertTrue(checkin['url'].endswith(reverse('unvalidated-checkin-detail', 
                                                kwargs={'id': checkin['id']})))
        self.assertEqual(checkin['player'], 'user1')
        self.assertEqual(checkin['brewery'], 'Brewery 7')
        self.assertEqual(checkin['beer'], 'Beer 7')