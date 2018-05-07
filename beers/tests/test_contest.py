"""Tests the core contest features and their models"""

import datetime
import json
from django.test import TestCase, override_settings, Client
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from beers.models import Beer, Brewery, Contest, Contest_Player, \
                         Unvalidated_Checkin, Contest_Checkin, Contest_Beer, \
                         Contest_Brewery, Player

@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class ContestTestCase(TestCase):
    """The tests on the contest features"""

    fixtures = ['permissions',
                'users',
                'contest_tests',
                'unvalidated_checkins',
                ]

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_successful_modify_checkin_beer(self):
        """Tests that the API call to modify a checkin works for a beer"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        uv = Unvalidated_Checkin.objects.get(
            untappd_title='Unvalidated Checkin 2')
        response = c.post(reverse('validate-checkin',
                                  kwargs={'contest_id': 1}),
                          content_type='application/json',
                          data=json.dumps({'as_beer': 1,
                                           'checkin': uv.id,
                                           'preserve': False}),
                          HTTP_ACCEPT='application/json')
        q = Contest_Checkin.objects.filter(contest_beer__id=1,
                                           contest_player__id=1)
        self.assertEqual(q.count(), 1)
        checkin = q.get()
        self.assertEqual(checkin.checkin_points, 1)
        self.assertEqual(checkin.untappd_checkin, uv.untappd_checkin)
        self.assertEqual(checkin.contest_player.beer_count, 1)
        self.assertEqual(checkin.contest_player.beer_points, 1)
        self.assertEqual(Unvalidated_Checkin.objects.filter(
            untappd_title='Unvalidated Checkin 2').count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_successful_modify_checkin_challenge(self):
        """Tests that the API call to modify a checkin works for a beer"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        uv = Unvalidated_Checkin.objects.get(
            untappd_title='Unvalidated Checkin 8')
        response = c.post(reverse('validate-checkin',
                                  kwargs={'contest_id': 1}),
                          content_type='application/json',
                          data=json.dumps({'as_beer': 6,
                                           'checkin': uv.id,
                                           'preserve': False}),
                          HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        q = Contest_Checkin.objects.filter(contest_beer__id=6,
                                           contest_player=uv.contest_player)
        self.assertEqual(q.count(), 1)
        checkin = q.get()
        self.assertEqual(checkin.checkin_points, 12)
        self.assertEqual(checkin.untappd_checkin, uv.untappd_checkin)
        self.assertEqual(checkin.contest_player.beer_count, 1)
        self.assertEqual(checkin.contest_player.beer_points, 0)
        self.assertEqual(checkin.contest_player.challenge_point_gain, 12)
        self.assertEqual(Unvalidated_Checkin.objects.filter(
            untappd_title='Unvalidated Checkin 8').count(), 0)

    def test_successful_modify_checkin_brewery(self):
        """Tests that the API call to modify a checkin works for a brewery"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        uv = Unvalidated_Checkin.objects.get(
            untappd_title='Unvalidated Checkin 2')
        response = c.post(reverse('validate-checkin',
                                  kwargs={'contest_id': 1}),
                          content_type='application/json',
                          data=json.dumps({'as_brewery': 1,
                                           'checkin': uv.id,
                                           'preserve': False}),
                          HTTP_ACCEPT='application/json')
        brewery = Contest_Brewery.objects.get(id=1)
        q = Contest_Checkin.objects.filter(contest_brewery=brewery,
                                           contest_player__id=1)
        self.assertEqual(q.count(), 1)
        checkin = q.get()
        self.assertEqual(checkin.checkin_points, brewery.point_value)
        self.assertEqual(checkin.untappd_checkin,
                         'https://example.com/unvalidated_2')
        self.assertEqual(checkin.contest_player.beer_count, 0)
        self.assertEqual(checkin.contest_player.beer_points, 0)
        self.assertEqual(checkin.contest_player.brewery_points,
                         brewery.point_value)
        self.assertEqual(Unvalidated_Checkin.objects.filter(
            untappd_title='Unvalidated Checkin 2').count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_successful_modify_checkin_bonus_with_beer(self):
        """Tests that the API call to modify a checkin works for a beer with a bonus"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        uv = Unvalidated_Checkin.objects.get(
            untappd_title='Unvalidated Checkin 2')
        response = c.post(reverse('validate-checkin',
                                  kwargs={'contest_id': 1}),
                          content_type='application/json',
                          data=json.dumps({'as_beer': 1,
                                           'bonuses': [ 'pun' ],
                                           'checkin': uv.id,
                                           'preserve': False}),
                          HTTP_ACCEPT='application/json')
        q = Contest_Checkin.objects.filter(contest_player__id=1)
        self.assertEqual(q.count(), 2)
        self.assertEqual(q.filter(tx_type='BO').count(), 1)
        self.assertEqual(q.filter(tx_type='BE').count(), 1)
        checkin = q.filter(tx_type='BE').get()
        self.assertEqual(checkin.checkin_points, 1)
        self.assertEqual(checkin.untappd_checkin, uv.untappd_checkin)
        self.assertEqual(checkin.contest_player.beer_count, 1)
        self.assertEqual(checkin.contest_player.beer_points, 1)
        self.assertEqual(checkin.contest_player.bonus_points, 1)
        self.assertEqual(Unvalidated_Checkin.objects.filter(
            untappd_title='Unvalidated Checkin 2').count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_successful_modify_checkin_bonus(self):
        """
        Tests that the API call to modify a checkin works for bonus with no beer
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        uv = Unvalidated_Checkin.objects.get(
            untappd_title='Unvalidated Checkin 2')
        response = c.post(reverse('validate-checkin',
                                  kwargs={'contest_id': 1}),
                          content_type='application/json',
                          data=json.dumps({'bonuses': [ 'pun' ],
                                           'checkin': uv.id,
                                           'preserve': False}),
                          HTTP_ACCEPT='application/json')
        q = Contest_Checkin.objects.filter(contest_player__id=1)
        self.assertEqual(q.count(), 1)
        checkin = q.get()
        self.assertEqual(checkin.checkin_points, 1)
        self.assertEqual(checkin.tx_type, 'BO')
        self.assertEqual(checkin.untappd_checkin, uv.untappd_checkin)
        self.assertEqual(checkin.contest_player.beer_count, 0)
        self.assertEqual(checkin.contest_player.beer_points, 0)
        self.assertEqual(checkin.contest_player.bonus_points, 1)
        self.assertEqual(Unvalidated_Checkin.objects.filter(
            untappd_title='Unvalidated Checkin 2').count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_dismiss_unvalidated_checkin(self):
        """Tests whether a delete of a checkin works"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.delete(reverse('unvalidated-checkin-detail',
                                    kwargs={'id': 1, }),
                            HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Unvalidated_Checkin.DoesNotExist):
            Unvalidated_Checkin.objects.get(id=1)

    def test_unauthenticated_dismiss_unvalidated_checkin(self):
        """Tests whether an attempt of delete of a checkin
        by a player who is not the contest runner fails"""
        c = Client()
        self.assertTrue(c.login(username='user1', password='password1%'))
        response = c.delete(reverse('unvalidated-checkin-detail',
                                    kwargs={'id': 1, }),
                            HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)
        uv = Unvalidated_Checkin.objects.get(id=1)
        self.assertIsNotNone(uv)

    def test_unvalidated_api_single(self):
        """Tests if the JSON API gets the right values for a single request"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.get(reverse('unvalidated-checkin-detail',
                                 kwargs={'id': 3}))
        self.assertEqual(response.status_code, 200)
        checkin = json.loads(response.content)
        self.assertTrue(checkin['url'].endswith(
             reverse('unvalidated-checkin-detail', kwargs={'id': 3})))
        self.assertEqual(checkin['player'], 'user1')
        self.assertEqual(checkin['brewery'], 'Brewery 3')
        self.assertEqual(checkin['beer'], 'Beer 3')

    def test_unvalidated_api_many(self):
        """Tests if the JSON API gets the right values for multiple results"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.get(reverse('unvalidated-checkin-list',
                                 kwargs={'contest_id': 1}),
                         {'limit': 3, 'offset': 3, 'sort': 'id',})
        self.assertEqual(response.status_code, 200)
        checkins = json.loads(response.content)
        self.assertEqual(len(checkins['results']), 3)
        cid = 4
        for checkin in checkins['results']:
            self.assertTrue(checkin['url'].endswith( 
                 reverse('unvalidated-checkin-detail', kwargs={'id': cid})))
            self.assertEqual(checkin['player'], 'user1')
            self.assertEqual(checkin['brewery'], 'Brewery {}'.format(cid))
            self.assertEqual(checkin['beer'], 'Beer {}'.format(cid))
            cid = cid + 1

    def test_unvalidated_api_past_end(self):
        """
        Tests if the JSON API returns nothing when the slice goes beyond
        the end of the page
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.get(reverse('unvalidated-checkin-list',
                                 kwargs={'contest_id': 1}),
                         {'limit': 25, 'offset': 100})
        self.assertEqual(response.status_code, 200)
        checkins = json.loads(response.content)
        self.assertEqual(len(checkins['results']), 0)

    def test_unvalidated_api_possibles_only(self):
        """
        Tests if the results get filtered by possibles.
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        response = c.get(reverse('unvalidated-checkin-list',
                                 kwargs={'contest_id': 1}),
                         {'possibles_only': 'true'})
        self.assertEqual(response.status_code, 200)
        checkins = json.loads(response.content)
        for checkin in checkins['results']:
            uv = Unvalidated_Checkin.objects.get(id=int(checkin['id']))
            self.assertTrue(uv.has_possibles or uv.possible_bonuses is not None)
            self.assertEqual(uv.contest_player.user_name, checkin['player'])
            self.assertEqual(uv.brewery, checkin['brewery'])
            self.assertEqual(uv.beer, checkin['beer'])
        self.assertEqual(len(checkins['results']), 
             Unvalidated_Checkin.objects.filter(contest_player__contest__id=1).filter(
                    Q(has_possibles=True) | Q(possible_bonuses__isnull=False)).count())

    def __test_beer_and_brewery_calculations(self, cp, beers, breweries, bonuses=[]):
        """
        Helper function to iterate through a set of beers for a user to
        drink. It checks the point values for the passed in player and any
        challenger
        """
        beer_points = cp.beer_points
        brewery_points = cp.brewery_points
        bonus_points = cp.bonus_points
        challengers = {
            cp.id: {
                'gain': cp.challenge_point_gain,
                'loss': cp.challenge_point_loss,
            }
        }
        for beer in beers:
            # We should only be accumulating points if the beer hasn't already
            # been drunk
            had_prior = Contest_Checkin.objects.filter(
                contest_player=cp,
                contest_beer=beer).count() > 0
            if beer.challenger and beer.challenger.id not in challengers:
                challengers[beer.challenger.id] = {
                    'gain': beer.challenger.challenge_point_gain,
                    'loss': beer.challenger.challenge_point_loss,
                }
            cp.drink_beer(
                beer,
                data={
                    'untappd_checkin': 'https://untappd.com/checkin/beer',
                    'checkin_time': timezone.make_aware(datetime.datetime.now()),
                })
            if not had_prior:
                if beer.challenger:
                    if beer.challenger.id == cp.id:
                        challengers[beer.challenger.id]['gain'] = (
                            challengers[beer.challenger.id]['gain']
                            + beer.challenge_point_value)
                    else:
                        beer_points = beer_points + beer.point_value
                        challengers[beer.challenger.id]['loss'] = (
                            challengers[beer.challenger.id]['loss']
                            + beer.challenge_point_loss)
                        if challengers[beer.challenger.id]['loss'] > beer.max_point_loss:
                            challengers[beer.challenger.id]['loss'] = beer.max_point_loss
                else:
                    beer_points = beer_points + beer.point_value
        for brewery in breweries:
            had_prior = Contest_Checkin.objects.filter(contest_player=cp,
                                                       contest_brewery=brewery).count() > 0
            cp.drink_at_brewery(
                brewery,
                data={
                    'untappd_checkin': 'https://untappd.com/checkin/brewery',
                    'checkin_time': timezone.make_aware(datetime.datetime.now()),
                })
            if not had_prior:
                brewery_points = brewery_points + brewery.point_value
        for bonus in bonuses:
            # No limit on how many times you can accumlate bonus points
            cp.drink_bonus(
                bonus,
                data={
                    'untappd_checkin': 'https://untappd.com/checkin/bonus',
                    'checkin_time': timezone.make_aware(datetime.datetime.now()),
                })
            bonus_points = bonus_points + 1
        # Test all of these and then run compute_points and rerun the tests
        # compute_points should not change the values`
        self.assertEqual(
            cp.brewery_points,
            brewery_points,
            msg='Cumulative sum of brewery points for {}'.format(cp))
        self.assertEqual(
            cp.beer_points, beer_points,
            msg='Cumulative sum of beer points for {}'.format(cp))
        self.assertEqual(
            cp.challenge_point_gain,
            challengers[cp.id]['gain'],
            msg='Cumulative challenge point gain for {}'.format(cp))
        self.assertEqual(
            cp.challenge_point_loss,
            challengers[cp.id]['loss'],
            msg='Cumulative challenge point loss for {}'.format(cp))
        self.assertEqual(
            cp.bonus_points,
            bonus_points,
            msg='Cumulative bonus points for {}'.format(cp))
        self.assertEqual(
            cp.total_points,
            (beer_points
             + brewery_points
             + bonus_points
             + challengers[cp.id]['gain']
             - challengers[cp.id]['loss']),
            msg='Cumulative sum of total points for {}'.format(cp))
        for ch_id in challengers.keys():
            challenger = Contest_Player.objects.get(id=ch_id)
            self.assertEqual(
                challengers[ch_id]['gain'],
                challenger.challenge_point_gain,
                msg='Cumulative challenger {} gain against player {}'
                    .format(challenger, cp))
            self.assertEqual(
                challengers[ch_id]['loss'],
                challenger.challenge_point_loss,
                msg='Cumulative challenger {} loss against player {}'
                    .format(challenger, cp))
        cp.compute_points()
        # Testing the compute points computation
        self.assertEqual(
            cp.brewery_points,
            brewery_points,
            msg='Computed sum of brewery points for {}'.format(cp))
        self.assertEqual(
            cp.beer_points,
            beer_points,
            msg='Computed sum of beer points for {}'.format(cp))
        self.assertEqual(
            cp.challenge_point_gain,
            challengers[cp.id]['gain'],
            msg='Computed challenge point gain for {}'.format(cp))
        self.assertEqual(
            cp.challenge_point_loss,
            challengers[cp.id]['loss'],
            msg='Computed challenge point loss for {}'.format(cp))
        self.assertEqual(
            cp.bonus_points,
            bonus_points,
            msg='Computed bonus points for {}'.format(cp))
        self.assertEqual(
            cp.total_points,
            (beer_points
             + brewery_points
             + bonus_points
             + challengers[cp.id]['gain']
             - challengers[cp.id]['loss']),
            msg='Computed sum of total points for {}'.format(cp))
        for ch_id in challengers.keys():
            challenger = Contest_Player.objects.get(id=ch_id)
            self.assertEqual(
                challengers[ch_id]['gain'],
                challenger.challenge_point_gain,
                msg='Computed challenger {} gain against player {}'
                    .format(challenger, cp))
            self.assertEqual(
                challengers[ch_id]['loss'],
                challenger.challenge_point_loss,
                msg='Computed challenger {} loss against player {}'
                    .format(challenger, cp))

    def test_beers_and_brewery_point_computation(self):
        """
        This tests that a non-zero and non-one count of beers and breweries sum correctly
        """
        cp = Contest_Player.objects.get(id=1)
        beers = [Contest_Beer.objects.get(id=1),
                 Contest_Beer.objects.get(id=2),
                 Contest_Beer.objects.get(id=3),
                 ]
        breweries = [Contest_Brewery.objects.get(id=1),
                     Contest_Brewery.objects.get(id=2),]
        self.__test_beer_and_brewery_calculations(cp, beers, breweries)

    def test_beers_and_no_brewery_point_computation(self):
        """
        This tests that non-zero beers and zero breweries sum correctly
        """
        cp = Contest_Player.objects.get(id=1)
        beers = [Contest_Beer.objects.get(id=1),
                 Contest_Beer.objects.get(id=2),
                 Contest_Beer.objects.get(id=3),]
        breweries = []
        self.__test_beer_and_brewery_calculations(cp, beers, breweries)

    def test_no_beers_and_brewery_point_computation(self):
        """
        This tests that zero beers and non-zero breweries sum correctly
        """
        cp = Contest_Player.objects.get(id=1)
        beers = []
        breweries = [Contest_Brewery.objects.get(id=1),
                     Contest_Brewery.objects.get(id=2),]
        self.__test_beer_and_brewery_calculations(cp, beers, breweries)

    def test_one_beer_and_brewery_point_computation(self):
        """
        This tests that one beer and one brewery sum correctly
        """
        cp = Contest_Player.objects.get(id=1)
        beers = [Contest_Beer.objects.get(id=1),]
        breweries = [Contest_Brewery.objects.get(id=1),]
        self.__test_beer_and_brewery_calculations(cp, beers, breweries)

    def _unvalidated_checkin_from_beer(self, contest_player, beer,
                                       checkin_time=None):
        """
        Creates a new unvalidaated checkin which matches the beer.
        """
        if checkin_time is None:
            checkin_time = timezone.make_aware(datetime.datetime.now())
        uv = Unvalidated_Checkin.objects.create_checkin(contest_player,
                                                        '{}'.format(beer),
                                                        beer.name,
                                                        beer.brewery,
                                                        'https://untappd.com',
                                                        checkin_time
                                                       )
        return uv

    def test_challenge_points_for_challenger(self):
        """
        This tests that a challenger gets the usual point value for drinking
        their own beer.
        """
        challenge = Contest_Beer.objects.get(id=6)
        challenger = challenge.challenger
        self.__test_beer_and_brewery_calculations(challenger, [challenge], [])

    def test_challenge_points_for_player(self):
        """
        This tests that player gets the usual point value for drinking
        a challenger's beers and that the challenger gets a loss
        """
        challenge = Contest_Beer.objects.get(id=6)
        player = Contest_Player.objects.get(id=1)
        self.__test_beer_and_brewery_calculations(player, [challenge], [])

    def test_challenge_points_for_multiple_players(self):
        """
        This tests that a challenger loses the right amount of points for
        multiple people drinking their beer
        """
        challenge = Contest_Beer.objects.get(id=6)
        player = Contest_Player.objects.get(id=1)
        self.__test_beer_and_brewery_calculations(player, [challenge], [])
        player = Contest_Player.objects.get(id=2)
        self.__test_beer_and_brewery_calculations(player, [challenge], [])
        self.__test_beer_and_brewery_calculations(challenge.challenger, [challenge], [])

    def test_bonus_points(self):
        """
        This tests that bonus points can be gained by a player.
        """
        player = Contest_Player.objects.get(id=1)
        self.__test_beer_and_brewery_calculations(player, [], [], ['pun'])

    def test_multiple_bonus_points(self):
        """
        This tests that bonus points can be gained by a player.
        """
        player = Contest_Player.objects.get(id=1)
        self.__test_beer_and_brewery_calculations(player, [], [], ['pun', 'ballgame'])

    def test_same_bonus_points(self):
        """
        This tests that bonus points can be gained by a player.
        """
        player = Contest_Player.objects.get(id=1)
        self.__test_beer_and_brewery_calculations(player, [], [], ['pun', 'pun'])

    def test_beer_and_bonus_points(self):
        """
        This tests that bonus points can be gained by a player.
        """
        player = Contest_Player.objects.get(id=1)
        beer = Contest_Beer.objects.get(id=1)

    def test_mix_of_points(self):
        """
        This tests that bonus points can be gained by a player.
        """
        player = Contest_Player.objects.get(id=1)
        beer1 = Contest_Beer.objects.get(id=1)
        beer2 = Contest_Beer.objects.get(id=2)
        brewery = Contest_Brewery.objects.get(id=1)
        challenge = Contest_Beer.objects.get(id=6)
        brewery = Contest_Brewery.objects.get(id=1)
        self.__test_beer_and_brewery_calculations(player, 
                                                  [beer1, beer2, challenge], 
                                                  [brewery], 
                                                  ['pun', 'ballgame'])

    def test_unvalidated_beer_list(self):
        """
        This tests that a call to Contest.beers() works with an unvalidated
        call. It should return the beers associated with a contest in
        alphabetical order. We add a couple beers into the list that are
        out of alpha order to test this explicitly.

        The beer list should include challenge beers.
        """
        beer_a = Beer.objects.create_beer('Aaaa', 'AA Brewery')
        beer_z = Beer.objects.create_beer('Zzzz', 'ZZ Brewery')
        contest = Contest.objects.get(id=1)
        contest.add_beer(beer_z)
        contest.add_beer(beer_a)
        beers = contest.beers()
        self.assertEqual(beers.count(), 9)
        self.assertEqual(beers[0].beer_name, 'Aaaa')
        self.assertEqual(beers[1].beer_name, 'Beer 1')
        self.assertEqual(beers[2].beer_name, 'Beer 2')
        self.assertEqual(beers[3].beer_name, 'Beer 3')
        self.assertEqual(beers[4].beer_name, 'Beer 4')
        self.assertEqual(beers[5].beer_name, 'Beer 5')
        self.assertEqual(beers[6].beer_name, 'Challenge Beer 6')
        self.assertEqual(beers[7].beer_name, 'Challenge Beer 7')
        self.assertEqual(beers[8].beer_name, 'Zzzz')

    def test_validated_beer_list(self):
        """
        This tests that a call to Contest.beers() works with an validated
        call. It should return the beers associated with a contest in
        alphabetical order with a checked_into value for those beers
        that the play has drunk. We add a couple beers into the list that
        are out of alpha order to test this explicitly.

        The beer list should include challenge beers.
        """
        beer_a = Beer.objects.create_beer('Aaaa', 'AA Brewery')
        beer_z = Beer.objects.create_beer('Zzzz', 'ZZ Brewery')
        contest = Contest.objects.get(id=1)
        contest.add_beer(beer_z)
        contest.add_beer(beer_a)
        player = Player.objects.get(id=1)
        contest_player = Contest_Player.objects.get(player=player)
        beer3 = Contest_Beer.objects.get(beer_name='Beer 3')
        challenge_beer6 = Contest_Beer.objects.get(beer_name='Challenge Beer 6')
        contest_player.drink_beer(beer3,
            data={
                'untapped_checkin': 'https://untappd.com/checkin/beer',
                'checkin_time': timezone.make_aware(datetime.datetime.now()),
            })
        contest_player.drink_beer(challenge_beer6,
            data={
                'untapped_checkin': 'https://untappd.com/checkin/beer',
                'checkin_time': timezone.make_aware(datetime.datetime.now()),
            })
        contest_player.drink_beer(challenge_beer6)
        beers = contest.beers(player)
        self.assertEqual(beers.count(), 9)
        self.assertEqual(beers[0].beer_name, 'Aaaa')
        self.assertFalse(beers[0].checked_into)
        self.assertEqual(beers[1].beer_name, 'Beer 1')
        self.assertFalse(beers[1].checked_into)
        self.assertEqual(beers[2].beer_name, 'Beer 2')
        self.assertFalse(beers[2].checked_into)
        self.assertEqual(beers[3].beer_name, 'Beer 3')
        self.assertTrue(beers[3].checked_into)
        self.assertEqual(beers[4].beer_name, 'Beer 4')
        self.assertFalse(beers[4].checked_into)
        self.assertEqual(beers[5].beer_name, 'Beer 5')
        self.assertFalse(beers[5].checked_into)
        self.assertEqual(beers[6].beer_name, 'Challenge Beer 6')
        self.assertTrue(beers[6].checked_into)
        self.assertEqual(beers[7].beer_name, 'Challenge Beer 7')
        self.assertFalse(beers[7].checked_into)
        self.assertEqual(beers[8].beer_name, 'Zzzz')
        self.assertFalse(beers[8].checked_into)

    def test_unvalidated_brewery_list(self):
        """
        This tests that a call to Contest.breweries() works with an unvalidated
        call. It should return the breweries associated with a contest in
        alphabetical order. We add a couple breweries into the list that are
        out of alpha order to test this explicitly.
        """
        brewery_a = Brewery.objects.create_brewery('Aaaa Brewery', '1234')
        brewery_z = Brewery.objects.create_brewery('Zzzz Brewery', '5678')
        contest = Contest.objects.get(id=1)
        contest.add_brewery(brewery_z)
        contest.add_brewery(brewery_a)
        breweries = contest.breweries()
        self.assertEqual(breweries.count(), 7)
        self.assertEqual(breweries[0].brewery_name, 'Aaaa Brewery')
        self.assertEqual(breweries[1].brewery_name, 'Brewery 1')
        self.assertEqual(breweries[2].brewery_name, 'Brewery 2')
        self.assertEqual(breweries[3].brewery_name, 'Brewery 3')
        self.assertEqual(breweries[4].brewery_name, 'Brewery 4')
        self.assertEqual(breweries[5].brewery_name, 'Brewery 5')
        self.assertEqual(breweries[6].brewery_name, 'Zzzz Brewery')

    def test_validated_brewery_list(self):
        """
        This tests that a call to Contest.beers() works with an validated
        call. It should return the beers associated with a contest in
        alphabetical order with a checked_into value for those beers
        that the play has drunk. We add a couple beers into the list that
        are out of alpha order to test this explicitly.

        The beer list should include challenge beers.
        """
        brewery_a = Brewery.objects.create_brewery('Aaaa Brewery', '1234')
        brewery_z = Brewery.objects.create_brewery('Zzzz Brewery', '5678')
        contest = Contest.objects.get(id=1)
        contest.add_brewery(brewery_z)
        contest.add_brewery(brewery_a)
        player = Player.objects.get(id=1)
        contest_player = Contest_Player.objects.get(player=player)
        brewery3 = Contest_Brewery.objects.get(brewery_name='Brewery 3')
        brewery5 = Contest_Brewery.objects.get(brewery_name='Brewery 5')
        contest_player.drink_at_brewery(brewery3,
            data={
                'untapped_checkin': 'https://untappd.com/checkin/beer',
                'checkin_time': timezone.make_aware(datetime.datetime.now()),
            })
        contest_player.drink_at_brewery(brewery5,
            data={
                'untapped_checkin': 'https://untappd.com/checkin/beer',
                'checkin_time': timezone.make_aware(datetime.datetime.now()),
            })

        breweries = contest.breweries(player)
        self.assertEqual(breweries.count(), 7)
        self.assertEqual(breweries[0].brewery_name, 'Aaaa Brewery')
        self.assertFalse(breweries[0].checked_into)
        self.assertEqual(breweries[1].brewery_name, 'Brewery 1')
        self.assertFalse(breweries[1].checked_into)
        self.assertEqual(breweries[2].brewery_name, 'Brewery 2')
        self.assertFalse(breweries[2].checked_into)
        self.assertEqual(breweries[3].brewery_name, 'Brewery 3')
        self.assertTrue(breweries[3].checked_into)
        self.assertEqual(breweries[4].brewery_name, 'Brewery 4')
        self.assertFalse(breweries[4].checked_into)
        self.assertEqual(breweries[5].brewery_name, 'Brewery 5')
        self.assertTrue(breweries[5].checked_into)
        self.assertEqual(breweries[6].brewery_name, 'Zzzz Brewery')
        self.assertFalse(breweries[6].checked_into)
