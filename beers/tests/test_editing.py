"""Tests the contest editing features and their models"""

import datetime
import json
import unittest
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from beers.models import Beer, Brewery, Contest, Contest_Player, \
                         Unvalidated_Checkin, Contest_Checkin, Contest_Beer, \
                         Contest_Brewery, Contest_Bonus, Player

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
        Contest.objects.all().delete()


    def test_successful_add_contest(self):
        """
        Tests whether a new contest can be added, requiring a new name and a 
        valid start and end date.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        start_date = timezone.make_aware(datetime.datetime(2018, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2018, 12, 31))
        response = c.post(reverse('contest-list'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest 1',
                                           'start_date': start_date.isoformat(),
                                           'end_date': end_date.isoformat()}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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
        start_date = timezone.make_aware(datetime.datetime(2018, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2018, 12, 31))
        response = c.post(reverse('contest-list'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest 1',
                                           'start_date': start_date.isoformat(),
                                           'end_date': end_date.isoformat()}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Contest.objects.filter(name='Contest 1').count(), 0)


    def test_no_login_add_contest(self):
        """
        Tests whether there is a failure if a new contest is attempted to be
        added if a user is not logged in
        """
        c = Client()
        start_date = timezone.make_aware(datetime.datetime(2018, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2018, 12, 31))
        response = c.post(reverse('contest-list'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest 1',
                                           'start_date': start_date.isoformat(),
                                           'end_date': end_date.isoformat()}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Contest.objects.filter(name='Contest 1').count(), 0)


    def test_bad_contest_date_range_add_contest(self):
        """
        Tests whether the contests must end after the current date and have a
        start date before the end date.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        start_date = timezone.make_aware(datetime.datetime(2019, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2018, 12, 31))
        response = c.post(reverse('contest-list'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest 1',
                                           'start_date': start_date.isoformat(),
                                           'end_date': end_date.isoformat()}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Contest.objects.filter(name='Contest 1').count(), 0)
        self.assertIn('non_field_errors', response.json())


    def test_nonunique_contest_name_add_contest(self):
        """
        Tests whether the contest fails addition when a contest does not have a 
        unique name.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        start_date = timezone.make_aware(datetime.datetime(2018, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2018, 12, 31))
        response = c.post(reverse('contest-list'),
                          content_type='application/json',
                          data=json.dumps({'name': 'Contest Base',
                                           'start_date': start_date.isoformat(),
                                           'end_date': end_date.isoformat()}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Contest.objects.filter(name='Contest Base').count(), 1)
        self.assertTrue('name' in response.json())


    def test_successful_add_beer(self):
        """
        Tests whether a new beer can be added to a contest.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        beer_filter = Beer.objects.filter(name='Beer 1')
        self.assertEqual(beer_filter.count(), 1)
        beer = beer_filter.get()
        self.assertEqual(beer.brewery, 'Brewery 1')
        cbeer_filter = Contest_Beer.objects.filter(beer=beer)
        self.assertEqual(cbeer_filter.count(), 1)
        contest_beer = cbeer_filter.get()
        self.assertEqual(contest_beer.contest.id, contest.id)
        self.assertEqual(contest_beer.point_value, 2)
        self.assertEqual(response.json()['id'], contest_beer.id)


    def test_not_contest_runner_add_beer(self):
        """
        Tests whether a non-contest runner is prevented from adding a beer.
        """
        c = Client()
        self.assertTrue(c.login(username='user1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Beer.objects.filter(name='Beer 1').count(), 0)
        self.assertEqual(Contest_Beer.objects.filter(contest=contest).count(), 0)


    @unittest.skip("Allowing editing of active contests")
    def test_active_add_beer(self):
        """
        Tests whether a contest runner is prevented from adding a beer to an
        active contest.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        contest.active = True
        contest.save()
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Beer.objects.filter(name='Beer 1').count(), 0)
        self.assertIn('non_field_errors', response.json())


    def test_nonunique_add_beer(self):
        """
        Tests whether a beer fails to be added to a contest based on non-unique
        Untappd URLs
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        beer_filter = Beer.objects.filter(name='Beer 1')
        self.assertEqual(beer_filter.count(), 1)
        beer = beer_filter.get()
        self.assertEqual(beer.brewery, 'Brewery 1')
        cbeer_filter = Contest_Beer.objects.filter(beer=beer)
        self.assertEqual(cbeer_filter.count(), 1)
        contest_beer = cbeer_filter.get()
        self.assertEqual(contest_beer.contest.id, contest.id)
        self.assertEqual(contest_beer.point_value, 2)
        self.assertEqual(response.json()['id'], contest_beer.id)
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.json())

    def test_successful_delete_beer(self):
        """
        Tests whether a beer can be deleted successfully
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        beer = Beer.objects.create_beer('Beer 1', 'Brewery 1')
        contest = Contest.objects.get(name='Contest Base')
        contest_beer = contest.add_beer(beer)
        cb_id = contest_beer.id
        beer_id = beer.id
        response = c.delete(reverse('contest-beer-detail',
                                    kwargs={'contest_id': contest.id,
                                            'contest_beer_id': cb_id}),
                            content_type='application/json',
                            HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Contest_Beer.objects.filter(id=cb_id).exists())
        self.assertFalse(Beer.objects.filter(id=beer_id).exists())

    def test_non_runner_delete_beer(self):
        """
        Tests whether a beer does not get deleted if a non-runner tries to delete it
        """
        c = Client()
        beer = Beer.objects.create_beer('Beer 1', 'Brewery 1')
        contest = Contest.objects.get(name='Contest Base')
        contest_beer = contest.add_beer(beer)
        cb_id = contest_beer.id
        beer_id = beer.id
        response = c.delete(reverse('contest-beer-detail',
                                    kwargs={'contest_id': contest.id,
                                            'contest_beer_id': cb_id}),
                            content_type='application/json',
                            HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Contest_Beer.objects.filter(id=cb_id).exists())
        self.assertTrue(Beer.objects.filter(id=beer_id).exists())

    def test_successful_add_brewery(self):
        """
        Tests whether a brewery can successfully be added to a contest based.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        response = c.post(reverse('contest-brewery-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/brewery/1',
                                           'location': 'Location 1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        brewery_filter = Brewery.objects.filter(name='Brewery 1')
        self.assertEqual(brewery_filter.count(), 1)
        brewery = brewery_filter.get()
        self.assertEqual(brewery.untappd_url, 'https://untappd.com/brewery/1')
        self.assertEqual(brewery.location, 'Location 1')
        cbrewery_filter = Contest_Brewery.objects.filter(brewery=brewery)
        self.assertEqual(cbrewery_filter.count(), 1)
        contest_brewery = cbrewery_filter.get()
        self.assertEqual(contest_brewery.contest.id, contest.id)
        self.assertEqual(contest_brewery.point_value, 2)
        self.assertEqual(response.json()['id'], contest_brewery.id)
 
    def test_nonunique_add_brewery(self):
        """
        Tests whether a brewery fails to be added to a contest based on non-unique
        Untappd URLs
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        response = c.post(reverse('contest-brewery-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/brewery/1',
                                           'location': 'Location 1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        brewery_filter = Brewery.objects.filter(name='Brewery 1')
        self.assertEqual(brewery_filter.count(), 1)
        brewery = brewery_filter.get()
        self.assertEqual(brewery.untappd_url, 'https://untappd.com/brewery/1')
        self.assertEqual(brewery.location, 'Location 1')
        cbrewery_filter = Contest_Brewery.objects.filter(brewery=brewery)
        self.assertEqual(cbrewery_filter.count(), 1)
        contest_brewery = cbrewery_filter.get()
        self.assertEqual(contest_brewery.contest.id, contest.id)
        self.assertEqual(contest_brewery.point_value, 2)
        self.assertEqual(response.json()['id'], contest_brewery.id)
        response = c.post(reverse('contest-brewery-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/brewery/1',
                                           'location': 'Location 1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.json())
        brewery_filter = Brewery.objects.filter(name='Brewery 1')
        self.assertEqual(brewery_filter.count(), 1)
 

    @unittest.skip("Allowing editing of active contests")
    def test_active_add_brewery(self):
        """
        Tests whether a contest runner is prevented from adding a brewery to an
        active contest.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        contest.active = True
        contest.save()
        response = c.post(reverse('contest-brewery-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/brewery/1',
                                           'location': 'Location 1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Brewery.objects.filter(name='Brewery 1').count(), 0)
        self.assertIn('non_field_errors', response.json())
 
    def test_not_contest_runner_add_brewery(self):
        """
        Tests whether a non-contest runner is prevented from adding a brewery.
        """
        c = Client()
        self.assertTrue(c.login(username='user1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        contest.active = True
        contest.save()
        response = c.post(reverse('contest-brewery-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/brewery/1',
                                           'location': 'Location 1',
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Brewery.objects.filter(name='Brewery 1').count(), 0)
 

    def test_successful_add_challenge_by_runner(self):
        """
        Tests whether a contest runner can add a challenge
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        challenger_url = reverse('contest-player-detail', 
                                 kwargs={'contest_id': contest.id, 
                                         'username': 'runner1'})
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'challenger': challenger_url,
                                           'challenge_point_value': 12,
                                           'max_point_loss': 12,
                                           'challenge_point_loss': 3,
                                           'point_value': 3}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        beer_filter = Beer.objects.filter(name='Beer 1')
        self.assertEqual(beer_filter.count(), 1)
        beer = beer_filter.get()
        self.assertEqual(beer.brewery, 'Brewery 1')
        cbeer_filter = Contest_Beer.objects.filter(beer=beer)
        self.assertEqual(cbeer_filter.count(), 1)
        contest_beer = cbeer_filter.get()
        self.assertEqual(contest_beer.contest.id, contest.id)
        self.assertEqual(contest_beer.point_value, 3)
        self.assertIsNotNone(contest_beer.challenger)
        self.assertEqual(contest_beer.challenger.user_name, 'runner1')
        self.assertEqual(contest_beer.challenge_point_value, 12)
        self.assertEqual(contest_beer.max_point_loss, 12)
        self.assertEqual(contest_beer.challenge_point_loss, 3)
        self.assertEqual(response.json()['id'], contest_beer.id)

    def test_successful_add_challenge_for_player_by_runner(self):
        """
        Tests whether a contest runner can add a challenge for another player
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        player = Player.objects.get(user__username='user1')
        contest = Contest.objects.get(name='Contest Base')
        contest.add_player(player)
        challenger_url = reverse('contest-player-detail', 
                                 kwargs={'contest_id': contest.id, 
                                         'username': 'user1'})
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'challenger': challenger_url,
                                           'challenge_point_value': 12,
                                           'max_point_loss': 12,
                                           'challenge_point_loss': 3,
                                           'point_value': 3}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        beer_filter = Beer.objects.filter(name='Beer 1')
        self.assertEqual(beer_filter.count(), 1)
        beer = beer_filter.get()
        self.assertEqual(beer.brewery, 'Brewery 1')
        cbeer_filter = Contest_Beer.objects.filter(beer=beer)
        self.assertEqual(cbeer_filter.count(), 1)
        contest_beer = cbeer_filter.get()
        self.assertEqual(contest_beer.contest.id, contest.id)
        self.assertEqual(contest_beer.point_value, 3)
        self.assertIsNotNone(contest_beer.challenger)
        self.assertEqual(contest_beer.challenger.user_name, 'user1')
        self.assertEqual(contest_beer.challenge_point_value, 12)
        self.assertEqual(contest_beer.max_point_loss, 12)
        self.assertEqual(contest_beer.challenge_point_loss, 3)
        self.assertEqual(response.json()['id'], contest_beer.id)

    def test_successful_add_challenge_by_player(self):
        """
        Tests whether a contest player can add a challenge
        """
        c = Client()
        self.assertTrue(c.login(username='user1', password='password1%'))
        player = Player.objects.get(user__username='user1')
        contest = Contest.objects.get(name='Contest Base')
        contest.add_player(player)
        challenger_url = reverse('contest-player-detail', 
                                 kwargs={'contest_id': contest.id, 
                                         'username': 'user1'})
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'challenger': challenger_url,
                                           'challenge_point_value': 12,
                                           'max_point_loss': 12,
                                           'challenge_point_loss': 3,
                                           'point_value': 3}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        beer_filter = Beer.objects.filter(name='Beer 1')
        self.assertEqual(beer_filter.count(), 1)
        beer = beer_filter.get()
        self.assertEqual(beer.brewery, 'Brewery 1')
        cbeer_filter = Contest_Beer.objects.filter(beer=beer)
        self.assertEqual(cbeer_filter.count(), 1)
        contest_beer = cbeer_filter.get()
        self.assertEqual(contest_beer.contest.id, contest.id)
        self.assertEqual(contest_beer.point_value, 3)
        self.assertIsNotNone(contest_beer.challenger)
        self.assertEqual(contest_beer.challenger.user_name, 'user1')
        self.assertEqual(contest_beer.challenge_point_value, 12)
        self.assertEqual(contest_beer.max_point_loss, 12)
        self.assertEqual(contest_beer.challenge_point_loss, 3)
        self.assertEqual(response.json()['id'], contest_beer.id)

    def test_bad_add_challenge_by_player(self):
        """
        Tests whether a contest player cannot add a challenge if they try to add 
        a challenge for another player
        """
        c = Client()
        self.assertTrue(c.login(username='user1', password='password1%'))
        player = Player.objects.get(user__username='user1')
        contest = Contest.objects.get(name='Contest Base')
        contest.add_player(player)
        contest.add_player(Player.objects.get(user__username='user2'))
        challenger_url = reverse('contest-player-detail', 
                                 kwargs={'contest_id': contest.id, 
                                         'username': 'user2'})
        response = c.post(reverse('contest-beer-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'Beer 1',
                                           'brewery': 'Brewery 1',
                                           'untappd_url': 'https://untappd.com/beer/1',
                                           'brewery_url': 'https://untappd.com/brewery/1',
                                           'challenger': challenger_url,
                                           'challenge_point_value': 12,
                                           'max_point_loss': 12,
                                           'challenge_point_loss': 3,
                                           'point_value': 3}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_active_add_challenge(self):
        """
        Tests whether a player or contest runner cannot add a challenge to an 
        active contest.
        """
        pass

    def test_success_add_bonus(self):
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        response = c.post(reverse('contest-bonus-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'bonus1',
                                           'description': 'First Bonus',
                                           'hashtags': ['tag1', 'tag2'],
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bonus_filter = Contest_Bonus.objects.filter(contest=contest, name='bonus1')
        self.assertEqual(bonus_filter.count(), 1)
        bonus = bonus_filter.get()
        self.assertEqual(bonus.description, 'First Bonus')
        self.assertEqual(bonus.hashtags, ['tag1','tag2'])
        self.assertEqual(bonus.point_value, 2)
        get = c.get(reverse('contest-bonus-detail', 
                            kwargs={'contest_id': contest.id,
                                    'contest_bonus_id': bonus.id}),
                    HTTP_ACCEPT='application/json',
                    contest_type='application/json')
        obj = json.loads(get.content)
        self.assertEqual(obj['name'], 'bonus1')
        self.assertEqual(obj['description'], 'First Bonus')
        self.assertEqual(obj['point_value'], 2)
        self.assertEqual(len(obj['hashtags']), 2)
        self.assertIn('tag1', obj['hashtags'])
        self.assertIn('tag2', obj['hashtags'])

    def test_failed_duplicate_bonus_hash_tag(self):
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        contest = Contest.objects.get(name='Contest Base')
        response = c.post(reverse('contest-bonus-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'bonus1',
                                           'description': 'First Bonus',
                                           'hashtags': ['tag1', 'tag2'],
                                           'point_value': 2}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bonus_filter = Contest_Bonus.objects.filter(contest=contest, name='bonus1')
        self.assertEqual(bonus_filter.count(), 1)
        bonus = bonus_filter.get()
        self.assertEqual(bonus.description, 'First Bonus')
        self.assertEqual(bonus.hashtags, ['tag1','tag2'])
        self.assertEqual(bonus.point_value, 2)
        response = c.post(reverse('contest-bonus-list', 
                                  kwargs={'contest_id': contest.id}),
                          content_type='application/json',
                          data=json.dumps({'name': 'bonus2',
                                           'description': 'First Bonus',
                                           'hashtags': ['tag2', 'tag3'],
                                           'point_value': 1}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
