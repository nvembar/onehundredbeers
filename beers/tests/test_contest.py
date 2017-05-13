from django.test import TestCase, TransactionTestCase, override_settings
from django.test import Client
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from beers.models import Contest, Player, Contest_Player, Unvalidated_Checkin, Contest_Checkin
from django.utils import timezone
import datetime
import json

@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class ContestTestCase(TestCase):

    fixtures = [ 'permissions', 'contest_tests', 'unvalidated_checkins']

    def setUp(self):
        pass

    def tearDown(self):
        # Removes all checkin data and resets everyone's point values and beer counts
        # Unvalidated_Checkin.objects.all().delete()
        Contest_Checkin.objects.all().delete()
        Contest_Player.objects.all().update(beer_count=0, beer_points=0,
                    last_checkin_date=None, last_checkin_beer=None,
                    last_checkin_load=timezone.make_aware(datetime.datetime(2016, 1, 1)),)

    def test_successful_checkin_validate(self):
        """Logs in as the correct user and validates a beer"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        uv = Unvalidated_Checkin.objects.get(untappd_title='Unvalidated Checkin 2')
        response = c.post(reverse('update-checkin', kwargs={'contest_id': 1, 'uv_checkin': uv.id,}),
                content_type='application/json',
                data=json.dumps({ 'validate-beer': 'Validate', 'contest-beer': 1,}),
                HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        q = Contest_Checkin.objects.filter(contest_beer__id=1, contest_player__id=1)
        self.assertEqual(q.count(), 1)
        checkin = q.get()
        self.assertEqual(checkin.checkin_points, 1)
        self.assertEqual(checkin.untappd_checkin, 'https://example.com/unvalidated_2')
        self.assertEqual(checkin.contest_player.beer_count, 1)
        self.assertEqual(checkin.contest_player.beer_points, 1)
        self.assertEqual(Unvalidated_Checkin.objects.filter(untappd_title='Unvalidated Checkin 2').count(), 0)

    def test_invalid_checkin_validate(self):
        """Tests what happens when an unvalidated checkin is removed"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        uv = Unvalidated_Checkin.objects.get(untappd_title='Unvalidated Checkin 2')
        response = c.post(reverse('update-checkin', kwargs={'contest_id': 1, 'uv_checkin': uv.id,}),
                content_type='application/json',
                data=json.dumps({ 'remove-beer': 'Remove',}),
                HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        contest_player = Contest_Player.objects.get(id=1)
        self.assertEqual(contest_player.beer_count, 0)
        self.assertEqual(contest_player.beer_points, 0)
        self.assertEqual(Unvalidated_Checkin.objects.filter(untappd_title='Unvalidated Checkin 2').count(), 0)

    def test_unvalidated_api_single(self):
        """Tests if the JSON API gets the right values for a single request"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.get(reverse('unvalidated-checkins-json', kwargs={'contest_id': 1}),
                            { 'slice_start': 2, 'slice_end': 3})
        self.assertEqual(response.status_code, 200)
        checkins = json.loads(response.content)
        self.assertEqual(checkins['page_count'], 1)
        self.assertEqual(checkins['page_index'], 1)
        self.assertEqual(checkins['page_size'], 25)
        self.assertEqual(len(checkins['checkins']), 1)
        checkin = checkins['checkins'][0]
        self.assertEqual(checkin['id'], 3)
        self.assertEqual(checkin['index'], 2)
        self.assertEqual(checkin['player'], 'user1')
        self.assertEqual(checkin['brewery'], 'Brewery 3')
        self.assertEqual(checkin['beer'], 'Beer 3')

    def test_unvalidated_api_many(self):
        """Tests if the JSON API gets the right values for multiple results"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.get(reverse('unvalidated-checkins-json', kwargs={'contest_id': 1}),
                            { 'slice_start': 3, 'slice_end': 6})
        self.assertEqual(response.status_code, 200)
        checkins = json.loads(response.content)
        self.assertEqual(checkins['page_count'], 1)
        self.assertEqual(checkins['page_index'], 1)
        self.assertEqual(checkins['page_size'], 25)
        self.assertEqual(len(checkins['checkins']), 3)
        cid = 4
        cindex = 3
        for checkin in checkins['checkins']:
            self.assertEqual(checkin['id'], cid)
            self.assertEqual(checkin['index'], cindex)
            self.assertEqual(checkin['player'], 'user1')
            self.assertEqual(checkin['brewery'], 'Brewery {}'.format(cid))
            self.assertEqual(checkin['beer'], 'Beer {}'.format(cid))
            cid = cid + 1
            cindex = cindex + 1

    def test_unvalidated_api_past_end(self):
        """Tests if the JSON API returns nothing when the slice goes beyond the end of the page"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.get(reverse('unvalidated-checkins-json', kwargs={'contest_id': 1}),
                            { 'slice_start': 100, 'slice_end': 105})
        self.assertEqual(response.status_code, 200)
        checkins = json.loads(response.content)
        self.assertEqual(checkins['page_count'], 1)
        self.assertEqual(len(checkins['checkins']), 0)
