import datetime
import json
from django.test import TestCase, override_settings, Client
from django.core.urlresolvers import reverse
from django.utils import timezone
from beers.models import Contest_Player, Unvalidated_Checkin
from beers.models import Contest_Checkin, Contest_Beer, Contest_Brewery

@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class ContestTestCase(TestCase):

    fixtures = ['permissions', 'users', 'contest_tests', 'unvalidated_checkins']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_successful_checkin_validate(self):
        """Logs in as the correct user and validates a beer"""
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))
        uv = Unvalidated_Checkin.objects.get(untappd_title='Unvalidated Checkin 2')
        response = c.post(reverse('update-checkin',
                                  kwargs={'contest_id': 1, 'uv_checkin': uv.id,}),
                          content_type='application/json',
                          data=json.dumps({'validate-beer': 'Validate', 'contest-beer': 1,}),
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
        response = c.post(reverse('update-checkin',
                                  kwargs={'contest_id': 1, 'uv_checkin': uv.id,}),
                          content_type='application/json',
                          data=json.dumps({'remove-beer': 'Remove',}),
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
        response = c.get(reverse('unvalidated-checkins-json',
                                 kwargs={'contest_id': 1}),
                         {'slice_start': 2, 'slice_end': 3})
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
        response = c.get(reverse('unvalidated-checkins-json',
                                 kwargs={'contest_id': 1}),
                         {'slice_start': 3, 'slice_end': 6})
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
        response = c.get(reverse('unvalidated-checkins-json',
                                 kwargs={'contest_id': 1}),
                         {'slice_start': 100, 'slice_end': 105})
        self.assertEqual(response.status_code, 200)
        checkins = json.loads(response.content)
        self.assertEqual(checkins['page_count'], 1)
        self.assertEqual(len(checkins['checkins']), 0)

    def __test_beer_and_brewery_calculations(self, cp, beers, breweries):
        """
        Helper function to iterate through a set of beers for a user to
        drink. It checks the point values for the passed in player and any
        challenger
        """
        beer_points = cp.beer_points
        brewery_points = cp.brewery_points
        challengers = {
            cp.id: {
                'gain': cp.challenge_point_gain,
                'loss': cp.challenge_point_loss,
            }
        }
        for beer in beers:
            # We should only be accumulating points if the beer hasn't already
            # been drunk
            had_prior = Contest_Checkin.objects.filter(contest_player=cp,
                                                       contest_beer=beer).count() > 0
            if beer.challenger and beer.challenger.id not in challengers:
                challengers[beer.challenger.id] = {
                    'gain': beer.challenger.challenge_point_gain,
                    'loss': beer.challenger.challenge_point_loss,
                }
            cp.drink_beer(beer,
                          data={
                              'untapped_checkin': 'https://untappd.com/checkin/beer',
                              'checkin_time': timezone.make_aware(datetime.datetime.now()),
                          })
            if not had_prior:
                if beer.challenger:
                    if beer.challenger.id == cp.id:
                        challengers[beer.challenger.id]['gain'] = challengers[beer.challenger.id]['gain'] + beer.challenge_point_value
                    else:
                        beer_points = beer_points + beer.point_value
                        challengers[beer.challenger.id]['loss'] = challengers[beer.challenger.id]['loss'] + beer.challenge_point_loss
                        if challengers[beer.challenger.id]['loss'] > beer.max_point_loss:
                            challengers[beer.challenger.id]['loss'] = beer.max_point_loss
                else:
                    beer_points = beer_points + beer.point_value
        for brewery in breweries:
            had_prior = Contest_Checkin.objects.filter(contest_player=cp,
                                                       contest_brewery=brewery).count() > 0
            cp.drink_at_brewery(brewery,
                                data={
                                     'untapped_checkin': 'https://untappd.com/checkin/brewery',
                                     'checkin_time': timezone.make_aware(datetime.datetime.now()),
                                 })
            if not had_prior:
                brewery_points = brewery_points + brewery.point_value
        # Test all of these and then run compute_points and rerun the tests
        # compute_points should not change the values`
        self.assertEqual(cp.brewery_points, brewery_points,
                         msg='Cumulative sum of brewery points for {}'.format(cp))
        self.assertEqual(cp.beer_points, beer_points,
                         msg='Cumulative sum of beer points for {}'.format(cp))
        self.assertEqual(cp.challenge_point_gain, challengers[cp.id]['gain'],
                         msg='Cumulative challenge point gain for {}'.format(cp))
        self.assertEqual(cp.challenge_point_loss, challengers[cp.id]['loss'],
                         msg='Cumulative challenge point loss for {}'.format(cp))
        self.assertEqual(cp.total_points,
                         beer_points + brewery_points + challengers[cp.id]['gain'] - challengers[cp.id]['loss'],
                         msg='Cumulative sum of total points for {}'.format(cp))
        for ch_id in challengers.keys():
            challenger = Contest_Player.objects.get(id=ch_id)
            self.assertEqual(challengers[ch_id]['gain'], challenger.challenge_point_gain,
                             msg='Cumulative challenger {} gain against player {}'.format(challenger, cp))
            self.assertEqual(challengers[ch_id]['loss'], challenger.challenge_point_loss,
                             msg='Cumulative challenger {} loss against player {}'.format(challenger, cp))
        cp.compute_points()
        # Testing the compute points computation
        self.assertEqual(cp.brewery_points, brewery_points,
                         msg='Computed sum of brewery points for {}'.format(cp))
        self.assertEqual(cp.beer_points, beer_points,
                         msg='Computed sum of beer points for {}'.format(cp))
        self.assertEqual(cp.challenge_point_gain, challengers[cp.id]['gain'],
                         msg='Computed challenge point gain for {}'.format(cp))
        self.assertEqual(cp.challenge_point_loss, challengers[cp.id]['loss'],
                         msg='Computed challenge point loss for {}'.format(cp))
        self.assertEqual(cp.total_points,
                         beer_points + brewery_points + challengers[cp.id]['gain'] - challengers[cp.id]['loss'],
                         msg='Computed sum of total points for {}'.format(cp))
        for ch_id in challengers.keys():
            challenger = Contest_Player.objects.get(id=ch_id)
            self.assertEqual(challengers[ch_id]['gain'], challenger.challenge_point_gain,
                             msg='Computed challenger {} gain against player {}'.format(challenger, cp))
            self.assertEqual(challengers[ch_id]['loss'], challenger.challenge_point_loss,
                             msg='Computed challenger {} loss against player {}'.format(challenger, cp))

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
