"""Tests the contest editing features and their models"""

import datetime
import json
from django.test import TestCase, override_settings, Client
from django.core.urlresolvers import reverse
from django.utils import timezone
from beers.models import Beer, Brewery, Contest, Contest_Player, \
                         Unvalidated_Checkin, Contest_Checkin, Contest_Beer, \
                         Contest_Brewery, Player

@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class ContestEditingTestCase(TestCase):
    """Tests the contest editing features"""

    fixtures = ['permissions', 'users']

    def setUp(self):
        player = Player.objects.get(user__username='runner1')
        start_date = timezone.make_aware(datetime.datetime(2018, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2018, 12, 31))
        contest = Contest.objects.create_contest('Contest Base', 
                                                 player, 
                                                 start_date, 
                                                 end_date)


    def tearDown(self):
        Contest.objects.delete()


    def test_successful_add_contest(self):
        """
        Tests whether a new contest can be added, requiring a new name and a 
        valid start and end date.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.post(reverse('contests'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest 1',
                                           'start_date': '2018-01-01',
                                           'end_date': '2018-12-31'}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        contest = Contest.objects.get(name='Contest 1')
        self.assertIsNotNone(contest)
        self.assertEqual(contest.creator.user.username, 'runner1')
        self.assertEqual(contest.start_date, 
                         timezone.make_aware(datetime.datetime(2018, 1, 1)))
        self.assertEqual(contest.end_date, 
                         timezone.make_aware(datetime.datetime(2018, 12, 31)))
        self.assertFalse(contest.active)
        self.assertEqual(int(response.json()['id']), contest.id)


    def test_not_runner_add_contest(self):
        """
        Tests whether there is a failure if a new contest is attempted to be
        added if a user is not a contest runner
        """
        c = Client()
        self.assertTrue(c.login(username='user1', password='password1%'))
        response = c.post(reverse('contests'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest 1',
                                           'start_date': '2018-01-01',
                                           'end_date': '2018-12-31'}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Contest.objects.filter(name='Contest 1').count(), 0)


    def test_no_login_add_contest(self):
        """
        Tests whether there is a failure if a new contest is attempted to be
        added if a user is not logged in
        """
        c = Client()
        response = c.post(reverse('contests'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest 1',
                                           'start_date': '2018-01-01',
                                           'end_date': '2018-12-31'}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Contest.objects.filter(name='Contest 1').count(), 0)


    def test_bad_contest_date_range_add_contest(self):
        """
        Tests whether the contests must end after the current date and have a
        start date before the end date.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.post(reverse('contests'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest 1',
                                           'start_date': '2019-01-01',
                                           'end_date': '2018-12-31'}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Contests.objects.filter(name='Contest 1').count(), 0)


    def test_nonunique_contest_name_add_contest(self):
        """
        Tests whether the contest fails addition when a contest does not have a 
        unique name.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.post(reverse('contests'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest Base',
                                           'start_date': '2019-01-01',
                                           'end_date': '2019-12-31'}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Contest.objects.filter(name='Contest Base').count(), 1)


    def test_successful_add_beer(self):
        """
        Tests whether a new beer can be added to a contest.
        """
        response = c.post(reverse('contest-beers', 
                                  kwargs={'contest_id': 1}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'value': 1}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)


        pass


    def test_not_contest_runner_add_beer(self):
        """
        Tests whether a non-contest runner is prevented from adding a beer.
        """
        pass


    def test_active_add_beer(self):
        """
        Tests whether a contest runner is prevented from adding a beer to an
        active contest.
        """
        pass


    def test_nonunique_add_beer(self):
        """
        Tests whether a beer fails to be added to a contest based on non-unique
        Untappd URLs
        """
        pass


    def test_successful_add_brewery(self):
        """
        Tests whether a brewery can successfully be added to a contest based.
        """
        pass
 
 
    def test_nonunique_add_brewery(self):
        """
        Tests whether a brewery fails to be added to a contest based on non-unique
        Untappd URLs
        """
        pass
 

    def test_active_add_brewery(self):
        """
        Tests whether a contest runner is prevented from adding a brewery to an
        active contest.
        """
        pass
 
 
    def test_not_contest_runner_add_beer(self):
        """
        Tests whether a non-contest runner is prevented from adding a beer.
        """
        pass
 
 
    def test_successful_add_challenge_by_runner(self):
        """
        Tests whether a contest runner can add a challenge
        """
        pass


    def test_successful_add_challenge_by_runner(self):
        """
        Tests whether a contest player can add a challenge
        """
        pass


    def test_active_add_challenge(self):
        """
        Tests whether a player or contest runner cannot add a challenge to an 
        active contest.
        """
        pass
